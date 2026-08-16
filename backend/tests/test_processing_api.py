from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.db import get_database
from app.repositories import ProfileRepository, JobRepository, AIAnalysisRepository
from app.models import ProfileCreate, JobCreate
from app.processing import ProcessingService, get_processing_service
from app.analysis.service import AnalysisService
from app.analysis.ollama_client import OllamaClient


async def _make_analysis_service_with_mocked_ollama() -> AnalysisService:
    """Build an AnalysisService whose Ollama client is mocked to always succeed,
    so the pipeline test never depends on a real local Ollama daemon."""
    client = OllamaClient()
    mock_http = AsyncMock()
    client._client = mock_http
    client._client.is_closed = False

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": (
            '{"model_used": "qwen2.5:14b", "score": 85, "recommendation": "strong_match", '
            '"confidence": "high", "matching_skills": [{"claim": "Python", "source_excerpt": '
            '"requires Python"}], "matching_experience": [], "missing_requirements": [], '
            '"unknown_requirements": [], "explanation": "Strong Python match", "evidence": [], '
            '"status": "success"}'
        )
    }
    mock_http.post.return_value = mock_response

    return AnalysisService(client=client)


@pytest.fixture
async def profile_repo(test_db):
    return ProfileRepository(test_db)


@pytest.fixture
async def job_repo(test_db):
    return JobRepository(test_db)


@pytest.fixture
async def analysis_repo(test_db):
    return AIAnalysisRepository(test_db)


class TestProcessingRunEndpoint:
    @pytest.mark.asyncio
    async def test_no_profile_returns_404(self, test_db, profile_repo, job_repo, analysis_repo):
        from httpx import ASGITransport, AsyncClient

        async def override_get_db():
            return test_db

        app.dependency_overrides[get_database] = override_get_db

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/processing/run", json={})

            assert response.status_code == 404
            assert response.json()["detail"]["error_code"] == "PROFILE_NOT_FOUND"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_full_pipeline_runs_analysis_scoring_recommendation(
        self, test_db, profile_repo, job_repo, analysis_repo
    ):
        from httpx import ASGITransport, AsyncClient

        await profile_repo.upsert_profile(
            ProfileCreate(
                technical_skills=["Python", "FastAPI"],
                desired_roles=["Backend Engineer"],
                relevance_threshold=30,
            )
        )

        job1 = await job_repo.create_job(
            JobCreate(
                adzuna_id="job-1",
                title="Backend Engineer",
                company="Acme",
                location="Berlin",
                description="Python backend role",
                skills=["Python"],
                passed_prefilter=True,
            )
        )
        job2 = await job_repo.create_job(
            JobCreate(
                adzuna_id="job-2",
                title="Backend Developer",
                company="Globex",
                location="Munich",
                description="Another Python role",
                skills=["Python", "FastAPI"],
                passed_prefilter=True,
            )
        )

        analysis_service = await _make_analysis_service_with_mocked_ollama()
        processing_service = ProcessingService(analysis_service=analysis_service)

        async def override_get_db():
            return test_db

        async def override_get_processing_service():
            return processing_service

        app.dependency_overrides[get_database] = override_get_db
        app.dependency_overrides[get_processing_service] = override_get_processing_service

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/processing/run",
                    json={"only_passed": True, "limit": 10, "skip_existing": True},
                )

            assert response.status_code == 200
            body = response.json()
            assert body["jobs_total"] == 2
            assert body["processed"] == 2
            assert body["failed"] == 0
            assert body["skipped"] == 0
            assert {r["state"] for r in body["results"]} == {"completed"}

            updated1 = await job_repo.get_job(job1.id)
            updated2 = await job_repo.get_job(job2.id)
            assert updated1.score is not None
            assert updated1.recommendation_category is not None
            assert updated2.score is not None
            assert updated2.recommendation_category is not None

            latest_analysis = await analysis_repo.get_latest_analysis_for_job(job1.id)
            assert latest_analysis is not None
            assert latest_analysis.status == "success"
        finally:
            app.dependency_overrides.clear()
            await analysis_service.close()

    @pytest.mark.asyncio
    async def test_skip_existing_avoids_reprocessing(self, test_db, profile_repo, job_repo, analysis_repo):
        from httpx import ASGITransport, AsyncClient

        await profile_repo.upsert_profile(ProfileCreate(technical_skills=["Python"]))

        job = await job_repo.create_job(
            JobCreate(
                adzuna_id="job-already-done",
                title="Backend Engineer",
                passed_prefilter=True,
            )
        )
        await job_repo.update_recommendation(
            job.id,
            {
                "recommendation_category": "strong_match",
                "recommendation_priority": "high",
                "recommendation_primary_reason": "skills_match",
                "recommendation_secondary_reasons": [],
                "recommendation_explanation": "already processed",
                "recommendation_missing_skills": [],
                "recommendation_strengths": [],
                "recommendation_concerns": [],
                "recommendation_action_items": [],
            },
        )

        analysis_service = await _make_analysis_service_with_mocked_ollama()
        processing_service = ProcessingService(analysis_service=analysis_service)

        async def override_get_db():
            return test_db

        async def override_get_processing_service():
            return processing_service

        app.dependency_overrides[get_database] = override_get_db
        app.dependency_overrides[get_processing_service] = override_get_processing_service

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/processing/run",
                    json={"only_passed": True, "limit": 10, "skip_existing": True},
                )

            assert response.status_code == 200
            body = response.json()
            assert body["jobs_total"] == 1
            assert body["skipped"] == 1
            assert body["processed"] == 0
        finally:
            app.dependency_overrides.clear()
            await analysis_service.close()
