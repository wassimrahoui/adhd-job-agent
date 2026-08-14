# Development Process: Task Decomposition, Execution Loop, and Progress Dashboard

This document specifies *how implementation work on this project is planned, decomposed, executed, tested, committed, and made visible* — it governs the coding agent's workflow, not the ADHD Job Agent product itself. Everything in `00`–`14` remains the architecture; this document is the process layer that turns that architecture into shipped, testable code in small, verifiable steps.

**Scope note — do not confuse this with the product's own Home/Today screen.** `05-adhd-ux.md` describes screens that are part of the *product* the end user sees. This document describes a separate, developer-facing **task/progress dashboard** used to monitor implementation of the project itself — a dev tool, not a feature listed in `00-vision-and-requirements.md` or `05-adhd-ux.md`. The two are unrelated pages serving unrelated audiences and must not be merged into one screen.

**Scope note — this dashboard is a display, not a controller.** It is explicitly **not** an AI coordinator, does not orchestrate or control any agent, and does not itself make task-selection decisions. It only reads and displays state that the coding agent's own process (below) already produces. This distinction matters given ADR-001's hard "no coordinator, no multi-agent architecture" rule — the dashboard must never grow into anything resembling one.

**Scope note — "the coding agent" is tool-agnostic.** This document describes a workflow, not a specific tool. `10-deployment-and-dev-workflow.md` already establishes that the coding-model role and the product's own analysis-model role are completely separate and never conflated, and that Claude is never wired into the product itself. Nothing here changes that. Whichever tool acts as coding agent on a given work session, it follows the process below.

## AGENT_TASKS.md — the persistent implementation task system

A file named `AGENT_TASKS.md` lives at the repository root once implementation begins (it is not part of the architecture/design phase and is not created until implementation starts — see "Relationship to the design phase" below). It is the coding agent's first read at the start or resumption of any implementation session, and the single source of truth for what has been built, what is in progress, and what's next.

Every task entry, at any level of the hierarchy, must contain:

- **Task ID** — stable, unique, referenced by dependencies.
- **Task name** — short, specific.
- **Difficulty** — `EASY | MEDIUM | HARD` (see below).
- **Objective** — one or two sentences: what this task achieves and why.
- **Parent task** — the task this one decomposes from, or `none` for a root task.
- **Documents to read** — which of `00`–`15` (or other repo docs) must be read before implementing this task, and *only* those.
- **Source files to read** — the existing source files this task needs to understand before changing anything.
- **Files to modify** — the files this task is expected to create or touch.
- **Dependencies** — other Task IDs that must be `DONE` first.
- **Implementation requirements** — the specific, concrete behavior this task must deliver.
- **Acceptance criteria** — how to know the task is actually finished, stated as checkable conditions.
- **Test procedure** — the automated test(s) this task must have passing, described concretely enough to write and run.
- **Expected result** — what a passing run actually looks like/produces.
- **Commit message** — the message the resulting commit uses once the task is done.
- **Status** — `NOT_STARTED | IN_PROGRESS | TESTING | BLOCKED | DONE`.

## Recursive task decomposition (hard requirement)

**No MEDIUM or HARD task is ever directly implemented.** Every MEDIUM or HARD task must first be broken into smaller subtasks. If a subtask is still MEDIUM or HARD, it is broken down again. This repeats until every leaf task in the tree is EASY. MEDIUM and HARD tasks remain in `AGENT_TASKS.md` as **parent/group tasks for organization only** — they group and track their children's progress, but no code is ever written directly against a MEDIUM or HARD task. The coding agent must never say "I'll handle the whole feature" — a feature-sized ask is always broken into independently testable EASY tasks first.

**What counts as EASY:** implementable and testable in one focused change. Small, independently testable, easy to understand at a glance, limited in scope, completable in one short development cycle, and capable of producing a meaningful, demonstrable result on its own. A task is not EASY just because it's been renamed or split shallowly — if completing it still requires several non-trivial implementation steps or touches many unrelated concerns, it is decomposed further, not relabeled.

**Illustrative example of the decomposition depth this requires:** a HARD task like "Ollama Job Analysis Integration" is not implemented directly. It first breaks into MEDIUM areas: prompt/context construction from the job and profile, the Ollama client call itself, structured-output parsing, schema validation, evidence verification against Adzuna fields and the CV, and the low-concurrency queue. Each of those MEDIUM areas is then broken down again into EASY leaves — e.g. "Write the Pydantic model for the analysis response schema," "Implement the Ollama HTTP client wrapper with a configurable timeout," "Implement the FIFO analysis queue with concurrency=1," "Implement the deterministic substring check that verifies a `FACT`-labeled claim against the stored job snippet," each independently buildable and testable.

**Dependencies survive decomposition.** If Task A requires Task B's output, that dependency is preserved (and typically refined into more specific dependencies) as both are broken down — never bypassed, never assumed away because the pieces got smaller.

## Development order (easiest to hardest)

Tasks progress through increasing levels of dependency and complexity. This is a guide for sequencing, not a rigid gate — every MEDIUM/HARD task at any level still must be recursively broken down to EASY-only leaves before execution.

