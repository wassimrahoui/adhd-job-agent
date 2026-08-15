from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.config import settings
from app.db import init_db, close_db, get_database
from app.api import health_router, profile_router, jobs_router, search_router, analysis_router, settings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
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

    # Global exception handlers
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        # Convert errors to JSON-serializable format
        def serialize_errors(errors):
            result = []
            for error in errors:
                serialized = {}
                for key, value in error.items():
                    if isinstance(value, datetime):
                        serialized[key] = value.isoformat()
                    elif isinstance(value, dict):
                        serialized[key] = serialize_errors([value])[0]
                    elif isinstance(value, list):
                        serialized[key] = [serialize_errors([v])[0] if isinstance(v, dict) else v for v in value]
                    else:
                        serialized[key] = value
                result.append(serialized)
            return result
        
        from datetime import datetime
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": serialize_errors(exc.errors()),
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

    # Include routers
    app.include_router(health_router)
    app.include_router(profile_router)
    app.include_router(jobs_router)
    app.include_router(search_router)
    app.include_router(analysis_router)
    app.include_router(settings_router)

    return app


app = create_app()