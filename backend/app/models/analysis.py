from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class AnalysisStatus(str, Enum):
    SUCCESS = "success"
    REJECTED = "rejected"
    AI_UNAVAILABLE = "ai_unavailable"


class Recommendation(str, Enum):
    STRONG_MATCH = "strong_match"
    POSSIBLE_MATCH = "possible_match"
    WEAK_MATCH = "weak_match"
    NOT_ENOUGH_INFORMATION = "not_enough_information"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EvidenceItem(BaseModel):
    claim: str = Field(..., description="Factual statement (salary, location, remote_status, etc.)")
    source_excerpt: Optional[str] = Field(default=None, description="Supporting excerpt from job/CV data, or null")


class SkillMatchItem(BaseModel):
    claim: str = Field(..., description="The matching skill claim")
    source_excerpt: Optional[str] = Field(default=None, description="Supporting excerpt from CV/job text, or null")


class ExperienceMatchItem(BaseModel):
    claim: str = Field(..., description="The matching experience claim")
    source_excerpt: Optional[str] = Field(default=None, description="Supporting excerpt from CV/job text, or null")


class RequirementGapItem(BaseModel):
    claim: str = Field(..., description="Stated job requirement the CV does not demonstrate")
    source_excerpt: str = Field(..., description="Quote from job text showing this requirement")


class UnknownRequirementItem(BaseModel):
    claim: str = Field(..., description="Stated job requirement the CV says nothing about either way")
    source_excerpt: str = Field(..., description="Quote from job text showing this requirement")


class AIAnalysisBase(BaseModel):
    job_id: int = Field(..., description="Foreign key to job")
    model_used: str = Field(..., description="Exact pinned analysis model tag")
    score: Optional[int] = Field(default=None, ge=0, le=100, description="Match score 0-100")
    recommendation: Optional[Recommendation] = Field(default=None, description="Match recommendation")
    confidence: Optional[Confidence] = Field(default=None, description="Confidence level")
    matching_skills: List[SkillMatchItem] = Field(default_factory=list, description="Skills that match")
    matching_experience: List[ExperienceMatchItem] = Field(default_factory=list, description="Experience that matches")
    missing_requirements: List[RequirementGapItem] = Field(default_factory=list, description="Requirements CV doesn't demonstrate")
    unknown_requirements: List[UnknownRequirementItem] = Field(default_factory=list, description="Requirements CV says nothing about")
    explanation: Optional[str] = Field(default=None, description="2-4 sentence plain language explanation")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Other factual statements with evidence")
    status: AnalysisStatus = Field(default=AnalysisStatus.AI_UNAVAILABLE, description="Analysis status")


class AIAnalysisCreate(AIAnalysisBase):
    pass


class AIAnalysis(AIAnalysisBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Internal database ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AIAnalysisResponse(AIAnalysisBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)