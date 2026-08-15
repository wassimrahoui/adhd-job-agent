from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.analysis import (
    SkillMatchItem,
    ExperienceMatchItem,
    RequirementGapItem,
    UnknownRequirementItem,
    EvidenceItem,
    Recommendation,
    Confidence,
    AnalysisStatus,
)


class ScoringInput(BaseModel):
    """Input for the scoring model - analysis output + job/profile context."""
    model_config = ConfigDict(from_attributes=True)

    # From analysis
    matching_skills: List[SkillMatchItem] = Field(default_factory=list)
    matching_experience: List[ExperienceMatchItem] = Field(default_factory=list)
    missing_requirements: List[RequirementGapItem] = Field(default_factory=list)
    unknown_requirements: List[UnknownRequirementItem] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    explanation: Optional[str] = None
    status: AnalysisStatus = AnalysisStatus.SUCCESS

    # Job context
    job_id: Optional[int] = None
    job_title: str
    job_company: Optional[str] = None
    job_location: Optional[str] = None
    job_work_mode: Optional[str] = None
    job_salary_min: Optional[int] = None
    job_salary_max: Optional[int] = None
    job_salary_currency: Optional[str] = None
    job_salary_is_predicted: bool = False
    job_skills: List[str] = Field(default_factory=list)

    # Profile context
    profile_desired_roles: List[str] = Field(default_factory=list)
    profile_location_preferences: List[str] = Field(default_factory=list)
    profile_salary_min: Optional[int] = None
    profile_salary_max: Optional[int] = None
    profile_salary_currency: str = "USD"
    profile_remote_preference: Optional[str] = "any"
    profile_experience_level: Optional[str] = "any"


class ScoringOutput(BaseModel):
    """Structured output from the scoring model."""
    model_config = ConfigDict(from_attributes=True)

    model_used: str
    score: int = Field(ge=0, le=100, description="Final match score 0-100")
    recommendation: Recommendation
    confidence: Confidence
    skills_score: int = Field(ge=0, le=100, description="Skills match component score")
    experience_score: int = Field(ge=0, le=100, description="Experience match component score")
    requirements_score: int = Field(ge=0, le=100, description="Requirements coverage score")
    location_score: int = Field(ge=0, le=100, description="Location match score")
    salary_score: int = Field(ge=0, le=100, description="Salary match score")
    explanation: str = Field(description="2-4 sentence explanation of the score")
    evidence: List[EvidenceItem] = Field(default_factory=list)
    status: AnalysisStatus = AnalysisStatus.SUCCESS


class ScoringWeights(BaseModel):
    """Configurable weights for score components."""
    skills_weight: float = Field(default=0.35, ge=0.0, le=1.0)
    experience_weight: float = Field(default=0.25, ge=0.0, le=1.0)
    requirements_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    location_weight: float = Field(default=0.10, ge=0.0, le=1.0)
    salary_weight: float = Field(default=0.10, ge=0.0, le=1.0)


class ScoringConfig(BaseModel):
    """Configuration for scoring thresholds and behavior."""
    weights: ScoringWeights = Field(default_factory=ScoringWeights)
    strong_match_threshold: int = Field(default=80, ge=0, le=100)
    possible_match_threshold: int = Field(default=50, ge=0, le=100)
    weak_match_threshold: int = Field(default=20, ge=0, le=100)
    min_evidence_for_high_confidence: int = Field(default=3, ge=0)