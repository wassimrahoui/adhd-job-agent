from __future__ import annotations

from app.schemas.recommendation import (
    RecommendationInput,
    RecommendationCategory,
    RecommendationReason,
)


class ExplanationGenerator:
    """Generate human-readable explanations for recommendations."""

    def __init__(self):
        self.reason_details = {
            RecommendationReason.SKILLS_MATCH: "Your skills align well with the job requirements.",
            RecommendationReason.EXPERIENCE_MATCH: "Your experience level matches the position.",
            RecommendationReason.LOCATION_MATCH: "The job location matches your preferences.",
            RecommendationReason.SALARY_MATCH: "The salary range meets your expectations.",
            RecommendationReason.REQUIREMENTS_COVERED: "You meet most of the job requirements.",
            RecommendationReason.MISSING_CRITICAL_SKILLS: "You're missing some critical skills for this role.",
            RecommendationReason.EXPERIENCE_GAP: "Your experience level doesn't quite match the position.",
            RecommendationReason.LOCATION_MISMATCH: "The job location doesn't match your preferences.",
            RecommendationReason.SALARY_BELOW_EXPECTATIONS: "The salary may not meet your expectations.",
            RecommendationReason.INSUFFICIENT_INFORMATION: "There isn't enough information to assess fit.",
        }

    def generate_category_summary(self, category: RecommendationCategory) -> str:
        """Generate category summary text."""
        summaries = {
            RecommendationCategory.STRONG_MATCH: "This job is a strong match for your profile.",
            RecommendationCategory.POSSIBLE_MATCH: "This job is a possible match with some alignment.",
            RecommendationCategory.WEAK_MATCH: "This job has significant gaps.",
            RecommendationCategory.NOT_ENOUGH_INFORMATION: "There isn't enough information to determine fit.",
        }
        return summaries.get(category, "Unable to determine fit.")

    def generate_reason_details(self, reasons: list[RecommendationReason]) -> list[str]:
        """Generate detailed explanations for reasons."""
        return [self.reason_details.get(r, "") for r in reasons if r in self.reason_details]

    def build_explanation(
        self,
        input_data: RecommendationInput,
        category: RecommendationCategory,
        primary_reason: RecommendationReason,
        secondary_reasons: list[RecommendationReason],
    ) -> str:
        """Build complete human-readable explanation."""
        parts = []
        
        # Category summary
        parts.append(self.generate_category_summary(category))
        
        # Primary reason
        if primary_reason in self.reason_details:
            parts.append(self.reason_details[primary_reason])
        
        # Secondary reasons
        for reason in secondary_reasons:
            if reason in self.reason_details:
                parts.append(self.reason_details[reason])
        
        return " ".join(parts)