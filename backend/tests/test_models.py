import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models import (
    Profile, ProfileCreate, ProfileUpdate,
    Job, JobCreate, JobUpdate, JobListItem,
    AIAnalysis, AIAnalysisCreate,
    RemotePreference, ExperienceLevel,
    AnalysisStatus, Recommendation, Confidence,
    SkillMatchItem, ExperienceMatchItem,
    RequirementGapItem, UnknownRequirementItem, EvidenceItem
)


class TestProfileModels:
    def test_profile_create_valid(self):
        """Test creating a valid profile."""
        profile = ProfileCreate(
            work_experience="5 years Python",
            technical_skills=["Python", "FastAPI"],
            desired_roles=["Backend Engineer"],
            salary_min=80000,
            salary_max=120000,
        )
        assert profile.work_experience == "5 years Python"
        assert profile.technical_skills == ["Python", "FastAPI"]
        assert profile.desired_roles == ["Backend Engineer"]
        assert profile.salary_min == 80000
        assert profile.salary_max == 120000

    def test_profile_create_defaults(self):
        """Test profile defaults."""
        profile = ProfileCreate()
        assert profile.technical_skills == []
        assert profile.certifications == []
        assert profile.languages == []
        assert profile.desired_roles == []
        assert profile.location_preferences == []
        assert profile.excluded_keywords == []
        assert profile.relevance_threshold == 50
        assert profile.salary_currency == "USD"
        assert profile.remote_preference == RemotePreference.ANY
        assert profile.experience_level == ExperienceLevel.ANY

    def test_profile_invalid_relevance_threshold(self):
        """Test profile validation for relevance_threshold."""
        with pytest.raises(ValidationError):
            ProfileCreate(relevance_threshold=101)
        with pytest.raises(ValidationError):
            ProfileCreate(relevance_threshold=-1)

    def test_profile_update_partial(self):
        """Test partial profile update."""
        update = ProfileUpdate(work_experience="Updated experience")
        assert update.work_experience == "Updated experience"
        # Fields not explicitly set have default values (empty lists for list fields)
        assert update.technical_skills == []
        assert update.networking_experience is None

    def test_profile_model_validation(self):
        """Test full Profile model."""
        dt = datetime(2024, 1, 1)
        profile = Profile(
            id=1,
            work_experience="5 years Python",
            technical_skills=["Python"],
            created_at=dt,
            updated_at=dt,
        )
        assert profile.id == 1
        assert profile.work_experience == "5 years Python"


class TestJobModels:
    def test_job_create_valid(self):
        """Test creating a valid job."""
        job = JobCreate(
            adzuna_id="test-123",
            title="Python Developer",
            company="Tech Corp",
            location="San Francisco",
            redirect_url="https://adzuna.com/job/test-123",
        )
        assert job.adzuna_id == "test-123"
        assert job.title == "Python Developer"
        assert job.company == "Tech Corp"

    def test_job_create_defaults(self):
        """Test job defaults."""
        job = JobCreate(adzuna_id="test-123", title="Developer")
        assert job.skills == []
        assert job.raw_evidence == {}
        assert job.passed_prefilter is False
        assert job.salary_is_predicted is False

    def test_job_update_partial(self):
        """Test partial job update."""
        update = JobUpdate(title="Updated Title")
        assert update.title == "Updated Title"
        assert update.company is None

    def test_job_model_validation(self):
        """Test full Job model."""
        dt = datetime(2024, 1, 1)
        job = Job(
            id=1,
            adzuna_id="test-123",
            title="Python Developer",
            discovered_at=dt,
        )
        assert job.id == 1
        assert job.adzuna_id == "test-123"

    def test_job_list_item(self):
        """Test JobListItem model."""
        dt = datetime(2024, 1, 1)
        item = JobListItem(
            id=1,
            adzuna_id="test-123",
            title="Python Developer",
            discovered_at=dt,
            passed_prefilter=True,
        )
        assert item.id == 1
        assert item.passed_prefilter is True


class TestAIAnalysisModels:
    def test_analysis_create_valid(self):
        """Test creating a valid analysis."""
        analysis = AIAnalysisCreate(
            job_id=1,
            model_used="qwen2.5:14b-instruct-q4_K_M",
            score=85,
            recommendation=Recommendation.STRONG_MATCH,
            confidence=Confidence.HIGH,
            explanation="Good match",
        )
        assert analysis.job_id == 1
        assert analysis.score == 85
        assert analysis.recommendation == Recommendation.STRONG_MATCH
        assert analysis.confidence == Confidence.HIGH

    def test_analysis_create_defaults(self):
        """Test analysis defaults."""
        analysis = AIAnalysisCreate(job_id=1, model_used="test-model")
        assert analysis.matching_skills == []
        assert analysis.matching_experience == []
        assert analysis.missing_requirements == []
        assert analysis.unknown_requirements == []
        assert analysis.evidence == []
        assert analysis.status == AnalysisStatus.AI_UNAVAILABLE

    def test_analysis_score_validation(self):
        """Test score validation."""
        with pytest.raises(ValidationError):
            AIAnalysisCreate(job_id=1, model_used="test", score=101)
        with pytest.raises(ValidationError):
            AIAnalysisCreate(job_id=1, model_used="test", score=-1)

    def test_skill_match_item(self):
        """Test SkillMatchItem."""
        item = SkillMatchItem(claim="Python", source_excerpt="Python experience")
        assert item.claim == "Python"
        assert item.source_excerpt == "Python experience"

    def test_evidence_item(self):
        """Test EvidenceItem."""
        item = EvidenceItem(claim="Remote work", source_excerpt="Remote position")
        assert item.claim == "Remote work"

    def test_requirement_gap_item(self):
        """Test RequirementGapItem."""
        item = RequirementGapItem(
            claim="5 years Java",
            source_excerpt="Requires 5 years Java experience"
        )
        assert item.claim == "5 years Java"

    def test_analysis_model_validation(self):
        """Test full AIAnalysis model."""
        dt = datetime(2024, 1, 1)
        analysis = AIAnalysis(
            id=1,
            job_id=1,
            model_used="test-model",
            created_at=dt,
        )
        assert analysis.id == 1
        assert analysis.job_id == 1