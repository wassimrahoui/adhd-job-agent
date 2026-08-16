from .base import JobSourceAdapter, JobRef
from .schemas import (
    RawJobRecord,
    AdzunaArea,
    AdzunaCategory,
    AdzunaCompany,
    JobSourceError,
    QuotaExhaustedError,
    AuthError,
    APIError,
    RateLimitError,
)
from .adzuna import AdzunaSourceAdapter, _test_adzuna_adapter
from .query_builder import build_adzuna_query, build_adzuna_queries, build_adzuna_query_simple
from .normalize import (
    normalize_job,
    dedup_key,
    is_duplicate,
    merge_job_data,
)
from .adzuna import set_test_adzuna_adapter

__all__ = [
    "JobSourceAdapter",
    "JobRef",
    "RawJobRecord",
    "AdzunaArea",
    "AdzunaCategory",
    "AdzunaCompany",
    "JobSourceError",
    "QuotaExhaustedError",
    "AuthError",
    "APIError",
    "RateLimitError",
    "AdzunaSourceAdapter",
    "build_adzuna_query",
    "build_adzuna_queries",
    "build_adzuna_query_simple",
    "normalize_job",
    "dedup_key",
    "is_duplicate",
    "merge_job_data",
    "set_test_adzuna_adapter",
    "_test_adzuna_adapter",
]