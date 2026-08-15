from __future__ import annotations

import json
import asyncio
from typing import Optional
import httpx
from pydantic import BaseModel, Field

from app.core.config import settings
from app.schemas.analysis import AnalysisOutput, AnalysisInput


class OllamaClientError(Exception):
    """Base exception for Ollama client errors."""
    def __init__(self, message: str, error_code: str = "OLLAMA_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class OllamaConnectionError(OllamaClientError):
    def __init__(self, message: str = "Failed to connect to Ollama"):
        super().__init__(message, "OLLAMA_CONNECTION_ERROR")


class OllamaTimeoutError(OllamaClientError):
    def __init__(self, message: str = "Ollama request timed out"):
        super().__init__(message, "OLLAMA_TIMEOUT")


class OllamaResponseError(OllamaClientError):
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message, "OLLAMA_RESPONSE_ERROR")


class OllamaClient:
    """Async client for Ollama API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 120.0,
    ):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or getattr(self._client, "is_closed", False):
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.1,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate completion from Ollama."""
        client = await self._get_client()

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
            },
        }
        if system:
            payload["system"] = system
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        try:
            response = await client.post("/api/generate", json=payload)
        except httpx.ConnectError as e:
            raise OllamaConnectionError(f"Cannot connect to Ollama at {self.base_url}: {e}")
        except httpx.TimeoutException as e:
            raise OllamaTimeoutError(f"Request timed out after {self.timeout}s: {e}")

        if response.status_code != 200:
            raise OllamaResponseError(
                f"Ollama returned {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

        try:
            data = response.json()
            return data.get("response", "")
        except json.JSONDecodeError as e:
            raise OllamaResponseError(f"Invalid JSON response: {e}")

    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[AnalysisOutput],
        system: Optional[str] = None,
        temperature: float = 0.1,
        max_retries: int = 2,
    ) -> AnalysisOutput:
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
                # Try to parse JSON from response
                parsed = response_schema.model_validate_json(response_text)
                return parsed
            except json.JSONDecodeError as e:
                last_error = f"JSON decode error: {e}. Response: {response_text[:500]}"
            except Exception as e:
                last_error = f"Validation error: {e}. Response: {response_text[:500]}"

        raise OllamaResponseError(
            f"Failed to get valid structured response after {max_retries + 1} attempts. Last error: {last_error}"
        )

    async def analyze_job(
        self,
        input_data: AnalysisInput,
        prompt: str,
    ) -> AnalysisOutput:
        """Analyze a job using the configured model."""
        return await self.generate_structured(
            prompt=prompt,
            response_schema=AnalysisOutput,
            system="You are an expert job match analyst. Output only valid JSON.",
        )

    async def health_check(self) -> bool:
        """Check if Ollama is available and model is loaded."""
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return any(self.model in m for m in models)
            return False
        except Exception:
            return False


async def get_ollama_client() -> OllamaClient:
    """Dependency injection for Ollama client."""
    return OllamaClient()