from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.models import WorkMode, EmploymentType, AnalysisStatus, Recommendation, Confidence


class SkillMatchItemSchema(BaseModel):
    claim: str
    source_excerpt: Optional[str] = None


class ExperienceMatchItemSchema(BaseModel):
    claim: str
    source_excerpt: Optional[str] = None


class RequirementGapItemSchema(BaseModel):
    claim: str
    source_excerpt: str


class UnknownRequirementItemSchema(BaseModel):
    claim: str
    source_excerpt: str


class EvidenceItemSchema(BaseModel):
    claim: str
    source_excerpt: Optional[str] = None


class AIAnalysisResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    model_used: str
    score: Optional[int] = None
    recommendation: Optional[Recommendation] = None
    confidence: Optional[Confidence] = None
    matching_skills: List[SkillMatchItemSchema] = Field(default_factory=list)
    matching_experience: List[ExperienceMatchItemSchema] = Field(default_factory=list)
    missing_requirements: List[RequirementGapItemSchema] = Field(default_factory=list)
    unknown_requirements: List[UnknownRequirementItemSchema] = Field(default_factory=list)
    explanation: Optional[str] = None
    evidence: List[EvidenceItemSchema] = Field(default_factory=list)
    status: AnalysisStatus
    created_at: datetime


class JobListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class JobDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    salary_is_predicted: bool = False
    description: Optional[str] = None
    requirements: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    redirect_url: Optional[str] = None
    posted_at: Optional[datetime] = None
    discovered_at: datetime
    raw_evidence: Dict[str, Any] = Field(default_factory=dict)
    passed_prefilter: bool
    analysis: Optional[AIAnalysisResponseSchema] = None