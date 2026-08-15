from __future__ import annotations

import pytest
from app.filters.schemas import (
    FilterResult,
    PreFilterJobInput,
    PreFilterProfileInput,
    PreFilterConfig,
    PreFilterInput,
)
from app.filters.pipeline import run_pre_filter_pipeline


class TestFilterPipeline:
    def test_pipeline_all_pass(self):
        job = PreFilterJobInput(
            id=1,
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
        profile = PreFilterProfileInput(
            location_preferences=["San Francisco"],
            salary_min=100000,
            salary_max=200000,
            remote_preference="remote",
            excluded_keywords=["sales"],
        )
        config = PreFilterConfig()
        input_data = PreFilterInput(job=job, profile=profile)

        result = run_pre_filter_pipeline(input_data, config)

        assert result.overall_result == FilterResult.PASS
        assert len(result.reasons) == 4

    def test_pipeline_location_fail(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            location="New York, NY",
            work_mode="remote",
            employment_type="full_time",
            salary_min=120000,
        )
        profile = PreFilterProfileInput(
            location_preferences=["San Francisco"],
            salary_min=100000,
            remote_preference="remote",
        )
        config = PreFilterConfig()
        input_data = PreFilterInput(job=job, profile=profile)

        result = run_pre_filter_pipeline(input_data, config)

        assert result.overall_result == FilterResult.FAIL
        location_reason = next(r for r in result.reasons if r.filter_name == "location")
        assert location_reason.result == FilterResult.FAIL

    def test_pipeline_salary_fail(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            location="San Francisco, CA",
            work_mode="remote",
            employment_type="full_time",
            salary_min=80000,
        )
        profile = PreFilterProfileInput(
            location_preferences=["San Francisco"],
            salary_min=100000,
            remote_preference="remote",
        )
        config = PreFilterConfig()
        input_data = PreFilterInput(job=job, profile=profile)

        result = run_pre_filter_pipeline(input_data, config)

        assert result.overall_result == FilterResult.FAIL
        salary_reason = next(r for r in result.reasons if r.filter_name == "salary")
        assert salary_reason.result == FilterResult.FAIL

    def test_pipeline_employment_fail(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            location="San Francisco, CA",
            work_mode="on_site",
            employment_type="full_time",
            salary_min=120000,
        )
        profile = PreFilterProfileInput(
            location_preferences=["San Francisco"],
            salary_min=100000,
            remote_preference="remote",
        )
        config = PreFilterConfig(work_mode_match_mode="exact")
        input_data = PreFilterInput(job=job, profile=profile)

        result = run_pre_filter_pipeline(input_data, config)

        assert result.overall_result == FilterResult.FAIL
        employment_reason = next(r for r in result.reasons if r.filter_name == "employment")
        assert employment_reason.result == FilterResult.FAIL

    def test_pipeline_keywords_fail(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            location="San Francisco, CA",
            work_mode="remote",
            employment_type="full_time",
            salary_min=120000,
            description="This is a sales position",
        )
        profile = PreFilterProfileInput(
            location_preferences=["San Francisco"],
            salary_min=100000,
            remote_preference="remote",
            excluded_keywords=["sales"],
        )
        config = PreFilterConfig()
        input_data = PreFilterInput(job=job, profile=profile)

        result = run_pre_filter_pipeline(input_data, config)

        assert result.overall_result == FilterResult.FAIL
        keywords_reason = next(r for r in result.reasons if r.filter_name == "excluded_keywords")
        assert keywords_reason.result == FilterResult.FAIL

    def test_pipeline_unknown_salary(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            location="San Francisco, CA",
            work_mode="remote",
            employment_type="full_time",
            salary_min=None,
            salary_max=None,
        )
        profile = PreFilterProfileInput(
            location_preferences=["San Francisco"],
            salary_min=100000,
            remote_preference="remote",
        )
        config = PreFilterConfig(unknown_salary_behavior="unknown")
        input_data = PreFilterInput(job=job, profile=profile)

        result = run_pre_filter_pipeline(input_data, config)

        assert result.overall_result == FilterResult.UNKNOWN
        salary_reason = next(r for r in result.reasons if r.filter_name == "salary")
        assert salary_reason.result == FilterResult.UNKNOWN

    def test_pipeline_unknown_location(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            location=None,
            work_mode="remote",
            employment_type="full_time",
            salary_min=120000,
            salary_max=150000,
        )
        profile = PreFilterProfileInput(
            location_preferences=["San Francisco"],
            salary_min=100000,
            salary_max=200000,
            remote_preference="remote",
        )
        config = PreFilterConfig(unknown_location_behavior="unknown")
        input_data = PreFilterInput(job=job, profile=profile)

        result = run_pre_filter_pipeline(input_data, config)

        assert result.overall_result == FilterResult.UNKNOWN
        location_reason = next(r for r in result.reasons if r.filter_name == "location")
        assert location_reason.result == FilterResult.UNKNOWN

    def test_pipeline_deterministic(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            location="San Francisco, CA",
            work_mode="remote",
            employment_type="full_time",
            salary_min=120000,
        )
        profile = PreFilterProfileInput(
            location_preferences=["San Francisco"],
            salary_min=100000,
            remote_preference="remote",
        )
        config = PreFilterConfig()
        input_data = PreFilterInput(job=job, profile=profile)

        result1 = run_pre_filter_pipeline(input_data, config)
        result2 = run_pre_filter_pipeline(input_data, config)

        assert result1.overall_result == result2.overall_result
        assert len(result1.reasons) == len(result2.reasons)
        for r1, r2 in zip(result1.reasons, result2.reasons):
            assert r1.filter_name == r2.filter_name
            assert r1.result == r2.result

    def test_pipeline_matched_fields_collected(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            location="San Francisco, CA",
            work_mode="remote",
            employment_type="full_time",
            salary_min=120000,
            salary_max=150000,
        )
        profile = PreFilterProfileInput(
            location_preferences=["San Francisco"],
            salary_min=100000,
            remote_preference="remote",
        )
        config = PreFilterConfig()
        input_data = PreFilterInput(job=job, profile=profile)

        result = run_pre_filter_pipeline(input_data, config)

        assert "matched_location" in result.matched_fields or "job_min" in result.matched_fields