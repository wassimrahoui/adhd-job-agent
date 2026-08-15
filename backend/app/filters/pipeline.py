from __future__ import annotations

from app.filters.schemas import (
    FilterResult,
    FilterReason,
    PreFilterInput,
    PreFilterOutput,
    PreFilterConfig,
)
from app.filters.location import filter_location
from app.filters.salary import filter_salary
from app.filters.employment import filter_employment
from app.filters.keywords import filter_excluded_keywords


def run_pre_filter_pipeline(
    input_data: PreFilterInput,
    config: PreFilterConfig,
) -> PreFilterOutput:
    job = input_data.job
    profile = input_data.profile

    reasons = []
    matched_fields = {}

    location_reason = filter_location(job, profile, config)
    reasons.append(location_reason)
    if location_reason.result == FilterResult.PASS and location_reason.details:
        matched_fields.update(location_reason.details)

    salary_reason = filter_salary(job, profile, config)
    reasons.append(salary_reason)
    if salary_reason.result == FilterResult.PASS and salary_reason.details:
        matched_fields.update(salary_reason.details)

    employment_reason = filter_employment(job, profile, config)
    reasons.append(employment_reason)
    if employment_reason.result == FilterResult.PASS and employment_reason.details:
        matched_fields.update(employment_reason.details)

    keywords_reason = filter_excluded_keywords(job, profile, config)
    reasons.append(keywords_reason)
    if keywords_reason.result == FilterResult.PASS and keywords_reason.details:
        matched_fields.update(keywords_reason.details)

    overall_result = _determine_overall_result(reasons)

    return PreFilterOutput(
        overall_result=overall_result,
        reasons=reasons,
        matched_fields=matched_fields,
    )


def _determine_overall_result(reasons: list[FilterReason]) -> FilterResult:
    has_fail = any(r.result == FilterResult.FAIL for r in reasons)
    has_unknown = any(r.result == FilterResult.UNKNOWN for r in reasons)

    if has_fail:
        return FilterResult.FAIL
    elif has_unknown:
        return FilterResult.UNKNOWN
    else:
        return FilterResult.PASS