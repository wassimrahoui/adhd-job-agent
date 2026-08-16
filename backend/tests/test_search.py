from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import os

from app.main import app
from app.db import init_db, close_db, get_database
from app.repositories import ProfileRepository, JobRepository
from app.job_sources import (
    AdzunaSourceAdapter, 
    RawJobRecord, 
    QuotaExhaustedError,
    AuthError,
)
from app.models import ProfileCreate, RemotePreference
from app.job_sources import build_adzuna_query, RawJobRecord as RawJobRecordSchema


# Sample Adzuna response fixtures
SAMPLE_ADZUNA_RESPONSE_PAGE1 = {
    "results": [
        {
            "id": "111111111",
            "title": "Python Developer",
            "company": {"display_name": "Tech Corp"},
            "location": {
                "area": ["US", "CA", "San Francisco"],
                "display_name": "San Francisco, CA"
            },
            "description": "Python developer role with FastAPI",
            "salary_min": 100000,
            "salary_max": 150000,
            "salary_is_predicted": False,
            "contract_type": "permanent",
            "contract_time": "full_time",
            "category": {"label": "IT Jobs", "tag": "it-jobs"},
            "created": "2024-01-15T10:30:00Z",
            "redirect_url": "https://www.adzuna.com/job/111111111",
            "latitude": 37.7749,
            "longitude": -122.4194
        },
        {
            "id": "222222222",
            "title": "Senior Backend Engineer",
            "company": {"display_name": "StartupXYZ"},
            "location": {
                "area": ["US", "NY", "New York"],
                "display_name": "New York, NY"
            },
            "description": "Backend engineer with Python and PostgreSQL",
            "salary_min": 120000,
            "salary_max": 180000,
            "salary_is_predicted": True,
            "contract_type": "permanent",
            "contract_time": "full_time",
            "category": {"label": "IT Jobs", "tag": "it-jobs"},
            "created": "2024-01-14T09:00:00Z",
            "redirect_url": "https://www.adzuna.com/job/222222222",
            "latitude": 40.7128,
            "longitude": -74.0060
        }
    ],
    "count": 2,
    "mean": 125000
}

SAMPLE_ADZUNA_RESPONSE_PAGE2 = {
    "results": [
        {
            "id": "333333333",
            "title": "Full Stack Developer",
            "company": {"display_name": "BigTech Inc"},
            "location": {
                "area": ["US", "WA", "Seattle"],
                "display_name": "Seattle, WA"
            },
            "description": "Full stack with React and Python",
            "salary_min": 110000,
            "salary_max": 160000,
            "salary_is_predicted": False,
            "contract_type": "permanent",
            "contract_time": "full_time",
            "category": {"label": "IT Jobs", "tag": "it-jobs"},
            "created": "2024-01-13T14:00:00Z",
            "redirect_url": "https://www.adzuna.com/job/333333333",
            "latitude": 47.6062,
            "longitude": -122.3321
        }
    ],
    "count": 1,
    "mean": 135000
}

QUOTA_EXHAUSTED_RESPONSE = {
    "error": "Daily quota exhausted",
    "message": "You have exceeded your daily quota"
}


@pytest.fixture
async def test_db():
    """Create a test database."""
    import tempfile
    import os
    from app.db import Database
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    db = Database(db_path)
    await db.connect()
    yield db
    await db.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
async def profile_repo(test_db):
    """Create a ProfileRepository with test profile."""
    from app.repositories import ProfileRepository
    repo = ProfileRepository(test_db)
    
    profile_data = ProfileCreate(
        work_experience="5 years Python development",
        technical_skills=["Python", "FastAPI", "PostgreSQL"],
        desired_roles=["Backend Engineer", "Python Developer"],
        location_preferences=["San Francisco", "New York"],
        salary_min=100000,
        salary_max=150000,
        remote_preference=RemotePreference.REMOTE,
    )
    await repo.upsert_profile(profile_data)
    return repo


@pytest.fixture
def mock_adzuna_adapter():
    """Create a mocked AdzunaSourceAdapter."""
    adapter = AsyncMock()
    adapter.source_name = "adzuna"
    adapter.search_jobs = AsyncMock()
    adapter.close = AsyncMock()
    return adapter


