from __future__ import annotations

import httpx
import pytest

from app.job_sources.adzuna import AdzunaSourceAdapter
from app.job_sources.schemas import QuotaExhaustedError, AuthError, APIError


def make_adapter(**overrides) -> AdzunaSourceAdapter:
    config = {
        "app_id": "test-app-id",
        "app_key": "test-app-key",
        "base_url": "https://api.adzuna.com/v1/api/jobs",
        "country": "de",
        "max_pages": 1,
        "results_per_page": 20,
    }
    config.update(overrides)
    return AdzunaSourceAdapter(config=config)


class TestBuildSearchUrl:
    """Regression coverage for a real bug: urljoin() against a base URL with no
    trailing slash silently dropped the '/jobs' path segment, producing
    'https://api.adzuna.com/v1/api/de/search/1' instead of the correct
    'https://api.adzuna.com/v1/api/jobs/de/search/1' — Adzuna returned 404 for
    every real search."""

    def test_url_includes_jobs_segment_with_no_trailing_slash_on_base(self):
        adapter = make_adapter(base_url="https://api.adzuna.com/v1/api/jobs")
        url = adapter._build_search_url(1)
        assert url == "https://api.adzuna.com/v1/api/jobs/de/search/1"

    def test_url_correct_with_trailing_slash_on_base(self):
        adapter = make_adapter(base_url="https://api.adzuna.com/v1/api/jobs/")
        url = adapter._build_search_url(1)
        assert url == "https://api.adzuna.com/v1/api/jobs/de/search/1"

    def test_url_uses_configured_country_and_page(self):
        adapter = make_adapter(country="gb")
        url = adapter._build_search_url(3)
        assert url == "https://api.adzuna.com/v1/api/jobs/gb/search/3"


class TestSearchJobsRealRequestUrl:
    """Verify the adapter issues the request to the exact URL Adzuna expects,
    at the actual httpx transport level (not bypassed by a fake adapter)."""

    @pytest.mark.asyncio
    async def test_search_jobs_requests_expected_url_and_params(self):
        captured = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url.copy_with(query=None))
            captured["params"] = dict(request.url.params)
            return httpx.Response(200, json={"results": [], "count": 0})

        adapter = make_adapter()
        adapter._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        await adapter.search_jobs({"what": "python developer", "where": "Berlin"}, max_pages=1)

        assert captured["url"] == "https://api.adzuna.com/v1/api/jobs/de/search/1"
        assert captured["params"]["app_id"] == "test-app-id"
        assert captured["params"]["app_key"] == "test-app-key"
        assert captured["params"]["what"] == "python developer"
        assert captured["params"]["where"] == "Berlin"
        # Regression: page number lives in the URL path only; Adzuna returns
        # 400 if a redundant 'page' query parameter is also sent.
        assert "page" not in captured["params"]

        await adapter.close()

    @pytest.mark.asyncio
    async def test_search_jobs_parses_results(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "id": "123",
                            "title": "Security Engineer",
                            "company": {"display_name": "Acme"},
                            "location": {"display_name": "Munich, Germany"},
                            "description": "Great role",
                            "redirect_url": "https://example.com/job/123",
                        }
                    ],
                    "count": 1,
                },
            )

        adapter = make_adapter()
        adapter._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        jobs = await adapter.search_jobs({"what": "security"}, max_pages=1)

        assert len(jobs) == 1
        assert jobs[0].id == "123"
        assert jobs[0].title == "Security Engineer"
        assert jobs[0].company.display_name == "Acme"

        await adapter.close()

    @pytest.mark.asyncio
    async def test_404_raises_api_error_not_silently_swallowed(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"error": "Not found"})

        adapter = make_adapter()
        adapter._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        with pytest.raises(APIError):
            await adapter.search_jobs({"what": "python"}, max_pages=1)

        await adapter.close()

    @pytest.mark.asyncio
    async def test_401_raises_auth_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"error": "Invalid credentials"})

        adapter = make_adapter()
        adapter._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        with pytest.raises(AuthError):
            await adapter.search_jobs({"what": "python"}, max_pages=1)

        await adapter.close()

    @pytest.mark.asyncio
    async def test_403_raises_quota_exhausted(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(403, json={"error": "Quota exceeded"})

        adapter = make_adapter()
        adapter._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        with pytest.raises(QuotaExhaustedError):
            await adapter.search_jobs({"what": "python"}, max_pages=1)

        await adapter.close()


class TestAdapterRequiresCredentials:
    def test_missing_app_id_raises(self):
        with pytest.raises(ValueError):
            AdzunaSourceAdapter(config={"app_id": None, "app_key": "key"})

    def test_missing_app_key_raises(self):
        with pytest.raises(ValueError):
            AdzunaSourceAdapter(config={"app_id": "id", "app_key": None})
