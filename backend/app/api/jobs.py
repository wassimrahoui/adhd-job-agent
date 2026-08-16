from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated, Optional, List

from app.db import get_database
from app.repositories import JobRepository, AIAnalysisRepository
from app.schemas.job import JobListItemSchema, JobDetailSchema

router = APIRouter(prefix="/jobs", tags=["jobs"])


def get_job_repo(db=Depends(get_database)) -> JobRepository:
    return JobRepository(db)


def get_analysis_repo(db=Depends(get_database)) -> AIAnalysisRepository:
    return AIAnalysisRepository(db)


@router.get("", response_model=List[JobListItemSchema])
async def list_jobs(
    repo: Annotated[JobRepository, Depends(get_job_repo)],
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    passed_prefilter: Optional[bool] = Query(None),
    sort_by_score: bool = Query(True, description="Sort by score descending"),
) -> List[JobListItemSchema]:
    """List jobs from the most recent search, with score/recommendation, sorted by score."""
    jobs = await repo.list_jobs(limit=limit, offset=offset, passed_prefilter=passed_prefilter)
    result = [JobListItemSchema.model_validate(job) for job in jobs]

    # Sort by score descending (None scores last)
    if sort_by_score:
        result.sort(key=lambda x: x.score or -1, reverse=True)
    return result


@router.get("/{job_id}", response_model=JobDetailSchema)
async def get_job(
    job_id: int,
    repo: Annotated[JobRepository, Depends(get_job_repo)],
    analysis_repo: Annotated[AIAnalysisRepository, Depends(get_analysis_repo)],
) -> JobDetailSchema:
    """Get full job detail with latest analysis data."""
    job = await repo.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": "Job not found"}
        )
    
    job_dict = job.model_dump()
    latest_analysis = await analysis_repo.get_latest_analysis_for_job(job_id)
    if latest_analysis:
        from app.schemas.job import AIAnalysisResponseSchema
        job_dict["analysis"] = AIAnalysisResponseSchema.model_validate(latest_analysis)
    
    return JobDetailSchema(**job_dict)