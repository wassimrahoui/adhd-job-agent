from __future__ import annotations

from typing import Optional

from app.schemas.analysis import AnalysisInput, AnalysisJobInput, AnalysisProfileInput


class EvidenceExtractor:
    """Extract relevant evidence from job and profile data for analysis."""

    def __init__(self, max_description_chars: int = 2000, max_requirements_chars: int = 2000):
        self.max_description_chars = max_description_chars
        self.max_requirements_chars = max_requirements_chars

    def extract_job_evidence(self, job: AnalysisJobInput) -> dict:
        """Extract structured evidence from job data."""
        evidence = {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "work_mode": job.work_mode,
            "employment_type": job.employment_type,
            "salary": None,
            "description": job.description[:self.max_description_chars] if job.description else None,
            "requirements": job.requirements[:self.max_requirements_chars] if job.requirements else None,
            "skills": job.skills,
        }

        if job.salary_min or job.salary_max:
            salary_parts = []
            if job.salary_min:
                salary_parts.append(f"min: {job.salary_min}")
            if job.salary_max:
                salary_parts.append(f"max: {job.salary_max}")
            if job.salary_currency:
                salary_parts.append(f"currency: {job.salary_currency}")
            evidence["salary"] = ", ".join(salary_parts)
            if job.salary_is_predicted:
                evidence["salary"] += " (predicted)"

        return evidence

    def extract_profile_evidence(self, profile: AnalysisProfileInput) -> dict:
        """Extract structured evidence from profile data."""
        evidence = {
            "work_experience": profile.work_experience,
            "technical_skills": profile.technical_skills,
            "networking_experience": profile.networking_experience,
            "education": profile.education,
            "certifications": profile.certifications,
            "languages": profile.languages,
            "desired_roles": profile.desired_roles,
            "location_preferences": profile.location_preferences,
            "salary_expectations": None,
            "remote_preference": profile.remote_preference,
            "experience_level": profile.experience_level,
            "excluded_keywords": profile.excluded_keywords,
            "resume_text": profile.resume_text[:3000] if profile.resume_text else None,
        }

        if profile.salary_min or profile.salary_max:
            salary_parts = []
            if profile.salary_min:
                salary_parts.append(f"min: {profile.salary_min}")
            if profile.salary_max:
                salary_parts.append(f"max: {profile.salary_max}")
            salary_parts.append(f"currency: {profile.salary_currency}")
            evidence["salary_expectations"] = ", ".join(salary_parts)

        return evidence

    def extract_all(self, input_data: AnalysisInput) -> dict:
        """Extract all evidence from analysis input."""
        return {
            "job": self.extract_job_evidence(input_data.job),
            "profile": self.extract_profile_evidence(input_data.profile),
        }


def extract_evidence(input_data: AnalysisInput) -> dict:
    """Convenience function to extract evidence."""
    extractor = EvidenceExtractor()
    return extractor.extract_all(input_data)