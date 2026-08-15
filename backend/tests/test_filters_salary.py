from __future__ import annotations

import pytest
from app.filters.schemas import (
    FilterResult,
    PreFilterJobInput,
    PreFilterProfileInput,
    PreFilterConfig,
)
from app.filters.salary import filter_salary


class TestSalaryFilter:
    def test_salary_min_only_job_meets_minimum(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            salary_min=120000,
            salary_max=150000,
        )
        profile = PreFilterProfileInput(salary_min=100000)
        config = PreFilterConfig(salary_compare_mode="min_only")

        result = filter_salary(job, profile, config)
        assert result.result == FilterResult.PASS
        assert "meets preferred minimum" in result.reason

    def test_salary_min_only_job_below_minimum(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            salary_min=80000,
            salary_max=100000,
        )
        profile = PreFilterProfileInput(salary_min=100000)
        config = PreFilterConfig(salary_compare_mode="min_only")

        result = filter_salary(job, profile, config)
        assert result.result == FilterResult.FAIL
        assert "below preferred minimum" in result.reason

    def test_salary_min_only_job_has_max_only(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            salary_min=None,
            salary_max=120000,
        )
        profile = PreFilterProfileInput(salary_min=100000)
        config = PreFilterConfig(salary_compare_mode="min_only")

        result = filter_salary(job, profile, config)
        assert result.result == FilterResult.PASS

    def test_salary_max_only_job_within_maximum(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            salary_min=80000,
            salary_max=120000,
        )
        profile = PreFilterProfileInput(salary_max=150000)
        config = PreFilterConfig(salary_compare_mode="max_only")

        result = filter_salary(job, profile, config)
        assert result.result == FilterResult.PASS
        assert "within preferred maximum" in result.reason

    def test_salary_max_only_job_exceeds_maximum(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            salary_min=120000,
            salary_max=180000,
        )
        profile = PreFilterProfileInput(salary_max=150000)
        config = PreFilterConfig(salary_compare_mode="max_only")

        result = filter_salary(job, profile, config)
        assert result.result == FilterResult.FAIL
        assert "exceeds preferred maximum" in result.reason

    def test_salary_range_overlap_pass(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            salary_min=100000,
            salary_max=150000,
        )
        profile = PreFilterProfileInput(salary_min=120000, salary_max=180000)
        config = PreFilterConfig(salary_compare_mode="range_overlap")

        result = filter_salary(job, profile, config)
        assert result.result == FilterResult.PASS
        assert "overlap" in result.reason

    def test_salary_range_overlap_fail(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            salary_min=100000,
            salary_max=120000,
        )
        profile = PreFilterProfileInput(salary_min=150000, salary_max=200000)
        config = PreFilterConfig(salary_compare_mode="range_overlap")

        result = filter_salary(job, profile, config)
        assert result.result == FilterResult.FAIL
        assert "do not overlap" in result.reason

    def test_salary_range_overlap_job_single_value(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            salary_min=120000,
            salary_max=None,
        )
        profile = PreFilterProfileInput(salary_min=100000, salary_max=150000)
        config = PreFilterConfig(salary_compare_mode="range_overlap")

        result = filter_salary(job, profile, config)
        assert result.result == FilterResult.PASS

    def test_salary_no_job_salary_unknown(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            salary_min=None,
            salary_max=None,
        )
        profile = PreFilterProfileInput(salary_min=100000)
        config = PreFilterConfig(salary_compare_mode="range_overlap", unknown_salary_behavior="unknown")

        result = filter_salary(job, profile, config)
        assert result.result == FilterResult.UNKNOWN

    def test_salary_no_job_salary_pass(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            salary_min=None,
            salary_max=None,
        )
        profile = PreFilterProfileInput(salary_min=100000)
        config = PreFilterConfig(salary_compare_mode="range_overlap", unknown_salary_behavior="pass")

        result = filter_salary(job, profile, config)
        assert result.result == FilterResult.PASS

    def test_salary_no_job_salary_fail(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            salary_min=None,
            salary_max=None,
        )
        profile = PreFilterProfileInput(salary_min=100000)
        config = PreFilterConfig(salary_compare_mode="range_overlap", unknown_salary_behavior="fail")

        result = filter_salary(job, profile, config)
        assert result.result == FilterResult.FAIL

    def test_salary_no_profile_preference(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            salary_min=100000,
            salary_max=150000,
        )
        profile = PreFilterProfileInput(salary_min=None, salary_max=None)
        config = PreFilterConfig(salary_compare_mode="range_overlap")

        result = filter_salary(job, profile, config)
        assert result.result == FilterResult.PASS
        assert "No salary preference" in result.reason