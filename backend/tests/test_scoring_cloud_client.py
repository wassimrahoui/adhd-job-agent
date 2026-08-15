from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.scoring.cloud_client import (
    CloudScoringClient,
    CloudConnectionError,
    CloudTimeoutError,
    CloudResponseError,
)
from app.schemas.scoring import ScoringOutput, ScoringInput


class TestCloudScoringClient:
    def test_client_initialization_defaults(self):
        client = CloudScoringClient()
        assert client.base_url == "https://api.openai.com/v1"
        assert client.model == "gpt-4"
        assert client.timeout == 60.0

    def test_client_initialization_custom(self):
        client = CloudScoringClient(
            api_key="test-key",
            base_url="https://custom-api.com/v1",
            model="gpt-3.5-turbo",
            timeout=30.0,
        )
        assert client.api_key == "test-key"
        assert client.base_url == "https://custom-api.com/v1"
        assert client.model == "gpt-3.5-turbo"
        assert client.timeout == 30.0

    @pytest.mark.asyncio
    async def test_generate_success(self):
        client = CloudScoringClient()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello, world!"}}]
        }
        mock_client.post.return_value = mock_response
        mock_client.is_closed = False
        client._client = mock_client

        result = await client.generate("Test prompt")

        assert result == "Hello, world!"
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_with_system(self):
        client = CloudScoringClient()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response with system"}}]
        }
        mock_client.post.return_value = mock_response
        mock_client.is_closed = False
        client._client = mock_client

        result = await client.generate("Test prompt", system="System prompt")

        assert result == "Response with system"
        # Check that system was included in payload
        call_args = mock_client.post.call_args
        payload = call_args.kwargs.get("json", {})
        assert any(m.get("role") == "system" for m in payload.get("messages", []))

    @pytest.mark.asyncio
    async def test_generate_connection_error(self):
        client = CloudScoringClient()
        mock_client = AsyncMock()
        import httpx
        mock_client.post.side_effect = httpx.ConnectError("Connection refused")
        mock_client.is_closed = False
        client._client = mock_client

        with pytest.raises(CloudConnectionError):
            await client.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_timeout_error(self):
        client = CloudScoringClient()
        mock_client = AsyncMock()
        import httpx
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")
        mock_client.is_closed = False
        client._client = mock_client

        with pytest.raises(CloudTimeoutError):
            await client.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_response_error(self):
        client = CloudScoringClient()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_client.post.return_value = mock_response
        client._client = mock_client

        with pytest.raises(CloudResponseError):
            await client.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_structured_success(self):
        client = CloudScoringClient()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"model_used": "gpt-4", "score": 85, "recommendation": "strong_match", "confidence": "high", "skills_score": 90, "experience_score": 80, "requirements_score": 70, "location_score": 95, "salary_score": 85, "explanation": "Excellent match", "evidence": [], "status": "success"}'
                }
            }]
        }
        mock_client.post.return_value = mock_response
        mock_client.is_closed = False
        client._client = mock_client

        input_data = ScoringInput(job_title="Software Engineer")
        prompt = "Test prompt"

        result = await client.generate_structured(prompt, ScoringOutput)

        assert isinstance(result, ScoringOutput)
        assert result.score == 85
        assert result.recommendation == "strong_match"

    @pytest.mark.asyncio
    async def test_generate_structured_json_decode_error(self):
        client = CloudScoringClient()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "not valid json"}}]}
        mock_client.post.return_value = mock_response
        client._client = mock_client

        with pytest.raises(CloudResponseError):
            await client.generate_structured("Test prompt", ScoringOutput, max_retries=1)

    @pytest.mark.asyncio
    async def test_generate_structured_validation_error(self):
        client = CloudScoringClient()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": '{"invalid": "data"}'}}]}
        mock_client.post.return_value = mock_response
        client._client = mock_client

        with pytest.raises(CloudResponseError):
            await client.generate_structured("Test prompt", ScoringOutput, max_retries=1)

    @pytest.mark.asyncio
    async def test_close(self):
        client = CloudScoringClient()
        mock_client = AsyncMock()
        mock_client.is_closed = False
        client._client = mock_client

        await client.close()

        mock_client.aclose.assert_called_once()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        client = CloudScoringClient()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        mock_client.is_closed = False
        client._client = mock_client

        result = await client.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_error(self):
        client = CloudScoringClient()
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Connection refused")
        client._client = mock_client

        result = await client.health_check()

        assert result is False


class TestGetCloudScoringClient:
    @pytest.mark.asyncio
    async def test_get_cloud_scoring_client(self):
        from app.scoring.cloud_client import get_cloud_scoring_client

        client = await get_cloud_scoring_client()
        assert isinstance(client, CloudScoringClient)
        await client.close()