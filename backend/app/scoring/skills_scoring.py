from __future__ import annotations

from typing import List, Set
from app.schemas.scoring import ScoringInput, ScoringConfig
from app.schemas.analysis import SkillMatchItem


def calculate_skills_score(input_data: ScoringInput, config: ScoringConfig) -> int:
    """Calculate skills match score based on job requirements vs profile skills.
    
    Score is based on the percentage of job skills that are matched by profile skills.
    """
    if not input_data.job_skills:
        return 50  # Neutral if no job skills specified
    
    job_skills_lower = {s.lower().strip() for s in input_data.job_skills}
    if not job_skills_lower:
        return 50
    
    # Get matched skills from analysis evidence
    matched_skills: Set[str] = set()
    for item in input_data.matching_skills:
        matched_skills.add(item.claim.lower().strip())
    
    # Also check profile technical skills directly
    profile_skills = {s.lower().strip() for s in input_data.profile_desired_roles}
    # Note: profile technical skills would be in a different field, but we use matching_skills from analysis
    
    # Calculate match percentage
    matched_count = len(matched_skills & job_skills_lower)
    total_job_skills = len(job_skills_lower)
    
    if total_job_skills == 0:
        return 50
    
    match_ratio = matched_count / total_job_skills
    
    # Convert to 0-100 score
    # 100% match = 100, 50% match = 75, 0% match = 25 (not 0 because some skills may be implicit)
    score = round(25 + match_ratio * 75)
    
    return max(0, min(100, score))


def extract_matched_skills(input_data: ScoringInput) -> List[str]:
    """Extract list of matched skill claims from analysis."""
    return [item.claim for item in input_data.matching_skills]


def extract_missing_skills(input_data: ScoringInput) -> List[str]:
    """Extract list of missing skill claims from analysis."""
    return [item.claim for item in input_data.missing_requirements if item.claim.lower() in 
            {s.lower() for s in input_data.job_skills}]