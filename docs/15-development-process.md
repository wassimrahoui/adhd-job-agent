# Development Process: Task Decomposition, Execution Loop, and Progress Dashboard

This document specifies *how implementation work on this project is planned, decomposed, executed, tested, committed, and made visible* — it governs the coding agent's workflow, not the ADHD Job Agent product itself. Everything in `00`–`14` remains the architecture; this document is the process layer that turns that architecture into shipped, testable code in small, verifiable steps.

**Scope note — do not confuse this with the product's own Dashboard screen.** `05-adhd-ux.md` describes a "Home / Today" screen as part of the *product* the end user sees. This document describes a separate, developer-facing **task/progress dashboard** used to monitor implementation of the project itself — a dev tool, not a feature listed in `00-vision-and-requirements.md` or `05-adhd-ux.md`. The two are unrelated pages serving unrelated audiences and must not be merged into one screen.

**Scope note — "the coding agent" is tool-agnostic.** This document describes a workflow, not a specific tool. `10-deployment-and-dev-workflow.md` already establishes that development uses a coding agent (e.g. OpenCode) that is never the same model/runtime as the product's own Ollama-served AI, and that Claude is not wired into the product or its pipeline (rules 1 and 4). Nothing here changes that. Whichever tool acts as coding agent on a given work session, it follows the process below.

## AGENT_TASKS.md — the persistent implementation task system

A file named `AGENT_TASKS.md` lives at the repository root once implementation begins (it is not part of the architecture/design phase and is not created until implementation starts — see "Relationship to the design phase" below). It is the coding agent's first read at the start or resumption of any implementation session, and the single source of truth for what has been built, what is in progress, and what's next.

Every task entry, at any level of the hierarchy, must contain:

- **Task ID** — stable, unique, referenced by dependencies.
- **Task name** — short, specific.
- **Parent task** — the task this one decomposes from, or `none` for a root task.
- **Difficulty** — `EASY | MEDIUM | HARD` (see below).
- **Status** — `NOT_STARTED | IN_PROGRESS | TESTING | BLOCKED | DONE`.
- **Objective** — one or two sentences: what this task achieves and why.
- **Required documents** — which of `00`–`15` (or other repo docs) must be read/consulted before implementing this task.
- **Relevant source files** — files this task is expected to create or touch, once known.
- **Dependencies** — other Task IDs that must be `DONE` first.
- **Requirements** — the specific, concrete behavior this task must deliver.
- **Acceptance criteria** — how to know the task is actually finished, stated as checkable conditions.
- **Tests** — the automated test(s) this task must have passing, named or described concretely enough to write.
- **Definition of Done** — the full bar: implemented, tested, manually verified, committed, `AGENT_TASKS.md` updated, dashboard updated.

## Recursive task decomposition (hard requirement)

**No MEDIUM or HARD task is ever directly implemented.** Every MEDIUM or HARD task must first be broken into smaller subtasks. If a subtask is still MEDIUM or HARD, it is broken down again. This repeats until every leaf task in the tree is EASY. MEDIUM and HARD tasks remain in `AGENT_TASKS.md` as **parent/group tasks for organization only** — they group and track their children's progress, but no code is ever written directly against a MEDIUM or HARD task.

**What counts as EASY:** small, focused, independently testable, easy to understand at a glance, limited in scope, completable in one short development cycle, and capable of producing a meaningful, demonstrable result on its own. A task is not EASY just because it's been renamed or split shallowly — if completing it still requires several non-trivial implementation steps or touches many unrelated concerns, it is decomposed further, not relabeled.

**Illustrative example of the decomposition depth this requires:** a HARD task like "AI Application Assistance" is not implemented directly. It first breaks into MEDIUM areas: form detection, CV-to-form field mapping, "Assist Me" activation/deactivation, safe answer generation (verified-data-only, per `03-job-sources-and-browser-automation.md`), browser interaction, and security restrictions (never touching Submit). Each of those MEDIUM areas is then broken down again into EASY leaves — e.g. "Add an 'Assist Me' button to the application page component," "Load the active resume's structured fields into memory for the current session," "Map the detected 'full name' field to the profile's name field," each independently buildable and testable.

