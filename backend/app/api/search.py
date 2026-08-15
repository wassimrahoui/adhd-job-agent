from __future__ import annotations

import time
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.db import get_database
from app.repositories import ProfileRepository, JobRepository
from app.job_sources import (
    AdzunaSourceAdapter,
    build_adzuna_query,
    normalize_job,
    is_duplicate,
    merge_job_data,
    QuotaExhaustedError,
    AuthError,
    APIError,
    _test_adzuna_adapter,
    set_test_adzuna_adapter,
)
from app.schemas.search import SearchResponse, SearchErrorResponse
from app.core.config import settings

router = APIRouter(prefix="/jobs", tags=["search"])


def get_profile_repo(db=Depends(get_database)) -> ProfileRepository:
    return ProfileRepository(db)


def get_job_repo(db=Depends(get_database)) -> JobRepository:
    return JobRepository(db)


def get_adzuna_adapter() -> AdzunaSourceAdapter:
    """Get configured Adzuna adapter."""
    return AdzunaSourceAdapter(config={
        "app_id": settings.adzuna_app_id,
        "app_key": settings.adzuna_app_key,
        "base_url": settings.adzuna_base_url,
        "country": settings.adzuna_country,
        "max_pages": settings.adzuna_max_pages,
        "results_per_page": settings.adzuna_results_per_page,
    })


def get_adzuna_adapter_for_request() -> AdzunaSourceAdapter:
    """Get Adzuna adapter - uses test override if set."""
    # Import the adzuna module to access the shared test adapter variable
    from app.job_sources import adzuna as adzuna_module
    if adzuna_module._test_adzuna_adapter is not None:
        return adzuna_module._test_adzuna_adapter
    return AdzunaSourceAdapter(config={
        "app_id": settings.adzuna_app_id,
        "app_key": settings.adzuna_app_key,
        "base_url": settings.adzuna_base_url,
        "country": settings.adzuna_country,
        "max_pages": settings.adzuna_max_pages,
        "results_per_page": settings.adzuna_results_per_page,
    })


@router.post(
    "/search",
    response_model=SearchResponse,
    responses={
        404: {"model": SearchErrorResponse, "description": "Profile not found"},
        401: {"model": SearchErrorResponse, "description": "Adzuna authentication failed"},
        429: {"model": SearchErrorResponse, "description": "Adzuna quota exhausted"},
        500: {"model": SearchErrorResponse, "description": "Adzuna API error"},
    },
)
async def search_jobs(
    profile_repo: Annotated[ProfileRepository, Depends(get_profile_repo)],
    job_repo: Annotated[JobRepository, Depends(get_job_repo)],
    adzuna: Annotated[AdzunaSourceAdapter, Depends(get_adzuna_adapter_for_request)],
) -> SearchResponse:
    """Trigger the full job search pipeline.
    
    This endpoint:
    1. Gets the current user profile
    2. Builds Adzuna query parameters from profile
    3. Calls Adzuna API with pagination
    4. Normalizes and deduplicates jobs
    5. Stores/updates jobs in database
    6. Returns summary statistics
    
    Returns:
        SearchResponse with counts of jobs found, new, updated, and quota status
    """
    start_time = time.perf_counter()
    
    # Step 1: Get profile
    profile = await profile_repo.get_profile()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "PROFILE_NOT_FOUND", "message": "Profile not set. Please create a profile first."}
        )
    
    # Step 2: Build query from profile
    query_params = build_adzuna_query(profile)
    
    # Step 3: Search Adzuna
    jobs_found = 0
    jobs_new = 0
    jobs_updated = 0
    jobs_duplicate = 0
    quota_exhausted = False
    quota_message = None
    
    try:
        raw_jobs = await adzuna.search_jobs(query_params)
        jobs_found = len(raw_jobs)
        
        # Process each job
        for raw_job in raw_jobs:
            # Normalize
            job_create = normalize_job(raw_job)
            
            # Check for duplicates
            existing = await job_repo.get_job_by_adzuna_id(job_create.adzuna_id)
            
            if existing:
                if is_duplicate(existing, job_create):
                    # Update existing job with any new data
                    updates = merge_job_data(existing, job_create)
                    if updates:
                        from app.models import JobUpdate
                        update_data = JobUpdate(**updates)
                        await job_repo.update_job(existing.id, update_data)
                        jobs_updated += 1
                    else:
                        jobs_duplicate += 1
                else:
                    # Different job with same adzuna_id (shouldn't happen but handle)
                    jobs_duplicate += 1
            else:
                # Check redirect_url duplicate
                if job_create.redirect_url:
                    existing_by_url = await job_repo.get_job_by_redirect_url(job_create.redirect_url)
                    if existing_by_url:
                        jobs_duplicate += 1
                        continue
                
                # Create new job
                await job_repo.create_job(job_create)
                jobs_new += 1
    
    except QuotaExhaustedError as e:
        quota_exhausted = True
        quota_message = str(e)
        # Jobs already fetched are already processed above
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "ADZUNA_AUTH_ERROR", "message": str(e)}
        )
    except APIError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "ADZUNA_API_ERROR", "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "SEARCH_ERROR", "message": f"Search failed: {str(e)}"}
        )
    finally:
        await adzuna.close()
    
    duration_ms = int((time.perf_counter() - start_time) * 1000)
    
    return SearchResponse(
        jobs_found=jobs_found,
        jobs_new=jobs_new,
        jobs_updated=jobs_updated,
        jobs_duplicate=jobs_duplicate,
        quota_exhausted=quota_exhausted,
        quota_message=quota_message,
        search_duration_ms=duration_ms,
    )