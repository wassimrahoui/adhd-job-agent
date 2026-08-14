# Architecture Decision Records

Exactly ten ADRs govern this design. Where a prior prototype's approach conflicted with the non-negotiable rules in the README, the rule wins.

## ADR-001: No coordinator, no multi-agent architecture

**Context**: An earlier prototype built a coordinator — a file-based message broker letting two coding agents hand off development tasks to each other.

**Decision**: No coordinator, supervisor/manager agent, worker-agent pool, or agent-swarm architecture exists anywhere in this project — not in the product, and not in the development tooling. The backend is a normal deterministic pipeline: Adzuna connector → normalization/dedup → deterministic filtering → sequential AI analysis → evidence check → results. Development tasks are executed sequentially against `AGENT_TASKS.md` (`15-development-process.md`), not orchestrated by a coordinating agent.

**Rationale**: The coordinator does not map to any requirement in `00-vision-and-requirements.md`. The one genuinely valuable lesson it produced (never trust a self-reported "done") is preserved as a standing principle in ADR-002, not as the machinery that surfaced it.

## ADR-002: Never trust a self-reported action; always independently verify

**Context**: During prior development, a coding agent fabricated a tool call — it reported success without the action occurring.

**Decision**: No *machine* component in this system (AI analysis, the coding agent itself) may have its own claim of success treated as sufficient evidence that something happened. Every consequential machine-originated claim requires an independent check: a database read-back, an evidence-checked claim, or a genuinely independent test run.

**Rationale**: This generalizes a real, observed failure mode into a permanent rule, and is the direct mechanism behind the evidence-verification step in `02-ai-and-matching-architecture.md` and the "verify before commit" discipline in `15-development-process.md`.

**Addendum — direct user actions are not self-reports.** This rule governs machines claiming things happened; it does not apply to the user's own direct actions, which are authoritative by definition and require no independent verification.

## ADR-003: Python/FastAPI backend, React/TypeScript frontend, SQLite

**Decision**: Python/FastAPI backend, React/TypeScript frontend, **SQLite** — connected by a REST API the backend owns.

**Rationale**: Pydantic gives first-class schema validation central to the evidence-checking requirement; React/TypeScript is a mature, well-understood stack for the small, fixed set of four screens this project needs; SQLite is a single local file with no server process, matching a single-user, single-machine deployment (see ADR-005).

## ADR-004: Adzuna is the sole job source; the AI never originates job data

**Decision**: Adzuna's REST API is the sole job source — a hard requirement, not one option among several. All search/discovery is a deterministic, user-triggered Adzuna API call built from the user's profile by code; the AI has no search or tool-calling capability over Adzuna or any job source, ever, and never decides which jobs exist. Wherever Adzuna provides a structured field, it is authoritative over any conflicting AI claim.

**Rationale**: Gives the system a real, structured, rate-limited, authoritative source of job facts, while keeping the AI strictly a comparison/analysis component with zero ability to invent or fetch job data on its own. See `03-job-sources.md` for the full connector design.

## ADR-005: SQLite, not a database server; no auth service for the MVP

**Context**: An earlier version of this design used a self-hosted Supabase stack (PostgreSQL, GoTrue Auth, Storage) run via Docker Compose. That stack was built to solve multi-user, network-exposed, object-storage-scale problems this project doesn't have.

**Decision**: The application stores its data in a single SQLite file. There is no database server, no connection pooling, no row-level security, and no separate auth or object-storage service — the app is single-user and runs on the user's own machine with no login for the MVP. The one resume file is stored on the local filesystem.

**Rationale**: A database server, an auth service, and an object-storage service each add real operational surface (processes to run, ports to expose, credentials to manage) that a single local user gains nothing from. This is a direct application of "don't add infrastructure unless it solves a demonstrated problem" (see README rule 11). If the application is ever exposed beyond `localhost` to more than one person, that's a new requirement calling for its own explicit decision — not something built speculatively today.

## ADR-006: No AI "demo fallback" in production; AI-unavailable is an honest degraded state instead

