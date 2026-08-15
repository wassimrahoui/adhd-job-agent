from __future__ import annotations

import pytest
import pytest_asyncio
from app.db import Database
from app.repositories import JobRepository
from app.models import JobCreate
from datetime import datetime


@pytest_asyncio.fixture
async def db():
    db = Database(":memory:")
    await db.connect()
    yield db
    await db.close()


@pytest_asyncio.fixture
async def job_repo(db):
    return JobRepository(db)


class TestPrefilterPersistence:
    @pytest.mark.asyncio
    async def test_update_prefilter_status_pass(self, job_repo):
        job_data = JobCreate(
            adzuna_id="test-1",
            title="Software Engineer",
            location="San Francisco, CA",
            work_mode="remote",
            employment_type="full_time",
            salary_min=120000,
            salary_max=150000,
            description="Great job",
            skills=["Python", "FastAPI"],
        )
        job = await job_repo.create_job(job_data)
        assert job.passed_prefilter is False

        updated = await job_repo.update_prefilter_status(job.id, True)
        assert updated is not None
        assert updated.passed_prefilter is True

    @pytest.mark.asyncio
    async def test_update_prefilter_status_fail(self, job_repo):
        job_data = JobCreate(
            adzuna_id="test-1",
            title="Software Engineer",
            location="San Francisco, CA",
            work_mode="remote",
            employment_type="full_time",
            salary_min=120000,
            salary_max=150000,
            description="Great job",
            skills=["Python", "FastAPI"],
        )
        job = await job_repo.create_job(job_data)

        updated = await job_repo.update_prefilter_status(job.id, False)
        assert updated is not None
        assert updated.passed_prefilter is False

    @pytest.mark.asyncio
    async def test_update_prefilter_status_not_found(self, job_repo):
        updated = await job_repo.update_prefilter_status(999, True)
        assert updated is None

    @pytest.mark.asyncio
    async def test_list_jobs_by_prefilter(self, job_repo):
        job_data1 = JobCreate(
            adzuna_id="test-1",
            title="Software Engineer",
            location="San Francisco, CA",
            work_mode="remote",
            employment_type="full_time",
            salary_min=120000,
            salary_max=150000,
            description="Great job",
            skills=["Python", "FastAPI"],
        )
        job_data2 = JobCreate(
            adzuna_id="test-2",
            title="Sales Manager",
            location="New York, NY",
            work_mode="on_site",
            employment_type="full_time",
            salary_min=80000,
            salary_max=100000,
            description="Sales job",
            skills=["Sales"],
        )

        job1 = await job_repo.create_job(job_data1)
        job2 = await job_repo.create_job(job_data2)

        await job_repo.update_prefilter_status(job1.id, True)
        await job_repo.update_prefilter_status(job2.id, False)

        passed_jobs = await job_repo.get_jobs_by_prefilter(True)
        failed_jobs = await job_repo.get_jobs_by_prefilter(False)

        assert len(passed_jobs) == 1
        assert passed_jobs[0].adzuna_id == "test-1"
        assert len(failed_jobs) == 1
        assert failed_jobs[0].adzuna_id == "test-2"

    @pytest.mark.asyncio
    async def test_list_jobs_with_prefilter_param(self, job_repo):
        job_data1 = JobCreate(
            adzuna_id="test-1",
            title="Software Engineer",
            location="San Francisco, CA",
            work_mode="remote",
            employment_type="full_time",
            salary_min=120000,
            salary_max=150000,
            description="Great job",
            skills=["Python", "FastAPI"],
        )
        job_data2 = JobCreate(
            adzuna_id="test-2",
            title="Sales Manager",
            location="New York, NY",
            work_mode="on_site",
            employment_type="full_time",
            salary_min=80000,
            salary_max=100000,
            description="Sales job",
            skills=["Sales"],
        )

        job1 = await job_repo.create_job(job_data1)
        job2 = await job_repo.create_job(job_data2)

        await job_repo.update_prefilter_status(job1.id, True)
        await job_repo.update_prefilter_status(job2.id, False)

        passed_jobs = await job_repo.list_jobs(passed_prefilter=True)
        failed_jobs = await job_repo.list_jobs(passed_prefilter=False)
        all_jobs = await job_repo.list_jobs()

        assert len(passed_jobs) == 1
        assert passed_jobs[0].adzuna_id == "test-1"
        assert len(failed_jobs) == 1
        assert failed_jobs[0].adzuna_id == "test-2"
        assert len(all_jobs) == 2