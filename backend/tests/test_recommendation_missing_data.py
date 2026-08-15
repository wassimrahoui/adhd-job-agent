from __future__ import annotations

import pytest

from app.recommendation.missing_data import MissingDataHandler
from app.schemas.recommendation import RecommendationInput, RecommendationCategory


class TestMissingDataHandler:
    @pytest.fixture
    def handler(self):
        return MissingDataHandler()

    def test_identify_missing_critical_fields_none(self, handler):
        input_data = RecommendationInput(
            score=85,
            recommendation_category=RecommendationCategory.STRONG_MATCH,
            confidence="high",
            skills_score=90,
            experience_score=85,
            requirements_score=80,
            location_score=95,
            salary_score=80,
            explanation="Excellent match",
            evidence=[{"type": "skill", "value": "Python"}],
            status="success",
            job_title="Engineer",
        )
        missing = handler.identify_missing_critical_fields(input_data)
        assert missing == []

    def test_identify_missing_critical_fields_missing_score(self, handler):
        # Can't easily test None score since it's required, but we can test negative
        input_data = RecommendationInput(
            score=-1,
            recommendation_category=RecommendationCategory.STRONG_MATCH,
            confidence="high",
            skills_score=90,
            experience_score=85,
            requirements_score=80,
            location_score=95,
            salary_score=80,
            explanation="Excellent match",
            evidence=[{"type": "skill", "value": "Python"}],
            status="success",
            job_title="Engineer",
        )
        missing = handler.identify_missing_critical_fields(input_data)
        assert "score" in missing

    def test_identify_missing_critical_fields_missing_job_title(self, handler):
        input_data = RecommendationInput(
            score=85,
            recommendation_category=RecommendationCategory.STRONG_MATCH,
            confidence="high",
            skills_score=90,
            experience_score=85,
            requirements_score=80,
            location_score=95,
            salary_score=80,
            explanation="Excellent match",
            evidence=[{"type": "skill", "value": "Python"}],
            status="success",
            job_title="",  # Empty
        )
        missing = handler.identify_missing_critical_fields(input_data)
        assert "job_title" in missing

    def test_identify_missing_optional_fields(self, handler):
        input_data = RecommendationInput(
            score=85,
            recommendation_category=RecommendationCategory.STRONG_MATCH,
            confidence="high",
            skills_score=90,
            experience_score=85,
            requirements_score=80,
            location_score=95,
            salary_score=80,
            explanation="Excellent match",
            evidence=[{"type": "skill", "value": "Python"}],
            status="success",
            job_title="Engineer",
            # Missing optional fields
        )
        missing = handler.identify_missing_optional_fields(input_data)
        assert "job_company" in missing
        assert "job_location" in missing
        assert "job_skills" in missing
        assert "job_salary" in missing
        assert "profile_desired_roles" in missing
        assert "profile_location_preferences" in missing
        assert "profile_salary" in missing
        assert "profile_skills" in missing
        assert "profile_experience_level" in missing

    def test_has_sufficient_data_true(self, handler):
        input_data = RecommendationInput(
            score=85,
            recommendation_category=RecommendationCategory.STRONG_MATCH,
            confidence="high",
            skills_score=90,
            experience_score=85,
            requirements_score=80,
            location_score=95,
            salary_score=80,
            explanation="Excellent match",
            evidence=[{"type": "skill", "value": "Python"}],
            status="success",
            job_title="Engineer",
        )
        assert handler.has_sufficient_data(input_data) is True

    def test_has_sufficient_data_false(self, handler):
        input_data = RecommendationInput(
            score=-1,
            recommendation_category=RecommendationCategory.STRONG_MATCH,
            confidence="high",
            skills_score=90,
            experience_score=85,
            requirements_score=80,
            location_score=95,
            salary_score=80,
            explanation="Excellent match",
            evidence=[{"type": "skill", "value": "Python"}],
            status="success",
            job_title="Engineer",
        )
        assert handler.has_sufficient_data(input_data) is False

    def test_get_data_quality_score_complete(self, handler):
        input_data = RecommendationInput(
            score=85,
            recommendation_category=RecommendationCategory.STRONG_MATCH,
            confidence="high",
            skills_score=90,
            experience_score=85,
            requirements_score=80,
            location_score=95,
            salary_score=80,
            explanation="Excellent match",
            evidence=[{"type": "skill", "value": "Python"}],
            status="success",
            job_title="Engineer",
            job_company="Tech Corp",
            job_location="Berlin",
            job_skills=["Python", "Django"],
            job_salary_min=60000,
            job_salary_max=80000,
            profile_desired_roles=["Backend Engineer"],
            profile_location_preferences=["Berlin", "Remote"],
            profile_salary_min=55000,
            profile_salary_max=75000,
            profile_skills=["Python", "Django", "PostgreSQL"],
            profile_experience_level="senior",
        )
        quality = handler.get_data_quality_score(input_data)
        assert quality == 1.0

    def test_get_data_quality_score_partial(self, handler):
        input_data = RecommendationInput(
            score=85,
            recommendation_category=RecommendationCategory.STRONG_MATCH,
            confidence="high",
            skills_score=90,
            experience_score=85,
            requirements_score=80,
            location_score=95,
            salary_score=80,
            explanation="Excellent match",
            evidence=[{"type": "skill", "value": "Python"}],
            status="success",
            job_title="Engineer",
        )
        quality = handler.get_data_quality_score(input_data)
        # Only critical fields present
        assert 0.3 < quality < 0.5

    def test_get_missing_data_warnings_critical(self, handler):
        input_data = RecommendationInput(
            score=-1,
            recommendation_category=RecommendationCategory.STRONG_MATCH,
            confidence="high",
            skills_score=90,
            experience_score=85,
            requirements_score=80,
            location_score=95,
            salary_score=80,
            explanation="Excellent match",
            evidence=[{"type": "skill", "value": "Python"}],
            status="success",
            job_title="Engineer",
        )
        warnings = handler.get_missing_data_warnings(input_data)
        assert len(warnings) >= 1
        assert "Critical fields missing" in warnings[0]

    def test_get_missing_data_warnings_no_evidence(self, handler):
        input_data = RecommendationInput(
            score=85,
            recommendation_category=RecommendationCategory.STRONG_MATCH,
            confidence="high",
            skills_score=90,
            experience_score=85,
            requirements_score=80,
            location_score=95,
            salary_score=80,
            explanation="Excellent match",
            evidence=[],  # No evidence
            status="success",
            job_title="Engineer",
        )
        warnings = handler.get_missing_data_warnings(input_data)
        assert len(warnings) >= 2  # Optional fields warning + no evidence warning
        assert any("No evidence provided" in w for w in warnings)