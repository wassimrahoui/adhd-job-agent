from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.analysis.service import AnalysisService
from app.analysis.ollama_client import OllamaClient
from app.repositories.analysis import AIAnalysisRepository
from app.schemas.analysis import AnalysisInput, AnalysisJobInput, AnalysisProfileInput, AnalysisOutput, AnalysisStatus
from app.models.analysis import AIAnalysis


class TestAnalysisServicePersist:
    @pytest.mark.asyncio
    async def test_analyze_and_persist_success(self):
        client = OllamaClient()
        mock_client = AsyncMock()
        client._client = mock_client
        client._client.is_closed = False

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": '{"model_used": "qwen2.5:14b", "score": 85, "recommendation": "strong_match", "confidence": "high", "matching_skills": [{"claim": "Python", "source_excerpt": "requires Python"}], "matching_experience": [], "missing_requirements": [], "unknown_requirements": [], "explanation": "Excellent match", "evidence": [], "status": "success"}'
        }
        mock_client.post.return_value = mock_response

        # Mock repository
        repo = AsyncMock(spec=AIAnalysisRepository)
        created_analysis = AIAnalysis(
            id=1,
            job_id=1,
            model_used="qwen2.5:14b",
            score=85,
            recommendation="strong_match",
            confidence="high",
            matching_skills=[],
            matching_experience=[],
            missing_requirements=[],
            unknown_requirements=[],
            explanation="Excellent match",
            evidence=[],
            status="success",
            created_at="2024-01-01T00:00:00",
        )
        repo.create_analysis.return_value = created_analysis

        service = AnalysisService(client=client, repo=repo)
        job = AnalysisJobInput(id=1, adzuna_id="test-1", title="Python Engineer")
        profile = AnalysisProfileInput(technical_skills=["Python"])
        input_data = AnalysisInput(job=job, profile=profile)

        result = await service.analyze_and_persist(input_data)

        assert isinstance(result, AnalysisOutput)
        assert result.score == 85
        repo.create_analysis.assert_called_once()
        await service.close()

    @pytest.mark.asyncio
    async def test_analyze_and_persist_without_repo(self):
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

        service = AnalysisService(client=client)  # No repo
        job = AnalysisJobInput(id=1, adzuna_id="test-1", title="Python Engineer")
        profile = AnalysisProfileInput(technical_skills=["Python"])
        input_data = AnalysisInput(job=job, profile=profile)

        result = await service.analyze_and_persist(input_data)

        assert isinstance(result, AnalysisOutput)
        assert result.score == 85
        await service.close()

    @pytest.mark.asyncio
    async def test_analyze_and_persist_failed_analysis(self):
        client = OllamaClient()
        mock_client = AsyncMock()
        client._client = mock_client
        client._client.is_closed = False

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "not valid json"}
        mock_client.post.return_value = mock_response

        repo = AsyncMock(spec=AIAnalysisRepository)
        created_analysis = AIAnalysis(
            id=1,
            job_id=1,
            model_used="qwen2.5:14b",
            score=None,
            recommendation=None,
            confidence=None,
            matching_skills=[],
            matching_experience=[],
            missing_requirements=[],
            unknown_requirements=[],
            explanation="Failed after 3 attempts. Last error: ...",
            evidence=[],
            status="failed",
            created_at="2024-01-01T00:00:00",
        )
        repo.create_analysis.return_value = created_analysis

        service = AnalysisService(client=client, repo=repo)
        job = AnalysisJobInput(id=1, adzuna_id="test-1", title="Engineer")
        profile = AnalysisProfileInput()
        input_data = AnalysisInput(job=job, profile=profile)

        result = await service.analyze_and_persist(input_data)

        assert result.status == AnalysisStatus.FAILED
        repo.create_analysis.assert_called_once()
        # Check that failed status was passed to repo
        call_args = repo.create_analysis.call_args[0][0]
        assert call_args.status == "failed"
        await service.close()

    @pytest.mark.asyncio
    async def test_set_repository(self):
        client = OllamaClient()
        service = AnalysisService(client=client)
        assert service._repo is None

        repo = AsyncMock(spec=AIAnalysisRepository)
        service.set_repository(repo)
        assert service._repo is repo
        await service.close()