class TestSearchEndpoint:
    """Integration tests for POST /jobs/search endpoint."""
    
    @pytest.mark.asyncio
    async def test_search_success_stores_jobs(self, test_db, profile_repo, mock_adzuna_adapter):
        """Test successful search stores jobs correctly."""
        # Setup mock adapter to return sample jobs
        raw_jobs = [
            RawJobRecord(**job) for job in SAMPLE_ADZUNA_RESPONSE_PAGE1["results"]
        ]
        raw_jobs.append(RawJobRecord(**SAMPLE_ADZUNA_RESPONSE_PAGE2["results"][0]))
        
        mock_adzuna_adapter.search_jobs.return_value = raw_jobs
        
        from httpx import ASGITransport, AsyncClient
        from app.main import app
        from app.db import get_database
        from app.repositories import ProfileRepository, JobRepository
        from app.job_sources import set_test_adzuna_adapter
        
        # Set test adapter
        from app.job_sources import set_test_adzuna_adapter
        set_test_adzuna_adapter(mock_adzuna_adapter)
        
        # Override dependencies
        async def override_get_db():
            return test_db
        
        async def override_get_profile_repo():
            return profile_repo
        
        async def override_get_job_repo():
            from app.repositories import JobRepository
            return JobRepository(test_db)
        
        app.dependency_overrides[get_database] = override_get_db
        app.dependency_overrides[ProfileRepository] = lambda: profile_repo
        app.dependency_overrides[JobRepository] = lambda: JobRepository(test_db)
        
        try:
            from httpx import ASGITransport, AsyncClient
            from app.main import app
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/jobs/search")
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["jobs_found"] == 3
                assert data["jobs_new"] == 3
                assert data["jobs_updated"] == 0
                assert data["quota_exhausted"] is False
                assert data["search_duration_ms"] is not None
                
                # Verify jobs were stored
                from app.repositories import JobRepository
                job_repo = JobRepository(test_db)
                jobs = await job_repo.list_jobs(limit=10)
                assert len(jobs) == 3
                
