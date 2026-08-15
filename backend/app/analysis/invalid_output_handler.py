from __future__ import annotations

import asyncio
from typing import Optional

from app.analysis.ollama_client import OllamaClient, OllamaResponseError
from app.analysis.request_builder import build_analysis_request
from app.analysis.response_parser import parse_analysis_response_safe, SchemaValidationError
from app.schemas.analysis import AnalysisInput, AnalysisOutput, AnalysisStatus


class InvalidOutputHandler:
    """Handle invalid LLM outputs with retries and fallback."""

    def __init__(
        self,
        client: OllamaClient,
        max_retries: int = 2,
        retry_delay: float = 1.0,
    ):
        self.client = client
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def analyze_with_retry(
        self,
        input_data: AnalysisInput,
        model_name: str,
    ) -> AnalysisOutput:
        """Analyze job with retry logic for invalid outputs."""
        request = build_analysis_request(input_data, model_name)

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                response_text = await self.client.generate(
                    prompt=request["prompt"],
                    system=request.get("system"),
                    temperature=request["options"].get("temperature", 0.1),
                    top_p=request["options"].get("top_p", 0.9),
                )

                result, error = parse_analysis_response_safe(response_text, model_name)
                if result is not None:
                    return result

                last_error = error
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))

            except OllamaResponseError as e:
                last_error = str(e)
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))

        # All retries exhausted - return failed analysis
        return AnalysisOutput(
            model_used=model_name,
            status=AnalysisStatus.FAILED,
            explanation=f"Failed after {self.max_retries + 1} attempts. Last error: {last_error}",
        )


async def analyze_job_with_retry(
    client: OllamaClient,
    input_data: AnalysisInput,
    model_name: str,
    max_retries: int = 2,
) -> AnalysisOutput:
    """Convenience function for analysis with retry."""
    handler = InvalidOutputHandler(client, max_retries=max_retries)
    return await handler.analyze_with_retry(input_data, model_name)