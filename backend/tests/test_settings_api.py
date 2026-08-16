from __future__ import annotations

import pytest

from app.main import app
from app.db import get_database
from app.repositories import ProfileRepository
from app.models import ProfileCreate


class TestSettingsStatusRelevanceThreshold:
    """Regression test: /settings/status must reflect the profile's actual
    relevance_threshold, not a hardcoded placeholder value."""

    @pytest.mark.asyncio
    async def test_reflects_profile_relevance_threshold(self, test_db):
        from httpx import ASGITransport, AsyncClient

        profile_repo = ProfileRepository(test_db)
        await profile_repo.upsert_profile(ProfileCreate(relevance_threshold=73))

        async def override_get_db():
            return test_db

        app.dependency_overrides[get_database] = override_get_db
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/settings/status")

            assert response.status_code == 200
            assert response.json()["relevance_threshold"] == 73
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_defaults_to_50_without_profile(self, test_db):
        from httpx import ASGITransport, AsyncClient

        async def override_get_db():
            return test_db

        app.dependency_overrides[get_database] = override_get_db
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/settings/status")

            assert response.status_code == 200
            assert response.json()["relevance_threshold"] == 50
        finally:
            app.dependency_overrides.clear()
