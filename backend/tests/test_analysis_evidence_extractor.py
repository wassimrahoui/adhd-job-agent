from __future__ import annotations

import pytest

from app.analysis.evidence_extractor import EvidenceExtractor, extract_evidence
from app.schemas.analysis import AnalysisInput, AnalysisJobInput, AnalysisProfileInput


class TestEvidenceExtractor:
    def setup_method(self):
        self.extractor = EvidenceExtractor()

    def test_extract_job_evidence_basic(self):
        job = AnalysisJobInput(
            id=1,
            adzuna_id="test-1",
            title="Software Engineer",
            company="Test Corp",
            location="Berlin, Germany",
            work_mode="hybrid",
            employment_type="full_time",
        )
        evidence = self.extractor.extract_job_evidence(job)
        assert evidence["title"] == "Software Engineer"
        assert evidence["company"] == "Test Corp"
        assert evidence["location"] == "Berlin, Germany"
        assert evidence["work_mode"] == "hybrid"
        assert evidence["employment_type"] == "full_time"
        assert evidence["salary"] is None
        assert evidence["description"] is None
        assert evidence["requirements"] is None
        assert evidence["skills"] == []

    def test_extract_job_evidence_with_salary(self):
        job = AnalysisJobInput(
            id=1,
            adzuna_id="test-1",
            title="Engineer",
            salary_min=50000,
            salary_max=70000,
            salary_currency="EUR",
            salary_is_predicted=True,
        )
        evidence = self.extractor.extract_job_evidence(job)
        assert evidence["salary"] == "min: 50000, max: 70000, currency: EUR (predicted)"

    def test_extract_job_evidence_salary_min_only(self):
        job = AnalysisJobInput(
            id=1,
            adzuna_id="test-1",
            title="Engineer",
            salary_min=45000,
            salary_currency="EUR",
        )
        evidence = self.extractor.extract_job_evidence(job)
        assert evidence["salary"] == "min: 45000, currency: EUR"

    def test_extract_job_evidence_salary_max_only(self):
        job = AnalysisJobInput(
            id=1,
            adzuna_id="test-1",
            title="Engineer",
            salary_max=80000,
            salary_currency="USD",
        )
        evidence = self.extractor.extract_job_evidence(job)
        assert evidence["salary"] == "max: 80000, currency: USD"

    def test_extract_job_evidence_truncates_description(self):
        long_desc = "x" * 5000
        job = AnalysisJobInput(
            id=1,
            adzuna_id="test-1",
            title="Engineer",
            description=long_desc,
        )
        evidence = self.extractor.extract_job_evidence(job)
        assert len(evidence["description"]) == 2000

    def test_extract_job_evidence_truncates_requirements(self):
        long_req = "y" * 5000
        job = AnalysisJobInput(
            id=1,
            adzuna_id="test-1",
            title="Engineer",
            requirements=long_req,
        )
        evidence = self.extractor.extract_job_evidence(job)
        assert len(evidence["requirements"]) == 2000

    def test_extract_job_evidence_with_skills(self):
        job = AnalysisJobInput(
            id=1,
            adzuna_id="test-1",
            title="Engineer",
            skills=["Python", "Docker", "Kubernetes"],
        )
        evidence = self.extractor.extract_job_evidence(job)
        assert evidence["skills"] == ["Python", "Docker", "Kubernetes"]

    def test_extract_profile_evidence_basic(self):
        profile = AnalysisProfileInput(
            work_experience="5 years backend development",
            technical_skills=["Python", "Go"],
            networking_experience="3 years network security",
            education="MSc Computer Science",
            certifications=["AWS Solutions Architect"],
            languages=["English", "German"],
            desired_roles=["Backend Engineer", "DevOps"],
            location_preferences=["Berlin", "Munich", "Remote"],
            remote_preference="hybrid",
            experience_level="mid",
            excluded_keywords=["senior", "lead"],
        )
        evidence = self.extractor.extract_profile_evidence(profile)
        assert evidence["work_experience"] == "5 years backend development"
        assert evidence["technical_skills"] == ["Python", "Go"]
        assert evidence["networking_experience"] == "3 years network security"
        assert evidence["education"] == "MSc Computer Science"
        assert evidence["certifications"] == ["AWS Solutions Architect"]
        assert evidence["languages"] == ["English", "German"]
        assert evidence["desired_roles"] == ["Backend Engineer", "DevOps"]
        assert evidence["location_preferences"] == ["Berlin", "Munich", "Remote"]
        assert evidence["remote_preference"] == "hybrid"
        assert evidence["experience_level"] == "mid"
        assert evidence["excluded_keywords"] == ["senior", "lead"]

    def test_extract_profile_evidence_with_salary(self):
        profile = AnalysisProfileInput(
            salary_min=55000,
            salary_max=65000,
            salary_currency="EUR",
        )
        evidence = self.extractor.extract_profile_evidence(profile)
        assert evidence["salary_expectations"] == "min: 55000, max: 65000, currency: EUR"

    def test_extract_profile_evidence_truncates_resume(self):
        long_resume = "z" * 5000
        profile = AnalysisProfileInput(resume_text=long_resume)
        evidence = self.extractor.extract_profile_evidence(profile)
        assert len(evidence["resume_text"]) == 3000

    def test_extract_all(self):
        job = AnalysisJobInput(
            id=1,
            adzuna_id="test-1",
            title="Engineer",
            company="Corp",
            skills=["Python"],
        )
        profile = AnalysisProfileInput(
            technical_skills=["Python", "Go"],
        )
        input_data = AnalysisInput(job=job, profile=profile)
        result = self.extractor.extract_all(input_data)
        assert "job" in result
        assert "profile" in result
        assert result["job"]["title"] == "Engineer"
        assert result["job"]["skills"] == ["Python"]
        assert result["profile"]["technical_skills"] == ["Python", "Go"]


class TestExtractEvidenceConvenience:
    def test_extract_evidence_function(self):
        job = AnalysisJobInput(id=1, adzuna_id="test-1", title="Engineer")
        profile = AnalysisProfileInput()
        input_data = AnalysisInput(job=job, profile=profile)
        result = extract_evidence(input_data)
        assert "job" in result
        assert "profile" in result
        assert result["job"]["title"] == "Engineer"