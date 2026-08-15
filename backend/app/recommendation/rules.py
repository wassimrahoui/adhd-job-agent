from __future__ import annotations

from typing import Optional
from dataclasses import dataclass, field

from app.schemas.recommendation import (
    RecommendationInput,
    RecommendationCategory,
    RecommendationPriority,
    RecommendationReason,
    RecommendationConfig,
)


@dataclass
class RuleResult:
    """Result of a rule evaluation."""
    category: Optional[RecommendationCategory] = None
    priority: Optional[RecommendationPriority] = None
    reasons: list[RecommendationReason] = field(default_factory=list)


class RecommendationRules:
    """Rule engine for recommendation decisions."""
    
    def __init__(self, config: Optional[RecommendationConfig] = None):
        self.config = config or RecommendationConfig()
    
    def evaluate_category(self, score: int) -> RecommendationCategory:
        """Determine category from score using thresholds."""
        if score >= self.config.strong_match_threshold:
            return RecommendationCategory.STRONG_MATCH
        elif score >= self.config.possible_match_threshold:
            return RecommendationCategory.POSSIBLE_MATCH
        elif score >= self.config.weak_match_threshold:
            return RecommendationCategory.WEAK_MATCH
        else:
            return RecommendationCategory.NOT_ENOUGH_INFORMATION
    
    def evaluate_priority(
        self, 
        category: RecommendationCategory, 
        evidence_count: int
    ) -> RecommendationPriority:
        """Determine priority based on category and evidence."""
        if category == RecommendationCategory.STRONG_MATCH:
            return (
                RecommendationPriority.HIGH 
                if evidence_count >= self.config.min_evidence_for_high_priority 
                else RecommendationPriority.MEDIUM
            )
        elif category == RecommendationCategory.POSSIBLE_MATCH:
            return RecommendationPriority.MEDIUM if evidence_count >= 2 else RecommendationPriority.LOW
        elif category == RecommendationCategory.WEAK_MATCH:
            return RecommendationPriority.LOW
        else:
            return RecommendationPriority.SKIP
    
    def evaluate_reasons(self, input_data: RecommendationInput) -> list[RecommendationReason]:
        """Determine reasons based on score components."""
        positive_reasons = []
        negative_reasons = []
        
        # Positive reasons (threshold >= 70)
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
        
        # Negative reasons (threshold < 40) - prioritized
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
        
        return all_reasons
    
    def evaluate_all(self, input_data: RecommendationInput) -> RuleResult:
        """Run all rules and return combined result."""
        category = self.evaluate_category(input_data.score)
        priority = self.evaluate_priority(category, len(input_data.evidence))
        reasons = self.evaluate_reasons(input_data)
        
        return RuleResult(
            category=category,
            priority=priority,
            reasons=reasons,
        )