# Check all jobs exist (order is by discovered_at DESC)
                adzuna_ids = {job.adzuna_id for job in jobs}
                assert adzuna_ids == {"111111111", "222222222", "333333333"}
                
                # Check raw_evidence stored (on detail, not list)
                # job1.raw_evidence is only on JobDetailSchema, not JobListItemSchema
        finally:
            from app.job_sources import set_test_adzuna_adapter
            from app.main import app
            app.dependency_overrides.clear()
            set_test_adzuna_adapter(None)
    
    @pytest.mark.asyncio
    async def test_search_deduplication_prevents_duplicates(self, test_db, profile_repo, mock_adzuna_adapter):
        """Test deduplication prevents duplicate jobs."""
        # First, create a job in the database
        from app.repositories import JobRepository
        from app.models import JobCreate
        
        job_repo = JobRepository(test_db)
        
        existing_job = JobCreate(
            adzuna_id="111111111",
            title="Python Developer",
            company="Tech Corp",
            location="San Francisco, CA",
            redirect_url="https://www.adzuna.com/job/111111111",
        )
        await job_repo.create_job(existing_job)
        
        # Mock adapter to return the same job
        raw_jobs = [
            RawJobRecord(**SAMPLE_ADZUNA_RESPONSE_PAGE1["results"][0])
        ]
        
        mock_adzuna_adapter.search_jobs.return_value = raw_jobs
        
        from httpx import ASGITransport, AsyncClient
        from app.main import app
        from app.db import get_database
        from app.repositories import ProfileRepository, JobRepository
        from app.job_sources import set_test_adzuna_adapter
        
        set_test_adzuna_adapter(mock_adzuna_adapter)
        
        async def override_get_db():
            return test_db
        
        async def override_get_profile_repo():
            return profile_repo
        
        async def override_get_job_repo():
            from app.repositories import JobRepository
            return JobRepository(test_db)
        
        app.dependency_overrides[get_database] = override_get_db
        app.dependency_overrides[ProfileRepository] = lambda: profile_repo
        app.dependency_overrides[JobRepository] = lambda: JobRepository(test_db)
        
        try:
            from httpx import ASGITransport, AsyncClient
            from app.main import app
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/jobs/search")
                
                assert response.status_code == 200
                data = response.json()
                
                # Should find 1 job but not create new (deduplication - updated as existing job)
                assert data["jobs_found"] == 1
                assert data["jobs_new"] == 0
                assert data["jobs_updated"] == 1
        finally:
            from app.job_sources import set_test_adzuna_adapter
            from app.main import app
            app.dependency_overrides.clear()
            set_test_adzuna_adapter(None)
    
    @pytest.mark.asyncio
    async def test_search_quota_exhausted(self, test_db, profile_repo, mock_adzuna_adapter):
        """Test quota exhaustion returns partial results + flag."""
        # Mock adapter to raise QuotaExhaustedError on second call
        raw_jobs = [
            RawJobRecord(**job) for job in SAMPLE_ADZUNA_RESPONSE_PAGE1["results"]
        ]
        
        call_count = 0
        async def mock_search_jobs(query_params):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return raw_jobs  # Return first page
            else:
                from app.job_sources import QuotaExhaustedError
                raise QuotaExhaustedError("Adzuna daily quota exhausted for today")
        
        mock_adzuna_adapter.search_jobs.side_effect = mock_search_jobs
        
        from httpx import ASGITransport, AsyncClient
        from app.main import app
        from app.db import get_database
        from app.repositories import ProfileRepository, JobRepository
        from app.job_sources import set_test_adzuna_adapter
        
        set_test_adzuna_adapter(mock_adzuna_adapter)
        
        async def override_get_db():
            return test_db
        
        async def override_get_profile_repo():
            return profile_repo
        
        async def override_get_job_repo():
            from app.repositories import JobRepository
            return JobRepository(test_db)
        
        app.dependency_overrides[get_database] = override_get_db
        app.dependency_overrides[ProfileRepository] = lambda: profile_repo
        app.dependency_overrides[JobRepository] = lambda: JobRepository(test_db)
        
        try:
            from httpx import ASGITransport, AsyncClient
            from app.main import app
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/jobs/search")
                
                assert response.status_code == 200
                data = response.json()

                # The profile has 2 desired_roles, so search issues one query
                # per role (see build_adzuna_queries). The 1st role's query
                # succeeds (2 jobs); the 2nd hits quota exhaustion - jobs
                # already fetched from the 1st are kept and processed, and
                # the quota flag/message are surfaced rather than discarded.
                assert data["jobs_found"] == 2
                assert data["quota_exhausted"] is True
                assert data["quota_message"] == "Adzuna daily quota exhausted for today"
        finally:
            from app.job_sources import set_test_adzuna_adapter
            from app.main import app
            app.dependency_overrides.clear()
            set_test_adzuna_adapter(None)
    
    @pytest.mark.asyncio
    async def test_search_no_profile_returns_404(self, test_db, mock_adzuna_adapter):
        """Test search without profile returns 404."""
        from httpx import ASGITransport, AsyncClient
        from app.main import app
        from app.db import get_database
        from app.repositories import ProfileRepository, JobRepository
        from app.job_sources import set_test_adzuna_adapter
        
        set_test_adzuna_adapter(mock_adzuna_adapter)
        
        async def override_get_db():
            return test_db
        
        async def override_get_profile_repo():
            # No profile created
            return None
        
        async def override_get_job_repo():
            from app.repositories import JobRepository
            return JobRepository(test_db)
        
        app.dependency_overrides[get_database] = override_get_db
        app.dependency_overrides[ProfileRepository] = override_get_profile_repo
        app.dependency_overrides[JobRepository] = lambda: JobRepository(test_db)
        
        try:
            from httpx import ASGITransport, AsyncClient
            from app.main import app
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/jobs/search")
                
                assert response.status_code == 404
                data = response.json()
                assert data["detail"]["error_code"] == "PROFILE_NOT_FOUND"
        finally:
            from app.job_sources import set_test_adzuna_adapter
            from app.main import app
            app.dependency_overrides.clear()
            set_test_adzuna_adapter(None)
    
    @pytest.mark.asyncio
    async def test_search_adzuna_auth_error(self, test_db, profile_repo, mock_adzuna_adapter):
        """Test Adzuna auth error returns 401."""
        from app.job_sources import AuthError
        
        mock_adzuna_adapter.search_jobs.side_effect = AuthError("Invalid credentials")
        
        from httpx import ASGITransport, AsyncClient
        from app.main import app
        from app.db import get_database
        from app.repositories import ProfileRepository, JobRepository
        from app.job_sources import set_test_adzuna_adapter
        
        set_test_adzuna_adapter(mock_adzuna_adapter)
        
        async def override_get_db():
            return test_db
        
        async def override_get_profile_repo():
            return profile_repo
        
        async def override_get_job_repo():
            from app.repositories import JobRepository
            return JobRepository(test_db)
        
        app.dependency_overrides[get_database] = override_get_db
        app.dependency_overrides[ProfileRepository] = lambda: profile_repo
        app.dependency_overrides[JobRepository] = lambda: JobRepository(test_db)
        
        try:
            from httpx import ASGITransport, AsyncClient
            from app.main import app
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/jobs/search")
                
                assert response.status_code == 401
                data = response.json()
                assert data["detail"]["error_code"] == "ADZUNA_AUTH_ERROR"
        finally:
            from app.job_sources import set_test_adzuna_adapter
            from app.main import app
            app.dependency_overrides.clear()
            set_test_adzuna_adapter(None)


