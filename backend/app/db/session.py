from __future__ import annotations

import aiosqlite
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, List
import json
from pathlib import Path

from app.core.config import settings


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._pool: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Initialize database connection and run migrations."""
        self._pool = await aiosqlite.connect(self.db_path)
        self._pool.row_factory = aiosqlite.Row
        # Enable foreign keys
        await self._pool.execute("PRAGMA foreign_keys = ON")
        await self._pool.commit()
        await self._run_migrations()

    async def close(self) -> None:
        """Close database connection."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Provide a transactional scope."""
        if not self._pool:
            raise RuntimeError("Database not connected. Call connect() first.")
        async with self._pool as conn:
            yield conn

    async def execute(self, query: str, params: tuple = ()) -> aiosqlite.Cursor:
        """Execute a query."""
        if not self._pool:
            raise RuntimeError("Database not connected. Call connect() first.")
        return await self._pool.execute(query, params)

    async def fetchone(self, query: str, params: tuple = ()) -> Optional[aiosqlite.Row]:
        """Fetch one row."""
        cursor = await self.execute(query, params)
        return await cursor.fetchone()

    async def fetchall(self, query: str, params: tuple = ()) -> List[aiosqlite.Row]:
        """Fetch all rows."""
        cursor = await self.execute(query, params)
        rows = await cursor.fetchall()
        return list(rows) if rows else []

    async def _run_migrations(self) -> None:
        """Run database migrations from schema.sql."""
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            schema_sql = schema_path.read_text()
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in schema_sql.split(";") if s.strip()]
            for stmt in statements:
                try:
                    await self._pool.execute(stmt)  # type: ignore[union-attr]
                except Exception:
                    # Log but continue - some statements might fail if already exist
                    pass
            await self._pool.commit()  # type: ignore[union-attr]


# Global database instance
_db: Optional[Database] = None


def get_database() -> Database:
    """Get the global database instance."""
    global _db
    if _db is None:
        _db = Database(settings.database_path)
    return _db


async def init_db() -> Database:
    """Initialize the database connection."""
    db = get_database()
    await db.connect()
    return db


async def close_db() -> None:
    """Close the database connection."""
    global _db
    if _db:
        await _db.close()
        _db = None