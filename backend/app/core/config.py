from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_path: str = "data/adhd_job_agent.db"

    # Adzuna API
    adzuna_app_id: Optional[str] = None
    adzuna_app_key: Optional[str] = None
    adzuna_base_url: str = "https://api.adzuna.com/v1/api/jobs"
    adzuna_country: str = "us"
    adzuna_results_per_page: int = 20
    adzuna_max_pages: int = 5

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:14b-instruct-q4_K_M"
    ollama_timeout: int = 120

    # Cloud Scoring (optional - for Phase 5)
    cloud_scoring_api_key: Optional[str] = None
    cloud_scoring_base_url: str = "https://api.openai.com/v1"
    cloud_scoring_model: str = "gpt-4"
    cloud_scoring_timeout: int = 60

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # Frontend
    frontend_url: str = "http://localhost:5173"

    # Logging
    log_level: str = "INFO"

    @property
    def database_dir(self) -> Path:
        path = Path(self.database_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()