class TestAdzunaAdapter:
    """Unit tests for AdzunaSourceAdapter."""
    
    @pytest.mark.asyncio
    async def test_adzuna_adapter_initialization(self):
        """Test adapter initializes with config."""
        adapter = AdzunaSourceAdapter(config={
            "app_id": "test_id",
            "app_key": "test_key",
            "base_url": "https://api.adzuna.com/v1/api/jobs",
            "country": "us",
            "max_pages": 3,
        })
        
        assert adapter._app_id == "test_id"
        assert adapter._app_key == "test_key"
        assert adapter._max_pages == 3
        
        await adapter.close()
    
    @pytest.mark.asyncio
    async def test_adzuna_adapter_requires_credentials(self):
        """Test adapter requires app_id and app_key.

        Explicitly overrides both to None rather than passing an empty config,
        since an empty config falls back to real ambient settings.adzuna_app_id/
        app_key - this must not depend on whether the environment happens to
        have Adzuna credentials configured.
        """
        with pytest.raises(ValueError):
            AdzunaSourceAdapter(config={"app_id": None, "app_key": None})
    
    @pytest.mark.asyncio
    async def test_query_builder(self):
        """Test query builder produces correct params."""
        from app.job_sources import build_adzuna_query
        from app.models import ProfileCreate, RemotePreference
        
        profile = ProfileCreate(
            desired_roles=["Backend Engineer", "Python Developer"],
            location_preferences=["San Francisco", "New York"],
            salary_min=100000,
            remote_preference=RemotePreference.REMOTE,
        )
        
        params = build_adzuna_query(profile)

        # what_or (not what) is Adzuna's real OR-across-terms parameter,
        # space-separated (not comma-separated) - see build_adzuna_query.
        assert params["what_or"] == "Backend Engineer Python Developer remote"
        assert "what" not in params
        # where is a single free-text location, not a multi-value list -
        # only the primary (first) preference is used.
        assert params["where"] == "San Francisco"
        assert params["salary_min"] == 100000
        assert params["sort_by"] == "relevance"
        assert params["content-type"] == "application/json"
        assert "sort_order" not in params  # not a real Adzuna parameter
    
    @pytest.mark.asyncio
    async def test_query_builder_empty_profile(self):
        """Test query builder with empty profile returns defaults."""
        from app.job_sources import build_adzuna_query
        from app.models import ProfileCreate
        
        profile = ProfileCreate()
        params = build_adzuna_query(profile)
        
        assert params["sort_by"] == "relevance"
        assert params["content-type"] == "application/json"
        assert "sort_order" not in params  # not a real Adzuna parameter
        assert "what" not in params
        assert "where" not in params

    @pytest.mark.asyncio
    async def test_build_adzuna_queries_one_per_role(self):
        """Regression: a single what_or query with multiple roles matches
        per-word (e.g. "Security Engineer" OR "SOC Analyst" becomes "Security"
        OR "Engineer" OR "SOC" OR "Analyst"), pulling in unrelated jobs like
        "Security Guard". build_adzuna_queries issues one exact-phrase query
        per role instead, to be merged/deduped by the caller."""
        from app.job_sources import build_adzuna_queries
        from app.models import ProfileCreate, RemotePreference

        profile = ProfileCreate(
            desired_roles=["Security Engineer", "SOC Analyst"],
            location_preferences=["Munich", "Berlin"],
            salary_min=60000,
            remote_preference=RemotePreference.REMOTE,
        )

        queries = build_adzuna_queries(profile)

        # 2 roles + 1 extra query for the remote-preference term
        assert len(queries) == 3
        whats = {q["what"] for q in queries}
        assert whats == {"Security Engineer", "SOC Analyst", "remote"}
        for q in queries:
            assert "what_or" not in q
            # With 2+ location preferences, Adzuna's single-valued "where"
            # can't represent them all - left unscoped here (country=de is
            # still applied at the URL level) and narrowed by the pre-filter
            # instead, which does correctly match against every preference.
            assert "where" not in q
            assert q["salary_min"] == 60000
            assert q["sort_by"] == "relevance"
            assert q["content-type"] == "application/json"

    @pytest.mark.asyncio
    async def test_build_adzuna_queries_single_location_is_scoped(self):
        from app.job_sources import build_adzuna_queries
        from app.models import ProfileCreate

        profile = ProfileCreate(desired_roles=["Security Engineer"], location_preferences=["Berlin"])
        queries = build_adzuna_queries(profile)

        assert len(queries) == 1
        assert queries[0]["where"] == "Berlin"

    @pytest.mark.asyncio
    async def test_build_adzuna_queries_no_roles_returns_single_query(self):
        from app.job_sources import build_adzuna_queries
        from app.models import ProfileCreate

        profile = ProfileCreate(location_preferences=["Berlin"])
        queries = build_adzuna_queries(profile)

        assert len(queries) == 1
        assert "what" not in queries[0]
        assert queries[0]["where"] == "Berlin"


