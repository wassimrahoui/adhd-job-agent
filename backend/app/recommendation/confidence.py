from __future__ import annotations

from enum import Enum
from typing import Optional

from app.schemas.recommendation import RecommendationInput


class ConfidenceLevel(str, Enum):
    """Confidence levels for recommendations."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfidenceHandler:
    """Handle confidence levels for recommendations."""
    
    # Thresholds for determining confidence from score
    HIGH_THRESHOLD = 80
    MEDIUM_THRESHOLD = 50
    LOW_THRESHOLD = 0
    
    # Evidence count thresholds
    HIGH_EVIDENCE_THRESHOLD = 4
    MEDIUM_EVIDENCE_THRESHOLD = 2
    
    def __init__(
        self,
        high_threshold: int = HIGH_THRESHOLD,
        medium_threshold: int = MEDIUM_THRESHOLD,
        low_threshold: int = LOW_THRESHOLD,
        high_evidence_threshold: int = HIGH_EVIDENCE_THRESHOLD,
        medium_evidence_threshold: int = MEDIUM_EVIDENCE_THRESHOLD,
    ):
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold
        self.low_threshold = low_threshold
        self.high_evidence_threshold = high_evidence_threshold
        self.medium_evidence_threshold = medium_evidence_threshold
    
    def determine_confidence_from_score(self, score: int) -> ConfidenceLevel:
        """Determine confidence level from overall score."""
        if score >= self.high_threshold:
            return ConfidenceLevel.HIGH
        elif score >= self.medium_threshold:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def determine_confidence_from_evidence(self, evidence_count: int) -> ConfidenceLevel:
        """Determine confidence level from evidence count."""
        if evidence_count >= self.high_evidence_threshold:
            return ConfidenceLevel.HIGH
        elif evidence_count >= self.medium_evidence_threshold:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def determine_confidence(
        self, 
        input_data: RecommendationInput,
        use_score: bool = True,
        use_evidence: bool = True,
    ) -> ConfidenceLevel:
        """Determine overall confidence from multiple factors."""
        confidence_levels = []
        
        if use_score:
            confidence_levels.append(self.determine_confidence_from_score(input_data.score))
        
        if use_evidence:
            confidence_levels.append(self.determine_confidence_from_evidence(len(input_data.evidence)))
        
        # Also consider the confidence from scoring if available
        if input_data.confidence:
            try:
                confidence_levels.append(ConfidenceLevel(input_data.confidence.lower()))
            except ValueError:
                pass
        
        if not confidence_levels:
            return ConfidenceLevel.LOW
        
        # Return the most common confidence level, or highest if tie
        from collections import Counter
        counts = Counter(confidence_levels)
        max_count = max(counts.values())
        most_common = [level for level, count in counts.items() if count == max_count]
        
        # Prefer higher confidence in case of tie
        priority = {
            ConfidenceLevel.HIGH: 3,
            ConfidenceLevel.MEDIUM: 2,
            ConfidenceLevel.LOW: 1,
        }
        
        return max(most_common, key=lambda c: priority[c])
    
    def adjust_confidence_for_missing_data(
        self, 
        confidence: ConfidenceLevel, 
        missing_critical_fields: list[str]
    ) -> ConfidenceLevel:
        """Adjust confidence down if critical data is missing."""
        if not missing_critical_fields:
            return confidence
        
        # Each missing critical field reduces confidence by one level
        priority = {
            ConfidenceLevel.HIGH: 3,
            ConfidenceLevel.MEDIUM: 2,
            ConfidenceLevel.LOW: 1,
        }
        
        current_priority = priority[confidence]
        reduction = min(len(missing_critical_fields), current_priority - 1)
        new_priority = max(1, current_priority - reduction)
        
        # Convert back to enum
        reverse_priority = {v: k for k, v in priority.items()}
        return reverse_priority[new_priority]