**Dependencies survive decomposition.** If Task A requires Task B's output, that dependency is preserved (and typically refined into more specific dependencies) as both are broken down — never bypassed, never assumed away because the pieces got smaller.

## Task execution loop

Only EASY leaf tasks are ever selected for execution. Selection priority, in order: task's dependencies are all `DONE` → task is an EASY leaf (not a MEDIUM/HARD parent) → lowest applicable Task ID among eligible tasks → task has no recorded blocker.

Per-task loop:

```
IMPLEMENT → RUN AUTOMATED TESTS → RUN THE APPLICATION → MANUALLY VERIFY
  → GIT COMMIT → UPDATE AGENT_TASKS.md → UPDATE LIVE DASHBOARD
  → REPORT A TESTABLE RESULT → SELECT NEXT EASY TASK → REPEAT
```

If a task cannot be completed (a real blocker — missing dependency, missing credential, hardware constraint, ambiguous requirement needing a decision), it is marked `BLOCKED` with the exact reason and what's missing recorded in `AGENT_TASKS.md`. It is never marked `DONE` to move on, and it is never silently dropped. If a different, independent EASY task can proceed without violating any dependency, work continues there. A dependency is never bypassed to avoid a blocker.

## Live task/progress dashboard

A dynamic, browser-viewable page for watching implementation progress in real time, showing at minimum: overall progress (e.g. tasks done / total EASY leaves), the current task and its parent and difficulty, current task status, completed tasks, remaining tasks, the next task queued for selection, any blocked tasks and why, task dependencies, required documents for the current task, acceptance criteria and tests for the current task, the latest action taken, latest update timestamp, any errors, recent activity (a short scrolling log), the latest git commit (hash + message), and the latest test result (pass/fail + summary).

**Hierarchy view.** The dashboard shows the parent/child task structure, not a flat list — a MEDIUM or HARD parent with its EASY children nested underneath, using simple status markers (e.g. `✓` done, `→` in progress, `○` not started) so the current position in the tree is legible at a glance. Only EASY leaf tasks can ever show as `IN_PROGRESS`, `TESTING`, or `DONE`; MEDIUM/HARD parents reflect an aggregate of their children's states.

**Live updates, no manual refresh.** The dashboard updates automatically as task events occur. Use whichever of WebSocket, Server-Sent Events, or lightweight polling is simplest and reliable for this stack — no unnecessary real-time infrastructure (no message broker, no pub/sub cluster) is justified for a single-user, single-machine tool.

**Task events.** The backend emits structured events as work happens: `TASK_STARTED`, `DOCUMENT_READING`, `IMPLEMENTATION_STARTED`, `IMPLEMENTATION_PROGRESS`, `TEST_STARTED`, `TEST_PASSED`, `TEST_FAILED`, `TASK_COMPLETED`, `TASK_BLOCKED`, `ERROR`. Each event carries a timestamp, the Task ID it relates to, the event type, and a short human-readable message. These events are what the dashboard's activity log and status fields are built from.

**State persistence.** Task state and event history must survive a browser refresh, a backend restart, and a coding-agent restart — persisted through the project's own backend/database (Postgres, per `06-database-design.md`), not held only in browser memory or an in-process variable that resets on restart.

## Git discipline

**Commit frequently, in small, focused, logical, reversible units.** A commit follows a meaningful completed task or milestone — never a large commit bundling unrelated features. Commit messages follow a conventional, descriptive style (e.g. `feat(ui): add dashboard shell`, `feat(jobs): add Adzuna integration`, `fix(matching): correct salary comparison edge case`).

