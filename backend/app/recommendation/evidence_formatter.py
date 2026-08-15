from __future__ import annotations

from typing import Any
from app.schemas.recommendation import RecommendationInput


class EvidenceFormatter:
    """Format evidence for recommendation output."""

    def __init__(self):
        pass

    def format_evidence(self, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format evidence items for output."""
        formatted = []
        for item in evidence:
            if isinstance(item, dict):
                formatted_item = {
                    "type": item.get("type", "unknown"),
                    "value": item.get("value", ""),
                    "source": item.get("source", "analysis"),
                    "confidence": item.get("confidence", "medium"),
                }
                formatted.append(formatted_item)
        return formatted

    def extract_skills_from_evidence(self, evidence: list[dict[str, Any]]) -> list[str]:
        """Extract skill names from evidence."""
        skills = []
        for item in evidence:
            if item.get("type") == "skill" and "value" in item:
                skills.append(str(item["value"]))
        return skills

    def extract_requirements_from_evidence(self, evidence: list[dict[str, Any]]) -> list[str]:
        """Extract requirements from evidence."""
        requirements = []
        for item in evidence:
            if item.get("type") == "requirement" and "value" in item:
                requirements.append(str(item["value"]))
        return requirements

    def extract_experience_from_evidence(self, evidence: list[dict[str, Any]]) -> list[str]:
        """Extract experience items from evidence."""
        experience = []
        for item in evidence:
            if item.get("type") == "experience" and "value" in item:
                experience.append(str(item["value"]))
        return experience

    def summarize_evidence(self, evidence: list[dict[str, Any]]) -> dict[str, int]:
        """Summarize evidence by type."""
        summary = {}
        for item in evidence:
            if isinstance(item, dict) and "type" in item:
                t = item["type"]
                summary[t] = summary.get(t, 0) + 1
        return summary

    def filter_high_confidence_evidence(
        self, 
        evidence: list[dict[str, Any]], 
        min_confidence: str = "high"
    ) -> list[dict[str, Any]]:
        """Filter evidence by minimum confidence level."""
        confidence_order = {"low": 0, "medium": 1, "high": 2}
        min_level = confidence_order.get(min_confidence, 1)
        
        filtered = []
        for item in evidence:
            if isinstance(item, dict):
                item_confidence = confidence_order.get(item.get("confidence", "medium"), 1)
                if item_confidence >= min_level:
                    filtered.append(item)
        return filtered