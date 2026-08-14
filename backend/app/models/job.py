from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class WorkMode(str):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ON_SITE = "on_site"


class EmploymentType(str):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    INTERN = "intern"


class JobBase(BaseModel):
    adzuna_id: str = Field(..., description="Unique Adzuna job ID")
    title: str = Field(..., description="Job title")
    company: Optional[str] = Field(default=None, description="Company name")
    location: Optional[str] = Field(default=None, description="Job location")
    work_mode: Optional[str] = Field(default=None, description="Work mode: remote, hybrid, on_site")
    employment_type: Optional[str] = Field(default=None, description="Employment type")
    salary_min: Optional[int] = Field(default=None, description="Minimum salary")
    salary_max: Optional[int] = Field(default=None, description="Maximum salary")
    salary_currency: Optional[str] = Field(default=None, description="Salary currency")
    salary_is_predicted: bool = Field(default=False, description="Whether salary is predicted by Adzuna")
    description: Optional[str] = Field(default=None, description="Job description snippet from Adzuna")
    requirements: Optional[str] = Field(default=None, description="Job requirements")
    skills: Optional[List[str]] = Field(default_factory=list, description="Required skills")
    redirect_url: Optional[str] = Field(default=None, description="Original Adzuna application URL")
    posted_at: Optional[datetime] = Field(default=None, description="When job was posted")
    discovered_at: datetime = Field(default_factory=datetime.utcnow, description="When we discovered this job")
    raw_evidence: Dict[str, Any] = Field(default_factory=dict, description="Raw Adzuna response for this job")
    passed_prefilter: bool = Field(default=False, description="Whether job passed deterministic pre-filter")


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    work_mode: Optional[str] = None
    employment_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    salary_is_predicted: Optional[bool] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    skills: Optional[List[str]] = None
    redirect_url: Optional[str] = None
    posted_at: Optional[datetime] = None
    raw_evidence: Optional[Dict[str, Any]] = None
    passed_prefilter: Optional[bool] = None


class Job(JobBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Internal database ID")


class JobListItem(BaseModel):
    id: int
    adzuna_id: str
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    work_mode: Optional[str] = None
    employment_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    posted_at: Optional[datetime] = None
    discovered_at: datetime
    passed_prefilter: bool
    score: Optional[int] = None
    recommendation: Optional[str] = None


class JobDetail(Job):
    analysis: Optional["AIAnalysisResponse"] = None