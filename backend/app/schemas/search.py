from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class SearchRequest(BaseModel):
    """Request for job search (empty for MVP - uses current profile)."""
    pass


class SearchResponse(BaseModel):
    """Response from job search."""
    model_config = ConfigDict(from_attributes=True)

    jobs_found: int = Field(..., description="Total jobs found from Adzuna")
    jobs_new: int = Field(..., description="New jobs inserted into database")
    jobs_updated: int = Field(..., description="Existing jobs updated")
    jobs_duplicate: int = Field(default=0, description="Jobs skipped as duplicates")
    quota_exhausted: bool = Field(default=False, description="Whether Adzuna quota was exhausted")
    quota_message: Optional[str] = Field(default=None, description="Quota exhausted message if applicable")
    search_duration_ms: Optional[int] = Field(default=None, description="Search duration in milliseconds")


class SearchErrorResponse(BaseModel):
    """Error response for search endpoint."""
    error_code: str
    message: str
    details: Optional[dict] = None