# ADHD Job Agent

A private, single-user, ADHD-friendly AI job-hunting assistant. It finds jobs via Adzuna, extracts and preserves the original source evidence, normalizes and deduplicates listings, compares them against your CV and preferences, uses **local** AI (Ollama) to analyze fit, verifies every AI claim against the original job data, and presents a simple, low-overload interface for you to review, approve, and track applications. You always apply manually, on the real employer/ATS page, in your own browser — this system never submits an application on your behalf, in MVP or in any future phase — and it never trusts an AI's word that something happened without independently checking.

**Status: architecture and specification only. No application code has been written yet.** This repository is the blueprint another engineer or coding agent should follow to implement the system.

## Start here

1. [`docs/00-vision-and-requirements.md`](docs/00-vision-and-requirements.md) — why this exists, what it must and must not do, user journeys.
2. [`docs/01-architecture-overview.md`](docs/01-architecture-overview.md) — components, responsibilities, data flow, overall system diagram, security boundaries.
3. [`docs/02-ai-and-matching-architecture.md`](docs/02-ai-and-matching-architecture.md) — the AI pipeline, hybrid matching/scoring, evidence and hallucination controls, LLM/model strategy.
4. [`docs/03-job-sources-and-browser-automation.md`](docs/03-job-sources-and-browser-automation.md) — Adzuna source design, the search-to-relevance flow, and the manual-apply / opt-in "Assist Me" application flow.
5. [`docs/04-application-lifecycle-and-email.md`](docs/04-application-lifecycle-and-email.md) — application state machine, audit trail, email monitoring.
6. [`docs/05-adhd-ux.md`](docs/05-adhd-ux.md) — UX principles and screen-by-screen design intent.
7. [`docs/06-database-design.md`](docs/06-database-design.md) — schema, ownership, ER diagram.
8. [`docs/07-api-design.md`](docs/07-api-design.md) — API surface and conventions.
9. [`docs/08-security-and-prompt-injection.md`](docs/08-security-and-prompt-injection.md) — auth, isolation, defenses against malicious job/email content.
10. [`docs/09-testing-strategy.md`](docs/09-testing-strategy.md) — what gets tested and how, including adversarial cases.
11. [`docs/10-deployment-and-dev-workflow.md`](docs/10-deployment-and-dev-workflow.md) — local/production deployment, technology choices, development workflow (OpenCode, not Claude).
12. [`docs/11-mvp-and-roadmap.md`](docs/11-mvp-and-roadmap.md) — MVP scope and phased roadmap.
13. [`docs/12-architecture-decisions.md`](docs/12-architecture-decisions.md) — the ten ADRs (ADR-001–ADR-010), and where/why this design departs from the two prior prototypes.
14. [`docs/13-risks-and-mitigations.md`](docs/13-risks-and-mitigations.md) — known risks and how the design addresses them.
15. [`docs/14-model-evaluation.md`](docs/14-model-evaluation.md) — the exact target hardware budget and the current candidate local model, pending real-hardware benchmark validation.
16. [`docs/15-development-process.md`](docs/15-development-process.md) — how implementation is planned, decomposed into EASY/MEDIUM/HARD tasks, executed, tested, committed, and tracked via `AGENT_TASKS.md` and a live progress dashboard, once implementation begins.

**Status note:** this is a proposed architecture only. No application source code exists in this repository, and none should be written from it without Wassim's explicit approval — the design phase being complete is not authorization to begin implementation.

## The ten non-negotiable rules

These govern every decision in this repository. See `docs/12-architecture-decisions.md` (ADR-000) for the full rationale.

1. **No Claude in the product.** Claude (or any cloud LLM) is never a runtime dependency of the Job Agent.
2. **No coordinator.** The multi-agent dev-tooling coordinator from prototype 1 is development infrastructure only and is not part of this product's architecture.
3. **Local AI first.** Production inference runs on local Ollama. No cloud LLM fallback. The system works with Ollama unreachable (degraded, not fake).
4. **Coding agent ≠ product AI.** Development may use OpenCode; the product always uses Ollama. These are never conflated.
5. **Don't trust the LLM.** The original job posting/source is the only authority on job facts. The LLM interprets; it does not originate facts.
6. **Structured AI output, always validated.** Every AI response is schema-checked; malformed or suspicious output is rejected, not patched over.
7. **Evidence first.** Every AI claim must trace back to the original source text. Unverifiable claims are labeled "unknown," never invented.
8. **Human approval.** The AI recommends. The user decides on anything that matters.
9. **No automatic applications, ever — the user always applies manually.** There is no automated application-submission capability anywhere in this system, in MVP or any future phase. The user clicks through to the original job's source URL and applies themselves, on the real employer/ATS page, in their own browser — filling the form, uploading documents, and clicking Submit with their own hands. Post-MVP, an explicit, opt-in "Assist Me" helper may fill fields with verified CV data after the user specifically clicks to activate it for that one application, but it never activates itself, never invents an answer, and never touches the Submit/Apply control — that click is always the user's own. See `docs/03-job-sources-and-browser-automation.md`.
10. **Security and privacy by design.** CV, profile, and application data are private, access-controlled, and never leave the user's infrastructure to a third-party AI provider.

A specific, hard corollary of rules 5 and 8 governs job discovery: **Adzuna is the sole source of job facts; the LLM never originates or searches for a job.** The AI Job Agent as a whole does drive the end-to-end search-to-relevance loop (query building, pre-filtering, comparison, scoring), but every job fact traces back to a specific Adzuna API response, and the LLM component itself has no search or tool-calling capability over any job source — Adzuna's structured fields are always authoritative over any conflicting AI claim. See `docs/03-job-sources-and-browser-automation.md` and ADR-004.

## Where prototypes influenced this design

- From `job-search-ai-prototype`: the canonical job model, evidence-first mindset, structured-AI-output discipline, local Ollama requirement, Playwright-based extraction, and the hard lesson that an AI (or coding agent) can *claim* an action succeeded when it did not — this is now a permanent architectural rule (see `docs/08-security-and-prompt-injection.md` and `docs/09-testing-strategy.md`). The coordinator was deliberately excluded.
- From `test-code`: the ADHD-friendly React UI structure, the application pipeline concept, Postgres + row-level security data isolation, and private resume storage. Its mocked job source, its AI "demo fallback," and its lack of independent verification of AI claims were identified as weaknesses and are not carried forward as designed (see ADR-004, ADR-006).