**Every commit must be testable (hard requirement).** Development does not spend many commits on invisible infrastructure before anything usable exists. The default pattern is: build → test → commit → show something testable → move to the next feature. This is why UI-first development and vertical slices (below) matter — they're what makes "testable" possible from very early on rather than only after a large backend is finished.

**Before every commit:** run the relevant automated tests, review the changed files, check for errors, check for secrets (API keys, passwords, tokens, credentials, `.env` contents), and check for unrelated changes accidentally swept into the commit. No commit ever contains a secret.

## Vertical slices and UI-first development

Implementation prioritizes complete vertical slices over horizontal layers whenever practical — a thin path all the way from UI through backend to data, rather than a fully built backend with no visible surface for weeks. Illustrative sequence: a working UI shell with navigation → the UI wired to a real backend endpoint → that endpoint backed by real database persistence → the UI backed by a real Adzuna search → the same flow with deterministic filtering applied → the same flow with real Ollama analysis applied on top. Each step in that sequence is itself a testable milestone, not an internal-only change.

**UI first.** The first usable milestone includes an application shell, navigation, the product's own dashboard/home screen, a job search page, job results, job details, and the task/progress dashboard described above — so there is something to open in a browser and interact with from very early in the project, not just once the backend is "done."

**Temporary mocks are allowed during development, never in production.** Controlled test data, fixture jobs, or a canned AI-analysis response are acceptable while a real dependency (Adzuna, Ollama) isn't wired up yet, so UI and integration work can proceed and be demonstrated. The moment the real dependency is ready, the mock is replaced — a mock is never left in as a silent production fallback (this is the same principle as ADR-006's ban on a fabricated "demo analysis," extended to development practice generally).

## Testable milestones

After every meaningful milestone, report: what was built, how to start it, where to open it (URL/port), what can actually be tested right now, and known limitations at this point. This keeps every reported milestone concrete and verifiable rather than a status claim taken on faith — consistent with ADR-002's "never trust a self-reported action" applied to development progress itself (`12-architecture-decisions.md`).

## Development cycle, end to end

```
READ AGENT_TASKS.md → READ REQUIRED DOCUMENTS FOR THE CURRENT TASK
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

If existing code ever contradicts the approved specification, the contradiction is identified and resolved according to the specification — the architecture is not silently redesigned around whatever the code happens to do.

## Relationship to the design phase

This document is part of the approved architecture set (`00`–`15`); it is design documentation, not itself a task tracker. `AGENT_TASKS.md`, the actual task hierarchy, and the live dashboard implementation are created only once implementation begins, following the process this document defines. Before implementation starts, the expected planning sequence is: read this full document set and both referenced prototypes' source code end to end, reconcile any contradictions against the specification, create `AGENT_TASKS.md`, build the initial task hierarchy, recursively decompose every MEDIUM/HARD task until every executable task is EASY, define dependencies/acceptance criteria/tests/commit points for the initial slice, and design the live dashboard's concrete data model — before any application code is written. This document does not itself constitute that planning pass; it defines the rules that pass must follow.

## What this document does not change

Everything in `00`–`14` stands as previously corrected: Adzuna as the sole MVP job-fact source with the LLM component never originating or searching for jobs; CV/profile-based matching with explicit field categories and `UNKNOWN` for anything unstated; the deterministic pre-filter and configurable relevance-threshold cutoff; the FACT/INFERENCE/UNKNOWN evidence schema with named `matching_skills`/`matching_experience`/`missing_requirements`; local-only Ollama with no cloud fallback and a single manually-managed candidate model; low/queued LLM concurrency; manual application as the permanent default with the opt-in, post-MVP, verified-data-only "Assist Me" helper that never touches Submit; the 11-state application lifecycle; no coordinator, no multi-agent architecture, no Claude in the product; and the 32GB RAM / 16GB VRAM shared-hardware budget. Nothing in this process document authorizes or implies a change to any of those decisions.
