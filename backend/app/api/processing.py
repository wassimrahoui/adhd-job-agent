from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.db import get_database
from app.repositories import JobRepository, AIAnalysisRepository, ProfileRepository
from app.processing import ProcessingService, get_processing_service
from app.schemas.processing import ProcessingRequest, ProcessingResponse
from app.schemas.search import SearchErrorResponse

router = APIRouter(prefix="/processing", tags=["processing"])


def get_job_repo(db=Depends(get_database)) -> JobRepository:
    return JobRepository(db)


def get_analysis_repo(db=Depends(get_database)) -> AIAnalysisRepository:
    return AIAnalysisRepository(db)


def get_profile_repo(db=Depends(get_database)) -> ProfileRepository:
    return ProfileRepository(db)


@router.post(
    "/run",
    response_model=ProcessingResponse,
    responses={
        404: {"model": SearchErrorResponse, "description": "Profile not found"},
    },
)
async def run_processing_pipeline(
    request: ProcessingRequest,
    job_repo: Annotated[JobRepository, Depends(get_job_repo)],
    analysis_repo: Annotated[AIAnalysisRepository, Depends(get_analysis_repo)],
    profile_repo: Annotated[ProfileRepository, Depends(get_profile_repo)],
    processing_service: Annotated[ProcessingService, Depends(get_processing_service)],
) -> ProcessingResponse:
    """Run the full analysis -> scoring -> recommendation pipeline on jobs.

    Coordinates the existing analysis, scoring, and recommendation components
    sequentially per job (concurrency=1, per ADR-010). One job's failure does
    not stop the batch. Does not introduce browser automation, applications,
    application tracking, or email monitoring.
    """
    profile = await profile_repo.get_profile()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "PROFILE_NOT_FOUND", "message": "Profile not set. Please create a profile first."},
        )

    processing_service.set_repositories(job_repo, analysis_repo)

    if request.only_passed:
        jobs = await job_repo.get_jobs_by_prefilter(passed=True, limit=request.limit)
    else:
        jobs = await job_repo.get_all_jobs(limit=request.limit)

    return await processing_service.process_jobs(jobs, profile, skip_existing=request.skip_existing)
