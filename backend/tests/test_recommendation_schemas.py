from __future__ import annotations

import pytest

from app.schemas.recommendation import (
    RecommendationCategory,
    RecommendationPriority,
    RecommendationReason,
    RecommendationConfig,
    RecommendationOutput,
    RecommendationInput,
)


class TestRecommendationCategory:
    def test_all_categories(self):
        assert RecommendationCategory.STRONG_MATCH.value == "strong_match"
        assert RecommendationCategory.POSSIBLE_MATCH.value == "possible_match"
        assert RecommendationCategory.WEAK_MATCH.value == "weak_match"
        assert RecommendationCategory.NOT_ENOUGH_INFORMATION.value == "not_enough_information"

    def test_all_values_exist(self):
        values = [c.value for c in RecommendationCategory]
        assert "strong_match" in values
        assert "possible_match" in values
        assert "weak_match" in values
        assert "not_enough_information" in values


class TestRecommendationPriority:
    def test_all_priorities(self):
        assert RecommendationPriority.HIGH.value == "high"
        assert RecommendationPriority.MEDIUM.value == "medium"
        assert RecommendationPriority.LOW.value == "low"
        assert RecommendationPriority.SKIP.value == "skip"


class TestRecommendationReason:
    def test_all_reasons(self):
        assert RecommendationReason.SKILLS_MATCH.value == "skills_match"
        assert RecommendationReason.EXPERIENCE_MATCH.value == "experience_match"
        assert RecommendationReason.LOCATION_MATCH.value == "location_match"
        assert RecommendationReason.SALARY_MATCH.value == "salary_match"
        assert RecommendationReason.REQUIREMENTS_COVERED.value == "requirements_covered"
        assert RecommendationReason.MISSING_CRITICAL_SKILLS.value == "missing_critical_skills"
        assert RecommendationReason.EXPERIENCE_GAP.value == "experience_gap"
        assert RecommendationReason.LOCATION_MISMATCH.value == "location_mismatch"
        assert RecommendationReason.SALARY_BELOW_EXPECTATIONS.value == "salary_below_expectations"
        assert RecommendationReason.INSUFFICIENT_INFORMATION.value == "insufficient_information"


class TestRecommendationConfig:
    def test_default_config(self):
        config = RecommendationConfig()
        assert config.strong_match_threshold == 80
        assert config.possible_match_threshold == 50
        assert config.weak_match_threshold == 20
        assert config.min_evidence_for_high_priority == 3

    def test_custom_thresholds(self):
        config = RecommendationConfig(
            strong_match_threshold=85,
            possible_match_threshold=55,
            weak_match_threshold=25,
            min_evidence_for_high_priority=5,
        )
        assert config.strong_match_threshold == 85
        assert config.possible_match_threshold == 55
        assert config.weak_match_threshold == 25
        assert config.min_evidence_for_high_priority == 5


class TestRecommendationOutput:
    def test_valid_output(self):
        output = RecommendationOutput(
            category=RecommendationCategory.STRONG_MATCH,
            priority=RecommendationPriority.HIGH,
            primary_reason=RecommendationReason.SKILLS_MATCH,
            secondary_reasons=[RecommendationReason.EXPERIENCE_MATCH],
            explanation="Strong match with excellent skills alignment",
            confidence="high",
            score=85,
            missing_critical_skills=[],
            strengths=["Python", "Django", "5 years experience"],
            concerns=[],
            action_items=["Apply now"],
            status="success",
        )
        assert output.category == RecommendationCategory.STRONG_MATCH
        assert output.priority == RecommendationPriority.HIGH
        assert output.score == 85

    def test_minimal_output(self):
        output = RecommendationOutput(
            category=RecommendationCategory.WEAK_MATCH,
            priority=RecommendationPriority.LOW,
            primary_reason=RecommendationReason.MISSING_CRITICAL_SKILLS,
            explanation="Missing key skills",
            confidence="low",
            score=30,
            status="success",
        )
        assert output.category == RecommendationCategory.WEAK_MATCH
        assert output.priority == RecommendationPriority.LOW
        assert output.missing_critical_skills == []


class TestRecommendationInput:
    def test_valid_input(self):
        input_data = RecommendationInput(
            score=85,
            recommendation_category=RecommendationCategory.STRONG_MATCH,
            confidence="high",
            skills_score=90,
            experience_score=80,
            requirements_score=70,
            location_score=95,
            salary_score=85,
            explanation="Excellent match",
            evidence=[],
            status="success",
            job_title="Software Engineer",
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
            profile_experience_level="mid",
        )
        assert input_data.score == 85
        assert input_data.job_title == "Software Engineer"

    def test_minimal_input(self):
        input_data = RecommendationInput(
            score=50,
            recommendation_category=RecommendationCategory.POSSIBLE_MATCH,
            confidence="medium",
            skills_score=50,
            experience_score=50,
            requirements_score=50,
            location_score=50,
            salary_score=50,
            explanation="Average match",
            status="success",
            job_title="Engineer",
        )
        assert input_data.score == 50
        assert input_data.job_company is None