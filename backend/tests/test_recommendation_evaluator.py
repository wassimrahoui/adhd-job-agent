from __future__ import annotations

import pytest

from app.recommendation.evaluator import RecommendationEvaluator
from app.schemas.recommendation import (
    RecommendationInput,
    RecommendationCategory,
    RecommendationPriority,
    RecommendationReason,
    RecommendationConfig,
)


class TestRecommendationEvaluator:
    @pytest.fixture
    def evaluator(self):
        return RecommendationEvaluator()

    @pytest.fixture
    def config(self):
        return RecommendationConfig(
            strong_match_threshold=80,
            possible_match_threshold=50,
            weak_match_threshold=20,
            min_evidence_for_high_priority=3,
        )

    def test_strong_match_high_priority(self, evaluator):
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
            evidence=[{"type": "skill", "value": "skill1"}, {"type": "skill", "value": "skill2"}, {"type": "skill", "value": "skill3"}, {"type": "skill", "value": "skill4"}],
            status="success",
            job_title="Senior Engineer",
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
        output = evaluator.evaluate(input_data)
        
        assert output.category == RecommendationCategory.STRONG_MATCH
        assert output.priority == RecommendationPriority.HIGH
        assert output.primary_reason == RecommendationReason.SKILLS_MATCH
        assert RecommendationReason.EXPERIENCE_MATCH in output.secondary_reasons
        assert "strong match" in output.explanation.lower()
        assert len(output.action_items) > 0

    def test_strong_match_medium_priority(self, evaluator):
        input_data = RecommendationInput(
            score=82,
            recommendation_category=RecommendationCategory.STRONG_MATCH,
            confidence="high",
            skills_score=85,
            experience_score=80,
            requirements_score=75,
            location_score=90,
            salary_score=75,
            explanation="Good match",
            evidence=[{"type": "skill", "value": "skill1"}, {"type": "skill", "value": "skill2"}],  # Only 2 evidence items
            status="success",
            job_title="Engineer",
        )
        output = evaluator.evaluate(input_data)
        
        assert output.category == RecommendationCategory.STRONG_MATCH
        assert output.priority == RecommendationPriority.MEDIUM

    def test_possible_match_medium_priority(self, evaluator):
        input_data = RecommendationInput(
            score=65,
            recommendation_category=RecommendationCategory.POSSIBLE_MATCH,
            confidence="medium",
            skills_score=70,
            experience_score=60,
            requirements_score=65,
            location_score=70,
            salary_score=65,
            explanation="Possible match",
            evidence=[{"type": "skill", "value": "skill1"}, {"type": "skill", "value": "skill2"}, {"type": "skill", "value": "skill3"}],
            status="success",
            job_title="Engineer",
        )
        output = evaluator.evaluate(input_data)
        
        assert output.category == RecommendationCategory.POSSIBLE_MATCH
        assert output.priority == RecommendationPriority.MEDIUM

    def test_possible_match_low_priority(self, evaluator):
        input_data = RecommendationInput(
            score=55,
            recommendation_category=RecommendationCategory.POSSIBLE_MATCH,
            confidence="medium",
            skills_score=60,
            experience_score=50,
            requirements_score=55,
            location_score=60,
            salary_score=55,
            explanation="Weak possible match",
            evidence=[{"type": "skill", "value": "skill1"}],  # Only 1 evidence item
            status="success",
            job_title="Engineer",
        )
        output = evaluator.evaluate(input_data)
        
        assert output.category == RecommendationCategory.POSSIBLE_MATCH
        assert output.priority == RecommendationPriority.LOW

    def test_weak_match(self, evaluator):
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
            evidence=[{"type": "skill", "value": "skill1"}],
            status="success",
            job_title="Engineer",
        )
        output = evaluator.evaluate(input_data)
        
        assert output.category == RecommendationCategory.WEAK_MATCH
        assert output.priority == RecommendationPriority.LOW
        assert output.primary_reason == RecommendationReason.MISSING_CRITICAL_SKILLS

    def test_not_enough_information(self, evaluator):
        input_data = RecommendationInput(
            score=10,
            recommendation_category=RecommendationCategory.NOT_ENOUGH_INFORMATION,
            confidence="low",
            skills_score=15,
            experience_score=10,
            requirements_score=10,
            location_score=15,
            salary_score=10,
            explanation="Not enough info",
            evidence=[],
            status="success",
            job_title="Engineer",
        )
        output = evaluator.evaluate(input_data)
        
        assert output.category == RecommendationCategory.NOT_ENOUGH_INFORMATION
        assert output.priority == RecommendationPriority.SKIP

    def test_missing_critical_skills_reason(self, evaluator):
        input_data = RecommendationInput(
            score=55,
            recommendation_category=RecommendationCategory.POSSIBLE_MATCH,
            confidence="medium",
            skills_score=30,  # Low skills score triggers missing_critical_skills
            experience_score=75,
            requirements_score=50,
            location_score=70,
            salary_score=60,
            explanation="Skills gap",
            evidence=[{"type": "skill", "value": "skill1"}, {"type": "skill", "value": "skill2"}],
            status="success",
            job_title="Engineer",
        )
        output = evaluator.evaluate(input_data)
        
        assert output.category == RecommendationCategory.POSSIBLE_MATCH
        assert output.primary_reason == RecommendationReason.MISSING_CRITICAL_SKILLS
        assert RecommendationReason.EXPERIENCE_MATCH in output.secondary_reasons
        assert RecommendationReason.LOCATION_MATCH in output.secondary_reasons

    def test_experience_gap_reason(self, evaluator):
        input_data = RecommendationInput(
            score=55,
            recommendation_category=RecommendationCategory.POSSIBLE_MATCH,
            confidence="medium",
            skills_score=75,
            experience_score=30,  # Low experience score triggers experience_gap
            requirements_score=50,
            location_score=70,
            salary_score=60,
            explanation="Experience gap",
            evidence=[{"type": "skill", "value": "skill1"}, {"type": "skill", "value": "skill2"}],
            status="success",
            job_title="Engineer",
        )
        output = evaluator.evaluate(input_data)
        
        assert output.category == RecommendationCategory.POSSIBLE_MATCH
        assert output.primary_reason == RecommendationReason.EXPERIENCE_GAP
        assert RecommendationReason.SKILLS_MATCH in output.secondary_reasons
        assert RecommendationReason.LOCATION_MATCH in output.secondary_reasons

    def test_location_mismatch_reason(self, evaluator):
        input_data = RecommendationInput(
            score=55,
            recommendation_category=RecommendationCategory.POSSIBLE_MATCH,
            confidence="medium",
            skills_score=70,
            experience_score=60,
            requirements_score=50,
            location_score=30,  # Low location score triggers location_mismatch
            salary_score=60,
            explanation="Location mismatch",
            evidence=[{"type": "skill", "value": "skill1"}, {"type": "skill", "value": "skill2"}],
            status="success",
            job_title="Engineer",
        )
        output = evaluator.evaluate(input_data)
        
        assert output.category == RecommendationCategory.POSSIBLE_MATCH
        assert output.primary_reason == RecommendationReason.LOCATION_MISMATCH
        assert RecommendationReason.SKILLS_MATCH in output.secondary_reasons

    def test_salary_below_expectations_reason(self, evaluator):
        input_data = RecommendationInput(
            score=55,
            recommendation_category=RecommendationCategory.POSSIBLE_MATCH,
            confidence="medium",
            skills_score=70,
            experience_score=60,
            requirements_score=50,
            location_score=70,
            salary_score=30,  # Low salary score triggers salary_below_expectations
            explanation="Salary below expectations",
            evidence=[{"type": "skill", "value": "skill1"}, {"type": "skill", "value": "skill2"}],
            status="success",
            job_title="Engineer",
        )
        output = evaluator.evaluate(input_data)
        
        assert output.category == RecommendationCategory.POSSIBLE_MATCH
        assert output.primary_reason == RecommendationReason.SALARY_BELOW_EXPECTATIONS
        assert RecommendationReason.SKILLS_MATCH in output.secondary_reasons
        assert RecommendationReason.LOCATION_MATCH in output.secondary_reasons

    def test_strengths_identification(self, evaluator):
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
            evidence=[{"type": "skill", "value": "skill1"}, {"type": "skill", "value": "skill2"}, {"type": "skill", "value": "skill3"}, {"type": "skill", "value": "skill4"}],
            status="success",
            job_title="Engineer",
        )
        output = evaluator.evaluate(input_data)
        
        assert "Strong skills alignment" in output.strengths
        assert "Relevant experience" in output.strengths
        assert "Location match" in output.strengths
        assert "Salary expectations met" in output.strengths
        assert "Requirements well-covered" in output.strengths

    def test_concerns_identification(self, evaluator):
        input_data = RecommendationInput(
            score=30,
            recommendation_category=RecommendationCategory.WEAK_MATCH,
            confidence="low",
            skills_score=35,
            experience_score=30,
            requirements_score=35,
            location_score=30,
            salary_score=30,
            explanation="Many gaps",
            evidence=[{"type": "skill", "value": "skill1"}],
            status="success",
            job_title="Engineer",
        )
        output = evaluator.evaluate(input_data)
        
        assert "Skills gap identified" in output.concerns
        assert "Experience gap" in output.concerns
        assert "Location mismatch" in output.concerns
        assert "Salary below expectations" in output.concerns
        assert "Many requirements not met" in output.concerns

    def test_action_items_strong_match(self, evaluator):
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
            evidence=[{"type": "skill", "value": "skill1"}, {"type": "skill", "value": "skill2"}, {"type": "skill", "value": "skill3"}, {"type": "skill", "value": "skill4"}],
            status="success",
            job_title="Engineer",
        )
        output = evaluator.evaluate(input_data)
        
        assert any("Apply immediately" in item for item in output.action_items)
        assert any("cover letter" in item.lower() for item in output.action_items)

    def test_action_items_possible_match(self, evaluator):
        input_data = RecommendationInput(
            score=65,
            recommendation_category=RecommendationCategory.POSSIBLE_MATCH,
            confidence="medium",
            skills_score=70,
            experience_score=60,
            requirements_score=65,
            location_score=70,
            salary_score=65,
            explanation="Possible match",
            evidence=[{"type": "skill", "value": "skill1"}, {"type": "skill", "value": "skill2"}, {"type": "skill", "value": "skill3"}],
            status="success",
            job_title="Engineer",
        )
        output = evaluator.evaluate(input_data)
        
        assert any("applying" in item.lower() for item in output.action_items)
        assert any("gap" in item.lower() for item in output.action_items)

    def test_action_items_weak_match(self, evaluator):
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
            evidence=[{"type": "skill", "value": "skill1"}],
            status="success",
            job_title="Engineer",
        )
        output = evaluator.evaluate(input_data)
        
        assert any("gap" in item.lower() for item in output.action_items)
        assert any("better-matched" in item.lower() or "better matched" in item.lower() for item in output.action_items)

    def test_action_items_not_enough_info(self, evaluator):
        input_data = RecommendationInput(
            score=10,
            recommendation_category=RecommendationCategory.NOT_ENOUGH_INFORMATION,
            confidence="low",
            skills_score=15,
            experience_score=10,
            requirements_score=10,
            location_score=15,
            salary_score=10,
            explanation="Not enough info",
            evidence=[],
            status="success",
            job_title="Engineer",
        )
        output = evaluator.evaluate(input_data)
        
        assert any("more information" in item.lower() for item in output.action_items)
        assert any("clarification" in item.lower() for item in output.action_items)

    def test_salary_negotiation_action(self, evaluator):
        input_data = RecommendationInput(
            score=65,
            recommendation_category=RecommendationCategory.POSSIBLE_MATCH,
            confidence="medium",
            skills_score=70,
            experience_score=60,
            requirements_score=65,
            location_score=70,
            salary_score=30,  # Low salary triggers negotiation action
            explanation="Salary below expectations",
            evidence=[{"type": "skill", "value": "skill1"}, {"type": "skill", "value": "skill2"}, {"type": "skill", "value": "skill3"}],
            status="success",
            job_title="Engineer",
        )
        output = evaluator.evaluate(input_data)
        
        assert any("negotiate" in item.lower() for item in output.action_items)

    def test_custom_config(self, config):
        evaluator = RecommendationEvaluator(config=config)
        
        # With custom config, 85 is still strong match (threshold 80)
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
            evidence=[{"type": "skill", "value": "skill1"}, {"type": "skill", "value": "skill2"}, {"type": "skill", "value": "skill3"}, {"type": "skill", "value": "skill4"}, {"type": "skill", "value": "skill5"}],
            status="success",
            job_title="Engineer",
        )
        output = evaluator.evaluate(input_data)
        
        assert output.category == RecommendationCategory.STRONG_MATCH
        assert output.priority == RecommendationPriority.HIGH  # 5 evidence >= min 3

    def test_insufficient_information_fallback(self, evaluator):
        input_data = RecommendationInput(
            score=40,
            recommendation_category=RecommendationCategory.POSSIBLE_MATCH,
            confidence="medium",
            skills_score=50,
            experience_score=50,
            requirements_score=50,
            location_score=50,
            salary_score=50,
            explanation="Average across board",
            evidence=[],
            status="success",
            job_title="Engineer",
        )
        output = evaluator.evaluate(input_data)
        
        # All scores at 50 don't trigger any specific reason, should fall back to insufficient_information
        assert output.primary_reason == RecommendationReason.INSUFFICIENT_INFORMATION