from fastapi import APIRouter, Depends
from app.core.config import settings
from app.db import get_database
import httpx

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/status")
async def get_settings_status(db=Depends(get_database)):
    # Check Adzuna connection
    adzuna_connected = bool(settings.adzuna_app_id and settings.adzuna_app_key)

    # Check Ollama connection
    ollama_connected = False
    ollama_model_installed = False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
            if response.status_code == 200:
                ollama_connected = True
                data = response.json()
                models = data.get("models", [])
                ollama_model_installed = any(
                    settings.ollama_model in m.get("name", "") for m in models
                )
    except Exception:
        pass

    return {
        "adzuna_connected": adzuna_connected,
        "ollama_connected": ollama_connected,
        "ollama_model": settings.ollama_model,
        "ollama_model_installed": ollama_model_installed,
        "relevance_threshold": 0,  # TODO: add to config
    }