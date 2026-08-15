from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class FilterResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


class FilterReason(BaseModel):
    filter_name: str
    result: FilterResult
    reason: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PreFilterJobInput(BaseModel):
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


class PreFilterProfileInput(BaseModel):
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


class PreFilterInput(BaseModel):
    job: PreFilterJobInput
    profile: PreFilterProfileInput


class PreFilterOutput(BaseModel):
    overall_result: FilterResult
    reasons: List[FilterReason] = Field(default_factory=list)
    matched_fields: Dict[str, Any] = Field(default_factory=dict)


class PreFilterConfig(BaseModel):
    location_match_mode: Literal["exact", "contains", "any"] = "contains"
    salary_compare_mode: Literal["min_only", "max_only", "range_overlap"] = "range_overlap"
    employment_type_match_mode: Literal["exact", "any"] = "any"
    work_mode_match_mode: Literal["exact", "any"] = "any"
    keyword_match_case_sensitive: bool = False
    unknown_salary_behavior: Literal["pass", "fail", "unknown"] = "unknown"
    unknown_location_behavior: Literal["pass", "fail", "unknown"] = "unknown"