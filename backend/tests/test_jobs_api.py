from __future__ import annotations

import pytest

from app.main import app
from app.db import get_database
from app.repositories import JobRepository, AIAnalysisRepository
from app.models import JobCreate, AIAnalysisCreate


@pytest.fixture
async def job_repo(test_db):
    return JobRepository(test_db)


@pytest.fixture
async def analysis_repo(test_db):
    return AIAnalysisRepository(test_db)


class TestListJobsScoreConsistency:
    """Regression test: GET /jobs must return the persisted jobs.score/recommendation
    (set by the scoring/recommendation pipeline), not silently overwrite them with the
    raw ai_analyses row's score, as a prior version of this endpoint did."""

    @pytest.mark.asyncio
    async def test_persisted_score_and_recommendation_survive_listing(self, test_db, job_repo, analysis_repo):
        from httpx import ASGITransport, AsyncClient

        job = await job_repo.create_job(
            JobCreate(adzuna_id="job-consistency", title="Security Engineer", passed_prefilter=True)
        )

        # The raw AI analysis has a different score than the final computed job score,
        # exactly the situation that exposed the bug (they should never be conflated).
        await analysis_repo.create_analysis(
            AIAnalysisCreate(
                job_id=job.id,
                model_used="qwen2.5:14b",
                score=40,
                recommendation="weak_match",
                confidence="low",
                status="success",
            )
        )
        await job_repo.update_scoring(
            job.id,
            {
                "score": 91,
                "recommendation": "strong_match",
                "confidence": "high",
                "skills_score": 88,
                "experience_score": 95,
                "requirements_score": 90,
                "location_score": 100,
                "salary_score": 85,
            },
        )
        await job_repo.update_recommendation(
            job.id,
            {
                "recommendation_category": "strong_match",
                "recommendation_priority": "high",
                "recommendation_primary_reason": "skills_match",
                "recommendation_secondary_reasons": [],
                "recommendation_explanation": "Strong fit",
                "recommendation_missing_skills": [],
                "recommendation_strengths": [],
                "recommendation_concerns": [],
                "recommendation_action_items": [],
            },
        )

        async def override_get_db():
            return test_db

        app.dependency_overrides[get_database] = override_get_db
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/jobs")

            assert response.status_code == 200
            listed = response.json()
            assert len(listed) == 1
            assert listed[0]["score"] == 91
            assert listed[0]["recommendation"] == "strong_match"
            assert listed[0]["recommendation_category"] == "strong_match"
        finally:
            app.dependency_overrides.clear()
