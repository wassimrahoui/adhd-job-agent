from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from app.core.config import settings
from app.job_sources.base import JobSourceAdapter, JobRef
from app.job_sources.schemas import (
    RawJobRecord,
    QuotaExhaustedError,
    AuthError,
    APIError,
    RateLimitError,
    JobSourceError,
)


class AdzunaSourceAdapter(JobSourceAdapter):
    """Adzuna job source adapter implementing the JobSourceAdapter interface.
    
    Handles HTTP communication with Adzuna API including authentication,
    pagination, response parsing, and error handling.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Adzuna adapter.
        
        Args:
            config: Optional configuration dict. If not provided, uses settings.
        """
        self._config = config or {}
        self._app_id = self._config.get("app_id", settings.adzuna_app_id)
        self._app_key = self._config.get("app_key", settings.adzuna_app_key)
        self._base_url = self._config.get("base_url", settings.adzuna_base_url)
        self._country = self._config.get("country", settings.adzuna_country)
        self._max_pages = self._config.get("max_pages", settings.adzuna_max_pages)
        self._results_per_page = self._config.get("results_per_page", settings.adzuna_results_per_page)
        self._timeout = self._config.get("timeout", 30.0)
        self._client: Optional[httpx.AsyncClient] = None
        
        if not self._app_id or not self._app_key:
            raise ValueError("Adzuna app_id and app_key are required")
    
    @property
    def source_name(self) -> str:
        return "adzuna"
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                limits=httpx.Limits(max_connections=1, max_keepalive_connections=1),
            )
        return self._client
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    def _build_search_url(self, page: int) -> str:
        """Build the search endpoint URL for a given page."""
        return urljoin(self._base_url, f"{self._country}/search/{page}")
    
    def _build_query_params(self, query_params: Dict[str, Any], page: int) -> Dict[str, Any]:
        """Build query parameters for Adzuna API request."""
        params = {
            "app_id": self._app_id,
            "app_key": self._app_key,
            "results_per_page": self._results_per_page,
            "page": page,
        }
        
        # Add user-provided query parameters
        for key, value in query_params.items():
            if value is not None and value != "":
                if isinstance(value, list):
                    params[key] = ",".join(str(v) for v in value)
                else:
                    params[key] = value
        
        return params
    
    def _parse_raw_job(self, data: Dict[str, Any]) -> RawJobRecord:
        """Parse a single Adzuna job response into RawJobRecord."""
        from app.job_sources.schemas import AdzunaArea, AdzunaCategory, AdzunaCompany
        
        # Parse location
        location = data.get("location")
        location_obj = None
        if isinstance(location, dict):
            area = location.get("area", [])
            display_name = location.get("display_name")
            if area or display_name:
                location_obj = AdzunaArea(area=area, display_name=display_name)
        elif isinstance(location, str):
            location_obj = AdzunaArea(display_name=location)
        
        # Parse company
        company = data.get("company")
        company_obj = None
        if isinstance(company, dict):
            company_display = company.get("display_name")
            if company_display:
                company_obj = AdzunaCompany(display_name=company_display)
        elif isinstance(company, str):
            company_obj = AdzunaCompany(display_name=company)
        
        # Parse category
        category = data.get("category")
        category_obj = None
        if isinstance(category, dict):
            category_label = category.get("label")
            category_tag = category.get("tag")
            if category_label:
                category_obj = AdzunaCategory(label=category_label, tag=category_tag)
        elif isinstance(category, str):
            category_obj = AdzunaCategory(label=category)
        
        return RawJobRecord(
            id=str(data.get("id", "")),
            title=data.get("title", ""),
            company=company_obj,
            location=location_obj,
            description=data.get("description"),
            salary_min=data.get("salary_min"),
            salary_max=data.get("salary_max"),
            salary_is_predicted=data.get("salary_is_predicted", False),
            contract_type=data.get("contract_type"),
            contract_time=data.get("contract_time"),
            category=category_obj,
            created=data.get("created"),
            redirect_url=data.get("redirect_url"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
        )
    
    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from Adzuna API."""
        status = response.status_code
        
        if status == 401:
            raise AuthError("Invalid Adzuna app_id or app_key")
        
        if status == 429:
            raise RateLimitError("Adzuna rate limit exceeded")
        
        if status == 403:
            # Adzuna returns 403 for quota exhausted
            raise QuotaExhaustedError("Adzuna daily quota exhausted for today")
        
        if status >= 500:
            raise APIError(f"Adzuna server error: {status}", status_code=status)
        
        # Try to parse error message from response
        try:
            error_data = response.json()
            error_msg = error_data.get("error", error_data.get("message", f"HTTP {status}"))
        except Exception:
            error_msg = f"HTTP {status}"
        
        if "quota" in error_msg.lower() or "limit" in error_msg.lower():
            raise QuotaExhaustedError(f"Adzuna quota exhausted: {error_msg}")
        
        raise APIError(f"Adzuna API error: {error_msg}", status_code=status)
    
    async def discover(self, query_params: Dict[str, Any], max_pages: int = 5) -> List[JobRef]:
        """Discover job references from Adzuna.
        
        Args:
            query_params: Search parameters (what, where, salary_min, etc.)
            max_pages: Maximum pages to fetch (default from config)
            
        Returns:
            List of JobRef objects for discovered jobs
            
        Raises:
            QuotaExhaustedError: If daily quota is exhausted
            AuthError: If authentication fails
            APIError: For other API errors
        """
        max_pages = min(max_pages, self._max_pages)
        all_refs: List[JobRef] = []
        
        client = await self._get_client()
        
        for page in range(1, max_pages + 1):
            url = self._build_search_url(page)
            params = self._build_query_params(query_params, page)
            
            try:
                response = await client.get(url, params=params)
            except httpx.TimeoutException:
                raise APIError("Adzuna request timed out")
            except httpx.RequestError as e:
                raise APIError(f"Adzuna request failed: {str(e)}")
            
            if response.status_code != 200:
                self._handle_error_response(response)
            
            try:
                data = response.json()
            except Exception as e:
                raise APIError(f"Failed to parse Adzuna response: {str(e)}")
            
            results = data.get("results", [])
            if not results:
                # No more results, stop pagination
                break
            
            for job_data in results:
                job_id = str(job_data.get("id", ""))
                if job_id:
                    all_refs.append(JobRef(
                        source_id=job_id,
                        source_name=self.source_name,
                        extra={"redirect_url": job_data.get("redirect_url")}
                    ))
            
            # Check if we got fewer results than requested (last page)
            if len(results) < self._results_per_page:
                break
        
        return all_refs
    
    async def extract(self, refs: List[JobRef]) -> List[RawJobRecord]:
        """Extract full job data for the given references.
        
        For Adzuna, the discover phase already returns full job data in results,
        so we can reconstruct RawJobRecord from the stored extra data.
        In a real implementation, we might fetch each job individually,
        but Adzuna's search endpoint already returns complete job data.
        
        Args:
            refs: List of job references from discover()
            
        Returns:
            List of RawJobRecord objects
        """
        # Since we already have the full data from discover, we need to re-fetch
        # or store the raw data during discover. For now, we'll return empty
        # and the orchestration layer will handle re-fetching if needed.
        # This is a simplification - in production we'd store raw data during discover.
        return []
    
    async def search_jobs(self, query_params: Dict[str, Any], max_pages: int = 5) -> List[RawJobRecord]:
        """Convenience method to search and extract in one call.
        
        This is the main entry point for the search orchestration layer.
        
        Args:
            query_params: Search parameters
            max_pages: Maximum pages to fetch
            
        Returns:
            List of RawJobRecord objects
        """
        max_pages = min(max_pages, self._max_pages)
        all_jobs: List[RawJobRecord] = []
        
        client = await self._get_client()
        
        for page in range(1, max_pages + 1):
            url = self._build_search_url(page)
            params = self._build_query_params(query_params, page)
            
            try:
                response = await client.get(url, params=params)
            except httpx.TimeoutException:
                raise APIError("Adzuna request timed out")
            except httpx.RequestError as e:
                raise APIError(f"Adzuna request failed: {str(e)}")
            
            if response.status_code != 200:
                self._handle_error_response(response)
            
            try:
                data = response.json()
            except Exception as e:
                raise APIError(f"Failed to parse Adzuna response: {str(e)}")
            
            results = data.get("results", [])
            if not results:
                break
            
            for job_data in results:
                try:
                    job = self._parse_raw_job(job_data)
                    all_jobs.append(job)
                except Exception as e:
                    # Log but continue - don't let one bad job break the whole search
                    continue
            
            # Check if we got fewer results than requested (last page)
            if len(results) < self._results_per_page:
                break
        
        return all_jobs


# Test override for dependency injection
_test_adzuna_adapter: Optional[AdzunaSourceAdapter] = None


def set_test_adzuna_adapter(adapter: Optional[AdzunaSourceAdapter]) -> None:
    """Set a test adapter (for testing only)."""
    global _test_adzuna_adapter
    _test_adzuna_adapter = adapter