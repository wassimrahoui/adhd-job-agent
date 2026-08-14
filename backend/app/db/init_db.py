from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db import init_db, close_db
from app.core.config import settings


async def main() -> None:
    """Initialize the database."""
    print(f"Initializing database at: {settings.database_path}")
    db = await init_db()
    print("Database initialized successfully!")
    
    # Verify tables exist
    tables = await db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
    print("Tables created:")
    for table in tables:
        print(f"  - {table['name']}")
    
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())