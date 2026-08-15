from __future__ import annotations

from app.schemas.analysis import AnalysisInput, AnalysisJobInput, AnalysisProfileInput


def build_analysis_prompt(input_data: AnalysisInput) -> str:
    """Build deterministic prompt for AI analysis from job and profile data.
    
    No invented facts - only uses evidence from job and profile.
    All evidence must remain traceable to source.
    """
    job = input_data.job
    profile = input_data.profile

    sections = []

    # System instruction
    sections.append("""You are an expert job match analyst. Analyze how well the candidate's profile matches the job requirements.

Rules:
1. ONLY use information explicitly provided in the job and profile data below
2. DO NOT invent qualifications, skills, or experiences not present in the data
3. For each claim, cite the source excerpt from the provided data
4. If information is missing, mark as UNKNOWN rather than assuming
5. Output valid JSON matching the specified schema

Return a JSON object with these fields:
- score (0-100 or null): Overall match score
- recommendation: "strong_match" | "possible_match" | "weak_match" | "not_enough_information"
- confidence: "high" | "medium" | "low"
- matching_skills: [{claim, source_excerpt}]
- matching_experience: [{claim, source_excerpt}]
- missing_requirements: [{claim, source_excerpt}]
- unknown_requirements: [{claim, source_excerpt}]
- explanation: 2-4 sentence plain language summary
- evidence: [{claim, source_excerpt}]
- status: "success" | "rejected" | "failed"

""")

    # Job section
    sections.append("=== JOB DATA ===")
    sections.append(f"Title: {job.title}")
    if job.company:
        sections.append(f"Company: {job.company}")
    if job.location:
        sections.append(f"Location: {job.location}")
    if job.work_mode:
        sections.append(f"Work Mode: {job.work_mode}")
    if job.employment_type:
        sections.append(f"Employment Type: {job.employment_type}")
    if job.salary_min or job.salary_max:
        salary_parts = []
        if job.salary_min:
            salary_parts.append(f"min: {job.salary_min}")
        if job.salary_max:
            salary_parts.append(f"max: {job.salary_max}")
        if job.salary_currency:
            salary_parts.append(f"currency: {job.salary_currency}")
        sections.append(f"Salary: {', '.join(salary_parts)}")
        if job.salary_is_predicted:
            sections.append("(Salary is predicted by source)")
    if job.description:
        sections.append(f"Description: {job.description[:2000]}")
    if job.requirements:
        sections.append(f"Requirements: {job.requirements[:2000]}")
    if job.skills:
        sections.append(f"Skills: {', '.join(job.skills)}")

    # Profile section
    sections.append("\n=== CANDIDATE PROFILE ===")
    if profile.work_experience:
        sections.append(f"Work Experience: {profile.work_experience}")
    if profile.technical_skills:
        sections.append(f"Technical Skills: {', '.join(profile.technical_skills)}")
    if profile.networking_experience:
        sections.append(f"Networking/Cybersecurity/Sysadmin Experience: {profile.networking_experience}")
    if profile.education:
        sections.append(f"Education: {profile.education}")
    if profile.certifications:
        sections.append(f"Certifications: {', '.join(profile.certifications)}")
    if profile.languages:
        sections.append(f"Languages: {', '.join(profile.languages)}")
    if profile.desired_roles:
        sections.append(f"Desired Roles: {', '.join(profile.desired_roles)}")
    if profile.location_preferences:
        sections.append(f"Location Preferences: {', '.join(profile.location_preferences)}")
    if profile.salary_min or profile.salary_max:
        salary_parts = []
        if profile.salary_min:
            salary_parts.append(f"min: {profile.salary_min}")
        if profile.salary_max:
            salary_parts.append(f"max: {profile.salary_max}")
        salary_parts.append(f"currency: {profile.salary_currency}")
        sections.append(f"Salary Expectations: {', '.join(salary_parts)}")
    sections.append(f"Remote Preference: {profile.remote_preference}")
    sections.append(f"Experience Level: {profile.experience_level}")
    if profile.excluded_keywords:
        sections.append(f"Excluded Keywords: {', '.join(profile.excluded_keywords)}")
    if profile.resume_text:
        sections.append(f"Resume Text: {profile.resume_text[:3000]}")

    # Analysis instructions
    sections.append("""

=== ANALYSIS INSTRUCTIONS ===

For each category, provide claims with source excerpts:

1. MATCHING SKILLS: Skills from profile that appear in job requirements/description
   - claim: e.g., "Python"
   - source_excerpt: exact quote from job showing this requirement AND from profile showing candidate has it

2. MATCHING EXPERIENCE: Experience from profile that matches job requirements
   - claim: e.g., "5 years backend API development"
   - source_excerpt: exact quotes supporting this

3. MISSING REQUIREMENTS: Job requirements the profile does NOT demonstrate
   - claim: e.g., "Kubernetes orchestration"
   - source_excerpt: exact quote from job showing this requirement

4. UNKNOWN REQUIREMENTS: Job requirements the profile mentions nothing about
   - claim: e.g., "GraphQL API design"
   - source_excerpt: exact quote from job showing this requirement

5. EVIDENCE: Other factual matches (salary, location, remote, etc.)
   - claim: e.g., "Salary range matches expectations"
   - source_excerpt: supporting quotes

SCORING GUIDELINES:
- 80-100: Strong match - most requirements met, good skill/experience alignment
- 50-79: Possible match - some requirements met, gaps but not deal-breakers
- 20-49: Weak match - significant gaps, few requirements met
- 0-19: Not enough information - cannot determine fit

CONFIDENCE:
- high: Clear evidence for most claims
- medium: Some evidence, some assumptions
- low: Limited evidence, many unknowns

RECOMMENDATION:
- strong_match: score >= 80, high confidence
- possible_match: score 50-79
- weak_match: score 20-49
- not_enough_information: score < 20 or insufficient data

Output ONLY valid JSON.
""")

    return "\n".join(sections)