from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.models import RemotePreference, ExperienceLevel


class ProfileBaseSchema(BaseModel):
    work_experience: Optional[str] = Field(default=None, description="Work experience summary")
    technical_skills: Optional[List[str]] = Field(default_factory=list, description="Technical skills list")
    networking_experience: Optional[str] = Field(default=None, description="Networking/cybersecurity/sysadmin experience")
    education: Optional[str] = Field(default=None, description="Education background")
    certifications: Optional[List[str]] = Field(default_factory=list, description="Certifications list")
    languages: Optional[List[str]] = Field(default_factory=list, description="Languages spoken")
    desired_roles: Optional[List[str]] = Field(default_factory=list, description="Desired roles/keywords for Adzuna query")
    location_preferences: Optional[List[str]] = Field(default_factory=list, description="Preferred locations")
    salary_min: Optional[int] = Field(default=None, description="Minimum salary requirement")
    salary_max: Optional[int] = Field(default=None, description="Maximum salary requirement")
    salary_currency: str = Field(default="USD", description="Salary currency")
    remote_preference: RemotePreference = Field(default=RemotePreference.ANY, description="Remote/hybrid/on-site preference")
    experience_level: ExperienceLevel = Field(default=ExperienceLevel.ANY, description="Experience level preference")
    excluded_keywords: Optional[List[str]] = Field(default_factory=list, description="Keywords to exclude from search")
    relevance_threshold: int = Field(default=50, ge=0, le=100, description="Relevance score threshold (0-100)")
    resume_text: Optional[str] = Field(default=None, description="Resume text content")
    resume_file_path: Optional[str] = Field(default=None, description="Path to resume file")


class ProfileCreateSchema(ProfileBaseSchema):
    pass


class ProfileUpdateSchema(ProfileBaseSchema):
    pass


class ProfileResponseSchema(ProfileBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(default=1, description="Always 1 for single-user profile")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None