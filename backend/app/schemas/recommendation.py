from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class RecommendationCategory(str, Enum):
    """Categories for job recommendations."""
    STRONG_MATCH = "strong_match"
    POSSIBLE_MATCH = "possible_match"
    WEAK_MATCH = "weak_match"
    NOT_ENOUGH_INFORMATION = "not_enough_information"


class RecommendationPriority(str, Enum):
    """Priority levels for recommendations."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SKIP = "skip"


class RecommendationReason(str, Enum):
    """Reason for the recommendation."""
    SKILLS_MATCH = "skills_match"
    EXPERIENCE_MATCH = "experience_match"
    LOCATION_MATCH = "location_match"
    SALARY_MATCH = "salary_match"
    REQUIREMENTS_COVERED = "requirements_covered"
    MISSING_CRITICAL_SKILLS = "missing_critical_skills"
    EXPERIENCE_GAP = "experience_gap"
    LOCATION_MISMATCH = "location_mismatch"
    SALARY_BELOW_EXPECTATIONS = "salary_below_expectations"
    INSUFFICIENT_INFORMATION = "insufficient_information"


class RecommendationConfig(BaseModel):
    """Configuration for recommendation engine."""
    model_config = ConfigDict(from_attributes=True)
    
    strong_match_threshold: int = Field(default=80, ge=0, le=100)
    possible_match_threshold: int = Field(default=50, ge=0, le=100)
    weak_match_threshold: int = Field(default=20, ge=0, le=100)
    min_evidence_for_high_priority: int = Field(default=3, ge=0)
    critical_skills_weight: float = Field(default=1.5, ge=0.0)
    experience_weight: float = Field(default=1.0, ge=0.0)
    location_weight: float = Field(default=1.0, ge=0.0)
    salary_weight: float = Field(default=1.0, ge=0.0)


class RecommendationOutput(BaseModel):
    """Structured output for job recommendation."""
    model_config = ConfigDict(from_attributes=True)
    
    category: RecommendationCategory
    priority: RecommendationPriority
    primary_reason: RecommendationReason
    secondary_reasons: list[RecommendationReason] = Field(default_factory=list)
    explanation: str
    confidence: str  # high, medium, low
    score: int = Field(ge=0, le=100)
    missing_critical_skills: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    status: str = "success"


class RecommendationInput(BaseModel):
    """Input for recommendation engine - scoring output + job/profile context."""
    model_config = ConfigDict(from_attributes=True)
    
    # From scoring
    score: int
    recommendation_category: RecommendationCategory
    confidence: str  # high, medium, low
    skills_score: int
    experience_score: int
    requirements_score: int
    location_score: int
    salary_score: int
    explanation: str
    evidence: list[dict] = Field(default_factory=list)
    status: str
    
    # Job context
    job_title: str
    job_company: Optional[str] = None
    job_location: Optional[str] = None
    job_skills: list[str] = Field(default_factory=list)
    job_salary_min: Optional[int] = None
    job_salary_max: Optional[int] = None
    
    # Profile context
    profile_desired_roles: list[str] = Field(default_factory=list)
    profile_location_preferences: list[str] = Field(default_factory=list)
    profile_salary_min: Optional[int] = None
    profile_salary_max: Optional[int] = None
    profile_skills: list[str] = Field(default_factory=list)
    profile_experience_level: Optional[str] = None