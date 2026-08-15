from .health import router as health_router
from .profile import router as profile_router
from .jobs import router as jobs_router
from .search import router as search_router

__all__ = ["health_router", "profile_router", "jobs_router", "search_router"]