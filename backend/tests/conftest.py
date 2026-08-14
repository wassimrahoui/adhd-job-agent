import pytest
import asyncio
from pathlib import Path
import tempfile
import os

from app.db import Database, init_db, close_db, get_database
from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db_path():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture(scope="function")
async def test_db(test_db_path):
    """Create a test database instance."""
    db = Database(test_db_path)
    await db.connect()
    yield db
    await db.close()


@pytest.fixture(scope="function")
async def profile_repo(test_db):
    """Create a ProfileRepository for testing."""
    from app.repositories import ProfileRepository
    return ProfileRepository(test_db)


@pytest.fixture(scope="function")
async def job_repo(test_db):
    """Create a JobRepository for testing."""
    from app.repositories import JobRepository
    return JobRepository(test_db)


@pytest.fixture(scope="function")
async def analysis_repo(test_db):
    """Create an AIAnalysisRepository for testing."""
    from app.repositories import AIAnalysisRepository
    return AIAnalysisRepository(test_db)