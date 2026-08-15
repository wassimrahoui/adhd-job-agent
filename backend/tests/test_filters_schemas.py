from __future__ import annotations

import pytest
from datetime import datetime
from app.filters.schemas import (
    FilterResult,
    FilterReason,
    PreFilterJobInput,
    PreFilterProfileInput,
    PreFilterInput,
    PreFilterOutput,
    PreFilterConfig,
)


class TestFilterResult:
    def test_filter_result_values(self):
        assert FilterResult.PASS == "pass"
        assert FilterResult.FAIL == "fail"
        assert FilterResult.UNKNOWN == "unknown"


class TestPreFilterJobInput:
    def test_valid_job_input(self):
        job = PreFilterJobInput(
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

    def test_job_input_minimal(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-123",
            title="Software Engineer",
        )
        assert job.company is None
        assert job.location is None
        assert job.skills == []
        assert job.raw_evidence == {}

    def test_job_input_invalid_missing_required(self):
        with pytest.raises(Exception):
            PreFilterJobInput(adzuna_id="test-123", title="Software Engineer")


class TestPreFilterProfileInput:
    def test_valid_profile_input(self):
        profile = PreFilterProfileInput(
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
        profile = PreFilterProfileInput()
        assert profile.technical_skills == []
        assert profile.desired_roles == []
        assert profile.location_preferences == []
        assert profile.salary_currency == "USD"
        assert profile.remote_preference == "any"
        assert profile.experience_level == "any"
        assert profile.relevance_threshold == 50


class TestPreFilterInput:
    def test_valid_prefilter_input(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-123",
            title="Software Engineer",
        )
        profile = PreFilterProfileInput()
        input_data = PreFilterInput(job=job, profile=profile)
        assert input_data.job.title == "Software Engineer"
        assert input_data.profile.salary_currency == "USD"


class TestPreFilterOutput:
    def test_valid_output(self):
        output = PreFilterOutput(
            overall_result=FilterResult.PASS,
            reasons=[
                FilterReason(filter_name="location", result=FilterResult.PASS, reason="Location matches"),
                FilterReason(filter_name="salary", result=FilterResult.UNKNOWN, reason="Salary not specified"),
            ],
            matched_fields={"location": "San Francisco"},
        )
        assert output.overall_result == FilterResult.PASS
        assert len(output.reasons) == 2
        assert output.matched_fields["location"] == "San Francisco"

    def test_output_defaults(self):
        output = PreFilterOutput(overall_result=FilterResult.FAIL)
        assert output.reasons == []
        assert output.matched_fields == {}


class TestPreFilterConfig:
    def test_default_config(self):
        config = PreFilterConfig()
        assert config.location_match_mode == "contains"
        assert config.salary_compare_mode == "range_overlap"
        assert config.employment_type_match_mode == "any"
        assert config.work_mode_match_mode == "any"
        assert config.keyword_match_case_sensitive is False
        assert config.unknown_salary_behavior == "unknown"
        assert config.unknown_location_behavior == "unknown"

    def test_custom_config(self):
        config = PreFilterConfig(
            location_match_mode="exact",
            salary_compare_mode="min_only",
            unknown_salary_behavior="pass",
        )
        assert config.location_match_mode == "exact"
        assert config.salary_compare_mode == "min_only"
        assert config.unknown_salary_behavior == "pass"

    def test_invalid_location_match_mode(self):
        with pytest.raises(Exception):
            PreFilterConfig(location_match_mode="invalid")

    def test_invalid_salary_compare_mode(self):
        with pytest.raises(Exception):
            PreFilterConfig(salary_compare_mode="invalid")