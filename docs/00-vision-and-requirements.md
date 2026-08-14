# Vision, Goals, and Requirements

## Vision

Job hunting is a long sequence of small, repetitive, high-friction tasks — search, read, compare, decide — each of which is easy to abandon under executive-dysfunction load. ADHD Job Agent exists to absorb the repetitive and easily-dropped parts (finding jobs, reading them carefully, comparing them against a CV) while keeping every consequential decision in the user's hands. It is a private, single-user AI job-discovery and job-relevance assistant: it finds jobs via Adzuna, scores them against the user's CV/profile with an evidence-based explanation, and shows the user the relevant ones along with their original application link. **That is the whole product.** It is not a SaaS product, not a job board, not an application tracker, and not an autonomous applier.

## Goals

- Reduce the time and working-memory cost of finding jobs worth looking at.
- Make it obvious, at a glance, what needs attention right now and why.
- Explain *why* a job is or isn't a good match in terms the user can verify against the original posting, not a black-box score.
- Do all of this with local inference, so the user's CV, career history, and job search activity never have to leave their own machine to a third-party AI vendor.

## Non-goals

- Not a multi-user or SaaS product. Single user, single deployment.
- Not a general-purpose job board or aggregator business.
- Not an autonomous "apply to jobs while I sleep" bot, and not a system with any application-submission capability at all. The user always applies manually, on the real employer/ATS page, and always personally clicks Submit/Apply — the system's involvement ends at showing the user a relevant job and its original application link (see `03-job-sources.md`).
- Not an application tracker. This project does not record application status, application history, or any post-click outcome. The user tracks their own applications elsewhere, outside this system.
- Not an email monitor. This project does not read, classify, or act on the user's mailbox.
- Not a resume-writing or career-coaching product, beyond what's needed to support matching.
- Not a guarantee of finding every job, or a perfect matcher. It is a discovery and evidence tool, not an oracle.
- Not a system that trusts its own AI's self-reported success. See ADR-002.

## Functional requirements

1. Discover jobs via Adzuna's job-search API — the sole job-fact source, queried deterministically from the user's profile. The AI never searches for, originates, or invents a job (see `03-job-sources.md`, ADR-004).
2. Preserve exactly what Adzuna returned (structured fields, description snippet, redirect URL) as evidence.
3. Normalize source-specific job data into one canonical job schema.
4. Deduplicate jobs discovered from the same or different sources.
5. Maintain a user profile as the central matching input, with explicit field categories: work experience, technical skills, networking experience, cybersecurity experience, sysadmin experience, education, certifications, languages, desired roles, location preferences, salary requirements, remote/hybrid/on-site preference, and experience level. Anything not present in the profile/CV is treated as `UNKNOWN`/not demonstrated for matching purposes, never assumed.
6. Run a cheap deterministic pre-filter (title, required keywords, technical skills, location, salary, employment type, remote/hybrid/on-site, experience level, configured exclusions) against the user profile before any job reaches the large analysis model.
7. Run the large local Ollama analysis model to compare each pre-filtered job against the user's profile/CV, producing a relevance score, recommendation, and evidence-based explanation — including named matching skills, matching experience, missing requirements, and unknown requirements.
8. Validate every AI response against a strict schema; reject and flag anything malformed or unsupported by the source text.
9. Verify AI factual claims (salary, location, remote status, requirements, etc.) against the stored evidence before showing them to the user; label each claim FACT / INFERENCE / UNKNOWN.
10. Apply a configurable relevance-score threshold cutoff so only jobs at or above the threshold are shown as relevant matches.
11. Present jobs, match reasoning, and evidence in an ADHD-friendly interface: one clear next action, minimal choices per screen.
12. Let the user save or dismiss a discovered job for later review — a simple bookmark, not a status/lifecycle object.
13. Show the user the job's original Adzuna application link (`redirect_url`), clearly and prominently, for every relevant job. The user clicks it and applies manually, entirely outside the app. That click is where this system's responsibility ends.
14. Log every AI call and every Adzuna call for audit and debugging.

## Non-functional requirements

- **Privacy**: CV, profile, and job-search activity belong to one user and must never be sent to a third-party AI API in production operation.
- **Reliability over speed**: a slower, verified answer beats a fast, unverified one everywhere in this system.
- **Local-first**: the core loop (discover → analyze → review) must keep working with no internet access to any AI provider, using local Ollama; only Adzuna requires external network access.
- **Auditability**: every AI output and every match decision must be reconstructable after the fact from the audit log and evidence store.
- **Resilience to source drift**: Adzuna's response shape can change; extraction failures must be visible errors, not silent bad data.
- **Untrusted input handling, kept simple**: job descriptions are external text and are treated as data only — never as instructions to the model, and the model has no tool access that could act on anything it reads (see `02-ai-and-matching-architecture.md`). This is a modest, practical precaution, not a dedicated security subsystem.
- **Low operational complexity**: runnable by one technically capable user on a single machine (or small self-hosted box) via Docker, without standing up a fleet of services.
- **Extensibility**: new job sources and new local analysis models must be addable without rewriting the core pipeline.

## Primary user journeys

### Journey 1 — Morning triage
User opens the app. The home screen shows how many new jobs were found overnight and how many are relevant matches awaiting review. The user reviews one job at a time: title, company, the deterministic match factors, the AI's plain-language explanation (with per-claim FACT/INFERENCE/UNKNOWN labels), and a clear "why" tied back to the original posting. They save it for later or dismiss it — two big obvious actions, nothing else competing for attention.

### Journey 2 — Reviewing and applying
User opens a relevant job's detail page. They see the deterministic factor breakdown, the AI's evidence-based explanation of matching skills, matching experience, missing requirements, and unknown requirements, and the original Adzuna application link. They click that link, which opens the employer/ATS page in their own browser, and apply manually. The system does nothing further — it does not track what happens next.

### Journey 3 — Trusting the score
User sees a job scored as a strong match. They tap into "why," see the deterministic factors (skills matched, location compatible, salary in range) and the AI's semantic notes, each traceable to a highlighted excerpt in the original posting. Where the posting doesn't mention something (e.g., remote policy), the system says so explicitly rather than guessing.

## What "done" looks like for a healthy system

A user should be able to trust every number and claim shown to them enough to *not* have to re-read the original posting to double check it — because the system already did that verification and shows its work — and then get out to the real application page with one click.
