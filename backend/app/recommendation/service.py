from __future__ import annotations

from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from app.schemas.scoring import ScoringOutput
from app.schemas.recommendation import (
    RecommendationInput,
    RecommendationOutput,
    RecommendationCategory,
    RecommendationConfig,
)
from app.recommendation.evaluator import RecommendationEvaluator
from app.recommendation.rules import RecommendationRules
from app.recommendation.confidence import ConfidenceHandler, ConfidenceLevel
from app.recommendation.missing_data import MissingDataHandler
from app.repositories.job import JobRepository


@dataclass
class RecommendationServiceConfig:
    """Configuration for recommendation service."""
    recommendation_config: Optional[RecommendationConfig] = None


class RecommendationService:
    """Service for generating recommendations from scoring output."""

    def __init__(self, config: Optional[RecommendationServiceConfig] = None):
        self.config = config or RecommendationServiceConfig()
        self.evaluator = RecommendationEvaluator(config=self.config.recommendation_config)
        self.rules = RecommendationRules()
        self.confidence_handler = ConfidenceHandler()
        self.missing_data_handler = MissingDataHandler()
        self._job_repo: Optional[JobRepository] = None

    def set_job_repository(self, job_repo: JobRepository) -> None:
        """Set the job repository for persistence."""
        self._job_repo = job_repo

    def generate_recommendation(self, scoring_output: ScoringOutput, job_data: dict, profile_data: dict) -> RecommendationOutput:
        """
        Generate a recommendation from scoring output.
        
        Args:
            scoring_output: Output from the scoring service
            job_data: Dictionary with job context (title, company, location, etc.)
            profile_data: Dictionary with profile context (desired_roles, location_preferences, etc.)
            
        Returns:
            RecommendationOutput with category, priority, reasons, explanation, etc.
        """
        # Convert scoring output to recommendation input
        recommendation_input = self._build_recommendation_input(scoring_output, job_data, profile_data)
        
        # Apply rules to get category, priority, reasons
        rule_result = self.rules.evaluate_all(recommendation_input)
        if rule_result.category:
            recommendation_input.recommendation_category = rule_result.category
        # Note: priority and reasons are used internally by evaluator
        
        # Handle missing/unknown data
        recommendation_input = self.missing_data_handler.fill_defaults(recommendation_input)
        missing_critical = self.missing_data_handler.identify_missing_critical_fields(recommendation_input)
        
        # Adjust confidence based on evidence and missing data
        confidence_level = self.confidence_handler.determine_confidence(recommendation_input)
        if missing_critical:
            confidence_level = self.confidence_handler.adjust_confidence_for_missing_data(confidence_level, missing_critical)
        recommendation_input.confidence = confidence_level.value
        
        # Generate recommendation via evaluator
        recommendation_output = self.evaluator.evaluate(recommendation_input)
        
        return recommendation_output

    async def generate_and_persist_recommendation(
        self, 
        scoring_output: ScoringOutput, 
        job_data: dict, 
        profile_data: dict,
        job_id: int
    ) -> RecommendationOutput:
        """
        Generate a recommendation and persist it to the database.
        
        Args:
            scoring_output: Output from the scoring service
            job_data: Dictionary with job context
            profile_data: Dictionary with profile context
            job_id: Database ID of the job
            
        Returns:
            RecommendationOutput with category, priority, reasons, explanation, etc.
        """
        recommendation_output = self.generate_recommendation(scoring_output, job_data, profile_data)
        
        if self._job_repo is not None:
            recommendation_data = {
                "recommendation_category": recommendation_output.category.value,
                "recommendation_priority": recommendation_output.priority.value,
                "recommendation_primary_reason": recommendation_output.primary_reason.value,
                "recommendation_secondary_reasons": [r.value for r in recommendation_output.secondary_reasons],
                "recommendation_explanation": recommendation_output.explanation,
                "recommendation_missing_skills": recommendation_output.missing_critical_skills,
                "recommendation_strengths": recommendation_output.strengths,
                "recommendation_concerns": recommendation_output.concerns,
                "recommendation_action_items": recommendation_output.action_items,
                "recommended_at": datetime.utcnow(),
                "recommendation_model": "recommendation_engine",
            }
            await self._job_repo.update_recommendation(job_id, recommendation_data)
        
        return recommendation_output

    def _build_recommendation_input(
        self, 
        scoring_output: ScoringOutput, 
        job_data: dict, 
        profile_data: dict
    ) -> RecommendationInput:
        """Convert ScoringOutput to RecommendationInput with job/profile context."""
        
        # Determine initial category from score
        category = self._score_to_category(scoring_output.score)
        
        # Convert evidence items to dict
        evidence_list = []
        for e in scoring_output.evidence:
            if hasattr(e, 'model_dump'):
                evidence_list.append(e.model_dump())
            elif isinstance(e, dict):
                evidence_list.append(e)
            else:
                evidence_list.append({"value": str(e)})
        
        # Handle confidence
        confidence_value = scoring_output.confidence
        if hasattr(confidence_value, 'value'):
            confidence_value = confidence_value.value
        elif confidence_value is None:
            confidence_value = "medium"
        
        # Handle status
        status_value = scoring_output.status
        if hasattr(status_value, 'value'):
            status_value = status_value.value
        elif status_value is None:
            status_value = "success"
        
        return RecommendationInput(
            # From scoring
            score=scoring_output.score,
            recommendation_category=category,
            confidence=confidence_value,
            skills_score=scoring_output.skills_score,
            experience_score=scoring_output.experience_score,
            requirements_score=scoring_output.requirements_score,
            location_score=scoring_output.location_score,
            salary_score=scoring_output.salary_score,
            explanation=scoring_output.explanation,
            evidence=evidence_list,
            status=status_value,
            
            # Job context
            job_title=job_data.get("title", ""),
            job_company=job_data.get("company"),
            job_location=job_data.get("location"),
            job_skills=job_data.get("skills", []),
            job_salary_min=job_data.get("salary_min"),
            job_salary_max=job_data.get("salary_max"),
            
            # Profile context
            profile_desired_roles=profile_data.get("desired_roles", []),
            profile_location_preferences=profile_data.get("location_preferences", []),
            profile_salary_min=profile_data.get("salary_min"),
            profile_salary_max=profile_data.get("salary_max"),
            profile_skills=profile_data.get("skills", []),
            profile_experience_level=profile_data.get("experience_level"),
        )

    def _score_to_category(self, score: int) -> RecommendationCategory:
        """Convert numeric score to recommendation category."""
        config = self.config.recommendation_config or RecommendationConfig()
        if score >= config.strong_match_threshold:
            return RecommendationCategory.STRONG_MATCH
        elif score >= config.possible_match_threshold:
            return RecommendationCategory.POSSIBLE_MATCH
        elif score >= config.weak_match_threshold:
            return RecommendationCategory.WEAK_MATCH
        else:
            return RecommendationCategory.NOT_ENOUGH_INFORMATION


async def get_recommendation_service() -> RecommendationService:
    """Dependency injection for RecommendationService."""
    return RecommendationService()