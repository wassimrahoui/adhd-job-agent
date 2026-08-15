from __future__ import annotations

import pytest
from app.schemas.analysis import AnalysisInput, AnalysisJobInput, AnalysisProfileInput
from app.analysis.prompt_builder import build_analysis_prompt


class TestPromptBuilder:
    def test_build_prompt_basic(self):
        job = AnalysisJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            company="Tech Corp",
            location="San Francisco, CA",
            work_mode="remote",
            employment_type="full_time",
            salary_min=120000,
            salary_max=150000,
            salary_currency="USD",
            description="Build backend APIs",
            requirements="Python, FastAPI, PostgreSQL",
            skills=["Python", "FastAPI", "PostgreSQL"],
        )
        profile = AnalysisProfileInput(
            work_experience="5 years Python backend development",
            technical_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
            education="BS Computer Science",
            desired_roles=["Software Engineer", "Backend Developer"],
            location_preferences=["San Francisco", "Remote"],
            salary_min=100000,
            salary_max=160000,
            remote_preference="remote",
        )
        input_data = AnalysisInput(job=job, profile=profile)

        prompt = build_analysis_prompt(input_data)

        assert "Software Engineer" in prompt
        assert "Tech Corp" in prompt
        assert "San Francisco, CA" in prompt
        assert "remote" in prompt.lower()
        assert "Python" in prompt
        assert "FastAPI" in prompt
        assert "PostgreSQL" in prompt
        assert "5 years Python backend" in prompt
        assert "BS Computer Science" in prompt
        assert "120000" in prompt
        assert "150000" in prompt
        assert "JSON" in prompt
        assert "matching_skills" in prompt
        assert "missing_requirements" in prompt
        assert "unknown_requirements" in prompt

    def test_build_prompt_minimal_job(self):
        job = AnalysisJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
        )
        profile = AnalysisProfileInput()
        input_data = AnalysisInput(job=job, profile=profile)

        prompt = build_analysis_prompt(input_data)

        assert "Software Engineer" in prompt
        assert "JOB DATA" in prompt
        assert "CANDIDATE PROFILE" in prompt

    def test_build_prompt_with_resume(self):
        job = AnalysisJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            description="Python backend role",
        )
        profile = AnalysisProfileInput(
            resume_text="John Doe\n5 years Python\nBuilt APIs with FastAPI",
        )
        input_data = AnalysisInput(job=job, profile=profile)

        prompt = build_analysis_prompt(input_data)

        assert "John Doe" in prompt
        assert "5 years Python" in prompt
        assert "Built APIs" in prompt

    def test_build_prompt_does_not_invent_facts(self):
        """Prompt should only contain facts from input in the data sections, not invented ones."""
        job = AnalysisJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            description="Python backend role",
        )
        profile = AnalysisProfileInput(
            technical_skills=["Python"],
        )
        input_data = AnalysisInput(job=job, profile=profile)

        prompt = build_analysis_prompt(input_data)

        # The JOB DATA and CANDIDATE PROFILE sections should only have input facts
        # (the instructions section may contain example terms like Kubernetes)
        job_section = prompt.split("=== CANDIDATE PROFILE ===")[0]
        profile_section = prompt.split("=== CANDIDATE PROFILE ===")[1].split("=== ANALYSIS INSTRUCTIONS ===")[0]

        assert "Kubernetes" not in job_section
        assert "Kubernetes" not in profile_section
        assert "AWS" not in job_section
        assert "AWS" not in profile_section
        assert "React" not in job_section
        assert "React" not in profile_section
        assert "GraphQL" not in job_section
        assert "GraphQL" not in profile_section

    def test_build_prompt_salary_predicted_flag(self):
        job = AnalysisJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            salary_min=100000,
            salary_is_predicted=True,
        )
        profile = AnalysisProfileInput()
        input_data = AnalysisInput(job=job, profile=profile)

        prompt = build_analysis_prompt(input_data)

        assert "predicted" in prompt.lower()

    def test_build_prompt_deterministic(self):
        """Same input should always produce same prompt."""
        job = AnalysisJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            description="Python role",
        )
        profile = AnalysisProfileInput(
            technical_skills=["Python"],
        )
        input_data = AnalysisInput(job=job, profile=profile)

        prompt1 = build_analysis_prompt(input_data)
        prompt2 = build_analysis_prompt(input_data)

        assert prompt1 == prompt2

    def test_build_prompt_excluded_keywords(self):
        job = AnalysisJobInput(
            id=1,
            adzuna_id="test-1",
            title="Sales Engineer",
            description="Sales role",
        )
        profile = AnalysisProfileInput(
            excluded_keywords=["sales", "marketing"],
        )
        input_data = AnalysisInput(job=job, profile=profile)

        prompt = build_analysis_prompt(input_data)

        assert "sales" in prompt.lower()
        assert "marketing" in prompt.lower()