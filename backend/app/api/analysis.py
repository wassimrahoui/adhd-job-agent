from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.db import get_database
from app.repositories import JobRepository, AIAnalysisRepository
from app.analysis import AnalysisService, get_analysis_service
from app.schemas.analysis import AnalysisInput, AnalysisJobInput, AnalysisProfileInput
from app.schemas.job import JobDetailSchema, JobListItemSchema
from app.schemas.search import SearchResponse, SearchErrorResponse
from app.filters import (
    run_pre_filter_pipeline,
    PreFilterInput,
    PreFilterConfig,
    PreFilterJobInput,
    PreFilterProfileInput,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])


def get_job_repo(db=Depends(get_database)) -> JobRepository:
    return JobRepository(db)


def get_analysis_repo(db=Depends(get_database)) -> AIAnalysisRepository:
    return AIAnalysisRepository(db)


@router.post(
    "/run",
    response_model=dict,
    responses={
        404: {"model": SearchErrorResponse, "description": "Profile not found"},
        500: {"model": SearchErrorResponse, "description": "Analysis failed"},
    },
)
async def run_analysis_on_filtered_jobs(
    job_repo: Annotated[JobRepository, Depends(get_job_repo)],
    analysis_repo: Annotated[AIAnalysisRepository, Depends(get_analysis_repo)],
    analysis_service: Annotated[AnalysisService, Depends(get_analysis_service)],
    profile_repo=Depends(get_database),
    only_passed: bool = Query(True, description="Only analyze jobs that passed pre-filter"),
    limit: int = Query(50, ge=1, le=200, description="Max jobs to analyze"),
) -> dict:
    """Run AI analysis on jobs that passed pre-filtering.
    
    This endpoint:
    1. Gets the current user profile
    2. Fetches jobs (filtered by pre-filter status if only_passed=True)
    3. Runs AI analysis on each job
    4. Persists analysis results
    4. Returns summary statistics
    """
    # Import here to avoid circular imports
    from app.repositories import ProfileRepository
    
    profile_repo_instance = ProfileRepository(profile_repo)
    profile = await profile_repo_instance.get_profile()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "PROFILE_NOT_FOUND", "message": "Profile not set. Please create a profile first."}
        )

    # Build pre-filter profile input for analysis
    prefilter_profile = PreFilterProfileInput(
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
        remote_preference=profile.remote_preference.value if hasattr(profile.remote_preference, 'value') else profile.remote_preference,
        experience_level=profile.experience_level.value if hasattr(profile.experience_level, 'value') else profile.experience_level,
        excluded_keywords=profile.excluded_keywords or [],
        relevance_threshold=profile.relevance_threshold,
    )

    # Set repository on service
    analysis_service.set_repository(analysis_repo)

    # Fetch jobs to analyze
    if only_passed:
        jobs = await job_repo.get_jobs_by_prefilter(passed=True, limit=limit)
    else:
        # For all jobs, we need to fetch them differently - get IDs first then fetch each
        # For simplicity, just get passed ones for now
        jobs = await job_repo.get_jobs_by_prefilter(passed=True, limit=limit)

    analyzed = 0
    failed = 0
    skipped = 0

    for job in jobs:
        # Skip if already has analysis
        existing = await analysis_repo.get_latest_analysis_for_job(job.id)
        if existing:
            skipped += 1
            continue

        # Build analysis input
        prefilter_job = PreFilterJobInput(
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

        # Build profile for analysis (using AnalysisProfileInput)
        analysis_profile = AnalysisProfileInput(
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
            remote_preference=profile.remote_preference.value if hasattr(profile.remote_preference, 'value') else profile.remote_preference,
            experience_level=profile.experience_level.value if hasattr(profile.experience_level, 'value') else profile.experience_level,
            excluded_keywords=profile.excluded_keywords or [],
            relevance_threshold=profile.relevance_threshold,
            resume_text=profile.resume_text,
        )

        analysis_job = AnalysisJobInput(
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

        input_data = AnalysisInput(job=analysis_job, profile=analysis_profile)

        try:
            await analysis_service.analyze_and_persist(input_data)
            analyzed += 1
        except Exception:
            failed += 1

    return {
        "jobs_total": len(jobs),
        "analyzed": analyzed,
        "failed": failed,
        "skipped_existing": skipped,
    }


@router.get(
    "/job/{job_id}",
    response_model=AnalysisInput,
    responses={
        404: {"model": SearchErrorResponse, "description": "Job not found"},
    },
)
async def get_analysis_input_for_job(
    job_id: int,
    job_repo: Annotated[JobRepository, Depends(get_job_repo)],
    profile_repo=Depends(get_database),
) -> AnalysisInput:
    """Get the analysis input (job + profile) for a specific job."""
    from app.repositories import ProfileRepository
    
    profile_repo_instance = ProfileRepository(profile_repo)
    profile = await profile_repo_instance.get_profile()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "PROFILE_NOT_FOUND", "message": "Profile not set."}
        )

    job = await job_repo.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "JOB_NOT_FOUND", "message": f"Job {job_id} not found."}
        )

    analysis_job = AnalysisJobInput(
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

    analysis_profile = AnalysisProfileInput(
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
        remote_preference=profile.remote_preference.value if hasattr(profile.remote_preference, 'value') else profile.remote_preference,
        experience_level=profile.experience_level.value if hasattr(profile.experience_level, 'value') else profile.experience_level,
        excluded_keywords=profile.excluded_keywords or [],
        relevance_threshold=profile.relevance_threshold,
        resume_text=profile.resume_text,
    )

    return AnalysisInput(job=analysis_job, profile=analysis_profile)