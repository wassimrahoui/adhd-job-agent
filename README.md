# ADHD Job Agent

A private, single-user AI job-discovery and job-relevance assistant, built with ADHD-friendly UX. It finds jobs via Adzuna, extracts and preserves the original source evidence, normalizes and deduplicates listings, runs them through cheap deterministic filtering, compares the survivors against your CV and preferences with a large local Ollama model, verifies every AI claim against the original job data, and shows you the relevant ones with an evidence-based explanation and the original application link. **That's the whole product.** You review the results and apply manually, on the real employer/ATS page, in your own browser — this system has no application-submission capability of any kind, and does not track what happens after you click through.

**Status: architecture and specification only. No application code has been written yet.** This repository is the blueprint another engineer or coding agent should follow to implement the system.

## Start here

1. [`docs/00-vision-and-requirements.md`](docs/00-vision-and-requirements.md) — why this exists, what it must and must not do, user journeys.
2. [`docs/01-architecture-overview.md`](docs/01-architecture-overview.md) — components, responsibilities, data flow, overall system diagram.
3. [`docs/02-ai-and-matching-architecture.md`](docs/02-ai-and-matching-architecture.md) — the AI pipeline, hybrid matching/scoring, evidence and hallucination controls, analysis-model vs. coding-model strategy.
4. [`docs/03-job-sources.md`](docs/03-job-sources.md) — Adzuna source design, the search-to-relevance flow, and where the system's involvement ends (the original application link).
5. [`docs/05-adhd-ux.md`](docs/05-adhd-ux.md) — UX principles and screen-by-screen design intent.
6. [`docs/06-database-design.md`](docs/06-database-design.md) — schema, ownership, ER diagram.
7. [`docs/07-api-design.md`](docs/07-api-design.md) — API surface and conventions.
8. [`docs/09-testing-strategy.md`](docs/09-testing-strategy.md) — what gets tested and how, including adversarial cases.
9. [`docs/10-deployment-and-dev-workflow.md`](docs/10-deployment-and-dev-workflow.md) — local/production deployment, technology choices, development workflow.
10. [`docs/11-mvp-and-roadmap.md`](docs/11-mvp-and-roadmap.md) — project scope and phased roadmap.
11. [`docs/12-architecture-decisions.md`](docs/12-architecture-decisions.md) — the ten ADRs (ADR-001–ADR-010).
12. [`docs/13-risks-and-mitigations.md`](docs/13-risks-and-mitigations.md) — known risks and how the design addresses them.
13. [`docs/14-model-evaluation.md`](docs/14-model-evaluation.md) — the exact target hardware budget and the current candidate local analysis model, pending real-hardware benchmark validation.
14. [`docs/15-development-process.md`](docs/15-development-process.md) — how implementation is planned, decomposed into EASY/MEDIUM/HARD tasks, executed, tested, committed, and tracked via `AGENT_TASKS.md` and a live progress dashboard, once implementation begins.

**Status note:** this is a proposed architecture only. No application source code exists in this repository, and none should be written from it without Wassim's explicit approval — the design phase being complete is not authorization to begin implementation.

## The non-negotiable rules

These govern every decision in this repository. See `docs/12-architecture-decisions.md` for the full rationale behind each.

1. **No Claude, no cloud LLM, in the product.** The finished application depends only on local Ollama for job/CV analysis. A coding agent (which may use any model, including Claude, during development) is a completely separate concern — see rule 4.
2. **No coordinator, no multi-agent architecture, anywhere.** Not in the product, not in the development process. A normal deterministic backend pipeline, and a coding agent working sequentially through a task list.
3. **Local AI first.** Production inference runs on local Ollama. No cloud LLM fallback. The system works with Ollama unreachable (degraded, not fake).
4. **Coding model ≠ analysis model.** A coding agent's model (if any) and the product's own Ollama analysis model are two separate roles, chosen for entirely different reasons, and never conflated.
5. **Don't trust the AI.** The original job posting/source and the user's own CV/profile are the only authorities on job and candidate facts. The AI interprets; it does not originate facts.
6. **Structured AI output, always validated.** Every AI response is schema-checked; malformed or suspicious output is rejected, not patched over.
7. **Evidence first.** Every AI claim must trace back to the original source text or the CV/profile. Unverifiable claims are labeled `UNKNOWN`, never invented.
8. **Adzuna is the sole job source.** The AI never searches the internet for jobs, never invents a job, and never discovers jobs independently. See `docs/03-job-sources.md` and ADR-004.
9. **No automatic applications, ever — full stop.** There is no application-submission capability anywhere in this system, in any form, under any name. No browser automation, no Playwright, no form-filling, no "Assist Me," no auto-click of Apply/Submit, no automatic document upload, no automatic answering of application questions. The system shows the user a relevant job and its original application link; the user does the rest, entirely outside the app.
10. **No application tracking.** This project does not implement an application database, application status, application lifecycle, application history, or email-based status monitoring. The user tracks their own applications elsewhere, outside this system.
11. **Simple architecture, kept simple.** No microservices, message queues, Kubernetes, distributed systems, or dedicated security subsystems. Untrusted job text is treated as data, not as a large adversarial-defense project (see `docs/02-ai-and-matching-architecture.md`).
12. **Security and privacy by design.** CV, profile, and job data are access-controlled and never leave the user's infrastructure to a third-party AI provider.

## Where prior prototypes influenced this design

- From `job-search-ai-prototype`: the canonical job model, evidence-first mindset, structured-AI-output discipline, the local Ollama requirement, and the hard lesson that an AI (or coding agent) can *claim* an action succeeded when it did not — this is now a permanent architectural rule (ADR-002).
- From `test-code`: the ADHD-friendly React UI structure and Postgres + row-level security data isolation. Its mocked job source and its AI "demo fallback" were identified as weaknesses and are not carried forward as designed (ADR-004, ADR-006).

Application tracking, browser automation, and email monitoring existed in earlier drafts of this project's own design and were subsequently removed as a deliberate scope decision (ADR-008) — they are not carried forward from either prototype and are not part of this project.