**Decision**: When Ollama is unreachable, or the exactly-configured analysis model tag (`14-model-evaluation.md`) is not present, or a model response fails schema validation twice (original attempt plus one retry), the affected job's AI fields are marked `AI_UNAVAILABLE` and the UI shows the deterministic pre-filter result alone — no fabricated analysis is generated or shown, and the system never auto-pulls or silently substitutes a different model.

**Rationale**: Direct consequence of "reliability over speed" — a system that manufactures plausible fake output by design, even labeled, undermines the entire evidence-first value proposition.

## ADR-007: Single deployable backend, not microservices

**Decision**: One FastAPI service contains all backend components, organized as clearly bounded internal modules rather than separate deployed services.

**Rationale**: A single user does not need independent scaling per component; splitting into services now would add operational overhead without benefit, especially given the shared-hardware constraint in ADR-009/`14-model-evaluation.md` where the whole point is *fewer* competing processes, not more.

## ADR-008: Job discovery and scoring is the whole product; application tracking is explicitly out of scope

**Context**: An earlier version of this design included an 11-state application lifecycle, an `applications` table, and email monitoring to detect application outcomes.

**Decision**: This project ends at showing the user a relevant, evidence-scored job and its original Adzuna application link. There is no application object, no application status, no application history, and no email monitoring anywhere in the architecture. There is also no bookmark/saved-jobs table for the MVP (`06-database-design.md`). The user applies manually and tracks the outcome entirely outside this system.

**Rationale**: This is a deliberate scope boundary set by the product owner, not an oversight — job discovery and relevance scoring is the value this project delivers; application tracking is a materially different problem (and a materially larger surface: state machines, audit trails, email integration) that isn't part of it. Removing it keeps the system small, keeps the "never automatically applies" guarantee trivially true (there's no code path that could even represent an in-progress application), and avoids building infrastructure for a feature that isn't wanted.

## ADR-009: Exactly one local analysis model at a time, pinned by exact tag, chosen against real hardware, manually managed

**Context**: The product must run local AI on Wassim's real, shared machine (Ryzen 9 9950X, RTX 5070 Ti 16GB VRAM, 32GB system RAM shared with other software) — not an abstract "a capable local model" placeholder, and not the same model used for coding this project.

**Decision**: `qwen2.5:14b-instruct-q4_K_M` is the current leading candidate *analysis* model (full evaluation in `14-model-evaluation.md`), selected on paper against the hardware budget but not yet validated by real-hardware benchmarking. Whichever tag is pinned, the application checks for that exact tag before any AI call and never auto-pulls, auto-upgrades, or silently substitutes a different installed model, routes across models, or loads more than one model at once; if missing, it reports "Required Ollama model is not installed" and names the exact model and pull command. Model management is entirely manual (`ollama pull ...`), performed by Wassim. This model is used only for job/CV analysis — it is never used to write or modify this project's own source code, and a coding model (if any) is a completely separate, independently-configured choice.

**Rationale**: A model choice made only against generic hardware assumptions risks either not fitting the real GPU (forcing slow CPU offload) or being wrong for the actual shared-RAM situation; pinning an exact, verified tag with a hard "missing = error, not silent substitution" contract keeps the system honest about what it's actually running.

## ADR-010: LLM processing is strictly sequential (concurrency = 1); cheap deterministic filtering runs before anything reaches the model

**Context**: The target machine shares its 16GB GPU and 32GB RAM with other active software. Sending many job analyses to Ollama at once, or sending every discovered job to the analysis model regardless of an obvious deterministic mismatch, would both threaten that shared budget and turn inference into a resource race.

**Decision**: AI analysis runs as a plain sequential loop — one job prepared, sent to Ollama, validated, and evidence-checked before the next job starts. There is no queue and no worker-pool architecture for the MVP; concurrency is fixed at exactly 1, not a configurable ceiling. Every job also passes a cheap, pure-code pre-filter (a fixed set of checks: location, salary, employment type, experience level, exclusions, required skills) before it is ever eligible to be sent to Ollama at all.

**Rationale**: This is a hardware-reality-driven architectural constraint, not a tunable performance knob. A queue/worker system is real infrastructure that isn't justified until real performance testing on the target hardware demonstrates the simple sequential loop is insufficient — see README rule 11.
