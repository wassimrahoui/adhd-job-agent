# Architecture Decision Records

Exactly ten ADRs govern this design. Where a prototype's existing approach conflicted with the ten non-negotiable rules in the README, the rule wins.

## ADR-001: Exclude the coordinator entirely

**Context**: Prototype 1 built a coordinator — a file-based message broker letting Claude Code and OpenCode hand off development tasks to each other, with its own tests and evidence.

**Decision**: The coordinator is not part of this project in any form, including a redesigned or renamed version. It was development infrastructure for a specific multi-agent experiment, not a Job Agent component.

**Rationale**: Rule 2 is explicit and absolute. The coordinator does not map to any requirement in `00-vision-and-requirements.md`. The one genuinely valuable lesson it produced (never trust a self-reported "done") is preserved as a standing principle in ADR-002, not as the machinery that surfaced it.

## ADR-002: Never trust a self-reported action; always independently verify

**Context**: During prototype 1's development, an OpenCode-driven coding agent fabricated a tool call — it reported success without the action occurring.

**Decision**: No component in this system (AI analysis, browser automation, email monitoring, or any future component) may have its own claim of success treated as sufficient evidence that something happened. Every consequential action requires an independent check: a database read-back, a DOM state check, a schema-and-evidence-verified claim, or a user attestation logged as a distinct fact from the automation's own output.

**Rationale**: This generalizes a real, observed failure mode into a permanent rule, and is the direct mechanism behind rules 5, 6, 7, and 9, and behind the FACT/INFERENCE/UNKNOWN claim schema in `02-ai-and-matching-architecture.md`.

## ADR-003: Python/FastAPI backend, React/TypeScript frontend, PostgreSQL

**Context**: Prototype 1 built a mature Python pipeline (Pydantic models, Ollama client, Playwright automation, evidence recording) but no user-facing product. Prototype 2 built a polished React frontend and a Postgres/Supabase data layer, but mocked its job source and gave its AI layer only shallow JSON-shape validation (confirmed by direct inspection of `supabase/functions/ai-job-analysis/index.ts`: it validates types but never checks a claim against the source job text).

**Decision**: Python/FastAPI backend, React/TypeScript frontend, PostgreSQL — connected by a REST API the backend owns.

**Rationale**: Each prototype already proved out the harder half of what it built; rewriting either in the other's language would discard real, tested work for no architectural benefit.

## ADR-004: Adzuna is the sole, mandatory MVP job source; the AI does not search for jobs

**Context**: Prototype 2 shipped with seeded mock job postings, explicitly because live job-source integration was out of scope. Prototype 1 never reached a general job-discovery source at all (it targeted a single ATS for extraction proof only). Neither prototype establishes a real, general-purpose job-discovery source.

**Decision**: Adzuna's REST API is the sole job source for MVP — a hard requirement, not one option among several. All search/discovery is a deterministic Adzuna API call built from the user's profile by code; the LLM has no search or tool-calling capability over Adzuna or any job source, ever. Wherever Adzuna provides a structured field, it is authoritative over any conflicting AI claim.

**Rationale**: This directly satisfies "the AI does not search for jobs, Adzuna searches for jobs," and gives the system a real, structured, rate-limited, authoritative source of job facts from day one instead of prototype 2's demo pool or a fragile general-purpose scraper. See `03-job-sources-and-browser-automation.md` for the full connector design.

## ADR-005: Self-hosted Supabase building blocks, not hosted Supabase

**Context**: Prototype 2 used Supabase's hosted cloud platform directly.

**Decision**: Use only the self-hostable, open-source parts of Supabase — Postgres, GoTrue, Storage — run via Docker Compose on the user's own infrastructure. No hosted Supabase cloud, no Edge Functions, no Realtime.

**Rationale**: Rule 10 and the deployment requirements call for self-hosting and low vendor lock-in; business logic lives in the FastAPI backend (ADR-003) rather than Supabase Edge Functions, further reducing platform coupling.

## ADR-006: No AI "demo fallback" in production; AI-unavailable is an honest degraded state instead

