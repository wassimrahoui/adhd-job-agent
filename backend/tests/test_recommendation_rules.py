from __future__ import annotations

import pytest

from app.recommendation.rules import RecommendationRules, RuleResult
from app.schemas.recommendation import (
    RecommendationInput,
    RecommendationCategory,
    RecommendationPriority,
    RecommendationReason,
    RecommendationConfig,
)


class TestRecommendationRules:
    @pytest.fixture
    def rules(self):
        return RecommendationRules()

    @pytest.fixture
    def config(self):
        return RecommendationConfig(
            strong_match_threshold=80,
            possible_match_threshold=50,
            weak_match_threshold=20,
            min_evidence_for_high_priority=3,
        )

    def test_evaluate_category_strong_match(self, rules):
        assert rules.evaluate_category(85) == RecommendationCategory.STRONG_MATCH
        assert rules.evaluate_category(80) == RecommendationCategory.STRONG_MATCH
        assert rules.evaluate_category(100) == RecommendationCategory.STRONG_MATCH

    def test_evaluate_category_possible_match(self, rules):
        assert rules.evaluate_category(65) == RecommendationCategory.POSSIBLE_MATCH
        assert rules.evaluate_category(50) == RecommendationCategory.POSSIBLE_MATCH
        assert rules.evaluate_category(79) == RecommendationCategory.POSSIBLE_MATCH

    def test_evaluate_category_weak_match(self, rules):
        assert rules.evaluate_category(35) == RecommendationCategory.WEAK_MATCH
        assert rules.evaluate_category(20) == RecommendationCategory.WEAK_MATCH
        assert rules.evaluate_category(49) == RecommendationCategory.WEAK_MATCH

    def test_evaluate_category_not_enough_info(self, rules):
        assert rules.evaluate_category(15) == RecommendationCategory.NOT_ENOUGH_INFORMATION
        assert rules.evaluate_category(0) == RecommendationCategory.NOT_ENOUGH_INFORMATION
        assert rules.evaluate_category(19) == RecommendationCategory.NOT_ENOUGH_INFORMATION

    def test_evaluate_priority_strong_match_high(self, rules):
        priority = rules.evaluate_priority(RecommendationCategory.STRONG_MATCH, 4)
        assert priority == RecommendationPriority.HIGH

    def test_evaluate_priority_strong_match_medium(self, rules):
        priority = rules.evaluate_priority(RecommendationCategory.STRONG_MATCH, 2)
        assert priority == RecommendationPriority.MEDIUM

    def test_evaluate_priority_possible_match_medium(self, rules):
        priority = rules.evaluate_priority(RecommendationCategory.POSSIBLE_MATCH, 3)
        assert priority == RecommendationPriority.MEDIUM

    def test_evaluate_priority_possible_match_low(self, rules):
        priority = rules.evaluate_priority(RecommendationCategory.POSSIBLE_MATCH, 1)
        assert priority == RecommendationPriority.LOW

    def test_evaluate_priority_weak_match(self, rules):
        priority = rules.evaluate_priority(RecommendationCategory.WEAK_MATCH, 5)
        assert priority == RecommendationPriority.LOW

    def test_evaluate_priority_not_enough_info(self, rules):
        priority = rules.evaluate_priority(RecommendationCategory.NOT_ENOUGH_INFORMATION, 10)
        assert priority == RecommendationPriority.SKIP

    def test_evaluate_reasons_all_positive(self, rules):
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
        reasons = rules.evaluate_reasons(input_data)
        
        assert RecommendationReason.SKILLS_MATCH in reasons
        assert RecommendationReason.EXPERIENCE_MATCH in reasons
        assert RecommendationReason.LOCATION_MATCH in reasons
        assert RecommendationReason.SALARY_MATCH in reasons
        assert RecommendationReason.REQUIREMENTS_COVERED in reasons
        assert RecommendationReason.MISSING_CRITICAL_SKILLS not in reasons

    def test_evaluate_reasons_negative_prioritized(self, rules):
        input_data = RecommendationInput(
            score=45,
            recommendation_category=RecommendationCategory.POSSIBLE_MATCH,
            confidence="medium",
            skills_score=30,  # Low - triggers negative
            experience_score=75,  # High - triggers positive
            requirements_score=50,
            location_score=70,  # High - triggers positive
            salary_score=60,
            explanation="Mixed match",
            evidence=[{"type": "skill", "value": "Python"}],
            status="success",
            job_title="Engineer",
        )
        reasons = rules.evaluate_reasons(input_data)
        
        # Negative reasons should come first
        assert reasons[0] == RecommendationReason.MISSING_CRITICAL_SKILLS
        assert RecommendationReason.EXPERIENCE_MATCH in reasons
        assert RecommendationReason.LOCATION_MATCH in reasons

    def test_evaluate_reasons_insufficient_info(self, rules):
        input_data = RecommendationInput(
            score=50,
            recommendation_category=RecommendationCategory.POSSIBLE_MATCH,
            confidence="medium",
            skills_score=50,
            experience_score=50,
            requirements_score=50,
            location_score=50,
            salary_score=50,
            explanation="Average",
            evidence=[],
            status="success",
            job_title="Engineer",
        )
        reasons = rules.evaluate_reasons(input_data)
        
        assert reasons == [RecommendationReason.INSUFFICIENT_INFORMATION]

    def test_evaluate_all_combined(self, rules):
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
            evidence=[{"type": "skill", "value": "Python"}] * 4,
            status="success",
            job_title="Engineer",
        )
        result = rules.evaluate_all(input_data)
        
        assert result.category == RecommendationCategory.STRONG_MATCH
        assert result.priority == RecommendationPriority.HIGH
        assert RecommendationReason.SKILLS_MATCH in result.reasons
        assert len(result.reasons) > 0

    def test_custom_config(self, config):
        rules = RecommendationRules(config=config)
        
        # With custom config, 75 is possible match (threshold 50)
        assert rules.evaluate_category(75) == RecommendationCategory.POSSIBLE_MATCH
        # 85 is strong match (threshold 80)
        assert rules.evaluate_category(85) == RecommendationCategory.STRONG_MATCH