from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator

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
    salary_is_predicted: bool = False
    redirect_url: Optional[str] = None
    posted_at: Optional[datetime] = None
    discovered_at: datetime
    passed_prefilter: bool
    score: Optional[int] = None
    recommendation: Optional[str] = None
    confidence: Optional[str] = None
    # Recommendation fields
    recommendation_category: Optional[str] = None
    recommendation_priority: Optional[str] = None
    recommendation_primary_reason: Optional[str] = None
    recommendation_explanation: Optional[str] = None
    recommended_at: Optional[datetime] = None
    recommendation_model: Optional[str] = None


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
    # Recommendation fields
    recommendation_category: Optional[str] = None
    recommendation_priority: Optional[str] = None
    recommendation_primary_reason: Optional[str] = None
    recommendation_secondary_reasons: List[str] = Field(default_factory=list)
    recommendation_explanation: Optional[str] = None
    recommendation_missing_skills: List[str] = Field(default_factory=list)
    recommendation_strengths: List[str] = Field(default_factory=list)
    recommendation_concerns: List[str] = Field(default_factory=list)
    recommendation_action_items: List[str] = Field(default_factory=list)
    recommended_at: Optional[datetime] = None
    recommendation_model: Optional[str] = None

    @field_validator(
        "recommendation_secondary_reasons",
        "recommendation_missing_skills",
        "recommendation_strengths",
        "recommendation_concerns",
        "recommendation_action_items",
        mode="before",
    )
    @classmethod
    def _parse_json_array(cls, value):
        if value is None or isinstance(value, list):
            return value or []
        if isinstance(value, str):
            if not value.strip():
                return []
            try:
                import json
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except (json.JSONDecodeError, TypeError):
                return []
        return []