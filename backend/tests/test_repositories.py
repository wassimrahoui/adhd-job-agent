import pytest
from datetime import datetime, timezone

from app.models import (
    ProfileCreate, JobCreate, AIAnalysisCreate,
    RemotePreference, ExperienceLevel,
    AnalysisStatus, Recommendation, Confidence
)
from app.repositories import ProfileRepository, JobRepository, AIAnalysisRepository


class TestProfileRepository:
    @pytest.mark.asyncio
    async def test_get_profile_not_exists(self, profile_repo):
        """Test getting profile when none exists."""
        profile = await profile_repo.get_profile()
        assert profile is None

    @pytest.mark.asyncio
    async def test_create_profile(self, profile_repo):
        """Test creating a profile."""
        profile_data = ProfileCreate(
            work_experience="5 years Python",
            technical_skills=["Python", "FastAPI"],
            desired_roles=["Backend Engineer"],
            salary_min=80000,
            salary_max=120000,
        )
        profile = await profile_repo.upsert_profile(profile_data)
        
        assert profile.id == 1
        assert profile.work_experience == "5 years Python"
        assert profile.technical_skills == ["Python", "FastAPI"]
        assert profile.desired_roles == ["Backend Engineer"]
        assert profile.salary_min == 80000
        assert profile.salary_max == 120000

    @pytest.mark.asyncio
    async def test_get_profile_exists(self, profile_repo):
        """Test getting existing profile."""
        profile_data = ProfileCreate(work_experience="Test experience")
        await profile_repo.upsert_profile(profile_data)
        
        profile = await profile_repo.get_profile()
        assert profile is not None
        assert profile.work_experience == "Test experience"

    @pytest.mark.asyncio
    async def test_update_profile(self, profile_repo):
        """Test updating a profile."""
        # Create initial profile
        profile_data = ProfileCreate(work_experience="Initial")
        await profile_repo.upsert_profile(profile_data)
        
        # Update profile
        update_data = ProfileCreate(work_experience="Updated", salary_min=90000)
        profile = await profile_repo.upsert_profile(update_data)
        
        assert profile.work_experience == "Updated"
        assert profile.salary_min == 90000

    @pytest.mark.asyncio
    async def test_partial_update_profile(self, profile_repo):
        """Test partial profile update."""
        from app.models import ProfileUpdate
        
        # Create initial profile
        profile_data = ProfileCreate(work_experience="Initial", salary_min=80000)
        await profile_repo.upsert_profile(profile_data)
        
        # Partial update
        update_data = ProfileUpdate(salary_max=150000)
        profile = await profile_repo.upsert_profile(update_data)
        
        assert profile.work_experience == "Initial"  # Unchanged
        assert profile.salary_min == 80000  # Unchanged
        assert profile.salary_max == 150000  # Updated


class TestJobRepository:
    @pytest.mark.asyncio
    async def test_create_job(self, job_repo):
        """Test creating a job."""
        job_data = JobCreate(
            adzuna_id="test-123",
            title="Python Developer",
            company="Tech Corp",
            location="San Francisco",
            redirect_url="https://adzuna.com/job/test-123",
        )
        job = await job_repo.create_job(job_data)
        
        assert job.id is not None
        assert job.adzuna_id == "test-123"
        assert job.title == "Python Developer"
        assert job.company == "Tech Corp"

    @pytest.mark.asyncio
    async def test_get_job(self, job_repo):
        """Test getting a job by ID."""
        job_data = JobCreate(adzuna_id="test-456", title="Developer")
        created = await job_repo.create_job(job_data)
        
        job = await job_repo.get_job(created.id)
        assert job is not None
        assert job.id == created.id
        assert job.adzuna_id == "test-456"

    @pytest.mark.asyncio
    async def test_get_job_by_adzuna_id(self, job_repo):
        """Test getting a job by Adzuna ID."""
        job_data = JobCreate(adzuna_id="test-789", title="Developer")
        await job_repo.create_job(job_data)
        
        job = await job_repo.get_job_by_adzuna_id("test-789")
        assert job is not None
        assert job.adzuna_id == "test-789"

    @pytest.mark.asyncio
    async def test_list_jobs(self, job_repo):
        """Test listing jobs."""
        # Create multiple jobs
        for i in range(3):
            job_data = JobCreate(adzuna_id=f"test-{i}", title=f"Job {i}")
            await job_repo.create_job(job_data)
        
        jobs = await job_repo.list_jobs(limit=10)
        assert len(jobs) == 3

    @pytest.mark.asyncio
    async def test_list_jobs_with_prefilter(self, job_repo):
        """Test listing jobs with prefilter filter."""
        job1 = JobCreate(adzuna_id="prefilter-1", title="Job 1", passed_prefilter=True)
        job2 = JobCreate(adzuna_id="prefilter-2", title="Job 2", passed_prefilter=False)
        await job_repo.create_job(job1)
        await job_repo.create_job(job2)
        
        passed = await job_repo.list_jobs(passed_prefilter=True)
        failed = await job_repo.list_jobs(passed_prefilter=False)
        
        assert len(passed) == 1
        assert passed[0].adzuna_id == "prefilter-1"
        assert len(failed) == 1
        assert failed[0].adzuna_id == "prefilter-2"

    @pytest.mark.asyncio
    async def test_update_job(self, job_repo):
        """Test updating a job."""
        from app.models import JobUpdate
        
        job_data = JobCreate(adzuna_id="update-test", title="Original")
        created = await job_repo.create_job(job_data)
        
        update_data = JobUpdate(title="Updated", salary_min=100000)
        updated = await job_repo.update_job(created.id, update_data)
        
        assert updated is not None
        assert updated.title == "Updated"
        assert updated.salary_min == 100000

    @pytest.mark.asyncio
    async def test_delete_job(self, job_repo):
        """Test deleting a job."""
        job_data = JobCreate(adzuna_id="delete-test", title="To Delete")
        created = await job_repo.create_job(job_data)
        
        result = await job_repo.delete_job(created.id)
        assert result is True
        
        job = await job_repo.get_job(created.id)
        assert job is None

    @pytest.mark.asyncio
    async def test_job_skills_json(self, job_repo):
        """Test job skills are stored as JSON."""
        job_data = JobCreate(
            adzuna_id="skills-test",
            title="Developer",
            skills=["Python", "FastAPI", "PostgreSQL"]
        )
        job = await job_repo.create_job(job_data)
        
        assert job.skills == ["Python", "FastAPI", "PostgreSQL"]


