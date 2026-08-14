from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.db import get_database

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    database: str
    ollama: str


@router.get("", response_model=HealthResponse)
async def health_check(db=Depends(get_database)) -> HealthResponse:
    """Liveness/readiness check."""
    # Check database connection
    db_status = "connected"
    try:
        await db.fetchone("SELECT 1")
    except Exception:
        db_status = "disconnected"
    
    # Ollama status - for now just return unknown, will be implemented later
    ollama_status = "unknown"
    
    return HealthResponse(
        status="ok",
        database=db_status,
        ollama=ollama_status
    )