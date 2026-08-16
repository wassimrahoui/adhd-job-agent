from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.processing.service import ProcessingService, get_processing_service
from app.schemas.processing import ProcessingJobState
from app.schemas.analysis import AnalysisOutput, AnalysisStatus
from app.schemas.scoring import ScoringOutput
from app.schemas.recommendation import RecommendationOutput, RecommendationCategory, RecommendationPriority, RecommendationReason
from app.models.job import Job
from app.models.profile import Profile


def make_job(job_id: int = 1, recommendation_category=None) -> Job:
    return Job(
        id=job_id,
        adzuna_id=f"adzuna-{job_id}",
        title="Backend Engineer",
        company="Acme",
        location="Berlin",
        skills=["Python"],
        passed_prefilter=True,
        recommendation_category=recommendation_category,
    )


def make_profile() -> Profile:
    return Profile(technical_skills=["Python"], desired_roles=["Backend Engineer"])


def make_analysis_output() -> AnalysisOutput:
    return AnalysisOutput(
        model_used="qwen2.5:14b",
        score=80,
        recommendation="strong_match",
        confidence="high",
        explanation="Good match",
        status=AnalysisStatus.SUCCESS,
    )


def make_scoring_output() -> ScoringOutput:
    return ScoringOutput(
        model_used="evidence-based",
        score=80,
        recommendation="strong_match",
        confidence="high",
        skills_score=80,
        experience_score=80,
        requirements_score=80,
        location_score=80,
        salary_score=80,
        explanation="Good match",
        status=AnalysisStatus.SUCCESS,
    )


def make_recommendation_output() -> RecommendationOutput:
    return RecommendationOutput(
        category=RecommendationCategory.STRONG_MATCH,
        priority=RecommendationPriority.HIGH,
        primary_reason=RecommendationReason.SKILLS_MATCH,
        explanation="Strong match",
        confidence="high",
        score=80,
    )


def make_service() -> tuple[ProcessingService, AsyncMock, AsyncMock, AsyncMock]:
    analysis_service = AsyncMock()
    analysis_service.analyze_and_persist.return_value = make_analysis_output()
    analysis_service.set_repository = MagicMock()

    scoring_service = AsyncMock()
    scoring_service.score_and_persist.return_value = make_scoring_output()
    scoring_service.set_job_repository = MagicMock()

    recommendation_service = AsyncMock()
    recommendation_service.generate_and_persist_recommendation.return_value = make_recommendation_output()
    recommendation_service.set_job_repository = MagicMock()

    service = ProcessingService(
        analysis_service=analysis_service,
        scoring_service=scoring_service,
        recommendation_service=recommendation_service,
    )
    return service, analysis_service, scoring_service, recommendation_service


class TestProcessJob:
    @pytest.mark.asyncio
    async def test_success_runs_all_three_stages_in_order(self):
        service, analysis_service, scoring_service, recommendation_service = make_service()
        job = make_job()
        profile = make_profile()

        result = await service.process_job(job, profile)

        assert result.state == ProcessingJobState.COMPLETED
        assert result.error is None
        analysis_service.analyze_and_persist.assert_awaited_once()
        scoring_service.score_and_persist.assert_awaited_once()
        recommendation_service.generate_and_persist_recommendation.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_analysis_failure_isolated_and_reported(self):
        service, analysis_service, scoring_service, recommendation_service = make_service()
        analysis_service.analyze_and_persist.side_effect = RuntimeError("ollama down")

        result = await service.process_job(make_job(), make_profile())

        assert result.state == ProcessingJobState.FAILED
        assert "analyzing" in result.error
        scoring_service.score_and_persist.assert_not_awaited()
        recommendation_service.generate_and_persist_recommendation.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_scoring_failure_isolated_and_reported(self):
        service, analysis_service, scoring_service, recommendation_service = make_service()
        scoring_service.score_and_persist.side_effect = RuntimeError("scoring exploded")

        result = await service.process_job(make_job(), make_profile())

        assert result.state == ProcessingJobState.FAILED
        assert "scoring" in result.error
        analysis_service.analyze_and_persist.assert_awaited_once()
        recommendation_service.generate_and_persist_recommendation.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_recommendation_failure_isolated_and_reported(self):
        service, analysis_service, scoring_service, recommendation_service = make_service()
        recommendation_service.generate_and_persist_recommendation.side_effect = RuntimeError("bad data")

        result = await service.process_job(make_job(), make_profile())

        assert result.state == ProcessingJobState.FAILED
        assert "recommending" in result.error


class TestProcessJobs:
    @pytest.mark.asyncio
    async def test_processes_jobs_sequentially(self):
        service, analysis_service, scoring_service, recommendation_service = make_service()
        jobs = [make_job(1), make_job(2), make_job(3)]

        response = await service.process_jobs(jobs, make_profile(), skip_existing=False)

        assert response.jobs_total == 3
        assert response.processed == 3
        assert response.failed == 0
        assert response.skipped == 0
        assert analysis_service.analyze_and_persist.await_count == 3

    @pytest.mark.asyncio
    async def test_one_job_failure_does_not_abort_batch(self):
        service, analysis_service, scoring_service, recommendation_service = make_service()
        # Second job's analysis fails, first and third succeed.
        analysis_service.analyze_and_persist.side_effect = [
            make_analysis_output(),
            RuntimeError("transient failure"),
            make_analysis_output(),
        ]
        jobs = [make_job(1), make_job(2), make_job(3)]

        response = await service.process_jobs(jobs, make_profile(), skip_existing=False)

        assert response.jobs_total == 3
        assert response.processed == 2
        assert response.failed == 1
        states = {r.job_id: r.state for r in response.results}
        assert states[1] == ProcessingJobState.COMPLETED
        assert states[2] == ProcessingJobState.FAILED
        assert states[3] == ProcessingJobState.COMPLETED

    @pytest.mark.asyncio
    async def test_skip_existing_skips_jobs_with_recommendation(self):
        service, analysis_service, scoring_service, recommendation_service = make_service()
        jobs = [make_job(1, recommendation_category="strong_match"), make_job(2)]

        response = await service.process_jobs(jobs, make_profile(), skip_existing=True)

        assert response.skipped == 1
        assert response.processed == 1
        analysis_service.analyze_and_persist.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_empty_job_list(self):
        service, *_ = make_service()

        response = await service.process_jobs([], make_profile())

        assert response.jobs_total == 0
        assert response.results == []


class TestSetRepositories:
    def test_wires_repositories_into_sub_services(self):
        service, analysis_service, scoring_service, recommendation_service = make_service()
        job_repo = MagicMock()
        analysis_repo = MagicMock()

        service.set_repositories(job_repo, analysis_repo)

        analysis_service.set_repository.assert_called_once_with(analysis_repo)
        scoring_service.set_job_repository.assert_called_once_with(job_repo)
        recommendation_service.set_job_repository.assert_called_once_with(job_repo)


class TestGetProcessingService:
    @pytest.mark.asyncio
    async def test_returns_processing_service_instance(self):
        service = await get_processing_service()
        assert isinstance(service, ProcessingService)
