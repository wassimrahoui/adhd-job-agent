from __future__ import annotations

import pytest

from app.recommendation.confidence import ConfidenceHandler, ConfidenceLevel
from app.schemas.recommendation import RecommendationInput, RecommendationCategory


class TestConfidenceHandler:
    @pytest.fixture
    def handler(self):
        return ConfidenceHandler()

    def test_determine_confidence_from_score_high(self, handler):
        assert handler.determine_confidence_from_score(85) == ConfidenceLevel.HIGH
        assert handler.determine_confidence_from_score(80) == ConfidenceLevel.HIGH
        assert handler.determine_confidence_from_score(100) == ConfidenceLevel.HIGH

    def test_determine_confidence_from_score_medium(self, handler):
        assert handler.determine_confidence_from_score(65) == ConfidenceLevel.MEDIUM
        assert handler.determine_confidence_from_score(50) == ConfidenceLevel.MEDIUM
        assert handler.determine_confidence_from_score(79) == ConfidenceLevel.MEDIUM

    def test_determine_confidence_from_score_low(self, handler):
        assert handler.determine_confidence_from_score(35) == ConfidenceLevel.LOW
        assert handler.determine_confidence_from_score(0) == ConfidenceLevel.LOW
        assert handler.determine_confidence_from_score(49) == ConfidenceLevel.LOW

    def test_determine_confidence_from_evidence_high(self, handler):
        assert handler.determine_confidence_from_evidence(5) == ConfidenceLevel.HIGH
        assert handler.determine_confidence_from_evidence(4) == ConfidenceLevel.HIGH

    def test_determine_confidence_from_evidence_medium(self, handler):
        assert handler.determine_confidence_from_evidence(3) == ConfidenceLevel.MEDIUM
        assert handler.determine_confidence_from_evidence(2) == ConfidenceLevel.MEDIUM

    def test_determine_confidence_from_evidence_low(self, handler):
        assert handler.determine_confidence_from_evidence(1) == ConfidenceLevel.LOW
        assert handler.determine_confidence_from_evidence(0) == ConfidenceLevel.LOW

    def test_determine_confidence_combined_score_high(self, handler):
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
            evidence=[{"type": "skill", "value": "Python"}] * 5,
            status="success",
            job_title="Engineer",
        )
        confidence = handler.determine_confidence(input_data)
        assert confidence == ConfidenceLevel.HIGH

    def test_determine_confidence_combined_medium(self, handler):
        input_data = RecommendationInput(
            score=65,
            recommendation_category=RecommendationCategory.POSSIBLE_MATCH,
            confidence="medium",
            skills_score=70,
            experience_score=60,
            requirements_score=65,
            location_score=70,
            salary_score=65,
            explanation="Good match",
            evidence=[{"type": "skill", "value": "Python"}] * 3,
            status="success",
            job_title="Engineer",
        )
        confidence = handler.determine_confidence(input_data)
        assert confidence == ConfidenceLevel.MEDIUM

    def test_determine_confidence_combined_low(self, handler):
        input_data = RecommendationInput(
            score=35,
            recommendation_category=RecommendationCategory.WEAK_MATCH,
            confidence="low",
            skills_score=40,
            experience_score=30,
            requirements_score=35,
            location_score=40,
            salary_score=30,
            explanation="Weak match",
            evidence=[{"type": "skill", "value": "Python"}],
            status="success",
            job_title="Engineer",
        )
        confidence = handler.determine_confidence(input_data)
        assert confidence == ConfidenceLevel.LOW

    def test_determine_confidence_tie_breaker(self, handler):
        # Score says HIGH, evidence says LOW, input says MEDIUM
        # Should pick HIGH (highest priority in tie)
        input_data = RecommendationInput(
            score=85,
            recommendation_category=RecommendationCategory.STRONG_MATCH,
            confidence="medium",
            skills_score=90,
            experience_score=85,
            requirements_score=80,
            location_score=95,
            salary_score=80,
            explanation="Mixed signals",
            evidence=[],  # Low evidence
            status="success",
            job_title="Engineer",
        )
        confidence = handler.determine_confidence(input_data)
        # Score=HIGH, evidence=LOW, input=MEDIUM -> HIGH wins tie
        assert confidence == ConfidenceLevel.HIGH

    def test_adjust_confidence_for_missing_data(self, handler):
        assert handler.adjust_confidence_for_missing_data(ConfidenceLevel.HIGH, []) == ConfidenceLevel.HIGH
        assert handler.adjust_confidence_for_missing_data(ConfidenceLevel.HIGH, ["field1"]) == ConfidenceLevel.MEDIUM
        assert handler.adjust_confidence_for_missing_data(ConfidenceLevel.HIGH, ["field1", "field2"]) == ConfidenceLevel.LOW
        assert handler.adjust_confidence_for_missing_data(ConfidenceLevel.MEDIUM, ["field1"]) == ConfidenceLevel.LOW
        assert handler.adjust_confidence_for_missing_data(ConfidenceLevel.LOW, ["field1"]) == ConfidenceLevel.LOW

    def test_custom_thresholds(self):
        handler = ConfidenceHandler(
            high_threshold=90,
            medium_threshold=60,
            high_evidence_threshold=5,
            medium_evidence_threshold=3,
        )
        assert handler.determine_confidence_from_score(85) == ConfidenceLevel.MEDIUM
        assert handler.determine_confidence_from_score(90) == ConfidenceLevel.HIGH
        assert handler.determine_confidence_from_evidence(4) == ConfidenceLevel.MEDIUM
        assert handler.determine_confidence_from_evidence(5) == ConfidenceLevel.HIGH