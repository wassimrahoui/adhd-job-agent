from __future__ import annotations

import pytest
from datetime import datetime
from app.schemas.analysis import (
    AnalysisStatus,
    AnalysisJobInput,
    AnalysisProfileInput,
    AnalysisInput,
    AnalysisOutput,
    SkillMatchItem,
    ExperienceMatchItem,
    RequirementGapItem,
    UnknownRequirementItem,
    EvidenceItem,
    Recommendation,
    Confidence,
)


class TestAnalysisStatus:
    def test_status_values(self):
        assert AnalysisStatus.SUCCESS == "success"
        assert AnalysisStatus.REJECTED == "rejected"
        assert AnalysisStatus.AI_UNAVAILABLE == "ai_unavailable"
        assert AnalysisStatus.PENDING == "pending"
        assert AnalysisStatus.FAILED == "failed"


class TestAnalysisJobInput:
    def test_valid_job_input(self):
        job = AnalysisJobInput(
            id=1,
            adzuna_id="test-123",
            title="Software Engineer",
            company="Test Corp",
            location="San Francisco, CA",
            work_mode="remote",
            employment_type="full_time",
            salary_min=100000,
            salary_max=150000,
            salary_currency="USD",
            salary_is_predicted=False,
            description="Great job",
            requirements="Python, FastAPI",
            skills=["Python", "FastAPI"],
            redirect_url="https://example.com/job",
            posted_at=datetime(2024, 1, 1),
        )
        assert job.title == "Software Engineer"
        assert job.salary_min == 100000
        assert job.work_mode == "remote"

    def test_job_input_minimal(self):
        job = AnalysisJobInput(
            id=1,
            adzuna_id="test-123",
            title="Software Engineer",
        )
        assert job.company is None
        assert job.skills == []
        assert job.raw_evidence == {}


class TestAnalysisProfileInput:
    def test_valid_profile_input(self):
        profile = AnalysisProfileInput(
            work_experience="5 years Python",
            technical_skills=["Python", "FastAPI", "SQL"],
            networking_experience="CCNA",
            education="BS Computer Science",
            certifications=["AWS Solutions Architect"],
            languages=["English", "Spanish"],
            desired_roles=["Software Engineer", "Backend Developer"],
            location_preferences=["San Francisco", "Remote"],
            salary_min=100000,
            salary_max=150000,
            salary_currency="USD",
            remote_preference="remote",
            experience_level="senior",
            excluded_keywords=["sales", "marketing"],
            relevance_threshold=50,
        )
        assert profile.salary_min == 100000
        assert profile.remote_preference == "remote"
        assert "sales" in profile.excluded_keywords

    def test_profile_input_defaults(self):
        profile = AnalysisProfileInput()
        assert profile.technical_skills == []
        assert profile.desired_roles == []
        assert profile.location_preferences == []
        assert profile.salary_currency == "USD"
        assert profile.remote_preference == "any"
        assert profile.experience_level == "any"
        assert profile.relevance_threshold == 50


class TestAnalysisInput:
    def test_valid_analysis_input(self):
        job = AnalysisJobInput(
            id=1,
            adzuna_id="test-123",
            title="Software Engineer",
        )
        profile = AnalysisProfileInput()
        input_data = AnalysisInput(job=job, profile=profile)
        assert input_data.job.title == "Software Engineer"
        assert input_data.profile.salary_currency == "USD"


class TestAnalysisOutput:
    def test_valid_output(self):
        output = AnalysisOutput(
            model_used="llama3:70b",
            score=85,
            recommendation=Recommendation.STRONG_MATCH,
            confidence=Confidence.HIGH,
            matching_skills=[
                SkillMatchItem(claim="Python", source_excerpt="5 years Python experience"),
            ],
            matching_experience=[
                ExperienceMatchItem(claim="Backend development", source_excerpt="Built APIs"),
            ],
            missing_requirements=[
                RequirementGapItem(claim="Kubernetes", source_excerpt="Requires K8s experience"),
            ],
            unknown_requirements=[
                UnknownRequirementItem(claim="GraphQL", source_excerpt="GraphQL API experience"),
            ],
            explanation="Strong match for Python backend role",
            evidence=[
                EvidenceItem(claim="Salary matches", source_excerpt="120k-150k range"),
            ],
            status=AnalysisStatus.SUCCESS,
        )
        assert output.model_used == "llama3:70b"
        assert output.score == 85
        assert output.recommendation == Recommendation.STRONG_MATCH
        assert len(output.matching_skills) == 1
        assert len(output.missing_requirements) == 1

    def test_output_defaults(self):
        output = AnalysisOutput(model_used="llama3:70b")
        assert output.score is None
        assert output.recommendation is None
        assert output.confidence is None
        assert output.matching_skills == []
        assert output.missing_requirements == []
        assert output.status == AnalysisStatus.SUCCESS

    def test_score_validation(self):
        with pytest.raises(Exception):
            AnalysisOutput(model_used="test", score=101)
        with pytest.raises(Exception):
            AnalysisOutput(model_used="test", score=-1)

    def test_recommendation_enum(self):
        assert Recommendation.STRONG_MATCH == "strong_match"
        assert Recommendation.POSSIBLE_MATCH == "possible_match"
        assert Recommendation.WEAK_MATCH == "weak_match"
        assert Recommendation.NOT_ENOUGH_INFORMATION == "not_enough_information"

    def test_confidence_enum(self):
        assert Confidence.HIGH == "high"
        assert Confidence.MEDIUM == "medium"
        assert Confidence.LOW == "low"