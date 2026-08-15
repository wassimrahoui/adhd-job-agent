from __future__ import annotations

from typing import Any, Optional
from app.schemas.recommendation import RecommendationInput


class MissingDataHandler:
    """Handle missing or unknown data in recommendation input."""
    
    CRITICAL_FIELDS = [
        "score",
        "skills_score",
        "experience_score",
        "requirements_score",
        "location_score",
        "salary_score",
        "job_title",
    ]
    
    OPTIONAL_FIELDS = [
        "job_company",
        "job_location",
        "job_skills",
        "job_salary_min",
        "job_salary_max",
        "profile_desired_roles",
        "profile_location_preferences",
        "profile_salary_min",
        "profile_salary_max",
        "profile_skills",
        "profile_experience_level",
    ]
    
    def __init__(self):
        pass
    
    def identify_missing_critical_fields(self, input_data: RecommendationInput) -> list[str]:
        """Identify which critical fields are missing or have unknown values."""
        missing = []
        
        # Check critical fields
        if input_data.score is None or input_data.score < 0:
            missing.append("score")
        if input_data.skills_score is None or input_data.skills_score < 0:
            missing.append("skills_score")
        if input_data.experience_score is None or input_data.experience_score < 0:
            missing.append("experience_score")
        if input_data.requirements_score is None or input_data.requirements_score < 0:
            missing.append("requirements_score")
        if input_data.location_score is None or input_data.location_score < 0:
            missing.append("location_score")
        if input_data.salary_score is None or input_data.salary_score < 0:
            missing.append("salary_score")
        if not input_data.job_title:
            missing.append("job_title")
        
        return missing
    
    def identify_missing_optional_fields(self, input_data: RecommendationInput) -> list[str]:
        """Identify which optional fields are missing."""
        missing = []
        
        if not input_data.job_company:
            missing.append("job_company")
        if not input_data.job_location:
            missing.append("job_location")
        if not input_data.job_skills:
            missing.append("job_skills")
        if input_data.job_salary_min is None and input_data.job_salary_max is None:
            missing.append("job_salary")
        if not input_data.profile_desired_roles:
            missing.append("profile_desired_roles")
        if not input_data.profile_location_preferences:
            missing.append("profile_location_preferences")
        if input_data.profile_salary_min is None and input_data.profile_salary_max is None:
            missing.append("profile_salary")
        if not input_data.profile_skills:
            missing.append("profile_skills")
        if not input_data.profile_experience_level:
            missing.append("profile_experience_level")
        
        return missing
    
    def has_sufficient_data(self, input_data: RecommendationInput) -> bool:
        """Check if there's enough data to make a recommendation."""
        missing_critical = self.identify_missing_critical_fields(input_data)
        return len(missing_critical) == 0
    
    def get_data_quality_score(self, input_data: RecommendationInput) -> float:
        """Calculate a data quality score from 0.0 to 1.0."""
        all_fields = self.CRITICAL_FIELDS + self.OPTIONAL_FIELDS
        present_count = 0
        
        for field in self.CRITICAL_FIELDS:
            value = getattr(input_data, field, None)
            if value is not None and (not isinstance(value, str) or value.strip()):
                present_count += 1
        
        for field in self.OPTIONAL_FIELDS:
            value = getattr(input_data, field, None)
            if value is not None and (
                not isinstance(value, (list, str)) or 
                (isinstance(value, list) and len(value) > 0) or
                (isinstance(value, str) and value.strip())
            ):
                present_count += 1
        
        return present_count / len(all_fields) if all_fields else 0.0
    
    def fill_defaults(self, input_data: RecommendationInput) -> RecommendationInput:
        """Create a copy with defaults filled for missing optional fields."""
        # This would return a new instance with defaults
        # For now, just return the input as-is
        return input_data
    
    def get_missing_data_warnings(self, input_data: RecommendationInput) -> list[str]:
        """Get human-readable warnings about missing data."""
        warnings = []
        
        missing_critical = self.identify_missing_critical_fields(input_data)
        if missing_critical:
            warnings.append(
                f"Critical fields missing: {', '.join(missing_critical)}. "
                "Recommendation may be unreliable."
            )
        
        missing_optional = self.identify_missing_optional_fields(input_data)
        if missing_optional:
            warnings.append(
                f"Optional fields missing: {', '.join(missing_optional)}. "
                "Recommendation quality may be reduced."
            )
        
        if not input_data.evidence:
            warnings.append(
                "No evidence provided. Recommendation is based solely on scores."
            )
        
        return warnings