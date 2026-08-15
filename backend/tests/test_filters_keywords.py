from __future__ import annotations

import pytest
from app.filters.schemas import (
    FilterResult,
    PreFilterJobInput,
    PreFilterProfileInput,
    PreFilterConfig,
)
from app.filters.keywords import filter_excluded_keywords


class TestExcludedKeywordsFilter:
    def test_no_excluded_keywords(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            description="Great job",
            skills=["Python", "FastAPI"],
        )
        profile = PreFilterProfileInput(excluded_keywords=[])
        config = PreFilterConfig()

        result = filter_excluded_keywords(job, profile, config)
        assert result.result == FilterResult.PASS
        assert "No excluded keywords" in result.reason

    def test_excluded_keyword_in_title(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Sales Manager",
            description="Great job",
            skills=["Python"],
        )
        profile = PreFilterProfileInput(excluded_keywords=["sales"])
        config = PreFilterConfig()

        result = filter_excluded_keywords(job, profile, config)
        assert result.result == FilterResult.FAIL
        assert "sales" in result.reason

    def test_excluded_keyword_in_description(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            description="This is a sales position",
            skills=["Python"],
        )
        profile = PreFilterProfileInput(excluded_keywords=["sales"])
        config = PreFilterConfig()

        result = filter_excluded_keywords(job, profile, config)
        assert result.result == FilterResult.FAIL
        assert "sales" in result.reason

    def test_excluded_keyword_in_skills(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            description="Great job",
            skills=["Python", "Sales"],
        )
        profile = PreFilterProfileInput(excluded_keywords=["sales"])
        config = PreFilterConfig()

        result = filter_excluded_keywords(job, profile, config)
        assert result.result == FilterResult.FAIL
        assert "sales" in result.reason

    def test_excluded_keyword_in_company(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            company="Sales Corp",
            description="Great job",
            skills=["Python"],
        )
        profile = PreFilterProfileInput(excluded_keywords=["sales"])
        config = PreFilterConfig()

        result = filter_excluded_keywords(job, profile, config)
        assert result.result == FilterResult.FAIL
        assert "sales" in result.reason

    def test_excluded_keyword_in_requirements(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            description="Great job",
            requirements="Must have sales experience",
            skills=["Python"],
        )
        profile = PreFilterProfileInput(excluded_keywords=["sales"])
        config = PreFilterConfig()

        result = filter_excluded_keywords(job, profile, config)
        assert result.result == FilterResult.FAIL
        assert "sales" in result.reason

    def test_no_match(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            description="Great job",
            skills=["Python", "FastAPI"],
        )
        profile = PreFilterProfileInput(excluded_keywords=["sales", "marketing"])
        config = PreFilterConfig()

        result = filter_excluded_keywords(job, profile, config)
        assert result.result == FilterResult.PASS
        assert "No excluded keywords found" in result.reason

    def test_case_insensitive_default(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            description="Great job with sales focus",
            skills=["Python"],
        )
        profile = PreFilterProfileInput(excluded_keywords=["SALES"])
        config = PreFilterConfig(keyword_match_case_sensitive=False)

        result = filter_excluded_keywords(job, profile, config)
        assert result.result == FilterResult.FAIL
        assert "sales" in result.reason.lower()

    def test_case_sensitive_true(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            description="Great job",
            skills=["Python"],
        )
        profile = PreFilterProfileInput(excluded_keywords=["SALES"])
        config = PreFilterConfig(keyword_match_case_sensitive=True)

        result = filter_excluded_keywords(job, profile, config)
        assert result.result == FilterResult.PASS

    def test_case_sensitive_false_match(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            description="Great job with sales focus",
            skills=["Python"],
        )
        profile = PreFilterProfileInput(excluded_keywords=["sales"])
        config = PreFilterConfig(keyword_match_case_sensitive=True)

        result = filter_excluded_keywords(job, profile, config)
        assert result.result == FilterResult.FAIL

    def test_multiple_excluded_keywords_one_matches(self):
        job = PreFilterJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            description="Great job with marketing focus",
            skills=["Python"],
        )
        profile = PreFilterProfileInput(excluded_keywords=["sales", "marketing", "hr"])
        config = PreFilterConfig()

        result = filter_excluded_keywords(job, profile, config)
        assert result.result == FilterResult.FAIL
        assert "marketing" in result.reason