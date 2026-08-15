from __future__ import annotations

from typing import Optional
from pydantic import ValidationError

from app.schemas.scoring import ScoringOutput, ScoringConfig, Recommendation, Confidence, AnalysisStatus


class ScoringValidationError(Exception):
    """Exception for scoring validation errors."""
    def __init__(self, message: str, error_code: str = "SCORING_VALIDATION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


def validate_scoring_output(output: ScoringOutput, config: ScoringConfig) -> ScoringOutput:
    """Validate and normalize scoring output."""
    # Ensure recommendation matches score thresholds
    if output.score >= config.strong_match_threshold:
        expected_rec = Recommendation.STRONG_MATCH
    elif output.score >= config.possible_match_threshold:
        expected_rec = Recommendation.POSSIBLE_MATCH
    elif output.score >= config.weak_match_threshold:
        expected_rec = Recommendation.WEAK_MATCH
    else:
        expected_rec = Recommendation.NOT_ENOUGH_INFORMATION

    if output.recommendation != expected_rec:
        output.recommendation = expected_rec

    # Ensure confidence is reasonable based on evidence
    evidence_count = len(output.evidence) if output.evidence else 0
    if output.confidence == Confidence.HIGH and evidence_count < config.min_evidence_for_high_confidence:
        output.confidence = Confidence.MEDIUM
    elif output.confidence == Confidence.LOW and evidence_count >= config.min_evidence_for_high_confidence:
        output.confidence = Confidence.MEDIUM

    # Validate component scores are within range
    for field in ["skills_score", "experience_score", "requirements_score", "location_score", "salary_score"]:
        value = getattr(output, field)
        if value < 0 or value > 100:
            raise ScoringValidationError(f"{field} must be 0-100, got {value}")

    # Validate weighted composite matches (approximately)
    weights = config.weights
    expected_score = round(
        output.skills_score * weights.skills_weight +
        output.experience_score * weights.experience_weight +
        output.requirements_score * weights.requirements_weight +
        output.location_score * weights.location_weight +
        output.salary_score * weights.salary_weight
    )
    
    # Allow small rounding differences
    if abs(output.score - expected_score) > 5:
        # Adjust score to match weighted composite
        output.score = expected_score

    return output


def validate_scoring_output_safe(output: ScoringOutput, config: ScoringConfig) -> tuple[Optional[ScoringOutput], Optional[str]]:
    """Safely validate scoring output, returning (result, error_message)."""
    try:
        return validate_scoring_output(output, config), None
    except ScoringValidationError as e:
        return None, e.message
    except Exception as e:
        return None, f"Unexpected validation error: {e}"


def create_fallback_scoring(
    model_used: str,
    error_message: str,
    config: ScoringConfig,
) -> ScoringOutput:
    """Create a fallback scoring output when validation fails."""
    return ScoringOutput(
        model_used=model_used,
        score=0,
        recommendation=Recommendation.NOT_ENOUGH_INFORMATION,
        confidence=Confidence.LOW,
        skills_score=0,
        experience_score=0,
        requirements_score=0,
        location_score=0,
        salary_score=0,
        explanation=f"Scoring failed: {error_message}",
        evidence=[],
        status=AnalysisStatus.FAILED,
    )