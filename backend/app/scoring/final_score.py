from __future__ import annotations

from app.schemas.scoring import ScoringInput, ScoringConfig, ScoringOutput
from app.schemas.analysis import Recommendation, Confidence, AnalysisStatus
from app.scoring.skills_scoring import calculate_skills_score
from app.scoring.experience_scoring import calculate_experience_score
from app.scoring.requirements_scoring import calculate_requirements_score


def calculate_location_score(input_data: ScoringInput, config: ScoringConfig) -> int:
    """Calculate location match score."""
    if not input_data.job_location or not input_data.profile_location_preferences:
        return 50  # Neutral if no location info
    
    job_loc = input_data.job_location.lower()
    profile_locs = [loc.lower() for loc in input_data.profile_location_preferences]
    
    # Exact match
    if any(job_loc == loc for loc in profile_locs):
        return 100
    
    # Partial match (city in region, or remote match)
    if "remote" in job_loc and "remote" in profile_locs:
        return 100
    
    # Check if job location contains any profile location
    for loc in profile_locs:
        if loc in job_loc or job_loc in loc:
            return 75
    
    # Same country heuristic (simplified)
    return 25


def calculate_salary_score(input_data: ScoringInput, config: ScoringConfig) -> int:
    """Calculate salary match score."""
    # No salary info
    if not input_data.job_salary_min and not input_data.job_salary_max:
        return 50
    
    if not input_data.profile_salary_min and not input_data.profile_salary_max:
        return 50
    
    # Job salary range
    job_min = input_data.job_salary_min or 0
    job_max = input_data.job_salary_max or job_min * 2
    
    # Profile expectations
    profile_min = input_data.profile_salary_min or 0
    profile_max = input_data.profile_salary_max or profile_min * 2
    
    # Calculate overlap
    overlap_min = max(job_min, profile_min)
    overlap_max = min(job_max, profile_max)
    
    if overlap_min > overlap_max:
        return 0  # No overlap
    
    # Overlap ratio
    job_range = job_max - job_min if job_max > job_min else 1
    profile_range = profile_max - profile_min if profile_max > profile_min else 1
    overlap_range = overlap_max - overlap_min
    
    # Score based on overlap percentage
    overlap_ratio = overlap_range / max(job_range, profile_range)
    score = round(overlap_ratio * 100)
    
    return max(0, min(100, score))


def calculate_final_score(
    input_data: ScoringInput,
    config: ScoringConfig,
) -> ScoringOutput:
    """Calculate final evidence-based score from all components."""
    weights = config.weights
    
    # Calculate component scores
    skills_score = calculate_skills_score(input_data, config)
    experience_score = calculate_experience_score(input_data, config)
    requirements_score = calculate_requirements_score(input_data, config)
    location_score = calculate_location_score(input_data, config)
    salary_score = calculate_salary_score(input_data, config)
    
    # Weighted composite
    final_score = round(
        skills_score * weights.skills_weight +
        experience_score * weights.experience_weight +
        requirements_score * weights.requirements_weight +
        location_score * weights.location_weight +
        salary_score * weights.salary_weight
    )
    
    # Determine recommendation
    if final_score >= config.strong_match_threshold:
        recommendation = Recommendation.STRONG_MATCH
    elif final_score >= config.possible_match_threshold:
        recommendation = Recommendation.POSSIBLE_MATCH
    elif final_score >= config.weak_match_threshold:
        recommendation = Recommendation.WEAK_MATCH
    else:
        recommendation = Recommendation.NOT_ENOUGH_INFORMATION
    
    # Determine confidence based on evidence
    evidence_count = len(input_data.evidence) + len(input_data.matching_skills) + len(input_data.matching_experience)
    if evidence_count >= config.min_evidence_for_high_confidence and final_score >= 50:
        confidence = Confidence.HIGH
    elif evidence_count >= 1:
        confidence = Confidence.MEDIUM
    else:
        confidence = Confidence.LOW
    
    # Build explanation
    explanation_parts = []
    if skills_score >= 70:
        explanation_parts.append("Strong skills alignment")
    elif skills_score >= 40:
        explanation_parts.append("Partial skills match")
    else:
        explanation_parts.append("Limited skills match")
    
    if experience_score >= 70:
        explanation_parts.append("Experience well-aligned")
    elif experience_score >= 40:
        explanation_parts.append("Experience partially matches")
    
    if location_score >= 70:
        explanation_parts.append("Location matches preferences")
    elif location_score <= 30:
        explanation_parts.append("Location may not match preferences")
    
    explanation = ". ".join(explanation_parts) + "."
    
    # Build evidence
    evidence = []
    if skills_score > 0:
        evidence.append({"claim": f"Skills score: {skills_score}/100", "source_excerpt": f"{len(input_data.matching_skills)} matching skills"})
    if experience_score > 0:
        evidence.append({"claim": f"Experience score: {experience_score}/100", "source_excerpt": f"{len(input_data.matching_experience)} matching experiences"})
    if location_score > 50:
        evidence.append({"claim": "Location compatible", "source_excerpt": input_data.job_location or "N/A"})
    if salary_score > 50:
        evidence.append({"claim": "Salary compatible", "source_excerpt": f"Job: {input_data.job_salary_min}-{input_data.job_salary_max}, Profile: {input_data.profile_salary_min}-{input_data.profile_salary_max}"})
    
    return ScoringOutput(
        model_used="evidence-based",
        score=final_score,
        recommendation=recommendation,
        confidence=confidence,
        skills_score=skills_score,
        experience_score=experience_score,
        requirements_score=requirements_score,
        location_score=location_score,
        salary_score=salary_score,
        explanation=explanation,
        evidence=evidence,
        status=AnalysisStatus.SUCCESS,
    )