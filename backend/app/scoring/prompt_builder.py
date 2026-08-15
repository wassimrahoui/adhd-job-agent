from __future__ import annotations

from app.schemas.scoring import ScoringInput, ScoringConfig


def build_scoring_prompt(input_data: ScoringInput, config: ScoringConfig) -> str:
    """Build deterministic prompt for AI scoring from analysis and context data.
    
    No invented facts - only uses evidence from analysis and job/profile.
    All evidence must remain traceable to source.
    """
    sections = []

    # System instruction
    sections.append("""You are an expert job match scorer. Calculate a precise match score (0-100) based on the evidence provided.

Rules:
1. ONLY use information explicitly provided in the data below
2. DO NOT invent qualifications, skills, or experiences not present in the data
3. For each score component, cite the source evidence
4. If information is missing, score that component as 50 (neutral) rather than assuming
5. Output valid JSON matching the specified schema

SCORING COMPONENTS (weights from config):
""")

    weights = config.weights
    sections.append(f"- Skills Match: {weights.skills_weight*100:.0f}% - How well do profile skills match job requirements?")
    sections.append(f"- Experience Match: {weights.experience_weight*100:.0f}% - How well does experience match job level/type?")
    sections.append(f"- Requirements Coverage: {weights.requirements_weight*100:.0f}% - What fraction of requirements are met vs missing vs unknown?")
    sections.append(f"- Location Match: {weights.location_weight*100:.0f}% - Does job location match profile preferences?")
    sections.append(f"- Salary Match: {weights.salary_weight*100:.0f}% - Does job salary meet profile expectations?")

    sections.append("""

Return a JSON object with these fields:
- model_used: string (will be filled by system)
- score: integer 0-100 (weighted composite)
- recommendation: "strong_match" | "possible_match" | "weak_match" | "not_enough_information"
- confidence: "high" | "medium" | "low"
- skills_score: integer 0-100
- experience_score: integer 0-100
- requirements_score: integer 0-100
- location_score: integer 0-100
- salary_score: integer 0-100
- explanation: 2-4 sentence plain language summary
- evidence: [{claim, source_excerpt}]
- status: "success" | "rejected" | "failed"

RECOMMENDATION THRESHOLDS:
- strong_match: score >= 80
- possible_match: score 50-79
- weak_match: score 20-49
- not_enough_information: score < 20

CONFIDENCE:
- high: Clear evidence for most claims, >= 3 evidence items
- medium: Some evidence, some assumptions
- low: Limited evidence, many unknowns

Output ONLY valid JSON.
""")

    # Analysis evidence section
    sections.append("=== ANALYSIS EVIDENCE ===")

    if input_data.matching_skills:
        sections.append("MATCHING SKILLS:")
        for item in input_data.matching_skills:
            source = f" [{item.source_excerpt}]" if item.source_excerpt else ""
            sections.append(f"  - {item.claim}{source}")

    if input_data.matching_experience:
        sections.append("\nMATCHING EXPERIENCE:")
        for item in input_data.matching_experience:
            source = f" [{item.source_excerpt}]" if item.source_excerpt else ""
            sections.append(f"  - {item.claim}{source}")

    if input_data.missing_requirements:
        sections.append("\nMISSING REQUIREMENTS:")
        for item in input_data.missing_requirements:
            source = f" [{item.source_excerpt}]" if item.source_excerpt else ""
            sections.append(f"  - {item.claim}{source}")

    if input_data.unknown_requirements:
        sections.append("\nUNKNOWN REQUIREMENTS:")
        for item in input_data.unknown_requirements:
            source = f" [{item.source_excerpt}]" if item.source_excerpt else ""
            sections.append(f"  - {item.claim}{source}")

    if input_data.evidence:
        sections.append("\nOTHER EVIDENCE:")
        for item in input_data.evidence:
            source = f" [{item.source_excerpt}]" if item.source_excerpt else ""
            sections.append(f"  - {item.claim}{source}")

    if input_data.explanation:
        sections.append(f"\nANALYSIS EXPLANATION: {input_data.explanation}")

    # Job context
    sections.append("\n=== JOB CONTEXT ===")
    sections.append(f"Title: {input_data.job_title}")
    if input_data.job_company:
        sections.append(f"Company: {input_data.job_company}")
    if input_data.job_location:
        sections.append(f"Location: {input_data.job_location}")
    if input_data.job_work_mode:
        sections.append(f"Work Mode: {input_data.job_work_mode}")
    if input_data.job_salary_min or input_data.job_salary_max:
        salary_parts = []
        if input_data.job_salary_min:
            salary_parts.append(f"min: {input_data.job_salary_min}")
        if input_data.job_salary_max:
            salary_parts.append(f"max: {input_data.job_salary_max}")
        if input_data.job_salary_currency:
            salary_parts.append(f"currency: {input_data.job_salary_currency}")
        sections.append(f"Salary: {', '.join(salary_parts)}")
        if input_data.job_salary_is_predicted:
            sections.append("(Salary is predicted by source)")
    if input_data.job_skills:
        sections.append(f"Required Skills: {', '.join(input_data.job_skills)}")

    # Profile context
    sections.append("\n=== PROFILE CONTEXT ===")
    if input_data.profile_desired_roles:
        sections.append(f"Desired Roles: {', '.join(input_data.profile_desired_roles)}")
    if input_data.profile_location_preferences:
        sections.append(f"Location Preferences: {', '.join(input_data.profile_location_preferences)}")
    if input_data.profile_salary_min or input_data.profile_salary_max:
        salary_parts = []
        if input_data.profile_salary_min:
            salary_parts.append(f"min: {input_data.profile_salary_min}")
        if input_data.profile_salary_max:
            salary_parts.append(f"max: {input_data.profile_salary_max}")
        salary_parts.append(f"currency: {input_data.profile_salary_currency}")
        sections.append(f"Salary Expectations: {', '.join(salary_parts)}")
    sections.append(f"Remote Preference: {input_data.profile_remote_preference}")
    sections.append(f"Experience Level: {input_data.profile_experience_level}")

    # Scoring instructions
    sections.append("""

=== SCORING INSTRUCTIONS ===

For each component, provide score 0-100 with reasoning:

1. SKILLS SCORE: % of job skills matched by profile skills
   - 100: All required skills present
   - 75: Most required skills present
   - 50: About half matched
   - 25: Few matched
   - 0: None matched

2. EXPERIENCE SCORE: Alignment of experience level and type
   - 100: Exact match on level and relevant domain
   - 75: Close level, relevant domain
   - 50: Reasonable match
   - 25: Some relevant experience
   - 0: No relevant experience

3. REQUIREMENTS SCORE: Coverage of job requirements
   - 100: All requirements met, none missing
   - 75: Most met, few missing
   - 50: Half met, half missing/unknown
   - 25: Few met, many missing
   - 0: None met

4. LOCATION SCORE: Job location vs profile preferences
   - 100: Exact match (city or remote when preferred)
   - 75: Same region/country
   - 50: Different city, same country
   - 25: Different country, remote possible
   - 0: No match, on-site required but remote preferred

5. SALARY SCORE: Job salary vs expectations
   - 100: Job range fully within expectations
   - 75: Job range overlaps well
   - 50: Partial overlap
   - 25: Minimal overlap
   - 0: No overlap / below minimum

Calculate weighted composite score using config weights.
""")

    return "\n".join(sections)