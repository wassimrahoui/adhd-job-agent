from __future__ import annotations

from app.filters.schemas import (
    FilterResult,
    FilterReason,
    PreFilterJobInput,
    PreFilterProfileInput,
    PreFilterConfig,
)


def filter_employment(
    job: PreFilterJobInput,
    profile: PreFilterProfileInput,
    config: PreFilterConfig,
) -> FilterReason:
    job_employment_type = job.employment_type
    job_work_mode = job.work_mode
    profile_remote_preference = profile.remote_preference

    employment_pass = True
    employment_reasons = []

    if config.employment_type_match_mode == "any" and config.work_mode_match_mode == "any":
        if not job_employment_type and not job_work_mode:
            return FilterReason(
                filter_name="employment",
                result=FilterResult.PASS,
                reason="Job employment type and work mode not specified",
            )
        return FilterReason(
            filter_name="employment",
            result=FilterResult.PASS,
            reason="Any employment type and work mode accepted",
        )

    if job_employment_type:
        if config.employment_type_match_mode == "exact":
            pass
    else:
        employment_reasons.append("Job employment type not specified")

    if job_work_mode and profile_remote_preference:
        work_mode_pass, work_mode_reason = _check_work_mode(job_work_mode, profile_remote_preference, config)
        if not work_mode_pass:
            employment_pass = False
        employment_reasons.append(work_mode_reason)
    elif job_work_mode:
        employment_reasons.append("Profile work mode preference not specified")
    elif profile_remote_preference and profile_remote_preference != "any":
        employment_reasons.append("Job work mode not specified")

    if employment_pass:
        return FilterReason(
            filter_name="employment",
            result=FilterResult.PASS,
            reason="; ".join(employment_reasons) if employment_reasons else "Employment criteria met",
            details={"employment_type": job_employment_type, "work_mode": job_work_mode},
        )
    else:
        return FilterReason(
            filter_name="employment",
            result=FilterResult.FAIL,
            reason="; ".join(employment_reasons),
            details={"employment_type": job_employment_type, "work_mode": job_work_mode},
        )


def _check_work_mode(
    job_work_mode: str,
    profile_remote_preference: str,
    config: PreFilterConfig,
) -> tuple[bool, str]:
    job_mode = job_work_mode.lower()
    profile_pref = profile_remote_preference.lower()

    if profile_pref == "any":
        return True, "Any work mode accepted"

    if config.work_mode_match_mode == "exact":
        if job_mode == profile_pref:
            return True, f"Work mode matches exactly: {profile_pref}"
        else:
            return False, f"Work mode '{job_mode}' does not match preferred '{profile_pref}'"
    else:
        if job_mode == profile_pref:
            return True, f"Work mode matches: {profile_pref}"
        elif profile_pref == "hybrid" and job_mode in ["remote", "on_site"]:
            return True, f"Hybrid preference accepts '{job_mode}'"
        elif profile_pref == "remote" and job_mode == "hybrid":
            return True, "Remote preference accepts hybrid"
        else:
            return False, f"Work mode '{job_mode}' does not match preferred '{profile_pref}'"