**Context**: Prototype 2's edge functions transparently fell back to a fabricated "demo analysis" (`is_mock: true`, confirmed in source) whenever Ollama was unreachable, so the UI would always show *something*.

**Decision**: When Ollama is unreachable, or the exactly-pinned model tag (`14-model-evaluation.md`) is not present, AI-dependent fields are marked `AI_UNAVAILABLE` and the UI shows the deterministic match result alone — no fabricated analysis is generated or shown, labeled or not, and the system never auto-pulls or silently substitutes a different model.

**Rationale**: Direct consequence of "reliability over speed" and rule 5 applied one level up — a system that manufactures plausible fake output by design, even labeled, undermines the entire evidence-first value proposition.

## ADR-007: Single deployable backend, not microservices

**Context**: Neither prototype was a distributed system, and the spec never asks for one.

**Decision**: One FastAPI service contains all backend components, organized as clearly bounded internal modules rather than separate deployed services.

**Rationale**: A single user does not need independent scaling per component; splitting into services now would add operational overhead without benefit, especially given the shared-hardware constraint in ADR-009/`14-model-evaluation.md` where the whole point is *fewer* competing processes, not more.

## ADR-008: Application lifecycle as an 11-state model, separated from the deterministic ingestion pipeline

**Context**: The first version of this spec used one overloaded job-status field for both pipeline mechanics and user journey, and carried a redundant `saved_jobs` table alongside it.

**Decision**: Two separate state machines: `jobs.status` (deterministic pipeline only: `DISCOVERED, NORMALIZED, DUPLICATE, MATCHED, ERROR`) and `applications.status` (the user-facing 11-state lifecycle: `SAVED, REVIEWED, APPROVED, PREPARING, READY_FOR_USER, APPLYING, APPLIED, INTERVIEW, OFFER, REJECTED, WITHDRAWN`), with `READY_FOR_USER` as the Stop→Show→Wait→Continue gate materialized as a real, persisted state.

**Rationale**: Conflating pipeline mechanics with user journey made the first version's model harder to reason about and created redundant storage (`saved_jobs` duplicating what "an application in SAVED status" already means). Splitting them is simpler, not more complex — each state machine now has exactly one owner (code vs. user/automation/email).

## ADR-009: Exactly one local model, pinned by exact tag, chosen against real hardware, manually managed

**Context**: The product must run local AI on Wassim's real, shared machine (Ryzen 9 9950X, RTX 5070 Ti 16GB VRAM, 32GB system RAM shared with other software) — not an abstract "a capable local model" placeholder.

**Decision**: `qwen2.5:14b-instruct-q4_K_M` is the pinned model (full evaluation in `14-model-evaluation.md`). The application checks for this exact tag before any AI call and never auto-pulls, auto-upgrades, or silently substitutes a different installed model. Model management is entirely manual (`ollama pull ...`), performed by Wassim.

**Rationale**: A model choice made only against generic hardware assumptions risks either not fitting the real GPU (forcing slow CPU offload) or being wrong for the actual shared-RAM situation; pinning an exact, verified tag with a hard "missing = error, not silent substitution" contract keeps the system honest about what it's actually running, consistent with ADR-002's broader "never let a claim substitute for verification."

## ADR-010: LLM concurrency is low and queued; cheap deterministic filtering runs before anything reaches the model

**Context**: The target machine shares its 16GB GPU and 32GB RAM with other active software (OpenCode, Docker, browser, OS). Sending many job analyses to Ollama at once, or sending every discovered job to the LLM regardless of obvious deterministic mismatch, would both threaten that shared budget and contradict the "reliability over speed" principle by turning inference into a resource race.

**Decision**: AI analysis runs through a bounded, low-concurrency queue (default concurrency = 1, small configurable ceiling never intended to enable parallel-blasting Ollama), and every job passes a cheap, pure-code pre-filter (exclusion keywords, required-skill floor, location/salary compatibility) before it is ever eligible to be queued for LLM analysis at all.

**Rationale**: This is a hardware-reality-driven architectural constraint, not a tunable performance knob to be relaxed later without re-justifying it against the actual shared-machine budget in `14-model-evaluation.md`.
