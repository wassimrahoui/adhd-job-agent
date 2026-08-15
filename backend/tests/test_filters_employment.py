from __future__ import annotations

import pytest
from app.filters.schemas import (
    FilterResult,
    PreFilterJobInput,
    PreFilterProfileInput,
    PreFilterConfig,
)
from app.filters.employment import filter_employment


class TestEmploymentFilter:
    def test_employment_any_mode(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            employment_type="contract",
            work_mode="on_site",
        )
        profile = PreFilterProfileInput(remote_preference="remote")
        config = PreFilterConfig(employment_type_match_mode="any", work_mode_match_mode="any")

        result = filter_employment(job, profile, config)
        assert result.result == FilterResult.PASS
        assert "Any employment" in result.reason

    def test_employment_work_mode_exact_match(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            employment_type="full_time",
            work_mode="remote",
        )
        profile = PreFilterProfileInput(remote_preference="remote")
        config = PreFilterConfig(employment_type_match_mode="exact", work_mode_match_mode="exact")

        result = filter_employment(job, profile, config)
        assert result.result == FilterResult.PASS
        assert "matches exactly" in result.reason

    def test_employment_work_mode_exact_mismatch(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            employment_type="full_time",
            work_mode="on_site",
        )
        profile = PreFilterProfileInput(remote_preference="remote")
        config = PreFilterConfig(employment_type_match_mode="exact", work_mode_match_mode="exact")

        result = filter_employment(job, profile, config)
        assert result.result == FilterResult.FAIL
        assert "does not match" in result.reason

    def test_employment_work_mode_flexible_remote_matches_hybrid(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            employment_type="full_time",
            work_mode="hybrid",
        )
        profile = PreFilterProfileInput(remote_preference="remote")
        config = PreFilterConfig(employment_type_match_mode="exact", work_mode_match_mode="any")

        result = filter_employment(job, profile, config)
        assert result.result == FilterResult.PASS

    def test_employment_work_mode_flexible_hybrid_matches_remote(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            employment_type="full_time",
            work_mode="remote",
        )
        profile = PreFilterProfileInput(remote_preference="hybrid")
        config = PreFilterConfig(employment_type_match_mode="exact", work_mode_match_mode="any")

        result = filter_employment(job, profile, config)
        assert result.result == FilterResult.PASS

    def test_employment_work_mode_flexible_hybrid_matches_on_site(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            employment_type="full_time",
            work_mode="on_site",
        )
        profile = PreFilterProfileInput(remote_preference="hybrid")
        config = PreFilterConfig(employment_type_match_mode="exact", work_mode_match_mode="any")

        result = filter_employment(job, profile, config)
        assert result.result == FilterResult.PASS

    def test_employment_work_mode_flexible_on_site_not_match_remote(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            employment_type="full_time",
            work_mode="on_site",
        )
        profile = PreFilterProfileInput(remote_preference="remote")
        config = PreFilterConfig(employment_type_match_mode="exact", work_mode_match_mode="any")

        result = filter_employment(job, profile, config)
        assert result.result == FilterResult.FAIL
        assert "does not match" in result.reason

    def test_employment_no_job_work_mode(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            employment_type="full_time",
            work_mode=None,
        )
        profile = PreFilterProfileInput(remote_preference="remote")
        config = PreFilterConfig(employment_type_match_mode="exact", work_mode_match_mode="any")

        result = filter_employment(job, profile, config)
        assert result.result == FilterResult.PASS
        assert "Job work mode not specified" in result.reason

    def test_employment_no_profile_preference(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            employment_type="full_time",
            work_mode="remote",
        )
        profile = PreFilterProfileInput(remote_preference="any")
        config = PreFilterConfig(employment_type_match_mode="exact", work_mode_match_mode="any")

        result = filter_employment(job, profile, config)
        assert result.result == FilterResult.PASS
        assert "Any work mode" in result.reason

    def test_employment_no_job_employment_type(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            employment_type=None,
            work_mode=None,
        )
        profile = PreFilterProfileInput(remote_preference="remote")
        config = PreFilterConfig(employment_type_match_mode="any", work_mode_match_mode="any")

        result = filter_employment(job, profile, config)
        assert result.result == FilterResult.PASS
        assert "not specified" in result.reason