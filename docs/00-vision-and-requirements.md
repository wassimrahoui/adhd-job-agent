# Vision, Goals, and Requirements

## Vision

Job hunting is a long sequence of small, repetitive, high-friction tasks — search, read, compare, decide, track, follow up — each of which is easy to abandon under executive-dysfunction load. ADHD Job Agent exists to absorb the repetitive and easily-dropped parts (finding jobs, reading them carefully, comparing them against a CV, tracking status, noticing email updates) while keeping every consequential decision in the user's hands. It is a private, single-user assistant, not a SaaS product, not a job board, and not an autonomous applier.

## Goals

- Reduce the time and working-memory cost of finding jobs worth looking at.
- Make it obvious, at a glance, what needs attention right now and why.
- Explain *why* a job is or isn't a good match in terms the user can verify against the original posting, not a black-box score.
- Keep an honest, evidence-backed record of every job seen and every application made.
- Never let the user lose track of an application's status or a pending action.
- Do all of this with local inference, so the user's CV, career history, and job search activity never have to leave their own machine to a third-party AI vendor.

## Non-goals

- Not a multi-user or SaaS product. Single user, single deployment.
- Not a general-purpose job board or aggregator business.
- Not an autonomous "apply to 200 jobs while I sleep" bot, and not a system with any automated-submission capability at all, in MVP or any future phase. The user always applies manually, on the real employer/ATS page, and always personally clicks Submit/Apply (see `03-job-sources-and-browser-automation.md`).
- Not a resume-writing or career-coaching product, beyond what's needed to support matching and application prep.
- Not a guarantee of finding every job, or a perfect matcher. It is a triage and evidence tool, not an oracle.
- Not a system that trusts its own AI's self-reported success. See ADR-002.

## Functional requirements

1. Discover jobs via Adzuna's job-search API — the sole, mandatory MVP source of job facts, queried deterministically from the user's profile. The AI Job Agent (the system as a whole) drives the end-to-end search-to-relevance loop, but the LLM component itself never originates, searches for, or invents a job — Adzuna is the exclusive source of job data (see `03-job-sources-and-browser-automation.md`, ADR-004).
2. Preserve exactly what Adzuna returned (structured fields, description snippet, redirect URL) as evidence.
3. Normalize source-specific job data into one canonical job schema.
4. Deduplicate jobs discovered from the same or different sources.
5. Maintain a user profile as the central matching input, with explicit field categories: work experience, technical skills, cybersecurity/networking experience, education, certifications, languages, desired roles, location preferences, salary requirements, remote/hybrid/on-site preference, and experience level. Anything not present in the profile/CV is treated as `UNKNOWN` for matching purposes, never assumed.
6. Run a cheap deterministic pre-filter (title, skills, location, salary, work mode, employment type, exclusions) against the user profile before any job reaches the LLM, then a deterministic matching engine for the same factors.
7. Run local LLM analysis to compare each pre-filtered job against the user's profile/CV, producing a relevance score, recommendation, and evidence-based explanation — including named matching skills, matching experience, and missing requirements — for semantic aspects deterministic rules can't capture (transferable skills, nuanced requirements, missing-information flags, plain-language explanation).
8. Validate every LLM response against a strict schema; reject and flag anything malformed or unsupported by the source text.
9. Verify LLM factual claims (salary, location, remote status, requirements, deadlines, etc.) against the stored evidence before showing them to the user; label each claim Verified / Inferred / Unknown.
10. Apply a configurable relevance-score threshold cutoff so only jobs at or above the threshold are shown as relevant matches.
11. Present jobs, match reasoning, and evidence in an ADHD-friendly interface: one clear next action, minimal choices per screen.
12. Let the user save, dismiss, or approve a job, and move it through an explicit application lifecycle that ends in the user manually applying on the original source page — never an automated submission.
13. Optionally (post-MVP, opt-in only) help fill an application form's fields with verified CV data after the user explicitly requests assistance on a specific application, never automatically and never touching the final Submit/Apply action (`03-job-sources-and-browser-automation.md`).
14. Track applications and their status changes with a full audit history.
15. (Post-MVP) Monitor a connected mailbox for application-related email (confirmations, interview invites, rejections, recruiter messages) and associate detected events with the right application, without ever deleting mail or acting on instructions embedded in it.
16. Notify the user of what needs attention (new high-fit jobs, application follow-ups needed, detected email events) without becoming another noisy inbox.
17. Log every important system action (AI calls, matches, status transitions, user application actions) for audit and debugging.

## Non-functional requirements

- **Privacy**: CV, profile, job history, and application data belong to one user and must never be sent to a third-party AI API in production operation.
- **Reliability over speed**: a slower, verified answer beats a fast, unverified one everywhere in this system.
- **Local-first**: the core loop (discover → analyze → review) must keep working with no internet access to any AI provider, using local Ollama; only job-source fetching and the optional email connector require external network access.
- **Auditability**: every AI output, every match decision, and every state transition must be reconstructable after the fact from the audit log and evidence store.
- **Resilience to source drift**: job pages and ATS layouts change; extraction failures must be visible errors, not silent bad data.
- **Resilience to hostile input**: job descriptions and emails are untrusted external text and must never be able to make the system take an action, reveal data, or change its own rules.
- **Low operational complexity**: runnable by one technically capable user on a single machine (or small self-hosted box) via Docker, without standing up a fleet of services.
- **Extensibility**: new job sources, new local models, and new ATS targets must be addable without rewriting the core pipeline.

## Primary user journeys

### Journey 1 — Morning triage
User opens the app. The home screen shows: how many new jobs were found overnight, how many are strong matches awaiting review, and any application that needs a follow-up today. The user reviews one job at a time: title, company, the deterministic match factors, the AI's plain-language explanation (with per-claim FACT/INFERENCE/UNKNOWN labels), and a clear "why" tied back to the original posting. They approve, save for later, or dismiss — three big obvious actions, nothing else competing for attention.

### Journey 2 — Preparing an application
User approves a job. The system optionally stages reference materials: relevant CV sections, a drafted cover letter. The user reviews these (or skips straight past them), then clicks through to the job's original source URL and applies manually, themselves, on the employer/ATS page — filling the form, uploading documents, and clicking Submit with their own hands. Nothing in this system fills or submits that form on their behalf. (Post-MVP, once on that page, the user may optionally click "Assist Me" to get verified-CV-data field suggestions — they still click Submit themselves.) The user then returns to the app and marks the application "Applied."

### Journey 3 — Tracking after applying
A week later, an email arrives inviting the user to interview. The email-monitoring subsystem detects it, links it to the existing application, and updates the suggested-next-status to "Interview" — but does not silently change the tracked status without the user seeing and confirming the detected event on their dashboard.

### Journey 4 — Trusting the score
User sees a job scored as a strong match. They tap into "why," see the deterministic factors (skills matched, location compatible, salary in range) and the AI's semantic notes, each traceable to a highlighted excerpt in the original posting. Where the posting doesn't mention something (e.g., remote policy), the system says so explicitly rather than guessing.

## What "done" looks like for a healthy system

A user should be able to trust every number and claim shown to them enough to *not* have to re-read the original posting to double check it — because the system already did that verification and shows its work.
