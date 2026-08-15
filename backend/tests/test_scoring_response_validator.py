from __future__ import annotations

import pytest

from app.scoring.response_validator import (
    validate_scoring_output,
    validate_scoring_output_safe,
    create_fallback_scoring,
    ScoringValidationError,
)
from app.schemas.scoring import ScoringOutput, ScoringConfig, ScoringWeights, Recommendation, Confidence, AnalysisStatus
from app.schemas.analysis import EvidenceItem


class TestValidateScoringOutput:
    def setup_method(self):
        self.config = ScoringConfig()

    def test_valid_output_passes(self):
        output = ScoringOutput(
            model_used="gpt-4",
            score=85,
            recommendation=Recommendation.STRONG_MATCH,
            confidence=Confidence.HIGH,
            skills_score=90,
            experience_score=80,
            requirements_score=70,
            location_score=95,
            salary_score=85,
            explanation="Excellent match",
            evidence=[],
            status=AnalysisStatus.SUCCESS,
        )
        result = validate_scoring_output(output, self.config)
        assert result.score == 85
        assert result.recommendation == Recommendation.STRONG_MATCH

    def test_fixes_recommendation_from_score(self):
        output = ScoringOutput(
            model_used="gpt-4",
            score=85,
            recommendation=Recommendation.POSSIBLE_MATCH,  # Wrong for 85
            confidence=Confidence.HIGH,
            skills_score=90,
            experience_score=80,
            requirements_score=70,
            location_score=95,
            salary_score=85,
            explanation="Excellent match",
            evidence=[],
            status=AnalysisStatus.SUCCESS,
        )
        result = validate_scoring_output(output, self.config)
        assert result.recommendation == Recommendation.STRONG_MATCH

    def test_fixes_recommendation_weak_match(self):
        output = ScoringOutput(
            model_used="gpt-4",
            score=30,
            recommendation=Recommendation.POSSIBLE_MATCH,  # Wrong for 30
            confidence=Confidence.HIGH,
            skills_score=40,
            experience_score=30,
            requirements_score=20,
            location_score=50,
            salary_score=40,
            explanation="Weak match",
            evidence=[],
            status=AnalysisStatus.SUCCESS,
        )
        result = validate_scoring_output(output, self.config)
        assert result.recommendation == Recommendation.WEAK_MATCH

    def test_fixes_recommendation_not_enough_info(self):
        output = ScoringOutput(
            model_used="gpt-4",
            score=10,
            recommendation=Recommendation.WEAK_MATCH,  # Wrong for 10
            confidence=Confidence.HIGH,
            skills_score=10,
            experience_score=10,
            requirements_score=10,
            location_score=10,
            salary_score=10,
            explanation="Not enough info",
            evidence=[],
            status=AnalysisStatus.SUCCESS,
        )
        result = validate_scoring_output(output, self.config)
        assert result.recommendation == Recommendation.NOT_ENOUGH_INFORMATION

    def test_fixes_confidence_low_evidence(self):
        output = ScoringOutput(
            model_used="gpt-4",
            score=85,
            recommendation=Recommendation.STRONG_MATCH,
            confidence=Confidence.HIGH,  # HIGH but no evidence
            skills_score=90,
            experience_score=80,
            requirements_score=70,
            location_score=95,
            salary_score=85,
            explanation="Excellent match",
            evidence=[],  # 0 evidence items, min is 3
            status=AnalysisStatus.SUCCESS,
        )
        result = validate_scoring_output(output, self.config)
        assert result.confidence == Confidence.MEDIUM

    def test_fixes_confidence_high_evidence(self):
        output = ScoringOutput(
            model_used="gpt-4",
            score=50,
            recommendation=Recommendation.POSSIBLE_MATCH,
            confidence=Confidence.LOW,  # LOW but lots of evidence
            skills_score=60,
            experience_score=50,
            requirements_score=40,
            location_score=60,
            salary_score=50,
            explanation="Good match",
            evidence=[
                EvidenceItem(claim="a", source_excerpt="b"),
                EvidenceItem(claim="c", source_excerpt="d"),
                EvidenceItem(claim="e", source_excerpt="f"),
                EvidenceItem(claim="g", source_excerpt="h"),
            ],  # 4 evidence items, min is 3
            status=AnalysisStatus.SUCCESS,
        )
        result = validate_scoring_output(output, self.config)
        assert result.confidence == Confidence.MEDIUM

    def test_fixes_weighted_composite(self):
        # Create output where score doesn't match weighted composite
        output = ScoringOutput(
            model_used="gpt-4",
            score=50,  # Wrong - should be ~80 based on components
            recommendation=Recommendation.STRONG_MATCH,
            confidence=Confidence.HIGH,
            skills_score=90,
            experience_score=80,
            requirements_score=70,
            location_score=95,
            salary_score=85,
            explanation="Excellent match",
            evidence=[],
            status=AnalysisStatus.SUCCESS,
        )
        result = validate_scoring_output(output, self.config)
        # Weighted: 90*0.35 + 80*0.25 + 70*0.20 + 95*0.10 + 85*0.10 = 31.5 + 20 + 14 + 9.5 + 8.5 = 83.5
        assert result.score == 84  # Rounded


class TestValidateScoringOutputSafe:
    def setup_method(self):
        self.config = ScoringConfig()

    def test_safe_validate_success(self):
        output = ScoringOutput(
            model_used="gpt-4",
            score=85,
            recommendation=Recommendation.STRONG_MATCH,
            confidence=Confidence.HIGH,
            skills_score=90,
            experience_score=80,
            requirements_score=70,
            location_score=95,
            salary_score=85,
            explanation="Excellent match",
            evidence=[],
            status=AnalysisStatus.SUCCESS,
        )
        result, error = validate_scoring_output_safe(output, self.config)
        assert result is not None
        assert error is None

    def test_safe_validate_failure(self):
        output = ScoringOutput(
            model_used="gpt-4",
            score=85,
            recommendation=Recommendation.POSSIBLE_MATCH,  # Wrong for score
            confidence=Confidence.HIGH,
            skills_score=90,
            experience_score=80,
            requirements_score=70,
            location_score=95,
            salary_score=85,
            explanation="Excellent match",
            evidence=[],
            status=AnalysisStatus.SUCCESS,
        )
        # This should pass validation (just fixes recommendation)
        result, error = validate_scoring_output_safe(output, self.config)
        assert result is not None
        assert error is None
        assert result.recommendation == Recommendation.STRONG_MATCH


class TestCreateFallbackScoring:
    def test_create_fallback(self):
        config = ScoringConfig()
        result = create_fallback_scoring("gpt-4", "API error", config)

        assert result.model_used == "gpt-4"
        assert result.score == 0
        assert result.recommendation == Recommendation.NOT_ENOUGH_INFORMATION
        assert result.confidence == Confidence.LOW
        assert result.status == AnalysisStatus.FAILED
        assert "API error" in result.explanation


class TestScoringValidationError:
    def test_error_code(self):
        error = ScoringValidationError("Test error")
        assert error.error_code == "SCORING_VALIDATION_ERROR"

    def test_custom_error_code(self):
        error = ScoringValidationError("Test error", "CUSTOM_CODE")
        assert error.error_code == "CUSTOM_CODE"