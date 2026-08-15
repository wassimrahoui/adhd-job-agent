from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.scoring.service import ScoringService, get_scoring_service
from app.scoring.cloud_client import CloudScoringClient
from app.schemas.scoring import ScoringInput, ScoringOutput, ScoringConfig, ScoringWeights
from app.schemas.analysis import (
    SkillMatchItem,
    ExperienceMatchItem,
    EvidenceItem,
    AnalysisStatus,
)


class TestScoringService:
    @pytest.mark.asyncio
    async def test_score_job_evidence_based(self):
        client = CloudScoringClient()
        # No API key set, so should use evidence-based
        client.api_key = None

        service = ScoringService(client=client)
        input_data = ScoringInput(
            job_title="Software Engineer",
            matching_skills=[SkillMatchItem(claim="Python", source_excerpt="requires Python")],
            matching_experience=[ExperienceMatchItem(claim="5 years", source_excerpt="5 years")],
        )

        result = await service.score_job(input_data)

        assert isinstance(result, ScoringOutput)
        assert result.score >= 0
        assert result.recommendation is not None
        await service.close()

    @pytest.mark.asyncio
    async def test_score_job_cloud_success(self):
        client = CloudScoringClient()
        client.api_key = "test-key"
        client.base_url = "https://api.test.com/v1"

        mock_client = AsyncMock()
        client._client = mock_client
        client._client.is_closed = False

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"model_used": "gpt-4", "score": 85, "recommendation": "strong_match", "confidence": "high", "skills_score": 90, "experience_score": 80, "requirements_score": 70, "location_score": 95, "salary_score": 85, "explanation": "Excellent match", "evidence": [], "status": "success"}'
                }
            }]
        }
        mock_client.post.return_value = mock_response

        service = ScoringService(client=client)
        input_data = ScoringInput(
            job_title="Software Engineer",
            matching_skills=[SkillMatchItem(claim="Python", source_excerpt="requires Python")],
        )

        result = await service.score_job(input_data)

        assert isinstance(result, ScoringOutput)
        assert result.score == 85
        assert result.recommendation.value == "strong_match"
        await service.close()

    @pytest.mark.asyncio
    async def test_score_job_cloud_fails_fallback(self):
        client = CloudScoringClient()
        client.api_key = "test-key"
        client.base_url = "https://api.test.com/v1"

        mock_client = AsyncMock()
        client._client = mock_client
        client._client.is_closed = False

        mock_client.post.side_effect = Exception("API Error")

        service = ScoringService(client=client)
        input_data = ScoringInput(
            job_title="Software Engineer",
            matching_skills=[SkillMatchItem(claim="Python", source_excerpt="requires Python")],
        )

        result = await service.score_job(input_data)

        # Should fall back to evidence-based
        assert isinstance(result, ScoringOutput)
        assert result.model_used == "evidence-based"
        await service.close()

    @pytest.mark.asyncio
    async def test_score_job_evidence_based_explicit(self):
        client = CloudScoringClient()
        client.api_key = "test-key"

        service = ScoringService(client=client)
        input_data = ScoringInput(
            job_title="Software Engineer",
            matching_skills=[SkillMatchItem(claim="Python", source_excerpt="requires Python")],
        )

        result = await service.score_job_evidence_based(input_data)

        assert isinstance(result, ScoringOutput)
        assert result.model_used == "evidence-based"
        await service.close()

    @pytest.mark.asyncio
    async def test_set_config(self):
        client = CloudScoringClient()
        service = ScoringService(client=client)

        custom_config = ScoringConfig(
            weights=ScoringWeights(skills_weight=0.5)
        )
        service.set_config(custom_config)

        assert service._config.weights.skills_weight == 0.5
        await service.close()

    @pytest.mark.asyncio
    async def test_health_check(self):
        client = CloudScoringClient()
        mock_client = AsyncMock()
        client._client = mock_client
        client._client.is_closed = False

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response

        service = ScoringService(client=client)
        result = await service.health_check()

        assert result is True
        await service.close()

    @pytest.mark.asyncio
    async def test_close(self):
        client = CloudScoringClient()
        mock_client = AsyncMock()
        mock_client.is_closed = False
        client._client = mock_client

        service = ScoringService(client=client)
        await service.close()

        mock_client.aclose.assert_called_once()


class TestGetScoringService:
    @pytest.mark.asyncio
    async def test_get_scoring_service(self):
        service = await get_scoring_service()
        assert isinstance(service, ScoringService)
        await service.close()