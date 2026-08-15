from __future__ import annotations

import pytest

from app.recommendation.explanation import ExplanationGenerator
from app.schemas.recommendation import (
    RecommendationInput,
    RecommendationCategory,
    RecommendationReason,
)


class TestExplanationGenerator:
    @pytest.fixture
    def generator(self):
        return ExplanationGenerator()

    def test_category_summary_strong_match(self, generator):
        summary = generator.generate_category_summary(RecommendationCategory.STRONG_MATCH)
        assert "strong match" in summary.lower()

    def test_category_summary_possible_match(self, generator):
        summary = generator.generate_category_summary(RecommendationCategory.POSSIBLE_MATCH)
        assert "possible match" in summary.lower()

    def test_category_summary_weak_match(self, generator):
        summary = generator.generate_category_summary(RecommendationCategory.WEAK_MATCH)
        assert "significant gaps" in summary.lower()

    def test_category_summary_not_enough_info(self, generator):
        summary = generator.generate_category_summary(RecommendationCategory.NOT_ENOUGH_INFORMATION)
        assert "enough information" in summary.lower()

    def test_reason_details_skills_match(self, generator):
        details = generator.generate_reason_details([RecommendationReason.SKILLS_MATCH])
        assert len(details) == 1
        assert "skills align" in details[0].lower()

    def test_reason_details_multiple(self, generator):
        reasons = [
            RecommendationReason.SKILLS_MATCH,
            RecommendationReason.EXPERIENCE_MATCH,
            RecommendationReason.LOCATION_MATCH,
        ]
        details = generator.generate_reason_details(reasons)
        assert len(details) == 3

    def test_reason_details_unknown_skipped(self, generator):
        details = generator.generate_reason_details([RecommendationReason.INSUFFICIENT_INFORMATION])
        assert len(details) == 1
        assert "enough information" in details[0].lower()

    def test_build_explanation_strong_match(self, generator):
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
        explanation = generator.build_explanation(
            input_data,
            RecommendationCategory.STRONG_MATCH,
            RecommendationReason.SKILLS_MATCH,
            [RecommendationReason.EXPERIENCE_MATCH, RecommendationReason.LOCATION_MATCH],
        )
        assert "strong match" in explanation.lower()
        assert "skills align" in explanation.lower()
        assert "experience level matches" in explanation.lower()
        assert "location matches" in explanation.lower()

    def test_build_explanation_weak_match(self, generator):
        input_data = RecommendationInput(
            score=30,
            recommendation_category=RecommendationCategory.WEAK_MATCH,
            confidence="low",
            skills_score=35,
            experience_score=30,
            requirements_score=35,
            location_score=40,
            salary_score=30,
            explanation="Weak match",
            evidence=[{"type": "skill", "value": "Python"}],
            status="success",
            job_title="Engineer",
        )
        explanation = generator.build_explanation(
            input_data,
            RecommendationCategory.WEAK_MATCH,
            RecommendationReason.MISSING_CRITICAL_SKILLS,
            [RecommendationReason.EXPERIENCE_GAP],
        )
        assert "significant gaps" in explanation.lower()
        assert "missing some critical skills" in explanation.lower()
        assert "experience level doesn't quite match" in explanation.lower()