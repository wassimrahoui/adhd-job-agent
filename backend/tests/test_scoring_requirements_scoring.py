from __future__ import annotations

import pytest

from app.scoring.requirements_scoring import (
    calculate_requirements_score,
    get_requirements_breakdown,
    categorize_missing_requirements,
)
from app.schemas.scoring import ScoringInput, ScoringConfig
from app.schemas.analysis import (
    SkillMatchItem,
    ExperienceMatchItem,
    RequirementGapItem,
    UnknownRequirementItem,
    AnalysisStatus,
)


class TestCalculateRequirementsScore:
    def setup_method(self):
        self.config = ScoringConfig()

    def test_no_requirements_returns_neutral(self):
        input_data = ScoringInput(job_title="Engineer")
        score = calculate_requirements_score(input_data, self.config)
        assert score == 50

    def test_all_met_requirements(self):
        input_data = ScoringInput(
            job_title="Engineer",
            matching_skills=[
                SkillMatchItem(claim="Python", source_excerpt="requires Python"),
                SkillMatchItem(claim="Django", source_excerpt="Django framework"),
            ],
            matching_experience=[
                ExperienceMatchItem(claim="5 years Python", source_excerpt="5 years"),
            ],
            missing_requirements=[],
            unknown_requirements=[],
        )
        # 3 met, 0 missing, 0 unknown -> 100% -> 100
        score = calculate_requirements_score(input_data, self.config)
        assert score == 100

    def test_half_met_requirements(self):
        input_data = ScoringInput(
            job_title="Engineer",
            matching_skills=[
                SkillMatchItem(claim="Python", source_excerpt="requires Python"),
            ],
            matching_experience=[],
            missing_requirements=[
                RequirementGapItem(claim="Django", source_excerpt="Django required"),
            ],
            unknown_requirements=[],
        )
        # 1 met, 1 missing, 0 unknown -> 50% -> 15 + 0.5 * 85 = 57.5 -> 58
        score = calculate_requirements_score(input_data, self.config)
        assert score == 58

    def test_mostly_missing(self):
        input_data = ScoringInput(
            job_title="Engineer",
            matching_skills=[],
            matching_experience=[],
            missing_requirements=[
                RequirementGapItem(claim="Python", source_excerpt="requires Python"),
                RequirementGapItem(claim="Django", source_excerpt="Django required"),
                RequirementGapItem(claim="PostgreSQL", source_excerpt="PostgreSQL required"),
            ],
            unknown_requirements=[],
        )
        # 0 met, 3 missing, 0 unknown -> 0% -> 15
        score = calculate_requirements_score(input_data, self.config)
        assert score == 15

    def test_with_unknown_requirements(self):
        input_data = ScoringInput(
            job_title="Engineer",
            matching_skills=[
                SkillMatchItem(claim="Python", source_excerpt="requires Python"),
            ],
            matching_experience=[],
            missing_requirements=[
                RequirementGapItem(claim="Django", source_excerpt="Django required"),
            ],
            unknown_requirements=[
                UnknownRequirementItem(claim="GraphQL", source_excerpt="GraphQL API"),
            ],
        )
        # 1 met, 1 missing, 1 unknown -> 33% -> 15 + 0.33 * 85 = 43
        score = calculate_requirements_score(input_data, self.config)
        assert score == 43


class TestGetRequirementsBreakdown:
    def test_breakdown(self):
        input_data = ScoringInput(
            job_title="Engineer",
            matching_skills=[
                SkillMatchItem(claim="Python", source_excerpt="requires Python"),
                SkillMatchItem(claim="Django", source_excerpt="Django framework"),
            ],
            matching_experience=[
                ExperienceMatchItem(claim="5 years Python", source_excerpt="5 years"),
            ],
            missing_requirements=[
                RequirementGapItem(claim="Redis", source_excerpt="Redis required"),
            ],
            unknown_requirements=[
                UnknownRequirementItem(claim="GraphQL", source_excerpt="GraphQL API"),
            ],
        )
        breakdown = get_requirements_breakdown(input_data)
        assert breakdown["met"] == 3
        assert breakdown["missing"] == 1
        assert breakdown["unknown"] == 1
        assert breakdown["total"] == 5
        assert breakdown["met_ratio"] == 0.6


class TestCategorizeMissingRequirements:
    def test_categorize_skills(self):
        input_data = ScoringInput(
            job_title="Engineer",
            missing_requirements=[
                RequirementGapItem(claim="Python", source_excerpt="requires Python"),
                RequirementGapItem(claim="Django framework", source_excerpt="Django"),
                RequirementGapItem(claim="AWS cloud", source_excerpt="AWS"),
                RequirementGapItem(claim="Kubernetes orchestration", source_excerpt="K8s"),
            ],
        )
        categories = categorize_missing_requirements(input_data)
        assert "Python" in categories["skill"]
        assert "Django framework" in categories["skill"]
        assert "AWS cloud" in categories["skill"]
        assert "Kubernetes orchestration" in categories["skill"]

    def test_categorize_experience(self):
        input_data = ScoringInput(
            job_title="Engineer",
            missing_requirements=[
                RequirementGapItem(claim="5 years experience", source_excerpt="5 years"),
                RequirementGapItem(claim="Senior level", source_excerpt="Senior"),
                RequirementGapItem(claim="Led team of 5", source_excerpt="led team"),
            ],
        )
        categories = categorize_missing_requirements(input_data)
        assert "5 years experience" in categories["experience"]
        assert "Senior level" in categories["experience"]
        assert "Led team of 5" in categories["experience"]

    def test_categorize_certification(self):
        input_data = ScoringInput(
            job_title="Engineer",
            missing_requirements=[
                RequirementGapItem(claim="AWS Certified", source_excerpt="AWS cert"),
                RequirementGapItem(claim="PMP certification", source_excerpt="PMP"),
            ],
        )
        categories = categorize_missing_requirements(input_data)
        assert "AWS Certified" in categories["certification"]
        assert "PMP certification" in categories["certification"]

    def test_categorize_education(self):
        input_data = ScoringInput(
            job_title="Engineer",
            missing_requirements=[
                RequirementGapItem(claim="Bachelor degree", source_excerpt="BS required"),
                RequirementGapItem(claim="Master in CS", source_excerpt="MS degree"),
            ],
        )
        categories = categorize_missing_requirements(input_data)
        assert "Bachelor degree" in categories["education"]
        assert "Master in CS" in categories["education"]

    def test_categorize_other(self):
        input_data = ScoringInput(
            job_title="Engineer",
            missing_requirements=[
                RequirementGapItem(claim="Security clearance", source_excerpt="clearance"),
                RequirementGapItem(claim="Willing to travel", source_excerpt="travel"),
            ],
        )
        categories = categorize_missing_requirements(input_data)
        assert "Security clearance" in categories["other"]
        assert "Willing to travel" in categories["other"]