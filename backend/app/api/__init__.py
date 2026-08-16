from .health import router as health_router
from .profile import router as profile_router
from .jobs import router as jobs_router
from .search import router as search_router
from .analysis import router as analysis_router
from .settings import router as settings_router
from .processing import router as processing_router

__all__ = [
    "health_router",
    "profile_router",
    "jobs_router",
    "search_router",
    "analysis_router",
    "settings_router",
    "processing_router",
]