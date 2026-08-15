from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.analysis.service import AnalysisService, get_analysis_service
from app.analysis.ollama_client import OllamaClient, OllamaResponseError
from app.schemas.analysis import AnalysisInput, AnalysisJobInput, AnalysisProfileInput, AnalysisOutput, AnalysisStatus


class TestAnalysisService:
    @pytest.mark.asyncio
    async def test_analyze_job_success(self):
        client = OllamaClient()
        mock_client = AsyncMock()
        client._client = mock_client
        client._client.is_closed = False

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": '{"model_used": "qwen2.5:14b", "score": 85, "recommendation": "strong_match", "confidence": "high", "matching_skills": [], "matching_experience": [], "missing_requirements": [], "unknown_requirements": [], "explanation": "Excellent match", "evidence": [], "status": "success"}'
        }
        mock_client.post.return_value = mock_response

        service = AnalysisService(client=client)
        job = AnalysisJobInput(id=1, adzuna_id="test-1", title="Python Engineer")
        profile = AnalysisProfileInput(technical_skills=["Python"])
        input_data = AnalysisInput(job=job, profile=profile)

        result = await service.analyze_job(input_data)

        assert isinstance(result, AnalysisOutput)
        assert result.score == 85
        assert result.recommendation == "strong_match"
        await service.close()

    @pytest.mark.asyncio
    async def test_analyze_job_failed_returns_failed_output(self):
        client = OllamaClient()
        mock_client = AsyncMock()
        client._client = mock_client
        client._client.is_closed = False

        # Always return invalid JSON
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "not valid json"}
        mock_client.post.return_value = mock_response

        service = AnalysisService(client=client)
        job = AnalysisJobInput(id=1, adzuna_id="test-1", title="Engineer")
        profile = AnalysisProfileInput()
        input_data = AnalysisInput(job=job, profile=profile)

        result = await service.analyze_job(input_data)

        assert result.status == AnalysisStatus.FAILED
        assert "Failed after" in result.explanation
        await service.close()

    @pytest.mark.asyncio
    async def test_health_check(self):
        client = OllamaClient()
        mock_client = AsyncMock()
        client._client = mock_client
        client._client.is_closed = False

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "qwen2.5:14b-instruct-q4_K_M"}]}
        mock_client.get.return_value = mock_response

        service = AnalysisService(client=client)
        result = await service.health_check()

        assert result is True
        await service.close()

    @pytest.mark.asyncio
    async def test_health_check_model_not_found(self):
        client = OllamaClient()
        mock_client = AsyncMock()
        client._client = mock_client
        client._client.is_closed = False

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "other-model"}]}
        mock_client.get.return_value = mock_response

        service = AnalysisService(client=client)
        result = await service.health_check()

        assert result is False
        await service.close()

    @pytest.mark.asyncio
    async def test_close(self):
        client = OllamaClient()
        mock_client = AsyncMock()
        mock_client.is_closed = False
        client._client = mock_client

        service = AnalysisService(client=client)
        await service.close()

        mock_client.aclose.assert_called_once()


class TestGetAnalysisService:
    @pytest.mark.asyncio
    async def test_get_analysis_service(self):
        service = await get_analysis_service()
        assert isinstance(service, AnalysisService)
        await service.close()