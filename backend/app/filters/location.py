from __future__ import annotations

from app.filters.schemas import (
    FilterResult,
    FilterReason,
    PreFilterJobInput,
    PreFilterProfileInput,
    PreFilterConfig,
)


def filter_location(
    job: PreFilterJobInput,
    profile: PreFilterProfileInput,
    config: PreFilterConfig,
) -> FilterReason:
    job_location = job.location
    profile_locations = profile.location_preferences

    if not job_location:
        if config.unknown_location_behavior == "pass":
            return FilterReason(
                filter_name="location",
                result=FilterResult.PASS,
                reason="Job location not specified, treating as pass per config",
            )
        elif config.unknown_location_behavior == "fail":
            return FilterReason(
                filter_name="location",
                result=FilterResult.FAIL,
                reason="Job location not specified",
            )
        else:
            return FilterReason(
                filter_name="location",
                result=FilterResult.UNKNOWN,
                reason="Job location not specified",
            )

    if not profile_locations:
        return FilterReason(
            filter_name="location",
            result=FilterResult.PASS,
            reason="No location preferences specified",
        )

    job_location_lower = job_location.lower()

    for pref_location in profile_locations:
        pref_lower = pref_location.lower()

        if config.location_match_mode == "exact":
            if job_location_lower == pref_lower:
                return FilterReason(
                    filter_name="location",
                    result=FilterResult.PASS,
                    reason=f"Location matches exactly: {pref_location}",
                    details={"matched_location": pref_location},
                )
        elif config.location_match_mode == "contains":
            if pref_lower in job_location_lower or job_location_lower in pref_lower:
                return FilterReason(
                    filter_name="location",
                    result=FilterResult.PASS,
                    reason=f"Location contains preference: {pref_location}",
                    details={"matched_location": pref_location},
                )
        elif config.location_match_mode == "any":
            return FilterReason(
                filter_name="location",
                result=FilterResult.PASS,
                reason="Any location accepted",
            )

    return FilterReason(
        filter_name="location",
        result=FilterResult.FAIL,
        reason=f"Location '{job_location}' does not match any preference",
        details={"job_location": job_location, "preferences": profile_locations},
    )