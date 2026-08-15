from __future__ import annotations

from typing import Optional

from app.schemas.recommendation import (
    RecommendationInput,
    RecommendationOutput,
    RecommendationCategory,
    RecommendationPriority,
    RecommendationReason,
    RecommendationConfig,
)
from app.recommendation.explanation import ExplanationGenerator
from app.recommendation.evidence_formatter import EvidenceFormatter


class RecommendationEvaluator:
    """Evaluate scoring output to produce actionable recommendations."""

    def __init__(self, config: Optional[RecommendationConfig] = None):
        self.config = config or RecommendationConfig()
        self.explanation_generator = ExplanationGenerator()
        self.evidence_formatter = EvidenceFormatter()

    def evaluate(self, input_data: RecommendationInput) -> RecommendationOutput:
        """Evaluate scoring input and produce recommendation."""
        
        # Determine category from score
        category = self._determine_category(input_data.score)
        
        # Determine priority
        priority = self._determine_priority(input_data, category)
        
        # Determine primary and secondary reasons
        primary_reason, secondary_reasons = self._determine_reasons(input_data)
        
        # Build explanation using ExplanationGenerator
        explanation = self.explanation_generator.build_explanation(
            input_data, category, primary_reason, secondary_reasons
        )
        
        # Identify missing critical skills
        missing_critical_skills = self._identify_missing_critical_skills(input_data)
        
        # Identify strengths
        strengths = self._identify_strengths(input_data)
        
        # Identify concerns
        concerns = self._identify_concerns(input_data)
        
        # Generate action items
        action_items = self._generate_action_items(input_data, category.value, missing_critical_skills)
        
        return RecommendationOutput(
            category=category,
            priority=priority,
            primary_reason=primary_reason,
            secondary_reasons=secondary_reasons,
            explanation=explanation,
            confidence=input_data.confidence,
            score=input_data.score,
            missing_critical_skills=missing_critical_skills,
            strengths=strengths,
            concerns=concerns,
            action_items=action_items,
            status="success",
        )

    def _determine_category(self, score: int) -> RecommendationCategory:
        """Determine recommendation category from score."""
        if score >= self.config.strong_match_threshold:
            return RecommendationCategory.STRONG_MATCH
        elif score >= self.config.possible_match_threshold:
            return RecommendationCategory.POSSIBLE_MATCH
        elif score >= self.config.weak_match_threshold:
            return RecommendationCategory.WEAK_MATCH
        else:
            return RecommendationCategory.NOT_ENOUGH_INFORMATION

    def _determine_priority(self, input_data: RecommendationInput, category: RecommendationCategory) -> RecommendationPriority:
        """Determine priority based on category and evidence."""
        evidence_count = len(input_data.evidence)
        
        if category == RecommendationCategory.STRONG_MATCH:
            return RecommendationPriority.HIGH if evidence_count >= self.config.min_evidence_for_high_priority else RecommendationPriority.MEDIUM
        elif category == RecommendationCategory.POSSIBLE_MATCH:
            return RecommendationPriority.MEDIUM if evidence_count >= 2 else RecommendationPriority.LOW
        elif category == RecommendationCategory.WEAK_MATCH:
            return RecommendationPriority.LOW
        else:
            return RecommendationPriority.SKIP

    def _determine_reasons(self, input_data: RecommendationInput) -> tuple[RecommendationReason, list[RecommendationReason]]:
        """Determine primary and secondary reasons for recommendation."""
        positive_reasons = []
        negative_reasons = []
        
        # Check each score component - positive reasons
        if input_data.skills_score >= 70:
            positive_reasons.append(RecommendationReason.SKILLS_MATCH)
        if input_data.experience_score >= 70:
            positive_reasons.append(RecommendationReason.EXPERIENCE_MATCH)
        if input_data.location_score >= 70:
            positive_reasons.append(RecommendationReason.LOCATION_MATCH)
        if input_data.salary_score >= 70:
            positive_reasons.append(RecommendationReason.SALARY_MATCH)
        if input_data.requirements_score >= 70:
            positive_reasons.append(RecommendationReason.REQUIREMENTS_COVERED)
        
        # Add negative reasons (prioritized)
        if input_data.skills_score < 40:
            negative_reasons.append(RecommendationReason.MISSING_CRITICAL_SKILLS)
        if input_data.experience_score < 40:
            negative_reasons.append(RecommendationReason.EXPERIENCE_GAP)
        if input_data.location_score < 40:
            negative_reasons.append(RecommendationReason.LOCATION_MISMATCH)
        if input_data.salary_score < 40:
            negative_reasons.append(RecommendationReason.SALARY_BELOW_EXPECTATIONS)
        
        # Prioritize negative reasons
        all_reasons = negative_reasons + positive_reasons
        
        if not all_reasons:
            all_reasons.append(RecommendationReason.INSUFFICIENT_INFORMATION)
        
        primary = all_reasons[0]
        secondary = all_reasons[1:] if len(all_reasons) > 1 else []
        
        return primary, secondary

    def _identify_missing_critical_skills(self, input_data: RecommendationInput) -> list[str]:
        """Identify missing critical skills from evidence."""
        missing = []
        # This would ideally come from the analysis evidence
        # For now, check if skills_score is low
        if input_data.skills_score < 50:
            # Could extract from evidence in a more sophisticated implementation
            pass
        return missing

    def _identify_strengths(self, input_data: RecommendationInput) -> list[str]:
        """Identify candidate strengths from evidence."""
        strengths = []
        if input_data.skills_score >= 70:
            strengths.append("Strong skills alignment")
        if input_data.experience_score >= 70:
            strengths.append("Relevant experience")
        if input_data.location_score >= 70:
            strengths.append("Location match")
        if input_data.salary_score >= 70:
            strengths.append("Salary expectations met")
        if input_data.requirements_score >= 70:
            strengths.append("Requirements well-covered")
        return strengths

    def _identify_concerns(self, input_data: RecommendationInput) -> list[str]:
        """Identify concerns from evidence."""
        concerns = []
        if input_data.skills_score < 40:
            concerns.append("Skills gap identified")
        if input_data.experience_score < 40:
            concerns.append("Experience gap")
        if input_data.location_score < 40:
            concerns.append("Location mismatch")
        if input_data.salary_score < 40:
            concerns.append("Salary below expectations")
        if input_data.requirements_score < 40:
            concerns.append("Many requirements not met")
        return concerns

    def _generate_action_items(self, input_data: RecommendationInput, category: str, missing_skills: list[str]) -> list[str]:
        """Generate actionable next steps."""
        actions = []
        
        if category == "strong_match":
            actions.append("Apply immediately - strong match!")
            actions.append("Prepare tailored cover letter highlighting matching skills")
        elif category == "possible_match":
            actions.append("Consider applying with tailored application")
            actions.append("Address any skill gaps in cover letter")
        elif category == "weak_match":
            actions.append("Consider if gaps can be addressed quickly")
            actions.append("May want to focus on better-matched opportunities")
        else:
            actions.append("Need more information before deciding")
            actions.append("Request clarification on requirements")
        
        if input_data.salary_score < 40:
            actions.append("Negotiate salary if applying")
        
        return actions