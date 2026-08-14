# Architecture Decision Records

## ADR-000: The ten non-negotiable rules govern every other decision

**Decision**: Rules 1–10 in the README are treated as constraints, not preferences. Every ADR below is written to be consistent with them; where a prototype's existing design conflicted with one of these rules, the rule wins and the prototype's approach is not carried forward.

## ADR-001: Exclude the coordinator entirely

**Context**: Prototype 1 built a coordinator — a file-based message broker letting Claude Code and OpenCode hand off development tasks to each other, with its own tests and evidence.

**Decision**: The coordinator is not part of this project in any form, including a redesigned or renamed version. It was development infrastructure for a specific multi-agent experiment, not a Job Agent component.

**Rationale**: Rule 2 is explicit and absolute. The coordinator also does not map to any requirement in `00-vision-and-requirements.md` — the product does not need two coding agents negotiating with each other at runtime. The one genuinely valuable lesson it produced (never trust a self-reported "done") is preserved as a standing architectural principle (ADR-002), not as the machinery that surfaced it.

## ADR-002: Never trust a self-reported action; always independently verify

**Context**: During prototype 1's development, an OpenCode-driven coding agent fabricated a tool call — it reported success without the action occurring.

**Decision**: No component in this system (AI analysis, browser automation, email monitoring, or any future component) may have its own claim of success treated as sufficient evidence that something happened. Every consequential action requires an independent check: a database read-back, a DOM state check, a schema-and-evidence-verified claim, or a user attestation logged as a distinct fact from the automation's own output.

**Rationale**: This generalizes a real, observed failure mode from software agents into a permanent rule, and it is the direct mechanism behind rules 5, 6, 7, and 9.

## ADR-003: Python/FastAPI backend, React/TypeScript frontend, PostgreSQL

**Context**: Prototype 1 built a mature Python pipeline (Pydantic models, CSV store, Ollama client, Playwright/SuccessFactors automation, evidence recording) but no user-facing product. Prototype 2 built a polished React frontend and a Postgres/Supabase data layer, but mocked its job source and gave its AI layer only shallow JSON-shape validation.

**Decision**: Take prototype 1's language and pipeline logic for the backend (Python/FastAPI), and prototype 2's frontend stack and data-isolation pattern (React/TypeScript, Postgres + RLS) for the client and storage layer, connected by a REST API the backend owns.

**Rationale**: Each prototype already proved out the harder half of what it built. Rewriting prototype 1's pipeline in TypeScript, or prototype 2's UI in Python, would throw away real, tested work for no architectural benefit — the two layers communicate over HTTP/JSON regardless of implementation language, so there's no polyglot cost beyond running two runtimes, which Docker Compose handles cleanly.

## ADR-004: No mocked job source in the target architecture; MVP ships with one real connector, not a mock pool

**Context**: Prototype 2 shipped with seeded mock job postings shared across all authenticated users, explicitly because live job-source integration was out of scope for that prototype.

**Decision**: The target architecture's job-source layer is built around the real adapter interface from day one (`03-job-sources-and-browser-automation.md`); MVP includes at least one real connector. Fixtures are used for testing, not as the running system's actual job pool, and are never presented to the user as real listings.

**Rationale**: A demo/mock job pool cannot be matched against a real CV with real consequences and is explicitly flagged in the spec as insufficient for the final system.

## ADR-005: Self-hosted Supabase building blocks, not hosted Supabase

**Context**: Prototype 2 used Supabase's hosted cloud platform directly.

**Decision**: Use only the self-hostable, open-source parts of Supabase — Postgres, GoTrue, Storage — run via Docker Compose on the user's own infrastructure. No use of hosted Supabase cloud or Supabase-cloud-only features (Edge Functions, Realtime).

**Rationale**: Rule 10 and the deployment requirements call for self-hosting and low vendor lock-in; the business logic also moves into the FastAPI backend (ADR-003) rather than Supabase Edge Functions, which further reduces platform coupling. See `10-deployment-and-dev-workflow.md` for exactly which parts are used and the self-hosting compatibility note.

## ADR-006: No AI "demo fallback" in production; AI-unavailable is an honest degraded state instead

**Context**: Prototype 2's edge functions transparently fell back to a fabricated "demo analysis" (labeled `is_mock`) whenever Ollama was unreachable, so the UI would always show *something*.

**Decision**: When Ollama is unreachable, AI-dependent fields are marked `AI_UNAVAILABLE` and the UI shows the deterministic match result alone with a clear "AI analysis unavailable" state — no fabricated analysis is generated or shown, labeled or not.

**Rationale**: This is a direct consequence of "reliability over speed" and "truth over producing an answer" from the spec's final principle, and of rule 5 (don't trust the LLM) applied one level up — a system that manufactures plausible-looking fake output by design, even clearly labeled, trains the user to skim past labels over time, and risks a labeling bug silently becoming a hallucination bug. Prototype 2's `is_mock` flag was a reasonable choice for a demo product; it is not the right choice for a system whose entire value proposition is trustworthy evidence-backed claims.

## ADR-007: Single deployable backend, not microservices

**Context**: Neither prototype was a distributed system, and the spec never asks for one.

**Decision**: One FastAPI service contains all backend components (discovery, matching, AI orchestration, evidence/verification, application tracking, email monitoring), organized as clearly bounded internal modules rather than separate deployed services.

**Rationale**: A single user does not need independent scaling per component; splitting into services now would add operational overhead (more containers, network calls, failure modes) without a corresponding benefit, contradicting the "simplest architecture that can reliably accomplish the requirements" instruction. The module boundaries mirror the component table in `01-architecture-overview.md` closely enough that a future split, if ever genuinely needed, would not require a redesign.

## ADR-008: Application state model synthesized from both prototypes, not copied from either

**Context**: Prototype 1's V1 spec used discovery/evaluation-oriented statuses (`DISCOVERED, NORMALIZED, DUPLICATE, EVALUATED, MATCHED, REJECTED, REVIEW_REQUIRED, REVIEWED, ERROR`) with no application-submission states at all (explicitly out of V1 scope). Prototype 2 used a post-application pipeline (`SAVED, PREPARING, APPLIED, SCREENING, INTERVIEW, OFFER, REJECTED, WITHDRAWN`) with no discovery/evaluation states, and treated "Applied" as a manual user toggle.

**Decision**: Combine both into one continuous lifecycle (`04-application-lifecycle-and-email.md`), covering discovery through outcome, with `Preparing`/`Applying` made explicit (rather than prototype 2's implicit manual toggle) so the Stop→Show→Wait→Continue gate has a real place to live in the state machine. `Screening` is dropped as a state the system has no reliable way to detect a transition into.

**Rationale**: Neither prototype's model alone covers the full journey in `00-vision-and-requirements.md`; synthesis was necessary, not optional.
