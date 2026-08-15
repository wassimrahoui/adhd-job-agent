from __future__ import annotations

from app.filters.schemas import (
    FilterResult,
    FilterReason,
    PreFilterJobInput,
    PreFilterProfileInput,
    PreFilterConfig,
)


def filter_excluded_keywords(
    job: PreFilterJobInput,
    profile: PreFilterProfileInput,
    config: PreFilterConfig,
) -> FilterReason:
    excluded_keywords = profile.excluded_keywords

    if not excluded_keywords:
        return FilterReason(
            filter_name="excluded_keywords",
            result=FilterResult.PASS,
            reason="No excluded keywords specified",
        )

    job_text_parts = []
    if job.title:
        job_text_parts.append(job.title)
    if job.company:
        job_text_parts.append(job.company)
    if job.description:
        job_text_parts.append(job.description)
    if job.requirements:
        job_text_parts.append(job.requirements)
    if job.skills:
        job_text_parts.extend(job.skills)

    job_text = " ".join(job_text_parts)

    if config.keyword_match_case_sensitive:
        search_text = job_text
        keywords = excluded_keywords
    else:
        search_text = job_text.lower()
        keywords = [kw.lower() for kw in excluded_keywords]

    matched_keywords = []
    for keyword in keywords:
        if keyword in search_text:
            matched_keywords.append(keyword)

    if matched_keywords:
        return FilterReason(
            filter_name="excluded_keywords",
            result=FilterResult.FAIL,
            reason=f"Job contains excluded keywords: {', '.join(matched_keywords)}",
            details={"matched_keywords": matched_keywords},
        )

    return FilterReason(
        filter_name="excluded_keywords",
        result=FilterResult.PASS,
        reason="No excluded keywords found in job",
        details={"checked_keywords": excluded_keywords},
    )