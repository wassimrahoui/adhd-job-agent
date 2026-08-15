from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.analysis.invalid_output_handler import InvalidOutputHandler, analyze_job_with_retry
from app.analysis.ollama_client import OllamaClient, OllamaResponseError
from app.schemas.analysis import AnalysisInput, AnalysisJobInput, AnalysisProfileInput, AnalysisOutput, AnalysisStatus


class TestInvalidOutputHandler:
    def setup_method(self):
        self.client = OllamaClient()
        self.mock_client = AsyncMock()
        self.client._client = self.mock_client
        self.client._client.is_closed = False
        self.handler = InvalidOutputHandler(self.client, max_retries=2, retry_delay=0.01)

    @pytest.mark.asyncio
    async def test_analyze_success_first_attempt(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": '{"model_used": "test-model", "score": 80, "recommendation": "strong_match", "confidence": "high", "matching_skills": [], "matching_experience": [], "missing_requirements": [], "unknown_requirements": [], "explanation": "Good match", "evidence": [], "status": "success"}'
        }
        self.mock_client.post.return_value = mock_response

        job = AnalysisJobInput(id=1, adzuna_id="test-1", title="Engineer")
        profile = AnalysisProfileInput()
        input_data = AnalysisInput(job=job, profile=profile)

        result = await self.handler.analyze_with_retry(input_data, "test-model")

        assert isinstance(result, AnalysisOutput)
        assert result.score == 80
        assert result.recommendation == "strong_match"
        assert self.mock_client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_analyze_success_after_retry(self):
        # First call returns invalid JSON, second succeeds
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {"response": "not valid json"}

        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "response": '{"model_used": "test-model", "score": 70, "recommendation": "possible_match", "confidence": "medium", "matching_skills": [], "matching_experience": [], "missing_requirements": [], "unknown_requirements": [], "explanation": "OK match", "evidence": [], "status": "success"}'
        }

        self.mock_client.post.side_effect = [mock_response1, mock_response2]

        job = AnalysisJobInput(id=1, adzuna_id="test-1", title="Engineer")
        profile = AnalysisProfileInput()
        input_data = AnalysisInput(job=job, profile=profile)

        result = await self.handler.analyze_with_retry(input_data, "test-model")

        assert isinstance(result, AnalysisOutput)
        assert result.score == 70
        assert self.mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_analyze_all_retries_fail_returns_failed(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "not valid json"}
        self.mock_client.post.return_value = mock_response

        job = AnalysisJobInput(id=1, adzuna_id="test-1", title="Engineer")
        profile = AnalysisProfileInput()
        input_data = AnalysisInput(job=job, profile=profile)

        result = await self.handler.analyze_with_retry(input_data, "test-model")

        assert isinstance(result, AnalysisOutput)
        assert result.status == AnalysisStatus.FAILED
        assert "Failed after 3 attempts" in result.explanation
        assert self.mock_client.post.call_count == 3  # initial + 2 retries

    @pytest.mark.asyncio
    async def test_analyze_ollama_error_retries(self):
        self.mock_client.post.side_effect = OllamaResponseError("Server error")

        job = AnalysisJobInput(id=1, adzuna_id="test-1", title="Engineer")
        profile = AnalysisProfileInput()
        input_data = AnalysisInput(job=job, profile=profile)

        result = await self.handler.analyze_with_retry(input_data, "test-model")

        assert result.status == AnalysisStatus.FAILED
        assert "Server error" in result.explanation
        assert self.mock_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_analyze_validation_error_retries(self):
        # Response has invalid score (out of range)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": '{"model_used": "test-model", "score": 150, "recommendation": "strong_match", "confidence": "high", "matching_skills": [], "matching_experience": [], "missing_requirements": [], "unknown_requirements": [], "explanation": "Good", "evidence": [], "status": "success"}'
        }
        self.mock_client.post.return_value = mock_response

        job = AnalysisJobInput(id=1, adzuna_id="test-1", title="Engineer")
        profile = AnalysisProfileInput()
        input_data = AnalysisInput(job=job, profile=profile)

        result = await self.handler.analyze_with_retry(input_data, "test-model")

        assert result.status == AnalysisStatus.FAILED
        assert self.mock_client.post.call_count == 3


class TestAnalyzeJobWithRetryConvenience:
    @pytest.mark.asyncio
    async def test_convenience_function(self):
        client = OllamaClient()
        mock_client = AsyncMock()
        client._client = mock_client
        client._client.is_closed = False

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": '{"model_used": "test-model", "score": 75, "recommendation": "possible_match", "confidence": "medium", "matching_skills": [], "matching_experience": [], "missing_requirements": [], "unknown_requirements": [], "explanation": "Decent", "evidence": [], "status": "success"}'
        }
        mock_client.post.return_value = mock_response

        job = AnalysisJobInput(id=1, adzuna_id="test-1", title="Engineer")
        profile = AnalysisProfileInput()
        input_data = AnalysisInput(job=job, profile=profile)

        result = await analyze_job_with_retry(client, input_data, "test-model", max_retries=1)

        assert result.score == 75