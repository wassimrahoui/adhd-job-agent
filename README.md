# ADHD Job Agent

A private, single-user, ADHD-friendly AI job-hunting assistant. It finds jobs, extracts and preserves the original source evidence, normalizes and deduplicates listings, compares them against your CV and preferences, uses **local** AI (Ollama) to analyze fit, verifies every AI claim against the original job data, and presents a simple, low-overload interface for you to review, approve, and track applications. It never submits an application without your explicit approval, and it never trusts an AI's word that something happened without independently checking.

**Status: architecture and specification only. No application code has been written yet.** This repository is the blueprint another engineer or coding agent should follow to implement the system.

## Start here

1. [`docs/00-vision-and-requirements.md`](docs/00-vision-and-requirements.md) — why this exists, what it must and must not do, user journeys.
2. [`docs/01-architecture-overview.md`](docs/01-architecture-overview.md) — components, responsibilities, data flow, overall system diagram, security boundaries.
3. [`docs/02-ai-and-matching-architecture.md`](docs/02-ai-and-matching-architecture.md) — the AI pipeline, hybrid matching/scoring, evidence and hallucination controls, LLM/model strategy.
4. [`docs/03-job-sources-and-browser-automation.md`](docs/03-job-sources-and-browser-automation.md) — Adzuna as the sole MVP source, extraction, Playwright automation, and the application-safety flow.
5. [`docs/04-application-lifecycle-and-email.md`](docs/04-application-lifecycle-and-email.md) — the 11-state application lifecycle, audit trail, email monitoring.
6. [`docs/05-adhd-ux.md`](docs/05-adhd-ux.md) — UX principles and screen-by-screen design intent.
7. [`docs/06-database-design.md`](docs/06-database-design.md) — schema, ownership, ER diagram.
8. [`docs/07-api-design.md`](docs/07-api-design.md) — API surface and conventions.
9. [`docs/08-security-and-prompt-injection.md`](docs/08-security-and-prompt-injection.md) — auth, isolation, defenses against malicious job/email content.
10. [`docs/09-testing-strategy.md`](docs/09-testing-strategy.md) — what gets tested and how, including adversarial cases.
11. [`docs/10-deployment-and-dev-workflow.md`](docs/10-deployment-and-dev-workflow.md) — target hardware, technology choices, deployment, development workflow (OpenCode, not Claude).
12. [`docs/11-mvp-and-roadmap.md`](docs/11-mvp-and-roadmap.md) — MVP scope, detailed exclusions, and phased roadmap.
13. [`docs/12-architecture-decisions.md`](docs/12-architecture-decisions.md) — the ten ADRs (ADR-001–ADR-010), and where/why this design departs from the two prior prototypes.
14. [`docs/13-risks-and-mitigations.md`](docs/13-risks-and-mitigations.md) — known risks and how the design addresses them.
15. [`docs/14-model-evaluation.md`](docs/14-model-evaluation.md) — the exact target hardware budget and the one pinned local model chosen against it.

**Status note:** this is a proposed architecture only. No application source code exists in this repository, and none should be written from it without Wassim's explicit approval — the design phase being complete is not authorization to begin implementation.

## The ten non-negotiable rules

These govern every decision in this repository. See `docs/12-architecture-decisions.md` (ADR-001–ADR-010) for the full rationale.

1. **No Claude in the product.** Claude (or any cloud LLM) is never a runtime dependency of the Job Agent.
2. **No coordinator.** The multi-agent dev-tooling coordinator from prototype 1 is development infrastructure only and is not part of this product's architecture.
3. **Local AI first.** Production inference runs on one pinned local Ollama model (`docs/14-model-evaluation.md`). No cloud LLM fallback. The system works with Ollama unreachable (degraded, not fake).
4. **Coding agent ≠ product AI.** Development may use OpenCode; the product always uses Ollama. These are never conflated.
5. **Don't trust the LLM.** Adzuna's structured fields and the original posting text are the only authority on job facts. The LLM interprets; it does not originate facts.
6. **Structured AI output, always validated.** Every AI response is schema-checked, per-claim (FACT/INFERENCE/UNKNOWN); malformed or suspicious output is rejected, not patched over.
7. **Evidence first.** Every AI claim must trace back to an Adzuna field or the source text. Unverifiable claims are labeled `UNKNOWN`, never invented.
8. **Human approval.** The AI recommends. The user decides on anything that matters.
9. **No automatic applications.** Browser automation may prepare an application; only the user can submit it. Every irreversible action stops, shows the user, and waits (`READY_FOR_USER`).
10. **Security and privacy by design.** CV, profile, and application data are private, access-controlled, and never leave the user's infrastructure to a third-party AI provider.

A specific, hard corollary of rules 5 and 8 governs job discovery: **Adzuna searches for jobs; the AI does not.** All job search/discovery is a deterministic Adzuna API call — the LLM has no search or tool-calling capability over any job source, and Adzuna's structured fields are authoritative over any conflicting AI claim. See `docs/03-job-sources-and-browser-automation.md` and ADR-004.

## Where prototypes influenced this design

- From `job-search-ai-prototype`: the canonical job model, evidence-first mindset, structured-AI-output discipline, local Ollama requirement, Playwright-based extraction, and the hard lesson that an AI (or coding agent) can *claim* an action succeeded when it did not — this is now a permanent architectural rule (ADR-002; see `docs/08-security-and-prompt-injection.md` and `docs/09-testing-strategy.md`). The coordinator was deliberately excluded (ADR-001).
- From `test-code`: the ADHD-friendly React UI structure, the application pipeline concept, Postgres + row-level security data isolation, and private resume storage. Its mocked job source, its AI "demo fallback" (confirmed by inspecting `supabase/functions/ai-job-analysis/index.ts`), and its lack of independent verification of AI claims were identified as weaknesses and are not carried forward as designed (ADR-004, ADR-006).
