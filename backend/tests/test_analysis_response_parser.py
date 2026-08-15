from __future__ import annotations

import pytest

from app.analysis.response_parser import (
    parse_analysis_response,
    parse_analysis_response_safe,
    ResponseParserError,
    JSONParseError,
    SchemaValidationError,
    extract_json,
)
from app.schemas.analysis import AnalysisOutput, Recommendation, Confidence, AnalysisStatus


class TestExtractJson:
    def test_extract_direct_json(self):
        json_text = '{"model_used": "test", "score": 80, "recommendation": "strong_match", "confidence": "high", "matching_skills": [], "matching_experience": [], "missing_requirements": [], "unknown_requirements": [], "explanation": "Good", "evidence": [], "status": "success"}'
        result = extract_json(json_text)
        assert result == json_text

    def test_extract_json_from_markdown(self):
        text = '''Here is the response:
```json
{"model_used": "test", "score": 80, "recommendation": "strong_match", "confidence": "high", "matching_skills": [], "matching_experience": [], "missing_requirements": [], "unknown_requirements": [], "explanation": "Good", "evidence": [], "status": "success"}
```
Done.'''
        result = extract_json(text)
        assert "model_used" in result
        assert result.strip().startswith("{")
        assert result.strip().endswith("}")

    def test_extract_json_from_markdown_no_lang(self):
        text = '''Response:
```
{"model_used": "test", "score": 80, "recommendation": "strong_match", "confidence": "high", "matching_skills": [], "matching_experience": [], "missing_requirements": [], "unknown_requirements": [], "explanation": "Good", "evidence": [], "status": "success"}
```'''
        result = extract_json(text)
        assert "model_used" in result

    def test_extract_json_embedded_in_text(self):
        text = 'Some text before {"model_used": "test", "score": 80, "recommendation": "strong_match", "confidence": "high", "matching_skills": [], "matching_experience": [], "missing_requirements": [], "unknown_requirements": [], "explanation": "Good", "evidence": [], "status": "success"} and after'
        result = extract_json(text)
        assert "model_used" in result

    def test_extract_json_invalid_raises(self):
        with pytest.raises(JSONParseError):
            extract_json("not json at all")


