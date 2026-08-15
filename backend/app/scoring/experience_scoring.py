from __future__ import annotations

from typing import Optional
import re

from app.schemas.scoring import ScoringInput, ScoringConfig
from app.schemas.analysis import ExperienceMatchItem


EXPERIENCE_LEVELS = {
    "entry": 0,
    "junior": 1,
    "mid": 2,
    "senior": 3,
    "lead": 4,
    "architect": 5,
    "any": 2,  # default to mid
}


def parse_experience_level(level: Optional[str]) -> int:
    """Parse experience level string to numeric value."""
    if not level:
        return 2
    return EXPERIENCE_LEVELS.get(level.lower(), 2)


def calculate_experience_score(input_data: ScoringInput, config: ScoringConfig) -> int:
    """Calculate experience match score based on analysis evidence and profile level."""
    # If no experience evidence, use level matching
    if not input_data.matching_experience:
        return calculate_level_match_score(input_data)
    
    # Score based on matching experience claims
    matched_count = len(input_data.matching_experience)
    
    # Base score from number of matching experiences
    # Each matching experience adds ~15 points, max 100
    base_score = min(100, matched_count * 20 + 40)
    
    # Adjust for experience level match
    profile_level = parse_experience_level(input_data.profile_experience_level)
    job_level = estimate_job_level(input_data)
    
    level_diff = abs(profile_level - job_level)
    if level_diff == 0:
        level_bonus = 20
    elif level_diff == 1:
        level_bonus = 10
    elif level_diff == 2:
        level_bonus = 0
    else:
        level_bonus = -10
    
    score = base_score + level_bonus
    
    return max(0, min(100, score))


def calculate_level_match_score(input_data: ScoringInput) -> int:
    """Calculate score based only on experience level match."""
    profile_level = parse_experience_level(input_data.profile_experience_level)
    job_level = estimate_job_level(input_data)
    
    level_diff = abs(profile_level - job_level)
    
    if level_diff == 0:
        return 80
    elif level_diff == 1:
        return 65
    elif level_diff == 2:
        return 50
    elif level_diff == 3:
        return 35
    else:
        return 25


def estimate_job_level(input_data: ScoringInput) -> int:
    """Estimate job experience level from title and requirements."""
    title = input_data.job_title.lower()
    
    # Check for senior/lead keywords in title
    if any(kw in title for kw in ["senior", "sr.", "lead", "principal", "architect", "staff"]):
        return 3
    if any(kw in title for kw in ["junior", "jr.", "entry", "graduate", "intern"]):
        return 1
    
    # Check requirements for experience years
    if input_data.matching_experience:
        for item in input_data.matching_experience:
            claim = item.claim.lower()
            # Look for year patterns like "5 years", "3+ years"
            import re
            years_match = re.search(r'(\d+)\+?\s*years?', claim)
            if years_match:
                years = int(years_match.group(1))
                if years >= 8:
                    return 4
                elif years >= 5:
                    return 3
                elif years >= 3:
                    return 2
                elif years >= 1:
                    return 1
    
    # Default to mid-level
    return 2


def extract_experience_years(input_data: ScoringInput) -> int:
    """Extract years of experience from matching experience claims."""
    max_years = 0
    import re
    for item in input_data.matching_experience:
        claim = item.claim.lower()
        years_match = re.search(r'(\d+)\+?\s*years?', claim)
        if years_match:
            max_years = max(max_years, int(years_match.group(1)))
    return max_years