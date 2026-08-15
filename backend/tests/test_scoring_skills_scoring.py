from __future__ import annotations

import pytest

from app.scoring.skills_scoring import calculate_skills_score, extract_matched_skills, extract_missing_skills
from app.schemas.scoring import ScoringInput, ScoringConfig
from app.schemas.analysis import SkillMatchItem, RequirementGapItem, AnalysisStatus


class TestCalculateSkillsScore:
    def setup_method(self):
        self.config = ScoringConfig()

    def test_no_job_skills_returns_neutral(self):
        input_data = ScoringInput(
            job_title="Engineer",
            job_skills=[],
        )
        score = calculate_skills_score(input_data, self.config)
        assert score == 50

    def test_all_skills_matched(self):
        input_data = ScoringInput(
            job_title="Engineer",
            job_skills=["Python", "Django", "PostgreSQL"],
            matching_skills=[
                SkillMatchItem(claim="Python", source_excerpt="requires Python"),
                SkillMatchItem(claim="Django", source_excerpt="Django framework"),
                SkillMatchItem(claim="PostgreSQL", source_excerpt="PostgreSQL database"),
            ],
        )
        score = calculate_skills_score(input_data, self.config)
        assert score == 100

    def test_partial_skills_matched(self):
        input_data = ScoringInput(
            job_title="Engineer",
            job_skills=["Python", "Django", "PostgreSQL", "Redis", "AWS"],
            matching_skills=[
                SkillMatchItem(claim="Python", source_excerpt="requires Python"),
                SkillMatchItem(claim="Django", source_excerpt="Django framework"),
                SkillMatchItem(claim="PostgreSQL", source_excerpt="PostgreSQL database"),
            ],
        )
        # 3/5 = 60% match -> 25 + 0.6 * 75 = 70
        score = calculate_skills_score(input_data, self.config)
        assert score == 70

    def test_no_skills_matched(self):
        input_data = ScoringInput(
            job_title="Engineer",
            job_skills=["Python", "Django"],
            matching_skills=[],
        )
        # 0/2 = 0% match -> 25 + 0 * 75 = 25
        score = calculate_skills_score(input_data, self.config)
        assert score == 25

    def test_case_insensitive_matching(self):
        input_data = ScoringInput(
            job_title="Engineer",
            job_skills=["Python", "Django"],
            matching_skills=[
                SkillMatchItem(claim="python", source_excerpt="requires python"),
                SkillMatchItem(claim="DJANGO", source_excerpt="django framework"),
            ],
        )
        score = calculate_skills_score(input_data, self.config)
        assert score == 100

    def test_whitespace_handling(self):
        input_data = ScoringInput(
            job_title="Engineer",
            job_skills=[" Python ", " Django "],
            matching_skills=[
                SkillMatchItem(claim="Python", source_excerpt="requires Python"),
                SkillMatchItem(claim="Django", source_excerpt="Django framework"),
            ],
        )
        score = calculate_skills_score(input_data, self.config)
        assert score == 100


class TestExtractMatchedSkills:
    def test_extract_matched_skills(self):
        input_data = ScoringInput(
            job_title="Engineer",
            matching_skills=[
                SkillMatchItem(claim="Python", source_excerpt="requires Python"),
                SkillMatchItem(claim="Django", source_excerpt="Django framework"),
            ],
        )
        matched = extract_matched_skills(input_data)
        assert matched == ["Python", "Django"]

    def test_extract_empty(self):
        input_data = ScoringInput(job_title="Engineer")
        matched = extract_matched_skills(input_data)
        assert matched == []


class TestExtractMissingSkills:
    def test_extract_missing_skills(self):
        input_data = ScoringInput(
            job_title="Engineer",
            job_skills=["Python", "Django", "Redis"],
            missing_requirements=[
                RequirementGapItem(claim="Redis", source_excerpt="Redis required"),
                RequirementGapItem(claim="Kubernetes", source_excerpt="K8s required"),
            ],
        )
        missing = extract_missing_skills(input_data)
        assert missing == ["Redis"]

    def test_extract_empty(self):
        input_data = ScoringInput(job_title="Engineer")
        missing = extract_missing_skills(input_data)
        assert missing == []