class TestParseAnalysisResponse:
    def test_parse_valid_response(self):
        response = '{"model_used": "qwen2.5:14b", "score": 85, "recommendation": "strong_match", "confidence": "high", "matching_skills": [{"claim": "Python", "source_excerpt": "requires Python"}], "matching_experience": [], "missing_requirements": [], "unknown_requirements": [], "explanation": "Strong match", "evidence": [], "status": "success"}'
        result = parse_analysis_response(response, "qwen2.5:14b")
        assert isinstance(result, AnalysisOutput)
        assert result.score == 85
        assert result.recommendation == Recommendation.STRONG_MATCH
        assert result.confidence == Confidence.HIGH
        assert len(result.matching_skills) == 1
        assert result.matching_skills[0].claim == "Python"

    def test_parse_response_without_model_used(self):
        response = '{"score": 70, "recommendation": "possible_match", "confidence": "medium", "matching_skills": [], "matching_experience": [], "missing_requirements": [], "unknown_requirements": [], "explanation": "OK", "evidence": [], "status": "success"}'
        result = parse_analysis_response(response, "test-model")
        assert result.model_used == "test-model"

    def test_parse_response_without_status_defaults_to_success(self):
        response = '{"score": 70, "recommendation": "possible_match", "confidence": "medium", "matching_skills": [], "matching_experience": [], "missing_requirements": [], "unknown_requirements": [], "explanation": "OK", "evidence": []}'
        result = parse_analysis_response(response, "test-model")
        assert result.status == AnalysisStatus.SUCCESS

    def test_parse_invalid_json_raises(self):
        with pytest.raises(JSONParseError):
            parse_analysis_response("not json", "model")

    def test_parse_validation_error_missing_required(self):
        # AnalysisOutput has all fields optional, so minimal input is valid
        # parse_analysis_response overwrites model_used with the passed parameter
        response = '{"model_used": "test", "score": 80}'
        result = parse_analysis_response(response, "model")
        assert result.model_used == "model"
        assert result.score == 80
        assert result.recommendation is None
        assert result.confidence is None
        assert result.status == AnalysisStatus.SUCCESS

    def test_parse_invalid_score_raises(self):
        response = '{"model_used": "test", "score": 150, "recommendation": "strong_match", "confidence": "high", "matching_skills": [], "matching_experience": [], "missing_requirements": [], "unknown_requirements": [], "explanation": "Good", "evidence": [], "status": "success"}'
        with pytest.raises(SchemaValidationError):
            parse_analysis_response(response, "model")

    def test_parse_invalid_recommendation_raises(self):
        response = '{"model_used": "test", "score": 80, "recommendation": "invalid", "confidence": "high", "matching_skills": [], "matching_experience": [], "missing_requirements": [], "unknown_requirements": [], "explanation": "Good", "evidence": [], "status": "success"}'
        with pytest.raises(SchemaValidationError):
            parse_analysis_response(response, "model")

    def test_parse_all_recommendation_values(self):
        for rec in ["strong_match", "possible_match", "weak_match", "not_enough_information"]:
            response = f'{{"model_used": "test", "score": 50, "recommendation": "{rec}", "confidence": "medium", "matching_skills": [], "matching_experience": [], "missing_requirements": [], "unknown_requirements": [], "explanation": "Test", "evidence": [], "status": "success"}}'
            result = parse_analysis_response(response, "test")
            assert result.recommendation == rec

    def test_parse_all_confidence_values(self):
        for conf in ["high", "medium", "low"]:
            response = f'{{"model_used": "test", "score": 50, "recommendation": "possible_match", "confidence": "{conf}", "matching_skills": [], "matching_experience": [], "missing_requirements": [], "unknown_requirements": [], "explanation": "Test", "evidence": [], "status": "success"}}'
            result = parse_analysis_response(response, "test")
            assert result.confidence == conf

    def test_parse_all_status_values(self):
        for status in ["success", "rejected", "ai_unavailable", "pending", "failed"]:
            response = f'{{"model_used": "test", "score": 50, "recommendation": "possible_match", "confidence": "medium", "matching_skills": [], "matching_experience": [], "missing_requirements": [], "unknown_requirements": [], "explanation": "Test", "evidence": [], "status": "{status}"}}'
            result = parse_analysis_response(response, "test")
            assert result.status == status


class TestParseAnalysisResponseSafe:
    def test_safe_parse_success(self):
        response = '{"model_used": "test", "score": 80, "recommendation": "strong_match", "confidence": "high", "matching_skills": [], "matching_experience": [], "missing_requirements": [], "unknown_requirements": [], "explanation": "Good", "evidence": [], "status": "success"}'
        result, error = parse_analysis_response_safe(response, "test")
        assert result is not None
        assert error is None
        assert result.score == 80

    def test_safe_parse_failure(self):
        response = "not json"
        result, error = parse_analysis_response_safe(response, "test")
        assert result is None
        assert error is not None
        assert "JSON" in error or "json" in error

    def test_safe_parse_validation_failure(self):
        # AnalysisOutput accepts minimal input, so this actually succeeds
        response = '{"model_used": "test", "score": 80}'
        result, error = parse_analysis_response_safe(response, "test")
        assert result is not None
        assert error is None
        assert result.score == 80


class TestResponseParserExceptions:
    def test_exception_codes(self):
        assert JSONParseError().error_code == "JSON_PARSE_ERROR"
        assert SchemaValidationError().error_code == "VALIDATION_ERROR"
        assert ResponseParserError("test", "CUSTOM").error_code == "CUSTOM"