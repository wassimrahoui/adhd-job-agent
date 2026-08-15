from __future__ import annotations

import json

import pytest

from app.analysis.request_builder import AnalysisRequestBuilder, build_analysis_request
from app.schemas.analysis import AnalysisInput, AnalysisJobInput, AnalysisProfileInput, AnalysisOutput


class TestAnalysisRequestBuilder:
    def setup_method(self):
        self.builder = AnalysisRequestBuilder("qwen2.5:14b-instruct-q4_K_M")

    def test_build_request_basic(self):
        job = AnalysisJobInput(id=1, adzuna_id="test-1", title="Software Engineer")
        profile = AnalysisProfileInput()
        input_data = AnalysisInput(job=job, profile=profile)

        request = self.builder.build_request(input_data)

        assert request["model"] == "qwen2.5:14b-instruct-q4_K_M"
        assert request["stream"] is False
        assert request["options"]["temperature"] == 0.1
        assert request["options"]["top_p"] == 0.9
        assert "prompt" in request
        assert "Software Engineer" in request["prompt"]
        assert "IMPORTANT: Respond ONLY with valid JSON" in request["prompt"]

    def test_build_request_includes_schema(self):
        job = AnalysisJobInput(id=1, adzuna_id="test-1", title="Engineer")
        profile = AnalysisProfileInput()
        input_data = AnalysisInput(job=job, profile=profile)

        request = self.builder.build_request(input_data)

        # Check schema is embedded in prompt
        assert "model_used" in request["prompt"]
        assert "score" in request["prompt"]
        assert "recommendation" in request["prompt"]
        assert "matching_skills" in request["prompt"]

    def test_build_request_with_full_data(self):
        job = AnalysisJobInput(
            id=1,
            adzuna_id="test-1",
            title="Senior Python Developer",
            company="Tech Corp",
            location="Berlin, Germany",
            work_mode="hybrid",
            salary_min=60000,
            salary_max=80000,
            salary_currency="EUR",
            skills=["Python", "Django", "PostgreSQL"],
        )
        profile = AnalysisProfileInput(
            technical_skills=["Python", "Go", "Docker"],
            work_experience="5 years Python backend",
            desired_roles=["Backend Engineer"],
            location_preferences=["Berlin", "Remote"],
            remote_preference="hybrid",
        )
        input_data = AnalysisInput(job=job, profile=profile)

        request = self.builder.build_request(input_data)

        assert "Senior Python Developer" in request["prompt"]
        assert "Tech Corp" in request["prompt"]
        assert "Berlin, Germany" in request["prompt"]
        assert "hybrid" in request["prompt"]
        assert "60000" in request["prompt"]
        assert "80000" in request["prompt"]
        assert "Python" in request["prompt"]
        assert "Django" in request["prompt"]
        assert "5 years Python backend" in request["prompt"]

    def test_format_schema(self):
        schema = self.builder._format_schema(AnalysisOutput.model_json_schema())
        parsed = json.loads(schema)
        assert "properties" in parsed
        assert "model_used" in parsed["properties"]
        assert "score" in parsed["properties"]


class TestBuildAnalysisRequestConvenience:
    def test_build_analysis_request_function(self):
        job = AnalysisJobInput(id=1, adzuna_id="test-1", title="Engineer")
        profile = AnalysisProfileInput()
        input_data = AnalysisInput(job=job, profile=profile)

        request = build_analysis_request(input_data, "test-model")

        assert request["model"] == "test-model"
        assert "prompt" in request