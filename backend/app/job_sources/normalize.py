from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from app.models import Job, JobCreate
from app.job_sources import RawJobRecord


def normalize_job(raw: RawJobRecord) -> JobCreate:
    """Normalize Adzuna RawJobRecord to canonical JobCreate schema.
    
    All fields from Adzuna are preserved; missing fields are set to None.
    Raw Adzuna response is stored in raw_evidence.
    
    Args:
        raw: Raw job record from Adzuna
        
    Returns:
        JobCreate with normalized fields
    """
    # Build raw_evidence from the raw record
    raw_evidence = raw.model_dump()
    
    # Parse posted_at from created field
    posted_at = None
    if raw.created:
        try:
            posted_at = datetime.fromisoformat(raw.created.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass
    
    # Build skills list from category and contract info
    skills = []
    if raw.category and raw.category.label:
        skills.append(raw.category.label)
    if raw.contract_type:
        skills.append(raw.contract_type)
    if raw.contract_time:
        skills.append(raw.contract_time)
    
    # Determine work_mode from contract_time and remote indicators
    work_mode = None
    if raw.contract_time:
        if "remote" in raw.contract_time.lower():
            work_mode = "remote"
        elif "hybrid" in raw.contract_time.lower():
            work_mode = "hybrid"
        elif "full" in raw.contract_time.lower() or "part" in raw.contract_time.lower():
            work_mode = "on_site"
    
    # Map contract_type to employment_type
    employment_type = None
    if raw.contract_type:
        ct = raw.contract_type.lower()
        if "permanent" in ct or "full" in ct:
            employment_type = "full_time"
        elif "contract" in ct:
            employment_type = "contract"
        elif "part" in ct:
            employment_type = "part_time"
        elif "temporary" in ct or "temp" in ct:
            employment_type = "temporary"
        elif "intern" in ct:
            employment_type = "intern"
    
    # Location display name
    location = raw.location.display_name if raw.location else None
    
    # Company name
    company = raw.company.display_name if raw.company else None
    
    # Description - use Adzuna's snippet
    description = raw.description
    
    # Requirements - not directly provided by Adzuna, but we can infer from description
    requirements = None
    
    return JobCreate(
        adzuna_id=raw.id,
        title=raw.title,
        company=company,
        location=location,
        work_mode=work_mode,
        employment_type=employment_type,
        salary_min=raw.salary_min,
        salary_max=raw.salary_max,
        salary_currency="USD",  # Adzuna typically uses local currency
        salary_is_predicted=raw.salary_is_predicted,
        description=description,
        requirements=requirements,
        skills=skills,
        redirect_url=raw.redirect_url,
        posted_at=posted_at,
        raw_evidence=raw_evidence,
        passed_prefilter=False,  # Will be set by pre-filter later
    )


def _normalize_string(s: str) -> str:
    """Normalize string for comparison: lowercase, strip, collapse whitespace."""
    if not s:
        return ""
    # Lowercase, strip, collapse multiple spaces
    normalized = re.sub(r'\s+', ' ', s.strip().lower())
    # Remove common punctuation that doesn't affect identity
    normalized = re.sub(r'[^\w\s]', '', normalized)
    return normalized


def dedup_key(job: JobCreate) -> Tuple[str, ...]:
    """Generate deduplication key for a job.
    
    Returns a tuple that can be used for exact matching.
    Priority order:
    1. Adzuna ID (primary)
    2. Redirect URL (normalized)
    3. Composite key: normalized title + company + location
    
    Args:
        job: JobCreate to generate key for
        
    Returns:
        Tuple representing the deduplication key
    """
    # Key 1: Adzuna ID (most reliable)
    if job.adzuna_id:
        return ("adzuna_id", job.adzuna_id)
    
    # Key 2: Redirect URL (normalized)
    if job.redirect_url:
        normalized_url = _normalize_string(job.redirect_url)
        if normalized_url:
            return ("redirect_url", normalized_url)
    
    # Key 3: Composite key
    title_norm = _normalize_string(job.title)
    company_norm = _normalize_string(job.company) if job.company else ""
    location_norm = _normalize_string(job.location) if job.location else ""
    
    if title_norm:
        composite = f"{title_norm}|{company_norm}|{location_norm}"
        return ("composite", composite)
    
    # Fallback: empty key (should not happen for valid jobs)
    return ("unknown", "")


def is_duplicate(existing: Job, new: JobCreate) -> bool:
    """Check if a new job duplicates an existing one.
    
    Checks in priority order:
    1. Adzuna ID match
    2. Redirect URL match (normalized)
    3. Composite key match (normalized title + company + location)
    
    Args:
        existing: Existing job in database
        new: New job to check
        
    Returns:
        True if duplicate, False otherwise
    """
    # Check 1: Adzuna ID
    if existing.adzuna_id and new.adzuna_id:
        if existing.adzuna_id == new.adzuna_id:
            return True
    
    # Check 2: Redirect URL (normalized)
    if existing.redirect_url and new.redirect_url:
        if _normalize_string(existing.redirect_url) == _normalize_string(new.redirect_url):
            return True
    
    # Check 3: Composite key
    existing_composite = _normalize_string(existing.title)
    if existing.company:
        existing_composite += f"|{_normalize_string(existing.company)}"
    if existing.location:
        existing_composite += f"|{_normalize_string(existing.location)}"
    
    new_composite = _normalize_string(new.title)
    if new.company:
        new_composite += f"|{_normalize_string(new.company)}"
    if new.location:
        new_composite += f"|{_normalize_string(new.location)}"
    
    if existing_composite and existing_composite == new_composite:
        return True
    
    return False


def merge_job_data(existing: Job, new: JobCreate) -> Dict[str, Any]:
    """Merge new job data into existing job, preserving non-null values.
    
    For deduplication: when a duplicate is found, update the existing job
    with any new non-null fields from the new job, but never overwrite
    existing non-null values with null.
    
    Args:
        existing: Existing job from database
        new: New job data from Adzuna
        
    Returns:
        Dictionary of fields to update
    """
    updates = {}
    new_data = new.model_dump()
    
    # Fields that can be updated if new has value and existing doesn't
    updatable_fields = [
        "title", "company", "location", "work_mode", "employment_type",
        "salary_min", "salary_max", "salary_currency", "salary_is_predicted",
        "description", "requirements", "skills", "redirect_url", "posted_at",
        "raw_evidence",
    ]
    
    for field in updatable_fields:
        new_value = new_data.get(field)
        existing_value = getattr(existing, field, None)
        
        # Only update if new has a value and existing doesn't (or is different for evidence)
        if new_value is not None:
            if field == "raw_evidence":
                # Always update evidence with latest
                updates[field] = new_value
            elif existing_value is None:
                updates[field] = new_value
            elif field in ["salary_min", "salary_max"] and existing_value != new_value:
                # Update salary if it changed (Adzuna might have corrected it)
                updates[field] = new_value
    
    return updates