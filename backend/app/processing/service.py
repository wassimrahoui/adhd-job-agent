from __future__ import annotations

from typing import Optional, List

from app.analysis.service import AnalysisService
from app.scoring.service import ScoringService
from app.recommendation.service import RecommendationService
from app.models.job import Job
from app.models.profile import Profile
from app.repositories.job import JobRepository
from app.repositories.analysis import AIAnalysisRepository
from app.schemas.analysis import AnalysisInput, AnalysisJobInput, AnalysisProfileInput
from app.schemas.scoring import ScoringInput
from app.schemas.processing import (
    ProcessingJobState,
    ProcessingResponse,
    JobProcessingResult,
)


def _enum_value(value):
    return value.value if hasattr(value, "value") else value


def _build_analysis_job_input(job: Job) -> AnalysisJobInput:
    return AnalysisJobInput(
        id=job.id,
        adzuna_id=job.adzuna_id,
        title=job.title,
        company=job.company,
        location=job.location,
        work_mode=job.work_mode,
        employment_type=job.employment_type,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        salary_is_predicted=job.salary_is_predicted,
        description=job.description,
        requirements=job.requirements,
        skills=job.skills or [],
        redirect_url=job.redirect_url,
        posted_at=job.posted_at,
        raw_evidence=job.raw_evidence or {},
    )


def _build_analysis_profile_input(profile: Profile) -> AnalysisProfileInput:
    return AnalysisProfileInput(
        work_experience=profile.work_experience,
        technical_skills=profile.technical_skills or [],
        networking_experience=profile.networking_experience,
        education=profile.education,
        certifications=profile.certifications or [],
        languages=profile.languages or [],
        desired_roles=profile.desired_roles or [],
        location_preferences=profile.location_preferences or [],
        salary_min=profile.salary_min,
        salary_max=profile.salary_max,
        salary_currency=profile.salary_currency,
        remote_preference=_enum_value(profile.remote_preference),
        experience_level=_enum_value(profile.experience_level),
        excluded_keywords=profile.excluded_keywords or [],
        relevance_threshold=profile.relevance_threshold,
        resume_text=profile.resume_text,
    )


def _build_scoring_input(job: Job, profile: Profile, analysis) -> ScoringInput:
    return ScoringInput(
        matching_skills=analysis.matching_skills,
        matching_experience=analysis.matching_experience,
        missing_requirements=analysis.missing_requirements,
        unknown_requirements=analysis.unknown_requirements,
        evidence=analysis.evidence,
        explanation=analysis.explanation,
        status=analysis.status,
        job_id=job.id,
        job_title=job.title,
        job_company=job.company,
        job_location=job.location,
        job_work_mode=job.work_mode,
        job_salary_min=job.salary_min,
        job_salary_max=job.salary_max,
        job_salary_currency=job.salary_currency,
        job_salary_is_predicted=job.salary_is_predicted,
        job_skills=job.skills or [],
        profile_desired_roles=profile.desired_roles or [],
        profile_location_preferences=profile.location_preferences or [],
        profile_salary_min=profile.salary_min,
        profile_salary_max=profile.salary_max,
        profile_salary_currency=profile.salary_currency,
        profile_remote_preference=_enum_value(profile.remote_preference),
        profile_experience_level=_enum_value(profile.experience_level),
    )


def _build_job_data(job: Job) -> dict:
    return {
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "skills": job.skills or [],
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
    }


def _build_profile_data(profile: Profile) -> dict:
    return {
        "desired_roles": profile.desired_roles or [],
        "location_preferences": profile.location_preferences or [],
        "salary_min": profile.salary_min,
        "salary_max": profile.salary_max,
        "skills": profile.technical_skills or [],
        "experience_level": _enum_value(profile.experience_level),
    }


class ProcessingService:
    """Orchestrates the analysis -> scoring -> recommendation pipeline for jobs.

    Runs strictly sequentially (ADR-010, concurrency=1) and isolates failures
    per job: one job's failure never aborts the batch.
    """

    def __init__(
        self,
        analysis_service: Optional[AnalysisService] = None,
        scoring_service: Optional[ScoringService] = None,
        recommendation_service: Optional[RecommendationService] = None,
    ):
        self._analysis_service = analysis_service or AnalysisService()
        self._scoring_service = scoring_service or ScoringService()
        self._recommendation_service = recommendation_service or RecommendationService()

    def set_repositories(self, job_repo: JobRepository, analysis_repo: AIAnalysisRepository) -> None:
        """Wire persistence repositories into the underlying stage services."""
        self._analysis_service.set_repository(analysis_repo)
        self._scoring_service.set_job_repository(job_repo)
        self._recommendation_service.set_job_repository(job_repo)

    async def process_job(self, job: Job, profile: Profile) -> JobProcessingResult:
        """Run one job through analysis, scoring, and recommendation.

        Any exception in a stage is caught and reported as a FAILED result
        for this job only; it never propagates to the caller.
        """
        state = ProcessingJobState.PENDING
        try:
            state = ProcessingJobState.ANALYZING
            analysis_input = AnalysisInput(
                job=_build_analysis_job_input(job),
                profile=_build_analysis_profile_input(profile),
            )
            analysis_output = await self._analysis_service.analyze_and_persist(analysis_input)

            state = ProcessingJobState.SCORING
            scoring_input = _build_scoring_input(job, profile, analysis_output)
            scoring_output = await self._scoring_service.score_and_persist(scoring_input)

            state = ProcessingJobState.RECOMMENDING
            await self._recommendation_service.generate_and_persist_recommendation(
                scoring_output,
                _build_job_data(job),
                _build_profile_data(profile),
                job.id,
            )

            return JobProcessingResult(job_id=job.id, state=ProcessingJobState.COMPLETED)
        except Exception as exc:
            return JobProcessingResult(
                job_id=job.id,
                state=ProcessingJobState.FAILED,
                error=f"{state.value}: {exc}",
            )

    async def process_jobs(
        self,
        jobs: List[Job],
        profile: Profile,
        skip_existing: bool = True,
    ) -> ProcessingResponse:
        """Process a batch of jobs sequentially, one at a time."""
        results: List[JobProcessingResult] = []
        processed = 0
        failed = 0
        skipped = 0

        for job in jobs:
            if skip_existing and job.recommendation_category is not None:
                results.append(JobProcessingResult(job_id=job.id, state=ProcessingJobState.SKIPPED))
                skipped += 1
                continue

            result = await self.process_job(job, profile)
            results.append(result)
            if result.state == ProcessingJobState.COMPLETED:
                processed += 1
            else:
                failed += 1

        return ProcessingResponse(
            jobs_total=len(jobs),
            processed=processed,
            failed=failed,
            skipped=skipped,
            results=results,
        )

    async def close(self) -> None:
        await self._analysis_service.close()
        await self._scoring_service.close()


async def get_processing_service() -> ProcessingService:
    """Dependency injection for ProcessingService. Call set_repositories() before use."""
    return ProcessingService()
