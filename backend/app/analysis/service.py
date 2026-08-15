from __future__ import annotations

from typing import Optional

from app.analysis.ollama_client import OllamaClient, get_ollama_client
from app.analysis.invalid_output_handler import analyze_job_with_retry
from app.schemas.analysis import (
    AnalysisInput,
    AnalysisOutput,
    AnalysisStatus as SchemaAnalysisStatus,
    Recommendation as SchemaRecommendation,
    Confidence as SchemaConfidence,
    SkillMatchItem as SchemaSkillMatchItem,
    ExperienceMatchItem as SchemaExperienceMatchItem,
    RequirementGapItem as SchemaRequirementGapItem,
    UnknownRequirementItem as SchemaUnknownRequirementItem,
    EvidenceItem as SchemaEvidenceItem,
)
from app.models.analysis import (
    AIAnalysisCreate,
    AnalysisStatus as ModelAnalysisStatus,
    Recommendation as ModelRecommendation,
    Confidence as ModelConfidence,
    SkillMatchItem as ModelSkillMatchItem,
    ExperienceMatchItem as ModelExperienceMatchItem,
    RequirementGapItem as ModelRequirementGapItem,
    UnknownRequirementItem as ModelUnknownRequirementItem,
    EvidenceItem as ModelEvidenceItem,
)
from app.repositories.analysis import AIAnalysisRepository
from app.core.config import settings


class AnalysisService:
    """Service for running AI job analysis via Ollama and persisting results."""

    def __init__(
        self,
        client: Optional[OllamaClient] = None,
        repo: Optional[AIAnalysisRepository] = None,
    ):
        self._client = client
        self._repo = repo
        self._model = settings.ollama_model

    async def _get_client(self) -> OllamaClient:
        if self._client is None:
            self._client = await get_ollama_client()
        return self._client

    def set_repository(self, repo: AIAnalysisRepository) -> None:
        """Set the repository for persistence."""
        self._repo = repo

    async def analyze_job(self, input_data: AnalysisInput) -> AnalysisOutput:
        """Analyze a job using the configured Ollama model."""
        client = await self._get_client()
        return await analyze_job_with_retry(
            client=client,
            input_data=input_data,
            model_name=self._model,
            max_retries=2,
        )

    def _convert_recommendation(self, rec: Optional[SchemaRecommendation]) -> Optional[ModelRecommendation]:
        if rec is None:
            return None
        return ModelRecommendation(rec.value)

    def _convert_confidence(self, conf: Optional[SchemaConfidence]) -> Optional[ModelConfidence]:
        if conf is None:
            return None
        return ModelConfidence(conf.value)

    def _convert_status(self, status: Optional[SchemaAnalysisStatus]) -> ModelAnalysisStatus:
        if status is None:
            return ModelAnalysisStatus.AI_UNAVAILABLE
        return ModelAnalysisStatus(status.value)

    def _convert_skill_matches(self, items: list[SchemaSkillMatchItem]) -> list[ModelSkillMatchItem]:
        return [ModelSkillMatchItem(claim=item.claim, source_excerpt=item.source_excerpt) for item in items]

    def _convert_experience_matches(self, items: list[SchemaExperienceMatchItem]) -> list[ModelExperienceMatchItem]:
        return [ModelExperienceMatchItem(claim=item.claim, source_excerpt=item.source_excerpt) for item in items]

    def _convert_missing_requirements(self, items: list[SchemaRequirementGapItem]) -> list[ModelRequirementGapItem]:
        return [ModelRequirementGapItem(claim=item.claim, source_excerpt=item.source_excerpt) for item in items]

    def _convert_unknown_requirements(self, items: list[SchemaUnknownRequirementItem]) -> list[ModelUnknownRequirementItem]:
        return [ModelUnknownRequirementItem(claim=item.claim, source_excerpt=item.source_excerpt) for item in items]

    def _convert_evidence(self, items: list[SchemaEvidenceItem]) -> list[ModelEvidenceItem]:
        return [ModelEvidenceItem(claim=item.claim, source_excerpt=item.source_excerpt) for item in items]

    async def analyze_and_persist(self, input_data: AnalysisInput) -> AnalysisOutput:
        """Analyze a job and persist the result to database."""
        result = await self.analyze_job(input_data)

        if self._repo is not None:
            create_data = AIAnalysisCreate(
                job_id=input_data.job.id,
                model_used=result.model_used,
                score=result.score,
                recommendation=self._convert_recommendation(result.recommendation),
                confidence=self._convert_confidence(result.confidence),
                matching_skills=self._convert_skill_matches(result.matching_skills),
                matching_experience=self._convert_experience_matches(result.matching_experience),
                missing_requirements=self._convert_missing_requirements(result.missing_requirements),
                unknown_requirements=self._convert_unknown_requirements(result.unknown_requirements),
                explanation=result.explanation,
                evidence=self._convert_evidence(result.evidence),
                status=self._convert_status(result.status),
            )
            await self._repo.create_analysis(create_data)

        return result

    async def health_check(self) -> bool:
        """Check if Ollama is available."""
        client = await self._get_client()
        return await client.health_check()

    async def close(self) -> None:
        """Close the Ollama client."""
        if self._client:
            await self._client.close()
            self._client = None


async def get_analysis_service() -> AnalysisService:
    """Dependency injection for AnalysisService."""
    return AnalysisService()