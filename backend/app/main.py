from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, date
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings
from app.core.logging import setup_logging
from app.db import init_db, close_db, get_database
from app.api import (
    health_router,
    profile_router,
    jobs_router,
    search_router,
    analysis_router,
    settings_router,
    processing_router,
)
from app.analysis.ollama_client import OllamaClientError
from app.analysis.response_parser import ResponseParserError
from app.job_sources.schemas import JobSourceError
from app.scoring.cloud_client import CloudScoringError
from app.scoring.response_validator import ScoringValidationError


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    await init_db()
    yield
    # Shutdown
    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title="ADHD Job Agent",
        description="ADHD-friendly job search assistant with local AI matching",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security headers middleware
    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            response: Response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            # HSTS is only for HTTPS
            if request.url.scheme == "https":
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            return response

    app.add_middleware(SecurityHeadersMiddleware)

    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0", "testserver", "test"],
    )

    # Global exception handlers
    def _json_safe(value):
        """Recursively convert a value into something json.dumps can handle.

        Pydantic's ValidationError.errors() embeds the raw offending input
        under each error's 'input' key, which can be arbitrary Python objects
        (model instances, dates, sets, ...) - not just dicts/lists/primitives.
        Failing to sanitize that meant a validation error whose bad input was
        e.g. a model instance would crash *this handler* while trying to
        report the original error, turning a clean 422 into an opaque 500.
        """
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, BaseModel):
            return _json_safe(value.model_dump(mode="json"))
        if isinstance(value, dict):
            return {str(k): _json_safe(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [_json_safe(v) for v in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        # Last resort: anything else (bytes, custom objects, exceptions...)
        return str(value)

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": _json_safe(exc.errors()),
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            },
        )

    @app.exception_handler(OllamaClientError)
    async def ollama_client_error_handler(request: Request, exc: OllamaClientError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
            },
        )

    @app.exception_handler(ResponseParserError)
    async def response_parser_error_handler(request: Request, exc: ResponseParserError):
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "error_code": "RESPONSE_PARSER_ERROR",
                "message": str(exc),
            },
        )

    @app.exception_handler(JobSourceError)
    async def job_source_error_handler(request: Request, exc: JobSourceError):
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "error_code": "JOB_SOURCE_ERROR",
                "message": str(exc),
            },
        )

    @app.exception_handler(CloudScoringError)
    async def cloud_scoring_error_handler(request: Request, exc: CloudScoringError):
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "error_code": "CLOUD_SCORING_ERROR",
                "message": str(exc),
            },
        )

    @app.exception_handler(ScoringValidationError)
    async def scoring_validation_error_handler(request: Request, exc: ScoringValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_code": "SCORING_VALIDATION_ERROR",
                "message": str(exc),
            },
        )

    # Include routers
    app.include_router(health_router)
    app.include_router(profile_router)
    app.include_router(jobs_router)
    app.include_router(search_router)
    app.include_router(analysis_router)
    app.include_router(settings_router)
    app.include_router(processing_router)

    return app


app = create_app()