- **L1** — Documentation, configuration, basic project setup, simple data models, utility functions.
- **L2** — Database models/migrations, basic API scaffolding, basic UI shell and navigation.
- **L3** — Adzuna connector, normalization, deduplication, the deterministic pre-filter.
- **L4** — CV/profile processing and the deterministic matching engine.
- **L5** — Ollama integration, structured AI analysis, evidence verification.
- **L6** — End-to-end pipeline wiring, UI integration against real data, performance optimization on real hardware.

## Task execution loop

Only EASY leaf tasks are ever selected for execution. Selection priority, in order: task's dependencies are all `DONE` → task is an EASY leaf (not a MEDIUM/HARD parent) → lowest applicable Task ID among eligible tasks → task has no recorded blocker.

Per-task loop:

```
IMPLEMENT → RUN AUTOMATED TESTS → RUN THE APPLICATION → MANUALLY VERIFY
  → GIT COMMIT → UPDATE AGENT_TASKS.md → UPDATE LIVE DASHBOARD
  → REPORT A TESTABLE RESULT → SELECT NEXT EASY TASK → REPEAT
```

If a task cannot be completed (a real blocker — missing dependency, missing credential, hardware constraint, ambiguous requirement needing a decision), it is marked `BLOCKED` with the exact reason and what's missing recorded in `AGENT_TASKS.md`. It is never marked `DONE` to move on, and it is never silently dropped. If a different, independent EASY task can proceed without violating any dependency, work continues there. A dependency is never bypassed to avoid a blocker.

## Resource-efficient task execution

The coding agent's own working process must stay efficient, not just the finished product:

- **Read only what the current task specifies** — the task's own `Documents to read` and `Source files to read` fields, not the entire repository, for every task. This keeps context usage bounded and is specifically important for local-LLM-driven coding-agent performance.
- **Don't regenerate files unnecessarily.** Prefer targeted edits to files that already exist over rewriting them wholesale when only a small change is needed.
- **Don't run multiple expensive LLM operations simultaneously** — this applies to development-time LLM use exactly as it applies to the finished app's own concurrency=1 rule (`02-ai-and-matching-architecture.md`).
- **Don't send the whole repository to any model** as context for a single task; task scoping exists precisely to prevent that.

## Live task/progress dashboard

A dynamic, browser-viewable page for watching implementation progress in real time, showing at minimum: overall progress (e.g. tasks done / total EASY leaves), the current task, its ID, its parent, and its difficulty, current task status, completed tasks, remaining tasks, the current phase/level (L1–L6), the next task queued for selection, any blocked tasks and why, task dependencies, the latest git commit (hash + message), and the latest test + its result (pass/fail + summary).

**Hierarchy view.** The dashboard shows the parent/child task structure, not a flat list — a MEDIUM or HARD parent with its EASY children nested underneath, using simple status markers (e.g. `✓` done, `→` in progress, `○` not started) so the current position in the tree is legible at a glance. Only EASY leaf tasks can ever show as `IN_PROGRESS`, `TESTING`, or `DONE`; MEDIUM/HARD parents reflect an aggregate of their children's states.

**Live updates, no manual refresh.** The dashboard updates automatically as task events occur. Use whichever of WebSocket, Server-Sent Events, or lightweight polling is simplest and reliable for this stack — no unnecessary real-time infrastructure (no message broker, no pub/sub cluster) is justified for a single-user, single-machine tool.

**State persistence.** Task state must survive a browser refresh, a backend restart, and a coding-agent restart — persisted through the project's own backend/database (Postgres, per `06-database-design.md`), not held only in browser memory or an in-process variable that resets on restart.

## Git discipline

**Commit frequently, in small, focused, logical, reversible units.** Every completed EASY task normally produces one commit — never a large commit bundling unrelated tasks. Commit messages follow a conventional, descriptive style tied to what kind of change it is (e.g. a UI commit leaves the UI visibly different and testable in the browser; an API commit leaves a new endpoint callable and testable; a database commit leaves a migration that applies cleanly and a model that round-trips; an Adzuna commit leaves a real or fixture-backed search callable end to end; a matching commit leaves a deterministic score computable and checkable by hand; an Ollama commit leaves a real or fixture-backed analysis callable end to end). Every task has an explicit test, and that test is what "testable" means for its commit.

**Every commit must be testable (hard requirement).** Development does not spend many commits on invisible infrastructure before anything usable exists. The default pattern is: build → test → commit → show something testable → move to the next feature.

**Before every commit:** run the relevant automated tests, review the changed files, check for errors, check for secrets (API keys, passwords, tokens, credentials, `.env` contents), and check for unrelated changes accidentally swept into the commit. No commit ever contains a secret.

## Vertical slices and UI-first development

Implementation prioritizes complete vertical slices over horizontal layers whenever practical — a thin path all the way from UI through backend to data, rather than a fully built backend with no visible surface for weeks. Illustrative sequence: a working UI shell with navigation → the UI wired to a real backend endpoint → that endpoint backed by real database persistence → the UI backed by a real Adzuna search → the same flow with deterministic filtering applied → the same flow with real Ollama analysis applied on top. Each step in that sequence is itself a testable milestone, not an internal-only change.

