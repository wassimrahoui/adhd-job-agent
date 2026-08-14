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
- Not an autonomous "apply to 200 jobs while I sleep" bot. Automation stops at preparation; submission is always a human act.
- Not a resume-writing or career-coaching product, beyond what's needed to support matching and application prep.
- Not a guarantee of finding every job, or a perfect matcher. It is a triage and evidence tool, not an oracle.
- Not a system that trusts its own AI's self-reported success. See ADR-002.

## Functional requirements

1. Discover jobs from one or more configured sources (API-based where available, page-based/browser-automation otherwise).
2. Extract the original job content and preserve it (text, and where useful, source URL and raw HTML/DOM snapshot) as evidence.
3. Normalize source-specific job data into one canonical job schema.
4. Deduplicate jobs discovered from the same or different sources.
5. Maintain a user profile: CV/resume data, skills, preferences, exclusions, salary and location constraints.
6. Run deterministic matching (title, skills, location, salary, work mode, employment type, exclusions) against the user profile.
7. Run local LLM analysis for semantic aspects deterministic rules can't capture (transferable skills, nuanced requirements, missing-information flags, plain-language explanation).
8. Validate every LLM response against a strict schema; reject and flag anything malformed or unsupported by the source text.
9. Verify LLM factual claims (salary, location, remote status, requirements, deadlines, etc.) against the stored evidence before showing them to the user; label each claim Verified / Inferred / Unknown.
10. Present jobs, match reasoning, and evidence in an ADHD-friendly interface: one clear next action, minimal choices per screen.
11. Let the user save, dismiss, or approve a job, and move it through an explicit application lifecycle.
12. Support browser automation to *prepare* an application (fill forms, stage data) but require explicit user confirmation before any submission.
13. Track applications and their status changes with a full audit history.
14. Monitor a connected mailbox for application-related email (confirmations, interview invites, rejections, recruiter messages) and associate detected events with the right application, without ever deleting mail or acting on instructions embedded in it.
15. Notify the user of what needs attention (new high-fit jobs, application follow-ups needed, detected email events) without becoming another noisy inbox.
16. Log every important system action (AI calls, matches, status transitions, automation steps, submissions) for audit and debugging.

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
User opens the app. The home screen shows: how many new jobs were found overnight, how many are strong matches awaiting review, and any application that needs a follow-up today. The user reviews one job at a time: title, company, the deterministic match factors, the AI's plain-language explanation (with Verified/Inferred/Unknown labels), and a clear "why" tied back to the original posting. They approve, save for later, or dismiss — three big obvious actions, nothing else competing for attention.

### Journey 2 — Preparing an application
User approves a job. The system stages an application: pulls relevant CV sections, drafts application material, and (where a browser-automation adapter exists for that source) navigates to the application form and fills it in a controlled browser session. Nothing is submitted. The user reviews the filled form and the staged materials, then explicitly confirms submission — or cancels and applies manually.

### Journey 3 — Tracking after applying
A week later, an email arrives inviting the user to interview. The email-monitoring subsystem detects it, links it to the existing application, and updates the suggested-next-status to "Interview" — but does not silently change the tracked status without the user seeing and confirming the detected event on their dashboard.

### Journey 4 — Trusting the score
User sees a job scored as a strong match. They tap into "why," see the deterministic factors (skills matched, location compatible, salary in range) and the AI's semantic notes, each traceable to a highlighted excerpt in the original posting. Where the posting doesn't mention something (e.g., remote policy), the system says so explicitly rather than guessing.

## What "done" looks like for a healthy system

A user should be able to trust every number and claim shown to them enough to *not* have to re-read the original posting to double check it — because the system already did that verification and shows its work.
