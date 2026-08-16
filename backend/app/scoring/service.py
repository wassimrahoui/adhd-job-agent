from __future__ import annotations

from typing import Optional
from datetime import datetime

from app.scoring.ollama_client import OllamaScoringClient, get_ollama_scoring_client
from app.scoring.final_score import calculate_final_score
from app.schemas.scoring import ScoringInput, ScoringOutput, ScoringConfig
from app.repositories.job import JobRepository
from app.core.config import settings


class ScoringService:
    """Service for running job scoring via local Ollama LLM with evidence-based fallback."""

    def __init__(
        self,
        client: Optional[OllamaScoringClient] = None,
        job_repo: Optional[JobRepository] = None,
    ):
        self._client = client
        self._job_repo = job_repo
        self._model = settings.ollama_model
        self._config = ScoringConfig()

    async def _get_client(self) -> OllamaScoringClient:
        if self._client is None:
            self._client = await get_ollama_scoring_client()
        return self._client

    def set_config(self, config: ScoringConfig) -> None:
        """Set custom scoring configuration."""
        self._config = config

    def set_job_repository(self, job_repo: JobRepository) -> None:
        """Set the job repository for persistence."""
        self._job_repo = job_repo

    async def score_job(self, input_data: ScoringInput) -> ScoringOutput:
        """Score a job using local Ollama LLM with evidence-based fallback."""
        client = await self._get_client()
        
        # Try local Ollama scoring first
        try:
            prompt = build_scoring_prompt(input_data, self._config)
            return await client.score_job(input_data, prompt)
        except Exception as e:
            # Fall back to evidence-based scoring
            print(f"Ollama scoring failed, falling back to evidence-based: {e}")
        
        # Evidence-based fallback
        return calculate_final_score(input_data, self._config)

    async def score_and_persist(self, input_data: ScoringInput) -> ScoringOutput:
        """Score a job and persist the result to database."""
        result = await self.score_job(input_data)
        
        if self._job_repo is not None:
            scoring_data = {
                "score": result.score,
                "recommendation": result.recommendation.value if result.recommendation else None,
                "confidence": result.confidence.value if result.confidence else None,
                "skills_score": result.skills_score,
                "experience_score": result.experience_score,
                "requirements_score": result.requirements_score,
                "location_score": result.location_score,
                "salary_score": result.salary_score,
                "scored_at": datetime.utcnow(),
                "scoring_model": result.model_used,
            }
            if input_data.job_id is not None:
                await self._job_repo.update_scoring(input_data.job_id, scoring_data)
        
        return result

    async def score_job_evidence_based(self, input_data: ScoringInput) -> ScoringOutput:
        """Score a job using only evidence-based scoring (no LLM)."""
        return calculate_final_score(input_data, self._config)

    async def health_check(self) -> bool:
        """Check if local Ollama is available."""
        client = await self._get_client()
        return await client.health_check()

    async def close(self) -> None:
        """Close the Ollama client."""
        if self._client:
            await self._client.close()
            self._client = None


async def get_scoring_service() -> ScoringService:
    """Dependency injection for ScoringService."""
    return ScoringService()


# Import here to avoid circular import
from app.scoring.prompt_builder import build_scoring_prompt