**UI first.** The first usable milestone includes an application shell, navigation, the product's own home screen, a job search page, job results, job details, and the task/progress dashboard described above — so there is something to open in a browser and interact with from very early in the project, not just once the backend is "done."

**Temporary mocks are allowed during development, never in production.** Controlled test data, fixture jobs, or a canned AI-analysis response are acceptable while a real dependency (Adzuna, Ollama) isn't wired up yet, so UI and integration work can proceed and be demonstrated. The moment the real dependency is ready, the mock is replaced — a mock is never left in as a silent production fallback (this is the same principle as ADR-006's ban on a fabricated "demo analysis," extended to development practice generally).

## Testable milestones

After every meaningful milestone, report: what was built, how to start it, where to open it (URL/port), what can actually be tested right now, and known limitations at this point. This keeps every reported milestone concrete and verifiable rather than a status claim taken on faith — consistent with ADR-002's "never trust a self-reported action" applied to development progress itself.

## Optional development memory layer (Mem0)

Mem0 (or an equivalent memory layer) **may** be used, optionally, during development if it genuinely helps a local coding agent's performance — for example, remembering architectural decisions already made, work already completed, bugs already found and fixed, and known constraints, so the agent doesn't have to rediscover them by re-reading large amounts of source on every task. If used:

- It never replaces source code, documentation, Git history, or `AGENT_TASKS.md` as the authoritative record — those remain the source of truth regardless of what's in memory.
- The coding agent retrieves only memories relevant to the current task, never the entire memory store, into context.
- If it adds complexity without a clear, demonstrated benefit, it is simply not used — this is an optional tool, never a mandatory dependency of the development process.

## Development cycle, end to end

```
READ AGENT_TASKS.md → READ THE CURRENT TASK'S REQUIRED DOCUMENTS AND SOURCE FILES ONLY
  → DECOMPOSE ANY COMPLEX (MEDIUM/HARD) TASK ENCOUNTERED
  → FIND THE NEXT ELIGIBLE EASY LEAF TASK
  → IMPLEMENT → RUN AUTOMATED TESTS → RUN THE APPLICATION → MANUALLY VERIFY
  → GIT COMMIT → UPDATE AGENT_TASKS.md → UPDATE THE LIVE DASHBOARD
  → REPORT A TESTABLE RESULT → SELECT THE NEXT EASY TASK → REPEAT
```

This loop runs for as long as a given work session is active — it is not a claim that implementation continues unattended indefinitely between sessions; it is what happens continuously *within* one.

## Source-of-truth priority

When something is ambiguous or two sources disagree, resolve in this order:

1. `AGENT_TASKS.md` (once implementation has begun) — the current, concrete plan of record.
2. The approved architecture/specification documents (`00`–`15` in this repository).
3. The existing implementation.
4. The test suite.
5. The coding agent's own assumptions — lowest priority, used only when nothing above resolves the question, and any such assumption should be surfaced rather than silently baked in.

If existing code ever contradicts the approved specification, the contradiction is identified and resolved according to the specification — the architecture is not silently redesigned around whatever the code happens to do. When something is genuinely unclear, the response is to stop and identify the exact ambiguity, not to guess or invent a requirement.

## Relationship to the design phase

This document is part of the approved architecture set (`00`–`15`); it is design documentation, not itself a task tracker. `AGENT_TASKS.md`, the actual task hierarchy, and the live dashboard implementation are created only once implementation begins, following the process this document defines. Before implementation starts, the expected planning sequence is: read this full document set end to end, create `AGENT_TASKS.md`, build the initial task hierarchy across the L1–L6 development order, recursively decompose every MEDIUM/HARD task until every executable task is EASY, define dependencies/acceptance criteria/tests/commit points for the initial slice, and design the live dashboard's concrete data model — before any application code is written. This document does not itself constitute that planning pass; it defines the rules that pass must follow.

## What this document does not change

Everything in `00`–`14` stands as currently scoped: Adzuna as the sole job-fact source with the AI never originating or searching for jobs; CV/profile-based matching with explicit field categories and `UNKNOWN`/not-demonstrated for anything unstated; the deterministic pre-filter and configurable relevance-threshold cutoff; the FACT/INFERENCE/UNKNOWN evidence schema with named `matching_skills`/`matching_experience`/`missing_requirements`/`unknown_requirements`; local-only Ollama with no cloud fallback and a single manually-managed candidate analysis model, kept completely separate from any coding model; low/queued LLM concurrency; the system's involvement ending at the original application link, with no application tracking, no browser automation, no "Assist Me," and no email monitoring anywhere in the project; no coordinator, no multi-agent architecture, no Claude in the product; untrusted job text treated simply as data with no dedicated prompt-injection subsystem; and the 32GB RAM / 16GB VRAM shared-hardware budget. Nothing in this process document authorizes or implies a change to any of those decisions.
