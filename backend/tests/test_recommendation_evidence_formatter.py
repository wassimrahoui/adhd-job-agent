from __future__ import annotations

import pytest

from app.recommendation.evidence_formatter import EvidenceFormatter


class TestEvidenceFormatter:
    @pytest.fixture
    def formatter(self):
        return EvidenceFormatter()

    def test_format_evidence_basic(self, formatter):
        evidence = [
            {"type": "skill", "value": "Python", "confidence": "high"},
            {"type": "skill", "value": "Django", "confidence": "medium"},
        ]
        formatted = formatter.format_evidence(evidence)
        
        assert len(formatted) == 2
        assert formatted[0]["type"] == "skill"
        assert formatted[0]["value"] == "Python"
        assert formatted[0]["source"] == "analysis"
        assert formatted[0]["confidence"] == "high"
        assert formatted[1]["confidence"] == "medium"

    def test_format_evidence_missing_fields(self, formatter):
        evidence = [
            {"type": "skill", "value": "Python"},
            {"value": "Django"},  # missing type
            {"type": "experience"},  # missing value
        ]
        formatted = formatter.format_evidence(evidence)
        
        assert len(formatted) == 3
        assert formatted[0]["type"] == "skill"
        assert formatted[1]["type"] == "unknown"
        assert formatted[2]["value"] == ""

    def test_extract_skills_from_evidence(self, formatter):
        evidence = [
            {"type": "skill", "value": "Python"},
            {"type": "skill", "value": "Django"},
            {"type": "experience", "value": "5 years"},
            {"type": "requirement", "value": "Bachelor's degree"},
        ]
        skills = formatter.extract_skills_from_evidence(evidence)
        
        assert skills == ["Python", "Django"]

    def test_extract_requirements_from_evidence(self, formatter):
        evidence = [
            {"type": "skill", "value": "Python"},
            {"type": "requirement", "value": "Bachelor's degree"},
            {"type": "requirement", "value": "3+ years experience"},
        ]
        requirements = formatter.extract_requirements_from_evidence(evidence)
        
        assert requirements == ["Bachelor's degree", "3+ years experience"]

    def test_extract_experience_from_evidence(self, formatter):
        evidence = [
            {"type": "skill", "value": "Python"},
            {"type": "experience", "value": "5 years Python"},
            {"type": "experience", "value": "3 years Django"},
        ]
        experience = formatter.extract_experience_from_evidence(evidence)
        
        assert experience == ["5 years Python", "3 years Django"]

    def test_summarize_evidence(self, formatter):
        evidence = [
            {"type": "skill", "value": "Python"},
            {"type": "skill", "value": "Django"},
            {"type": "experience", "value": "5 years"},
            {"type": "requirement", "value": "Degree"},
        ]
        summary = formatter.summarize_evidence(evidence)
        
        assert summary == {"skill": 2, "experience": 1, "requirement": 1}

    def test_filter_high_confidence_evidence(self, formatter):
        evidence = [
            {"type": "skill", "value": "Python", "confidence": "high"},
            {"type": "skill", "value": "Django", "confidence": "medium"},
            {"type": "skill", "value": "Flask", "confidence": "low"},
        ]
        high_conf = formatter.filter_high_confidence_evidence(evidence, "high")
        med_conf = formatter.filter_high_confidence_evidence(evidence, "medium")
        low_conf = formatter.filter_high_confidence_evidence(evidence, "low")
        
        assert len(high_conf) == 1
        assert high_conf[0]["value"] == "Python"
        assert len(med_conf) == 2
        assert len(low_conf) == 3

    def test_format_empty_evidence(self, formatter):
        formatted = formatter.format_evidence([])
        assert formatted == []

    def test_summarize_empty_evidence(self, formatter):
        summary = formatter.summarize_evidence([])
        assert summary == {}