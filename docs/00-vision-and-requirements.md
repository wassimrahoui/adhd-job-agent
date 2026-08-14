# Vision, Goals, and Requirements

## Vision

Job hunting is a long sequence of small, repetitive, high-friction tasks — search, read, compare, decide — each of which is easy to abandon under executive-dysfunction load. ADHD Job Agent exists to absorb the repetitive and easily-dropped parts (finding jobs, reading them carefully, comparing them against a CV) while keeping every consequential decision in the user's hands. It is a private, single-user AI job-discovery and job-relevance assistant: the user clicks "Search Jobs," the app finds jobs via Adzuna, scores them against the user's CV/profile with an evidence-based explanation, and shows the user the relevant ones along with their original application link. **That is the whole product.** It is not a SaaS product, not a job board, not an application tracker, and not an autonomous applier.

## Goals

- Reduce the time and working-memory cost of finding jobs worth looking at.
- Make it obvious, at a glance, what needs attention right now and why.
- Explain *why* a job is or isn't a good match in terms the user can verify against the original posting, not a black-box score.
- Do all of this with local inference, so the user's CV, career history, and job search activity never have to leave their own machine to a third-party AI vendor.
- Keep the system itself simple and boring: one database file, one local model, one job processed at a time. Complexity is added only when a real, demonstrated problem requires it.

## Non-goals

- Not a multi-user or SaaS product. Single user, single deployment, no authentication service.
- Not a general-purpose job board or aggregator business.
- Not an autonomous "apply to jobs while I sleep" bot, and not a system with any application-submission capability at all. The user always applies manually, on the real employer/ATS page, and always personally clicks Submit/Apply — the system's involvement ends at showing the user a relevant job and its original application link (see `03-job-sources.md`).
- Not an application tracker. This project does not record application status, application history, or any post-click outcome. The user tracks their own applications elsewhere, outside this system.
- Not an email monitor. This project does not read, classify, or act on the user's mailbox.
- Not a resume-writing or career-coaching product, beyond what's needed to support matching.
- Not a guarantee of finding every job, or a perfect matcher. It is a discovery and evidence tool, not an oracle.
- Not a system that trusts its own AI's self-reported success. See ADR-002.
- Not an automatically scheduled background service for the MVP. Job search is a deliberate user action, not a cron job.
- Not built on a heavier data/infrastructure stack than a single-user local tool needs — no Postgres, no self-hosted Supabase, no message queue, no worker pool, unless a real, demonstrated requirement later justifies one.

## Functional requirements

1. Let the user trigger a job search explicitly ("Search Jobs") — no automatic scheduler in the MVP.
2. Discover jobs via Adzuna's job-search API — the sole job-fact source, queried deterministically from the user's profile. The AI never searches for, originates, or invents a job (see `03-job-sources.md`, ADR-004).
3. Preserve exactly what Adzuna returned (structured fields, description snippet, redirect URL) as evidence, stored alongside the normalized job.
4. Normalize source-specific job data into one canonical job schema.
5. Deduplicate jobs discovered from the same or different sources.
6. Maintain a user profile as the central matching input, with explicit field categories: work experience, technical skills, networking experience, cybersecurity experience, sysadmin experience, education, certifications, languages, desired roles, location preferences, salary requirements, remote/hybrid/on-site preference, and experience level. Anything not present in the profile/CV is treated as `UNKNOWN`/not demonstrated for matching purposes, never assumed.
7. Run a cheap deterministic pre-filter (title, required keywords, technical skills, location, salary, employment type, remote/hybrid/on-site, experience level, configured exclusions) against the user profile before any job reaches the analysis model. This is a simple, fixed set of checks — not a configurable weighting framework.
8. For each job that survives the pre-filter, send a compact, relevant subset of the job data and the candidate profile to the single configured local Ollama model, one job at a time, to evaluate semantic compatibility and produce a relevance score, recommendation, and evidence-based explanation — including named matching skills, matching experience, missing requirements, and unknown requirements.
9. Validate every AI response against a strict schema; reject anything malformed or unsupported by the source text and retry once if appropriate.
10. Verify AI factual claims against the supplied job/CV data before showing them to the user; unsupported claims become `UNKNOWN`/`NOT_DEMONSTRATED`, never invented.
11. Apply a relevance-score threshold cutoff so only jobs at or above the threshold are shown as relevant matches.
12. Present jobs, match reasoning, and evidence in an ADHD-friendly interface: one clear next action, minimal choices per screen.
13. Show the user the job's original Adzuna application link (`redirect_url`), clearly and prominently, for every relevant job. The user clicks it and applies manually, entirely outside the app. That click is where this system's responsibility ends.

## Non-functional requirements

- **Privacy**: CV, profile, and job-search activity belong to one user and must never be sent to a third-party AI API in production operation.
- **Reliability over speed**: a slower, verified answer beats a fast, unverified one everywhere in this system.
- **Local-first**: the core loop (search → analyze → review) must keep working with no internet access to any AI provider, using local Ollama; only Adzuna requires external network access.
- **Resilience to source drift**: Adzuna's response shape can change; extraction failures must be visible errors, not silent bad data.
- **Untrusted input handling, kept simple**: job descriptions are external text and are treated as data only — never as instructions to the model, and the model has no tool access that could act on anything it reads (see `02-ai-and-matching-architecture.md`). This is a modest, practical precaution, not a dedicated security subsystem.
- **Low operational complexity**: runnable by one technically capable user on a single machine via Docker, with a single SQLite database file and no fleet of services.
- **Low resource usage**: the app must not attempt to consume all available RAM/VRAM; one Ollama request in flight at a time, compact per-job context, no duplicate or simultaneously loaded models (see `10-deployment-and-dev-workflow.md`, `14-model-evaluation.md`).
- **Extensibility**: new job sources and new local analysis models must be addable without rewriting the core pipeline — but nothing is built ahead of an actual need.

## Primary user journeys

### Journey 1 — Searching and reviewing
User opens the app and clicks "Search Jobs." The app queries Adzuna, normalizes and deduplicates the results, runs the deterministic pre-filter, and sends the survivors to the local Ollama model one at a time. When it finishes, the user sees a results list: title, company, location, salary when available, relevance score, recommendation, and a short explanation for each job. The user opens one job at a time for the full picture — the deterministic factors, the AI's evidence-based explanation (matching skills, matching experience, missing requirements, unknown requirements), and the original application link.

### Journey 2 — Reviewing and applying
User opens a relevant job's detail page. They see the original job information, matching skills, matching experience, missing requirements, unknown requirements, evidence, the AI's explanation, the score, and the original Adzuna application link. They click that link, which opens the employer/ATS page in their own browser, and apply manually. The system does nothing further — it does not track what happens next.

### Journey 3 — Trusting the score
User sees a job scored as a strong match. They open its detail page and see the deterministic factors (skills matched, location compatible, salary in range) alongside the AI's semantic notes, each traceable to the job text or CV it came from. Where the posting doesn't mention something (e.g., remote policy), the system says so explicitly (`UNKNOWN`) rather than guessing.

## What "done" looks like for a healthy system

A user should be able to trust every number and claim shown to them enough to *not* have to re-read the original posting to double check it — because the system already did that verification and shows its work — and then get out to the real application page with one click.
