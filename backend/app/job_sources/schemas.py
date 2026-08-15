from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class AdzunaArea(BaseModel):
    """Adzuna location area structure."""
    area: Optional[List[str]] = Field(default_factory=list)
    display_name: Optional[str] = None


class AdzunaCategory(BaseModel):
    """Adzuna job category."""
    label: Optional[str] = None
    tag: Optional[str] = None


class AdzunaCompany(BaseModel):
    """Adzuna company information."""
    display_name: Optional[str] = None


class RawJobRecord(BaseModel):
    """Raw job record from Adzuna API, preserved exactly as received."""
    model_config = ConfigDict(extra="allow")

    id: str = Field(..., description="Adzuna's unique job ID")
    title: str = Field(..., description="Job title")
    company: Optional[AdzunaCompany] = Field(default=None, description="Company info")
    location: Optional[AdzunaArea] = Field(default=None, description="Location info")
    description: Optional[str] = Field(default=None, description="Job description snippet")
    salary_min: Optional[int] = Field(default=None, description="Minimum salary")
    salary_max: Optional[int] = Field(default=None, description="Maximum salary")
    salary_is_predicted: bool = Field(default=False, description="Whether salary is predicted by Adzuna")
    contract_type: Optional[str] = Field(default=None, description="Contract type (e.g., permanent, contract)")
    contract_time: Optional[str] = Field(default=None, description="Contract time (e.g., full_time, part_time)")
    category: Optional[AdzunaCategory] = Field(default=None, description="Job category")
    created: Optional[str] = Field(default=None, description="Posting date (ISO format)")
    redirect_url: Optional[str] = Field(default=None, description="Original application URL")
    latitude: Optional[float] = Field(default=None, description="Job latitude")
    longitude: Optional[float] = Field(default=None, description="Job longitude")


class JobSourceError(Exception):
    """Base exception for job source errors."""
    def __init__(self, message: str, error_code: str = "JOB_SOURCE_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class QuotaExhaustedError(JobSourceError):
    """Raised when Adzuna daily quota is exhausted."""
    def __init__(self, message: str = "Adzuna daily quota exhausted for today"):
        super().__init__(message, error_code="QUOTA_EXHAUSTED")


class AuthError(JobSourceError):
    """Raised when Adzuna authentication fails."""
    def __init__(self, message: str = "Adzuna authentication failed"):
        super().__init__(message, error_code="AUTH_ERROR")


class APIError(JobSourceError):
    """Raised when Adzuna API returns an error."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message, error_code="API_ERROR")


class RateLimitError(JobSourceError):
    """Raised when Adzuna rate limit is hit."""
    def __init__(self, message: str = "Adzuna rate limit exceeded"):
        super().__init__(message, error_code="RATE_LIMIT")