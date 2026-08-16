from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class ProcessingJobState(str, Enum):
    """State of a single job as it moves through the processing pipeline."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    SCORING = "scoring"
    RECOMMENDING = "recommending"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ProcessingRequest(BaseModel):
    """Request to run the full analysis -> scoring -> recommendation pipeline."""
    only_passed: bool = Field(default=True, description="Only process jobs that passed pre-filter")
    limit: int = Field(default=50, ge=1, le=200, description="Max jobs to process")
    skip_existing: bool = Field(default=True, description="Skip jobs that already have a recommendation")


class JobProcessingResult(BaseModel):
    """Outcome of processing a single job through the pipeline."""
    job_id: int
    state: ProcessingJobState
    error: Optional[str] = None


class ProcessingResponse(BaseModel):
    """Summary of a processing run across a batch of jobs."""
    jobs_total: int
    processed: int
    failed: int
    skipped: int
    results: List[JobProcessingResult] = Field(default_factory=list)
