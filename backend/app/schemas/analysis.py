from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class AnalysisStatus(str, Enum):
    SUCCESS = "success"
    REJECTED = "rejected"
    AI_UNAVAILABLE = "ai_unavailable"
    PENDING = "pending"
    FAILED = "failed"


class AnalysisJobInput(BaseModel):
    """Job data supplied to the analysis model."""
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
    raw_evidence: Dict[str, Any] = Field(default_factory=dict)


class AnalysisProfileInput(BaseModel):
    """Profile data supplied to the analysis model."""
    model_config = ConfigDict(from_attributes=True)

    work_experience: Optional[str] = None
    technical_skills: List[str] = Field(default_factory=list)
    networking_experience: Optional[str] = None
    education: Optional[str] = None
    certifications: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    desired_roles: List[str] = Field(default_factory=list)
    location_preferences: List[str] = Field(default_factory=list)
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "USD"
    remote_preference: Optional[str] = "any"
    experience_level: Optional[str] = "any"
    excluded_keywords: List[str] = Field(default_factory=list)
    relevance_threshold: int = Field(default=50, ge=0, le=100)
    resume_text: Optional[str] = None


class AnalysisInput(BaseModel):
    """Complete input for the analysis model - job + profile."""
    job: AnalysisJobInput
    profile: AnalysisProfileInput


class SkillMatchItem(BaseModel):
    claim: str
    source_excerpt: Optional[str] = None


class ExperienceMatchItem(BaseModel):
    claim: str
    source_excerpt: Optional[str] = None


class RequirementGapItem(BaseModel):
    claim: str
    source_excerpt: str


class UnknownRequirementItem(BaseModel):
    claim: str
    source_excerpt: str


class EvidenceItem(BaseModel):
    claim: str
    source_excerpt: Optional[str] = None


class Recommendation(str, Enum):
    STRONG_MATCH = "strong_match"
    POSSIBLE_MATCH = "possible_match"
    WEAK_MATCH = "weak_match"
    NOT_ENOUGH_INFORMATION = "not_enough_information"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnalysisOutput(BaseModel):
    """Structured output from the analysis model."""
    model_used: str
    score: Optional[int] = Field(default=None, ge=0, le=100)
    recommendation: Optional[Recommendation] = None
    confidence: Optional[Confidence] = None
    matching_skills: List[SkillMatchItem] = Field(default_factory=list)
    matching_experience: List[ExperienceMatchItem] = Field(default_factory=list)
    missing_requirements: List[RequirementGapItem] = Field(default_factory=list)
    unknown_requirements: List[UnknownRequirementItem] = Field(default_factory=list)
    explanation: Optional[str] = None
    evidence: List[EvidenceItem] = Field(default_factory=list)
    status: AnalysisStatus = AnalysisStatus.SUCCESS