from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from app.job_sources.schemas import RawJobRecord, JobSourceError, QuotaExhaustedError


@dataclass
class JobRef:
    """Lightweight reference to a job for discovery phase."""
    source_id: str
    source_name: str = "adzuna"
    extra: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.extra is None:
            self.extra = {}


class JobSourceAdapter(ABC):
    """Abstract base class for job source adapters.
    
    Each adapter implements the two-phase discovery/extraction pattern:
    1. discover() - returns lightweight job references (for pagination/quota tracking)
    2. extract(refs) - fetches full job data for given references
    """
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier for this job source."""
        pass
    
    @abstractmethod
    async def discover(self, query_params: Dict[str, Any], max_pages: int = 5) -> List[JobRef]:
        """Discover job references from the source.
        
        Args:
            query_params: Search query parameters (what, where, salary_min, etc.)
            max_pages: Maximum number of pages to fetch
            
        Returns:
            List of JobRef objects for discovered jobs
            
        Raises:
            QuotaExhaustedError: If daily quota is exhausted
            JobSourceError: For other source-specific errors
        """
        pass
    
    @abstractmethod
    async def extract(self, refs: List[JobRef]) -> List[RawJobRecord]:
        """Extract full job data for the given references.
        
        Args:
            refs: List of job references from discover()
            
        Returns:
            List of RawJobRecord objects with full job data
            
        Raises:
            JobSourceError: For source-specific errors
        """
        pass
    
    async def close(self) -> None:
        """Close any open connections. Called after search completes."""
        pass