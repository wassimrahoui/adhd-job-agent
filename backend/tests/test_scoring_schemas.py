from __future__ import annotations

import pytest

from app.schemas.scoring import (
    ScoringInput,
    ScoringOutput,
    ScoringWeights,
    ScoringConfig,
)
from app.schemas.analysis import (
    SkillMatchItem,
    ExperienceMatchItem,
    RequirementGapItem,
    UnknownRequirementItem,
    EvidenceItem,
    Recommendation,
    Confidence,
    AnalysisStatus,
)


class TestScoringWeights:
    def test_default_weights(self):
        weights = ScoringWeights()
        assert weights.skills_weight == 0.35
        assert weights.experience_weight == 0.25
        assert weights.requirements_weight == 0.20
        assert weights.location_weight == 0.10
        assert weights.salary_weight == 0.10

    def test_custom_weights(self):
        weights = ScoringWeights(
            skills_weight=0.4,
            experience_weight=0.3,
            requirements_weight=0.2,
            location_weight=0.05,
            salary_weight=0.05,
        )
        assert weights.skills_weight == 0.4

    def test_weights_sum_to_one(self):
        # Weights don't have to sum to 1 but we test they can
        weights = ScoringWeights(
            skills_weight=0.4,
            experience_weight=0.3,
            requirements_weight=0.2,
            location_weight=0.05,
            salary_weight=0.05,
        )
        total = (weights.skills_weight + weights.experience_weight + 
                weights.requirements_weight + weights.location_weight + weights.salary_weight)
        assert abs(total - 1.0) < 0.001

    def test_invalid_weight_too_high(self):
        with pytest.raises(Exception):
            ScoringWeights(skills_weight=1.5)

    def test_invalid_weight_negative(self):
        with pytest.raises(Exception):
            ScoringWeights(skills_weight=-0.1)


class TestScoringConfig:
    def test_default_config(self):
        config = ScoringConfig()
        assert config.strong_match_threshold == 80
        assert config.possible_match_threshold == 50
        assert config.weak_match_threshold == 20
        assert config.min_evidence_for_high_confidence == 3
        assert isinstance(config.weights, ScoringWeights)

    def test_custom_thresholds(self):
        config = ScoringConfig(
            strong_match_threshold=85,
            possible_match_threshold=55,
            weak_match_threshold=25,
            min_evidence_for_high_confidence=5,
        )
        assert config.strong_match_threshold == 85
        assert config.possible_match_threshold == 55
        assert config.weak_match_threshold == 25
        assert config.min_evidence_for_high_confidence == 5


class TestScoringInput:
    def test_valid_scoring_input(self):
        input_data = ScoringInput(
            matching_skills=[SkillMatchItem(claim="Python", source_excerpt="requires Python")],
            matching_experience=[ExperienceMatchItem(claim="5 years Python", source_excerpt="5 years exp")],
            missing_requirements=[RequirementGapItem(claim="Kubernetes", source_excerpt="K8s required")],
            unknown_requirements=[UnknownRequirementItem(claim="GraphQL", source_excerpt="GraphQL API")],
            evidence=[EvidenceItem(claim="Salary matches", source_excerpt="60k-80k")],
            explanation="Good match",
            status=AnalysisStatus.SUCCESS,
            job_title="Software Engineer",
            job_company="Tech Corp",
            job_location="Berlin",
            job_work_mode="hybrid",
            job_skills=["Python", "Django"],
            profile_desired_roles=["Backend Engineer"],
            profile_location_preferences=["Berlin", "Remote"],
            profile_remote_preference="hybrid",
            profile_experience_level="mid",
        )
        assert input_data.job_title == "Software Engineer"
        assert len(input_data.matching_skills) == 1
        assert len(input_data.missing_requirements) == 1

    def test_minimal_scoring_input(self):
        input_data = ScoringInput(
            job_title="Engineer",
        )
        assert input_data.job_title == "Engineer"
        assert input_data.matching_skills == []
        assert input_data.status == AnalysisStatus.SUCCESS


class TestScoringOutput:
    def test_valid_scoring_output(self):
        output = ScoringOutput(
            model_used="gpt-4",
            score=85,
            recommendation=Recommendation.STRONG_MATCH,
            confidence=Confidence.HIGH,
            skills_score=90,
            experience_score=80,
            requirements_score=70,
            location_score=95,
            salary_score=85,
            explanation="Excellent match with strong skills alignment",
            evidence=[EvidenceItem(claim="Salary matches", source_excerpt="60k-80k")],
            status=AnalysisStatus.SUCCESS,
        )
        assert output.score == 85
        assert output.recommendation == Recommendation.STRONG_MATCH
        assert output.confidence == Confidence.HIGH

    def test_all_recommendation_values(self):
        for rec in [Recommendation.STRONG_MATCH, Recommendation.POSSIBLE_MATCH, 
                    Recommendation.WEAK_MATCH, Recommendation.NOT_ENOUGH_INFORMATION]:
            output = ScoringOutput(
                model_used="test",
                score=50,
                recommendation=rec,
                confidence=Confidence.MEDIUM,
                skills_score=50,
                experience_score=50,
                requirements_score=50,
                location_score=50,
                salary_score=50,
                explanation="Test",
            )
            assert output.recommendation == rec

    def test_all_confidence_values(self):
        for conf in [Confidence.HIGH, Confidence.MEDIUM, Confidence.LOW]:
            output = ScoringOutput(
                model_used="test",
                score=50,
                recommendation=Recommendation.POSSIBLE_MATCH,
                confidence=conf,
                skills_score=50,
                experience_score=50,
                requirements_score=50,
                location_score=50,
                salary_score=50,
                explanation="Test",
            )
            assert output.confidence == conf

    def test_score_validation(self):
        with pytest.raises(Exception):
            ScoringOutput(
                model_used="test",
                score=150,  # Invalid > 100
                recommendation=Recommendation.STRONG_MATCH,
                confidence=Confidence.HIGH,
                skills_score=50,
                experience_score=50,
                requirements_score=50,
                location_score=50,
                salary_score=50,
                explanation="Test",
            )

    def test_component_score_validation(self):
        with pytest.raises(Exception):
            ScoringOutput(
                model_used="test",
                score=80,
                recommendation=Recommendation.STRONG_MATCH,
                confidence=Confidence.HIGH,
                skills_score=150,  # Invalid > 100
                experience_score=50,
                requirements_score=50,
                location_score=50,
                salary_score=50,
                explanation="Test",
            )