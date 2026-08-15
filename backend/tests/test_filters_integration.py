from __future__ import annotations

import pytest
import pytest_asyncio
from app.db import Database
from app.repositories import ProfileRepository, JobRepository
from app.job_sources import normalize_job
from app.job_sources.schemas import RawJobRecord, AdzunaCompany, AdzunaArea, AdzunaCategory
from app.filters import (
    run_pre_filter_pipeline,
    PreFilterInput,
    PreFilterConfig,
    PreFilterJobInput,
    PreFilterProfileInput,
)
from app.schemas.search import SearchResponse


@pytest_asyncio.fixture
async def db():
    db = Database(":memory:")
    await db.connect()
    yield db
    await db.close()


@pytest_asyncio.fixture
async def profile_repo(db):
    return ProfileRepository(db)


@pytest_asyncio.fixture
async def job_repo(db):
    return JobRepository(db)


class TestPrefilterIntegration:
    @pytest.mark.asyncio
    async def test_search_creates_jobs_with_prefilter_status(self, profile_repo, job_repo):
        """Test that search pipeline creates jobs with prefilter status."""
        # Create a profile
        from app.models import ProfileCreate
        profile_data = ProfileCreate(
            location_preferences=["San Francisco"],
            salary_min=100000,
            salary_max=200000,
            remote_preference="remote",
            excluded_keywords=["sales"],
        )
        await profile_repo.upsert_profile(profile_data)
        
        # Create a raw job from Adzuna-like data
        raw_job = RawJobRecord(
            id="test-1",
            title="Software Engineer",
            company=AdzunaCompany(display_name="Tech Corp"),
            location=AdzunaArea(display_name="San Francisco, CA"),
            contract_type="permanent",
            contract_time="remote",
            category=AdzunaCategory(label="IT Jobs"),
            salary_min=120000,
            salary_max=150000,
            salary_is_predicted=False,
            description="Great software engineering role",
            redirect_url="https://example.com/job/1",
            created="2024-01-01T00:00:00Z",
        )
        
        job_create = normalize_job(raw_job)
        new_job = await job_repo.create_job(job_create)
        
        # Run pre-filter
        profile = await profile_repo.get_profile()
        
        prefilter_profile = PreFilterProfileInput(
            work_experience=profile.work_experience,
            technical_skills=profile.technical_skills or [],
            networking_experience=profile.networking_experience,
            education=profile.education,
            certifications=profile.certifications or [],
            languages=profile.languages or [],
            desired_roles=profile.desired_roles or [],
            location_preferences=profile.location_preferences or [],
            salary_min=profile.salary_min,
            salary_max=profile.salary_max,
            salary_currency=profile.salary_currency,
            remote_preference=profile.remote_preference.value if hasattr(profile.remote_preference, 'value') else profile.remote_preference,
            experience_level=profile.experience_level.value if hasattr(profile.experience_level, 'value') else profile.experience_level,
            excluded_keywords=profile.excluded_keywords or [],
            relevance_threshold=profile.relevance_threshold,
        )
        
        prefilter_job = PreFilterJobInput(
            id=new_job.id,
            adzuna_id=new_job.adzuna_id,
            title=new_job.title,
            company=new_job.company,
            location=new_job.location,
            work_mode=new_job.work_mode,
            employment_type=new_job.employment_type,
            salary_min=new_job.salary_min,
            salary_max=new_job.salary_max,
            salary_currency=new_job.salary_currency,
            salary_is_predicted=new_job.salary_is_predicted,
            description=new_job.description,
            requirements=new_job.requirements,
            skills=new_job.skills or [],
            redirect_url=new_job.redirect_url,
            posted_at=new_job.posted_at,
            raw_evidence=new_job.raw_evidence or {},
        )
        
        prefilter_input = PreFilterInput(job=prefilter_job, profile=prefilter_profile)
        prefilter_result = run_pre_filter_pipeline(prefilter_input, PreFilterConfig())
        
        # Update job with pre-filter result
        await job_repo.update_prefilter_status(new_job.id, prefilter_result.overall_result == "pass")
        
        # Verify
        updated_job = await job_repo.get_job(new_job.id)
        assert updated_job.passed_prefilter is True

    @pytest.mark.asyncio
    async def test_search_filters_out_mismatched_location(self, profile_repo, job_repo):
        """Test that jobs in wrong location get FAIL prefilter."""
        from app.models import ProfileCreate
        profile_data = ProfileCreate(
            location_preferences=["San Francisco"],
            salary_min=100000,
            salary_max=200000,
            remote_preference="remote",
        )
        await profile_repo.upsert_profile(profile_data)
        
        raw_job = RawJobRecord(
            id="test-2",
            title="Software Engineer",
            company=AdzunaCompany(display_name="Tech Corp"),
            location=AdzunaArea(display_name="New York, NY"),
            contract_type="permanent",
            contract_time="remote",
            category=AdzunaCategory(label="IT Jobs"),
            salary_min=120000,
            salary_max=150000,
            salary_is_predicted=False,
            description="Great software engineering role",
            redirect_url="https://example.com/job/2",
            created="2024-01-01T00:00:00Z",
        )
        
        job_create = normalize_job(raw_job)
        new_job = await job_repo.create_job(job_create)
        
        profile = await profile_repo.get_profile()
        
        prefilter_profile = PreFilterProfileInput(
            work_experience=profile.work_experience,
            technical_skills=profile.technical_skills or [],
            networking_experience=profile.networking_experience,
            education=profile.education,
            certifications=profile.certifications or [],
            languages=profile.languages or [],
            desired_roles=profile.desired_roles or [],
            location_preferences=profile.location_preferences or [],
            salary_min=profile.salary_min,
            salary_max=profile.salary_max,
            salary_currency=profile.salary_currency,
            remote_preference=profile.remote_preference.value if hasattr(profile.remote_preference, 'value') else profile.remote_preference,
            experience_level=profile.experience_level.value if hasattr(profile.experience_level, 'value') else profile.experience_level,
            excluded_keywords=profile.excluded_keywords or [],
            relevance_threshold=profile.relevance_threshold,
        )
        
        prefilter_job = PreFilterJobInput(
            id=new_job.id,
            adzuna_id=new_job.adzuna_id,
            title=new_job.title,
            company=new_job.company,
            location=new_job.location,
            work_mode=new_job.work_mode,
            employment_type=new_job.employment_type,
            salary_min=new_job.salary_min,
            salary_max=new_job.salary_max,
            salary_currency=new_job.salary_currency,
            salary_is_predicted=new_job.salary_is_predicted,
            description=new_job.description,
            requirements=new_job.requirements,
            skills=new_job.skills or [],
            redirect_url=new_job.redirect_url,
            posted_at=new_job.posted_at,
            raw_evidence=new_job.raw_evidence or {},
        )
        
        prefilter_input = PreFilterInput(job=prefilter_job, profile=prefilter_profile)
        prefilter_result = run_pre_filter_pipeline(prefilter_input, PreFilterConfig())
        
        await job_repo.update_prefilter_status(new_job.id, prefilter_result.overall_result == "pass")
        
        updated_job = await job_repo.get_job(new_job.id)
        assert updated_job.passed_prefilter is False

    @pytest.mark.asyncio
    async def test_search_filters_out_excluded_keyword(self, profile_repo, job_repo):
        """Test that jobs with excluded keywords get FAIL prefilter."""
        from app.models import ProfileCreate
        profile_data = ProfileCreate(
            location_preferences=["San Francisco"],
            salary_min=100000,
            remote_preference="remote",
            excluded_keywords=["sales"],
        )
        await profile_repo.upsert_profile(profile_data)
        
        raw_job = RawJobRecord(
            id="test-3",
            title="Sales Engineer",
            company=AdzunaCompany(display_name="Tech Corp"),
            location=AdzunaArea(display_name="San Francisco, CA"),
            contract_type="permanent",
            contract_time="remote",
            category=AdzunaCategory(label="IT Jobs"),
            salary_min=120000,
            salary_max=150000,
            salary_is_predicted=False,
            description="Great sales engineering role",
            redirect_url="https://example.com/job/3",
            created="2024-01-01T00:00:00Z",
        )
        
        job_create = normalize_job(raw_job)
        new_job = await job_repo.create_job(job_create)
        
        profile = await profile_repo.get_profile()
        
        prefilter_profile = PreFilterProfileInput(
            work_experience=profile.work_experience,
            technical_skills=profile.technical_skills or [],
            networking_experience=profile.networking_experience,
            education=profile.education,
            certifications=profile.certifications or [],
            languages=profile.languages or [],
            desired_roles=profile.desired_roles or [],
            location_preferences=profile.location_preferences or [],
            salary_min=profile.salary_min,
            salary_max=profile.salary_max,
            salary_currency=profile.salary_currency,
            remote_preference=profile.remote_preference.value if hasattr(profile.remote_preference, 'value') else profile.remote_preference,
            experience_level=profile.experience_level.value if hasattr(profile.experience_level, 'value') else profile.experience_level,
            excluded_keywords=profile.excluded_keywords or [],
            relevance_threshold=profile.relevance_threshold,
        )
        
        prefilter_job = PreFilterJobInput(
            id=new_job.id,
            adzuna_id=new_job.adzuna_id,
            title=new_job.title,
            company=new_job.company,
            location=new_job.location,
            work_mode=new_job.work_mode,
            employment_type=new_job.employment_type,
            salary_min=new_job.salary_min,
            salary_max=new_job.salary_max,
            salary_currency=new_job.salary_currency,
            salary_is_predicted=new_job.salary_is_predicted,
            description=new_job.description,
            requirements=new_job.requirements,
            skills=new_job.skills or [],
            redirect_url=new_job.redirect_url,
            posted_at=new_job.posted_at,
            raw_evidence=new_job.raw_evidence or {},
        )
        
        prefilter_input = PreFilterInput(job=prefilter_job, profile=prefilter_profile)
        prefilter_result = run_pre_filter_pipeline(prefilter_input, PreFilterConfig())
        
        await job_repo.update_prefilter_status(new_job.id, prefilter_result.overall_result == "pass")
        
        updated_job = await job_repo.get_job(new_job.id)
        assert updated_job.passed_prefilter is False

    @pytest.mark.asyncio
    async def test_list_jobs_filters_by_prefilter(self, profile_repo, job_repo):
        """Test that list_jobs endpoint can filter by passed_prefilter."""
        from app.models import ProfileCreate
        profile_data = ProfileCreate(
            location_preferences=["San Francisco"],
            salary_min=100000,
            salary_max=200000,
            remote_preference="remote",
        )
        await profile_repo.upsert_profile(profile_data)
        
        # Create passing job
        raw_job1 = RawJobRecord(
            id="pass-1",
            title="Software Engineer",
            company=AdzunaCompany(display_name="Tech Corp"),
            location=AdzunaArea(display_name="San Francisco, CA"),
            contract_type="permanent",
            contract_time="remote",
            category=AdzunaCategory(label="IT Jobs"),
            salary_min=120000,
            salary_max=150000,
            salary_is_predicted=False,
            description="Great role",
            redirect_url="https://example.com/job/pass1",
            created="2024-01-01T00:00:00Z",
        )
        
        # Create failing job (wrong location)
        raw_job2 = RawJobRecord(
            id="fail-1",
            title="Software Engineer",
            company=AdzunaCompany(display_name="Tech Corp"),
            location=AdzunaArea(display_name="New York, NY"),
            contract_type="permanent",
            contract_time="remote",
            category=AdzunaCategory(label="IT Jobs"),
            salary_min=120000,
            salary_max=150000,
            salary_is_predicted=False,
            description="Great role",
            redirect_url="https://example.com/job/fail1",
            created="2024-01-01T00:00:00Z",
        )
        
        job1 = await job_repo.create_job(normalize_job(raw_job1))
        job2 = await job_repo.create_job(normalize_job(raw_job2))
        
        profile = await profile_repo.get_profile()
        
        prefilter_profile = PreFilterProfileInput(
            work_experience=profile.work_experience,
            technical_skills=profile.technical_skills or [],
            networking_experience=profile.networking_experience,
            education=profile.education,
            certifications=profile.certifications or [],
            languages=profile.languages or [],
            desired_roles=profile.desired_roles or [],
            location_preferences=profile.location_preferences or [],
            salary_min=profile.salary_min,
            salary_max=profile.salary_max,
            salary_currency=profile.salary_currency,
            remote_preference=profile.remote_preference.value if hasattr(profile.remote_preference, 'value') else profile.remote_preference,
            experience_level=profile.experience_level.value if hasattr(profile.experience_level, 'value') else profile.experience_level,
            excluded_keywords=profile.excluded_keywords or [],
            relevance_threshold=profile.relevance_threshold,
        )
        
        prefilter_config = PreFilterConfig()
        
        for job in [job1, job2]:
            prefilter_job = PreFilterJobInput(
                id=job.id,
                adzuna_id=job.adzuna_id,
                title=job.title,
                company=job.company,
                location=job.location,
                work_mode=job.work_mode,
                employment_type=job.employment_type,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                salary_currency=job.salary_currency,
                salary_is_predicted=job.salary_is_predicted,
                description=job.description,
                requirements=job.requirements,
                skills=job.skills or [],
                redirect_url=job.redirect_url,
                posted_at=job.posted_at,
                raw_evidence=job.raw_evidence or {},
            )
            prefilter_input = PreFilterInput(job=prefilter_job, profile=prefilter_profile)
            prefilter_result = run_pre_filter_pipeline(prefilter_input, prefilter_config)
            await job_repo.update_prefilter_status(job.id, prefilter_result.overall_result == "pass")
        
        # Test filtering
        passed_jobs = await job_repo.list_jobs(passed_prefilter=True)
        failed_jobs = await job_repo.list_jobs(passed_prefilter=False)
        all_jobs = await job_repo.list_jobs()
        
        assert len(passed_jobs) == 1
        assert passed_jobs[0].adzuna_id == "pass-1"
        assert len(failed_jobs) == 1
        assert failed_jobs[0].adzuna_id == "fail-1"
        assert len(all_jobs) == 2