class TestAIAnalysisRepository:
    @pytest.mark.asyncio
    async def test_create_analysis(self, analysis_repo, job_repo):
        """Test creating an analysis."""
        # First create a job
        job = await job_repo.create_job(JobCreate(adzuna_id="analysis-test", title="Job"))
        
        analysis_data = AIAnalysisCreate(
            job_id=job.id,
            model_used="qwen2.5:14b-instruct-q4_K_M",
            score=85,
            recommendation=Recommendation.STRONG_MATCH,
            confidence=Confidence.HIGH,
            explanation="Great match",
        )
        analysis = await analysis_repo.create_analysis(analysis_data)
        
        assert analysis.id is not None
        assert analysis.job_id == job.id
        assert analysis.score == 85
        assert analysis.recommendation == Recommendation.STRONG_MATCH

    @pytest.mark.asyncio
    async def test_get_analysis(self, analysis_repo, job_repo):
        """Test getting an analysis by ID."""
        job = await job_repo.create_job(JobCreate(adzuna_id="get-analysis", title="Job"))
        analysis_data = AIAnalysisCreate(job_id=job.id, model_used="test-model")
        created = await analysis_repo.create_analysis(analysis_data)
        
        analysis = await analysis_repo.get_analysis(created.id)
        assert analysis is not None
        assert analysis.id == created.id

    @pytest.mark.asyncio
    async def test_get_analyses_for_job(self, analysis_repo, job_repo):
        """Test getting all analyses for a job."""
        job = await job_repo.create_job(JobCreate(adzuna_id="multi-analysis", title="Job"))
        
        # Create multiple analyses
        for i in range(3):
            analysis_data = AIAnalysisCreate(job_id=job.id, model_used=f"model-{i}")
            await analysis_repo.create_analysis(analysis_data)
        
        analyses = await analysis_repo.get_analyses_for_job(job.id)
        assert len(analyses) == 3

    @pytest.mark.asyncio
    async def test_get_latest_analysis_for_job(self, analysis_repo, job_repo):
        """Test getting latest analysis for a job."""
        job = await job_repo.create_job(JobCreate(adzuna_id="latest-analysis", title="Job"))
        
        # Create multiple analyses
        for i in range(3):
            analysis_data = AIAnalysisCreate(
                job_id=job.id, 
                model_used=f"model-{i}",
                score=80 + i
            )
            await analysis_repo.create_analysis(analysis_data)
        
        latest = await analysis_repo.get_latest_analysis_for_job(job.id)
        assert latest is not None
        # Should be the last one created (highest ID)
        assert latest.model_used == "model-2"

    @pytest.mark.asyncio
    async def test_analysis_empty_lists(self, analysis_repo, job_repo):
        """Test analysis with empty lists."""
        job = await job_repo.create_job(JobCreate(adzuna_id="empty-lists", title="Job"))
        
        analysis_data = AIAnalysisCreate(
            job_id=job.id,
            model_used="test-model",
            matching_skills=[],
            matching_experience=[],
            missing_requirements=[],
            unknown_requirements=[],
            evidence=[],
        )
        analysis = await analysis_repo.create_analysis(analysis_data)
        
        assert analysis.matching_skills == []
        assert analysis.matching_experience == []
        assert analysis.missing_requirements == []
        assert analysis.unknown_requirements == []
        assert analysis.evidence == []