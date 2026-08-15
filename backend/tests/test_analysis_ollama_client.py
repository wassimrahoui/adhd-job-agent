from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.analysis.ollama_client import (
    OllamaClient,
    OllamaConnectionError,
    OllamaTimeoutError,
    OllamaResponseError,
)
from app.schemas.analysis import AnalysisOutput, AnalysisInput, AnalysisJobInput, AnalysisProfileInput


class TestOllamaClient:
    def test_client_initialization_defaults(self):
        client = OllamaClient()
        assert client.base_url == "http://localhost:11434"
        assert client.model == "qwen2.5:14b-instruct-q4_K_M"
        assert client.timeout == 120.0

    def test_client_initialization_custom(self):
        client = OllamaClient(
            base_url="http://custom:11434",
            model="custom-model",
            timeout=60.0,
        )
        assert client.base_url == "http://custom:11434"
        assert client.model == "custom-model"
        assert client.timeout == 60.0

    @pytest.mark.asyncio
    async def test_generate_success(self):
        client = OllamaClient()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Hello, world!"}
        mock_client.post.return_value = mock_response
        mock_client.is_closed = False
        client._client = mock_client

        result = await client.generate("Test prompt")

        assert result == "Hello, world!"
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_connection_error(self):
        client = OllamaClient()
        mock_client = AsyncMock()
        mock_client.post.side_effect = Exception("Connection refused")
        client._client = mock_client

        with pytest.raises(OllamaConnectionError):
            await client.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_timeout_error(self):
        client = OllamaClient()
        mock_client = AsyncMock()
        import httpx
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")
        mock_client.is_closed = False
        client._client = mock_client

        with pytest.raises(OllamaTimeoutError):
            await client.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_response_error(self):
        client = OllamaClient()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_client.post.return_value = mock_response
        client._client = mock_client

        with pytest.raises(OllamaResponseError):
            await client.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_structured_success(self):
        client = OllamaClient()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": '{"model_used": "llama3:70b", "score": 85, "recommendation": "strong_match", "confidence": "high", "matching_skills": [], "matching_experience": [], "missing_requirements": [], "unknown_requirements": [], "explanation": "Good match", "evidence": [], "status": "success"}'
        }
        mock_client.post.return_value = mock_response
        client._client = mock_client

        input_data = AnalysisInput(
            job=AnalysisJobInput(id=1, adzuna_id="test-1", title="Software Engineer"),
            profile=AnalysisProfileInput(),
        )
        prompt = "Test prompt"

        result = await client.generate_structured(prompt, AnalysisOutput)

        assert isinstance(result, AnalysisOutput)
        assert result.score == 85
        assert result.recommendation == "strong_match"

    @pytest.mark.asyncio
    async def test_generate_structured_json_decode_error(self):
        client = OllamaClient()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "not valid json"}
        mock_client.post.return_value = mock_response
        client._client = mock_client

        with pytest.raises(OllamaResponseError):
            await client.generate_structured("Test prompt", AnalysisOutput, max_retries=1)

    @pytest.mark.asyncio
    async def test_generate_structured_validation_error(self):
        client = OllamaClient()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": '{"invalid": "data"}'}
        mock_client.post.return_value = mock_response
        client._client = mock_client

        with pytest.raises(OllamaResponseError):
            await client.generate_structured("Test prompt", AnalysisOutput, max_retries=1)

    @pytest.mark.asyncio
    async def test_close(self):
        client = OllamaClient()
        mock_client = AsyncMock()
        client._client = mock_client

        await client.close()

        mock_client.aclose.assert_called_once()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        client = OllamaClient()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "qwen2.5:14b-instruct-q4_K_M"}]}
        mock_client.get.return_value = mock_response
        mock_client.is_closed = False
        client._client = mock_client

        result = await client.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_model_not_found(self):
        client = OllamaClient()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "other-model"}]}
        mock_client.get.return_value = mock_response
        client._client = mock_client

        result = await client.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_connection_error(self):
        client = OllamaClient()
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Connection refused")
        client._client = mock_client

        result = await client.health_check()

        assert result is False


class TestGetOllamaClient:
    @pytest.mark.asyncio
    async def test_get_ollama_client(self):
        from app.analysis.ollama_client import get_ollama_client

        client = await get_ollama_client()
        assert isinstance(client, OllamaClient)
        await client.close()