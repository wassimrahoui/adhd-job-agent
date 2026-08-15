from __future__ import annotations

import pytest
from app.filters.schemas import (
    FilterResult,
    PreFilterJobInput,
    PreFilterProfileInput,
    PreFilterConfig,
)
from app.filters.location import filter_location


class TestLocationFilter:
    def test_location_exact_match(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            location="San Francisco, CA",
        )
        profile = PreFilterProfileInput(
            location_preferences=["San Francisco, CA"],
        )
        config = PreFilterConfig(location_match_mode="exact")

        result = filter_location(job, profile, config)
        assert result.result == FilterResult.PASS
        assert "exactly" in result.reason

    def test_location_contains_match(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            location="San Francisco, CA",
        )
        profile = PreFilterProfileInput(
            location_preferences=["San Francisco"],
        )
        config = PreFilterConfig(location_match_mode="contains")

        result = filter_location(job, profile, config)
        assert result.result == FilterResult.PASS
        assert "contains" in result.reason

    def test_location_contains_match_reverse(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            location="San Francisco",
        )
        profile = PreFilterProfileInput(
            location_preferences=["San Francisco, CA"],
        )
        config = PreFilterConfig(location_match_mode="contains")

        result = filter_location(job, profile, config)
        assert result.result == FilterResult.PASS

    def test_location_no_match(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            location="New York, NY",
        )
        profile = PreFilterProfileInput(
            location_preferences=["San Francisco", "Los Angeles"],
        )
        config = PreFilterConfig(location_match_mode="contains")

        result = filter_location(job, profile, config)
        assert result.result == FilterResult.FAIL
        assert "does not match" in result.reason

    def test_location_no_preferences(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            location="New York, NY",
        )
        profile = PreFilterProfileInput(location_preferences=[])
        config = PreFilterConfig(location_match_mode="contains")

        result = filter_location(job, profile, config)
        assert result.result == FilterResult.PASS
        assert "No location preferences" in result.reason

    def test_location_job_not_specified_unknown(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            location=None,
        )
        profile = PreFilterProfileInput(
            location_preferences=["San Francisco"],
        )
        config = PreFilterConfig(location_match_mode="contains", unknown_location_behavior="unknown")

        result = filter_location(job, profile, config)
        assert result.result == FilterResult.UNKNOWN

    def test_location_job_not_specified_pass(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            location=None,
        )
        profile = PreFilterProfileInput(
            location_preferences=["San Francisco"],
        )
        config = PreFilterConfig(location_match_mode="contains", unknown_location_behavior="pass")

        result = filter_location(job, profile, config)
        assert result.result == FilterResult.PASS

    def test_location_job_not_specified_fail(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            location=None,
        )
        profile = PreFilterProfileInput(
            location_preferences=["San Francisco"],
        )
        config = PreFilterConfig(location_match_mode="contains", unknown_location_behavior="fail")

        result = filter_location(job, profile, config)
        assert result.result == FilterResult.FAIL

    def test_location_any_mode(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            location="Anywhere",
        )
        profile = PreFilterProfileInput(
            location_preferences=["San Francisco"],
        )
        config = PreFilterConfig(location_match_mode="any")

        result = filter_location(job, profile, config)
        assert result.result == FilterResult.PASS
        assert "Any location" in result.reason

    def test_location_case_insensitive(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            location="SAN FRANCISCO, CA",
        )
        profile = PreFilterProfileInput(
            location_preferences=["san francisco"],
        )
        config = PreFilterConfig(location_match_mode="contains")

        result = filter_location(job, profile, config)
        assert result.result == FilterResult.PASS