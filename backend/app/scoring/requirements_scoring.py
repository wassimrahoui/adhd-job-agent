from __future__ import annotations

from app.schemas.scoring import ScoringInput, ScoringConfig
from app.schemas.analysis import RequirementGapItem, UnknownRequirementItem


def calculate_requirements_score(input_data: ScoringInput, config: ScoringConfig) -> int:
    """Calculate requirements coverage score.
    
    Based on: met requirements / (met + missing + unknown)
    - met = matching_skills + matching_experience (as proxy for met requirements)
    - missing = missing_requirements count
    - unknown = unknown_requirements count
    """
    # Count met requirements (from matching skills and experience)
    met_count = len(input_data.matching_skills) + len(input_data.matching_experience)
    
    # Count missing and unknown from analysis
    missing_count = len(input_data.missing_requirements)
    unknown_count = len(input_data.unknown_requirements)
    
    total_requirements = met_count + missing_count + unknown_count
    
    if total_requirements == 0:
        return 50  # Neutral if no requirements info
    
    # Score based on met ratio
    met_ratio = met_count / total_requirements
    
    # Convert to 0-100 score
    # 100% met = 100, 75% = 85, 50% = 65, 25% = 40, 0% = 15
    score = round(15 + met_ratio * 85)
    
    return max(0, min(100, score))


def get_requirements_breakdown(input_data: ScoringInput) -> dict:
    """Get detailed breakdown of requirements coverage."""
    met_count = len(input_data.matching_skills) + len(input_data.matching_experience)
    missing_count = len(input_data.missing_requirements)
    unknown_count = len(input_data.unknown_requirements)
    total = met_count + missing_count + unknown_count
    
    return {
        "met": met_count,
        "missing": missing_count,
        "unknown": unknown_count,
        "total": total,
        "met_ratio": met_count / total if total > 0 else 0.0,
    }


def categorize_missing_requirements(input_data: ScoringInput) -> dict:
    """Categorize missing requirements by type (skill, experience, certification, etc.)."""
    categories = {
        "skill": [],
        "experience": [],
        "certification": [],
        "education": [],
        "other": [],
    }
    
    skill_keywords = ["python", "java", "go", "rust", "sql", "nosql", "aws", "azure", "gcp", 
                      "docker", "kubernetes", "kafka", "redis", "postgresql", "mongodb",
                      "react", "vue", "angular", "django", "flask", "fastapi", "spring",
                      "microservices", "api", "graphql", "rest", "grpc"]
    
    exp_keywords = ["year", "experience", "senior", "lead", "architect", "managed", "led"]
    
    cert_keywords = ["certified", "certification", "aws certified", "azure certified", 
                     "google cloud", "ckad", "cka", "pmp", "scrum"]
    
    edu_keywords = ["degree", "bachelor", "master", "phd", "computer science", "engineering"]
    
    for item in input_data.missing_requirements:
        claim_lower = item.claim.lower()
        
        # Check certification first (more specific)
        if any(kw in claim_lower for kw in cert_keywords):
            categories["certification"].append(item.claim)
        elif any(kw in claim_lower for kw in exp_keywords):
            categories["experience"].append(item.claim)
        elif any(kw in claim_lower for kw in edu_keywords):
            categories["education"].append(item.claim)
        elif any(kw in claim_lower for kw in skill_keywords):
            categories["skill"].append(item.claim)
        else:
            categories["other"].append(item.claim)
    
    return categories