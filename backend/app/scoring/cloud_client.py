from __future__ import annotations

import json
import asyncio
from typing import Optional
import httpx
from pydantic import BaseModel

from app.schemas.scoring import ScoringOutput, ScoringInput
from app.core.config import settings


class CloudScoringError(Exception):
    """Base exception for cloud scoring client errors."""
    def __init__(self, message: str, error_code: str = "CLOUD_SCORING_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class CloudConnectionError(CloudScoringError):
    def __init__(self, message: str = "Failed to connect to cloud scoring API"):
        super().__init__(message, "CLOUD_CONNECTION_ERROR")


class CloudTimeoutError(CloudScoringError):
    def __init__(self, message: str = "Cloud scoring request timed out"):
        super().__init__(message, "CLOUD_TIMEOUT")


class CloudResponseError(CloudScoringError):
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message, "CLOUD_RESPONSE_ERROR")


class CloudScoringClient:
    """Async client for cloud LLM scoring API (e.g., OpenAI, Anthropic)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
    ):
        self.api_key = api_key or settings.cloud_scoring_api_key
        self.base_url = base_url or settings.cloud_scoring_base_url
        self.model = model or settings.cloud_scoring_model
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or getattr(self._client, "is_closed", False):
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            headers["Content-Type"] = "application/json"
            
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers=headers,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not getattr(self._client, "is_closed", False):
            await self._client.aclose()
            self._client = None

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate completion from cloud LLM."""
        client = await self._get_client()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            response = await client.post("/chat/completions", json=payload)
        except httpx.ConnectError as e:
            raise CloudConnectionError(f"Cannot connect to cloud API at {self.base_url}: {e}")
        except httpx.TimeoutException as e:
            raise CloudTimeoutError(f"Request timed out after {self.timeout}s: {e}")

        if response.status_code != 200:
            raise CloudResponseError(
                f"Cloud API returned {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            raise CloudResponseError(f"Invalid response format: {e}")

    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[ScoringOutput],
        system: Optional[str] = None,
        temperature: float = 0.1,
        max_retries: int = 2,
    ) -> ScoringOutput:
        """Generate structured output using JSON schema."""
        schema = response_schema.model_json_schema()

        structured_prompt = f"""{prompt}

IMPORTANT: Respond ONLY with valid JSON matching this schema:
{json.dumps(schema, indent=2)}

Do not include any explanation, markdown, or text outside the JSON object."""

        last_error = None
        for attempt in range(max_retries + 1):
            response_text = ""
            try:
                response_text = await self.generate(
                    structured_prompt,
                    system=system,
                    temperature=temperature,
                )
                parsed = response_schema.model_validate_json(response_text)
                return parsed
            except json.JSONDecodeError as e:
                last_error = f"JSON decode error: {e}. Response: {response_text[:500]}"
            except Exception as e:
                last_error = f"Validation error: {e}. Response: {response_text[:500]}"

        raise CloudResponseError(
            f"Failed to get valid structured response after {max_retries + 1} attempts. Last error: {last_error}"
        )

    async def score_job(
        self,
        input_data: ScoringInput,
        prompt: str,
    ) -> ScoringOutput:
        """Score a job using the configured cloud model."""
        return await self.generate_structured(
            prompt=prompt,
            response_schema=ScoringOutput,
            system="You are an expert job match scorer. Output only valid JSON.",
        )

    async def health_check(self) -> bool:
        """Check if cloud API is available."""
        try:
            client = await self._get_client()
            response = await client.get("/models")
            return response.status_code == 200
        except Exception:
            return False


async def get_cloud_scoring_client() -> CloudScoringClient:
    """Dependency injection for CloudScoringClient."""
    return CloudScoringClient()