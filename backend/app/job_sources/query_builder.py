from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models import Profile, RemotePreference


def build_adzuna_query(profile: Profile) -> Dict[str, Any]:
    """Build Adzuna search query parameters from user profile.
    
    This is a pure, deterministic function that converts profile preferences
    into Adzuna API query parameters.
    
    Args:
        profile: User profile with preferences
        
    Returns:
        Dictionary of query parameters for Adzuna API
    """
    params: Dict[str, Any] = {}
    
    # Keywords (what) - from desired_roles
    if profile.desired_roles:
        # Join multiple roles with OR logic (Adzuna accepts comma-separated)
        params["what"] = ", ".join(profile.desired_roles)
    
    # Location (where) - from location_preferences
    if profile.location_preferences:
        # Join multiple locations with OR logic
        params["where"] = ", ".join(profile.location_preferences)
    
    # Salary minimum
    if profile.salary_min is not None and profile.salary_min > 0:
        params["salary_min"] = profile.salary_min
    
    # Remote/hybrid/on-site preference
    # Adzuna uses contract_time for full/part time and doesn't have direct remote filter
    # We'll use sort_by for relevance and handle remote filtering client-side
    if profile.remote_preference == RemotePreference.REMOTE:
        # Adzuna doesn't have a direct remote filter in search
        # Could add "remote" to keywords or handle post-search
        params["what"] = (params.get("what", "") + ", remote").lstrip(", ")
    elif profile.remote_preference == RemotePreference.HYBRID:
        params["what"] = (params.get("what", "") + ", hybrid").lstrip(", ")
    
    # Contract type (employment type)
    if profile.experience_level:
        # Map experience level to seniority if needed
        pass  # Adzuna doesn't have direct experience level filter
    
    # Excluded keywords - not directly supported by Adzuna API
    # Will be handled as client-side post-filter
    # Could potentially add to 'what' with NOT operator but Adzuna doesn't support it
    
    # Default sort by relevance (date)
    params["sort_by"] = "relevance"
    params["sort_order"] = "desc"
    
    # Content type - full description not available, but we want max content
    params["content_type"] = "full"
    
    # Remove None/empty values
    return {k: v for k, v in params.items() if v is not None and v != ""}


def build_adzuna_query_simple(
    what: Optional[str] = None,
    where: Optional[str] = None,
    salary_min: Optional[int] = None,
    remote: Optional[str] = None,
    max_pages: int = 5,
) -> Dict[str, Any]:
    """Build a simple Adzuna query from individual parameters.
    
    Useful for testing or when profile is not available.
    
    Args:
        what: Job keywords/search terms
        where: Location
        salary_min: Minimum salary
        remote: Remote preference (remote, hybrid, on_site)
        max_pages: Maximum pages to fetch
        
    Returns:
        Dictionary of query parameters
    """
    params: Dict[str, Any] = {}
    
    if what:
        params["what"] = what
    if where:
        params["where"] = where
    if salary_min is not None and salary_min > 0:
        params["salary_min"] = salary_min
    if remote and remote != "any":
        params["what"] = (params.get("what", "") + f", {remote}").lstrip(", ")
    
    params["sort_by"] = "relevance"
    params["sort_order"] = "desc"
    params["content_type"] = "full"
    
    return {k: v for k, v in params.items() if v is not None and v != ""}