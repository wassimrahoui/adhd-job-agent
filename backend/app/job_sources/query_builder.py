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

    # Keywords - from desired_roles. Adzuna's "what" performs a whole-phrase
    # AND match, so comma-joining multiple roles into it (the previous
    # approach) matched nothing since no single job title contains every
    # role. "what_or" is Adzuna's real OR-across-terms parameter and expects
    # space-separated terms, not comma-separated.
    what_or_terms: List[str] = list(profile.desired_roles) if profile.desired_roles else []

    # Remote/hybrid/on-site preference
    # Adzuna has no direct remote filter; adding "remote"/"hybrid" as an
    # additional what_or candidate broadens the OR set rather than requiring
    # it, which is the best available approximation.
    if profile.remote_preference == RemotePreference.REMOTE:
        what_or_terms.append("remote")
    elif profile.remote_preference == RemotePreference.HYBRID:
        what_or_terms.append("hybrid")

    if what_or_terms:
        params["what_or"] = " ".join(what_or_terms)

    # Location (where) - Adzuna's "where" is a single free-text location, not
    # a multi-value OR list; comma-joining multiple preferences (the previous
    # approach) matched nothing. Use the primary (first) preference only.
    if profile.location_preferences:
        params["where"] = profile.location_preferences[0]

    # Salary minimum
    if profile.salary_min is not None and profile.salary_min > 0:
        params["salary_min"] = profile.salary_min
    
    # Contract type (employment type)
    if profile.experience_level:
        # Map experience level to seniority if needed
        pass  # Adzuna doesn't have direct experience level filter
    
    # Excluded keywords - not directly supported by Adzuna API
    # Will be handled as client-side post-filter
    # Could potentially add to 'what' with NOT operator but Adzuna doesn't support it
    
    # Default sort by relevance
    params["sort_by"] = "relevance"

    # Request JSON explicitly, per Adzuna's documented query parameter
    params["content-type"] = "application/json"
    
    # Remove None/empty values
    return {k: v for k, v in params.items() if v is not None and v != ""}


def build_adzuna_queries(profile: Profile) -> List[Dict[str, Any]]:
    """Build one precise Adzuna query per desired role, instead of one broad query.

    Adzuna's "what_or" performs OR matching across *individual words*, not
    across whole role phrases - "Security Engineer" OR "SOC Analyst" becomes
    "Security" OR "Engineer" OR "SOC" OR "Analyst", which matches unrelated
    jobs like "Security Guard" or "HVAC Engineer" just as readily as real
    matches. Issuing one exact-phrase "what" query per role (true AND-within-
    phrase matching) and merging the results client-side gives real OR-of-
    phrases semantics instead.

    Returns a list with one query dict per desired role, sharing the same
    location/salary/sort params. If the profile has no desired_roles, returns
    a single query with no "what" filter at all (relies on location/salary
    alone), matching the previous no-keywords behavior.
    """
    shared: Dict[str, Any] = {}

    # Adzuna's "where" is a single free-text location, not a multi-value OR
    # list. With exactly one preference it's safe to scope the query to it
    # directly. With multiple preferences, picking just one (e.g. the first)
    # would silently drop real jobs in the others - Adzuna has no way to
    # OR multiple locations in one query - so instead we search unscoped
    # (country=de only) and let the pre-filter's location check, which does
    # correctly match against every location_preference, narrow it down.
    if profile.location_preferences and len(profile.location_preferences) == 1:
        shared["where"] = profile.location_preferences[0]

    if profile.salary_min is not None and profile.salary_min > 0:
        shared["salary_min"] = profile.salary_min

    shared["sort_by"] = "relevance"
    shared["content-type"] = "application/json"

    roles = list(profile.desired_roles) if profile.desired_roles else []
    if profile.remote_preference == RemotePreference.REMOTE:
        roles.append("remote")
    elif profile.remote_preference == RemotePreference.HYBRID:
        roles.append("hybrid")

    if not roles:
        return [{k: v for k, v in shared.items() if v is not None and v != ""}]

    queries = []
    for role in roles:
        query = dict(shared)
        query["what"] = role
        queries.append({k: v for k, v in query.items() if v is not None and v != ""})
    return queries


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

    what_or_terms: List[str] = [what] if what else []
    if remote and remote != "any":
        what_or_terms.append(remote)
    if what_or_terms:
        params["what_or"] = " ".join(what_or_terms)

    if where:
        params["where"] = where
    if salary_min is not None and salary_min > 0:
        params["salary_min"] = salary_min

    params["sort_by"] = "relevance"
    params["content-type"] = "application/json"

    return {k: v for k, v in params.items() if v is not None and v != ""}