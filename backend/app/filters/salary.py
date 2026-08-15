from __future__ import annotations

from app.filters.schemas import (
    FilterResult,
    FilterReason,
    PreFilterJobInput,
    PreFilterProfileInput,
    PreFilterConfig,
)


def filter_salary(
    job: PreFilterJobInput,
    profile: PreFilterProfileInput,
    config: PreFilterConfig,
) -> FilterReason:
    job_salary_min = job.salary_min
    job_salary_max = job.salary_max
    profile_salary_min = profile.salary_min
    profile_salary_max = profile.salary_max

    if job_salary_min is None and job_salary_max is None:
        if config.unknown_salary_behavior == "pass":
            return FilterReason(
                filter_name="salary",
                result=FilterResult.PASS,
                reason="Job salary not specified, treating as pass per config",
            )
        elif config.unknown_salary_behavior == "fail":
            return FilterReason(
                filter_name="salary",
                result=FilterResult.FAIL,
                reason="Job salary not specified",
            )
        else:
            return FilterReason(
                filter_name="salary",
                result=FilterResult.UNKNOWN,
                reason="Job salary not specified",
            )

    if profile_salary_min is None and profile_salary_max is None:
        return FilterReason(
            filter_name="salary",
            result=FilterResult.PASS,
            reason="No salary preference specified",
        )

    if config.salary_compare_mode == "min_only":
        return _filter_salary_min_only(job, profile)
    elif config.salary_compare_mode == "max_only":
        return _filter_salary_max_only(job, profile)
    else:
        return _filter_salary_range_overlap(job, profile)


def _filter_salary_min_only(
    job: PreFilterJobInput,
    profile: PreFilterProfileInput,
) -> FilterReason:
    job_salary_min = job.salary_min
    job_salary_max = job.salary_max
    profile_salary_min = profile.salary_min

    if job_salary_min is not None:
        effective_job_min = job_salary_min
    elif job_salary_max is not None:
        effective_job_min = job_salary_max
    else:
        return FilterReason(
            filter_name="salary",
            result=FilterResult.UNKNOWN,
            reason="Job salary not specified",
        )

    if profile_salary_min is not None:
        if effective_job_min >= profile_salary_min:
            return FilterReason(
                filter_name="salary",
                result=FilterResult.PASS,
                reason=f"Job minimum salary {effective_job_min} meets preferred minimum {profile_salary_min}",
                details={"job_min": effective_job_min, "profile_min": profile_salary_min},
            )
        else:
            return FilterReason(
                filter_name="salary",
                result=FilterResult.FAIL,
                reason=f"Job minimum salary {effective_job_min} below preferred minimum {profile_salary_min}",
                details={"job_min": effective_job_min, "profile_min": profile_salary_min},
            )

    return FilterReason(
        filter_name="salary",
        result=FilterResult.PASS,
        reason="No minimum salary preference",
    )


def _filter_salary_max_only(
    job: PreFilterJobInput,
    profile: PreFilterProfileInput,
) -> FilterReason:
    job_salary_min = job.salary_min
    job_salary_max = job.salary_max
    profile_salary_max = profile.salary_max

    if job_salary_max is not None:
        effective_job_max = job_salary_max
    elif job_salary_min is not None:
        effective_job_max = job_salary_min
    else:
        return FilterReason(
            filter_name="salary",
            result=FilterResult.UNKNOWN,
            reason="Job salary not specified",
        )

    if profile_salary_max is not None:
        if effective_job_max <= profile_salary_max:
            return FilterReason(
                filter_name="salary",
                result=FilterResult.PASS,
                reason=f"Job maximum salary {effective_job_max} within preferred maximum {profile_salary_max}",
                details={"job_max": effective_job_max, "profile_max": profile_salary_max},
            )
        else:
            return FilterReason(
                filter_name="salary",
                result=FilterResult.FAIL,
                reason=f"Job maximum salary {effective_job_max} exceeds preferred maximum {profile_salary_max}",
                details={"job_max": effective_job_max, "profile_max": profile_salary_max},
            )

    return FilterReason(
        filter_name="salary",
        result=FilterResult.PASS,
        reason="No maximum salary preference",
    )


def _filter_salary_range_overlap(
    job: PreFilterJobInput,
    profile: PreFilterProfileInput,
) -> FilterReason:
    job_salary_min = job.salary_min
    job_salary_max = job.salary_max
    profile_salary_min = profile.salary_min
    profile_salary_max = profile.salary_max

    if job_salary_min is not None and job_salary_max is not None:
        job_min, job_max = job_salary_min, job_salary_max
    elif job_salary_min is not None:
        job_min, job_max = job_salary_min, job_salary_min
    elif job_salary_max is not None:
        job_min, job_max = job_salary_max, job_salary_max
    else:
        return FilterReason(
            filter_name="salary",
            result=FilterResult.UNKNOWN,
            reason="Job salary not specified",
        )

    if profile_salary_min is not None and profile_salary_max is not None:
        profile_min, profile_max = profile_salary_min, profile_salary_max
    elif profile_salary_min is not None:
        profile_min, profile_max = profile_salary_min, profile_salary_min
    elif profile_salary_max is not None:
        profile_min, profile_max = profile_salary_max, profile_salary_max
    else:
        return FilterReason(
            filter_name="salary",
            result=FilterResult.PASS,
            reason="No salary preference specified",
        )

    overlap_min = max(job_min, profile_min)
    overlap_max = min(job_max, profile_max)

    if overlap_min <= overlap_max:
        return FilterReason(
            filter_name="salary",
            result=FilterResult.PASS,
            reason=f"Salary ranges overlap: job [{job_min}-{job_max}], profile [{profile_min}-{profile_max}]",
            details={"job_min": job_min, "job_max": job_max, "profile_min": profile_min, "profile_max": profile_max},
        )
    else:
        return FilterReason(
            filter_name="salary",
            result=FilterResult.FAIL,
            reason=f"Salary ranges do not overlap: job [{job_min}-{job_max}], profile [{profile_min}-{profile_max}]",
            details={"job_min": job_min, "job_max": job_max, "profile_min": profile_min, "profile_max": profile_max},
        )