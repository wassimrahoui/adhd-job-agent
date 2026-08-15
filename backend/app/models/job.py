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
    # Scoring fields
    score: Optional[int] = Field(default=None, ge=0, le=100, description="Match score 0-100")
    recommendation: Optional[str] = Field(default=None, description="Match recommendation")
    confidence: Optional[str] = Field(default=None, description="Confidence level")
    skills_score: Optional[int] = Field(default=None, ge=0, le=100)
    experience_score: Optional[int] = Field(default=None, ge=0, le=100)
    requirements_score: Optional[int] = Field(default=None, ge=0, le=100)
    location_score: Optional[int] = Field(default=None, ge=0, le=100)
    salary_score: Optional[int] = Field(default=None, ge=0, le=100)
    scored_at: Optional[datetime] = Field(default=None, description="When job was scored")
    scoring_model: Optional[str] = Field(default=None, description="Model used for scoring")
    # Recommendation fields
    recommendation_category: Optional[str] = Field(default=None, description="Recommendation category")
    recommendation_priority: Optional[str] = Field(default=None, description="Recommendation priority")
    recommendation_primary_reason: Optional[str] = Field(default=None, description="Primary reason for recommendation")
    recommendation_secondary_reasons: Optional[str] = Field(default=None, description="Secondary reasons (JSON array)")
    recommendation_explanation: Optional[str] = Field(default=None, description="Full explanation")
    recommendation_missing_skills: Optional[str] = Field(default=None, description="Missing critical skills (JSON array)")
    recommendation_strengths: Optional[str] = Field(default=None, description="Candidate strengths (JSON array)")
    recommendation_concerns: Optional[str] = Field(default=None, description="Concerns (JSON array)")
    recommendation_action_items: Optional[str] = Field(default=None, description="Action items (JSON array)")
    recommended_at: Optional[datetime] = Field(default=None, description="When recommendation was generated")
    recommendation_model: Optional[str] = Field(default=None, description="Model used for recommendation")


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
    # Scoring fields
    score: Optional[int] = Field(default=None, ge=0, le=100)
    recommendation: Optional[str] = None
    confidence: Optional[str] = None
    skills_score: Optional[int] = Field(default=None, ge=0, le=100)
    experience_score: Optional[int] = Field(default=None, ge=0, le=100)
    requirements_score: Optional[int] = Field(default=None, ge=0, le=100)
    location_score: Optional[int] = Field(default=None, ge=0, le=100)
    salary_score: Optional[int] = Field(default=None, ge=0, le=100)
    scored_at: Optional[datetime] = None
    scoring_model: Optional[str] = None
    # Recommendation fields
    recommendation_category: Optional[str] = None
    recommendation_priority: Optional[str] = None
    recommendation_primary_reason: Optional[str] = None
    recommendation_secondary_reasons: Optional[str] = None
    recommendation_explanation: Optional[str] = None
    recommendation_missing_skills: Optional[str] = None
    recommendation_strengths: Optional[str] = None
    recommendation_concerns: Optional[str] = None
    recommendation_action_items: Optional[str] = None
    recommended_at: Optional[datetime] = None
    recommendation_model: Optional[str] = None


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
    confidence: Optional[str] = None
    skills_score: Optional[int] = None
    experience_score: Optional[int] = None
    requirements_score: Optional[int] = None
    location_score: Optional[int] = None
    salary_score: Optional[int] = None
    scored_at: Optional[datetime] = None
    scoring_model: Optional[str] = None
    # Recommendation fields
    recommendation_category: Optional[str] = None
    recommendation_priority: Optional[str] = None
    recommendation_primary_reason: Optional[str] = None
    recommendation_explanation: Optional[str] = None
    recommended_at: Optional[datetime] = None
    recommendation_model: Optional[str] = None


from app.models.analysis import AIAnalysisResponse


class JobDetail(Job):
    analysis: Optional[AIAnalysisResponse] = None