class TestNormalization:
    """Unit tests for job normalization and deduplication."""
    
    @pytest.mark.asyncio
    async def test_normalize_job(self):
        """Test normalizing RawJobRecord to JobCreate."""
        from app.job_sources import normalize_job, RawJobRecord
        
        raw = RawJobRecord(
            id="123456789",
            title="Python Developer",
            company={"display_name": "Tech Corp"},
            location={"area": ["US", "CA", "San Francisco"], "display_name": "San Francisco, CA"},
            description="Python developer role",
            salary_min=100000,
            salary_max=150000,
            salary_is_predicted=False,
            contract_type="permanent",
            contract_time="full_time",
            category={"label": "IT Jobs", "tag": "it-jobs"},
            created="2024-01-15T10:30:00Z",
            redirect_url="https://www.adzuna.com/job/123456789",
        )
        
        job = normalize_job(raw)
        
        assert job.adzuna_id == "123456789"
        assert job.title == "Python Developer"
        assert job.company == "Tech Corp"
        assert job.location == "San Francisco, CA"
        assert job.work_mode == "on_site"
        assert job.employment_type == "full_time"
        assert job.salary_min == 100000
        assert job.salary_max == 150000
        assert job.skills == ["IT Jobs", "permanent", "full_time"]
        assert job.redirect_url == "https://www.adzuna.com/job/123456789"
        assert job.raw_evidence is not None
    
    @pytest.mark.asyncio
    async def test_dedup_key(self):
        """Test deduplication key generation."""
        from app.job_sources import normalize_job, dedup_key, RawJobRecord
        
        raw = RawJobRecord(
            id="123456789",
            title="Python Developer",
            company={"display_name": "Tech Corp"},
            location={"area": ["US", "CA", "San Francisco"], "display_name": "San Francisco, CA"},
            redirect_url="https://www.adzuna.com/job/123456789",
        )
        
        job = normalize_job(raw)
        key = dedup_key(job)
        
        assert key[0] == "adzuna_id"
        assert key[1] == "123456789"
    
    @pytest.mark.asyncio
    async def test_is_duplicate(self):
        """Test duplicate detection."""
        from app.job_sources import normalize_job, is_duplicate, RawJobRecord
        from app.models import Job
        from datetime import datetime
        
        raw = RawJobRecord(
            id="123456789",
            title="Python Developer",
            company={"display_name": "Tech Corp"},
            location={"area": ["US", "CA", "San Francisco"], "display_name": "San Francisco, CA"},
            redirect_url="https://www.adzuna.com/job/123456789",
        )
        
        job = normalize_job(raw)
        
        # Test adzuna_id match
        existing = Job(
            id=1,
            adzuna_id="123456789",
            title="Python Developer",
            company="Tech Corp",
            location="San Francisco, CA",
            redirect_url="https://www.adzuna.com/job/123456789",
            discovered_at=datetime.now(),
            passed_prefilter=False
        )
        assert is_duplicate(existing, job) is True
        
        # Test redirect_url match
        existing2 = Job(
            id=2,
            adzuna_id="999999999",
            title="Python Developer",
            company="Tech Corp",
            location="San Francisco, CA",
            redirect_url="https://www.adzuna.com/job/123456789",
            discovered_at=datetime.now(),
            passed_prefilter=False
        )
        assert is_duplicate(existing2, job) is True
        
        # Test composite key match
        existing3 = Job(
            id=3,
            adzuna_id="888888888",
            title="Python Developer",
            company="Tech Corp",
            location="San Francisco, CA",
            redirect_url="https://different.url",
            discovered_at=datetime.now(),
            passed_prefilter=False
        )
        assert is_duplicate(existing3, job) is True
        
        # Test non-duplicate
        existing4 = Job(
            id=4,
            adzuna_id="777777777",
            title="Java Developer",
            company="Other Corp",
            location="New York, NY",
            redirect_url="https://different.url",
            discovered_at=datetime.now(),
            passed_prefilter=False
        )
        assert is_duplicate(existing4, job) is False