# API Design

FastAPI, JSON over HTTPS, JWT bearer auth (the Supabase-issued JWT, verified by backend middleware on every request). REST-shaped, resource-oriented; no GraphQL layer (unnecessary complexity for a single client app with well-known query shapes).

## Conventions

- All endpoints scoped to the authenticated user implicitly — no user ID is ever accepted as a client-supplied parameter for "whose data to return"; it always comes from the verified JWT.
- Mutations that trigger side effects with real-world consequences (submitting an application, connecting a mailbox) are explicit, separately-named endpoints, never folded into a generic `PATCH`, so they're easy to find, log, and rate-limit.
- Every response includes enough evidence/provenance references (not full payloads) for the frontend to link back to `job_evidence`/`ai_analyses` without a second round trip being required to know *that* evidence exists.
- Errors are structured (`error_code`, `message`, no stack traces) and categorized per `03-job-sources-and-browser-automation.md` / `09-testing-strategy.md`'s error taxonomy.

## Surface (representative, not exhaustive)

| Method & Path | Purpose |
|---|---|
| `POST /auth/session` | Exchange Supabase auth result for backend session context (first-request bootstrap). |
| `GET /profile` / `PUT /profile` | Read/update user profile, matching preferences, and Adzuna search defaults. |
| `POST /resumes` / `GET /resumes` / `PUT /resumes/{id}/activate` | Manage resume uploads and active resume. |
| `POST /discovery/run` | Trigger an on-demand Adzuna discovery run (in addition to the scheduled cadence). Adzuna is the sole MVP source; there is no multi-source configuration endpoint. |
| `GET /jobs?status=&min_score=&passed_prefilter=` | List jobs, filterable by pipeline status, score, and pre-filter outcome. |
| `GET /jobs/{id}` | Full job detail: canonical fields (from Adzuna), deterministic match breakdown, latest AI analysis with per-claim FACT/INFERENCE/UNKNOWN labels, evidence references. |
| `GET /jobs/{id}/evidence` | Raw Adzuna evidence record(s) for a job. |
| `POST /jobs/{id}/save` | Create an `applications` row in `SAVED` status for a `MATCHED` job — the only way an application comes into existence. |
| `POST /jobs/{id}/reanalyze` | Force a fresh AI analysis (e.g. after a profile change). |
| `GET /applications?status=SAVED` | Saved queue (no separate saved-jobs resource; see `06-database-design.md`). |
| `GET /applications` / `GET /applications/{id}` | List/detail, including full `application_events` history. |
| `POST /applications/{id}/review` | Move `SAVED → REVIEWED` (user opened full detail). |
| `POST /applications/{id}/approve` | Move `REVIEWED → APPROVED`. |
| `POST /applications/{id}/dismiss` | Move to `WITHDRAWN` from `REVIEWED` (dismiss before ever approving). |
| `POST /applications/{id}/prepare` | Move `APPROVED → PREPARING`; stage AI-drafted materials + (if available) start automation form-fill, landing in `READY_FOR_USER`. |
| `POST /applications/{id}/confirm-submission` | Move `READY_FOR_USER → APPLYING`: the explicit, user-only action that unlocks the final submit step (Stop→Show→Wait→Continue gate). |
| `PATCH /applications/{id}/status` | User-driven manual status update along a valid edge only (e.g. `APPLIED → INTERVIEW` after a phone call not captured by email monitoring); invalid edges rejected (`06-database-design.md`). |
| `GET /email/connection` / `POST /email/connection` | Manage mailbox connection (read-only scope). |
| `GET /email-events?confirmed=false` | Unconfirmed detected email events awaiting user action. |
| `POST /email-events/{id}/confirm` | User confirms/corrects a detected event and its proposed application link. |
| `GET /notifications` / `POST /notifications/{id}/dismiss` | "What needs attention" feed. |
| `GET /system/ai-status` | Ollama connectivity + whether the exact pinned model tag (`14-model-evaluation.md`) is present locally, for the honest "AI unavailable" UI state — never auto-triggers a pull. |
| `GET /system/adzuna-status` | Remaining daily Adzuna quota / last successful discovery run, for the honest "discovery unavailable today" UI state. |
| `GET /audit-logs?entity=&id=` | Read-only audit trail for a given entity, for transparency/debugging. |

## What the API deliberately does not expose

- No endpoint accepts a raw prompt or lets the frontend call the LLM directly — all AI orchestration, context-building, and verification happens server-side, so the untrusted-input handling in `08-security-and-prompt-injection.md` can't be bypassed by a client-crafted request.
- No endpoint performs an application submission by itself; submission is always a human-in-the-browser or human-click-confirmed action recorded through `confirm-submission`, never a single API call the frontend could fire unattended.
- No bulk "apply to all matches" endpoint — this would violate rule 9 (No Automatic Applications) even if gated by a single confirmation, since it collapses many individual irreversible decisions into one click; each application's submission is confirmed individually.
- No job-source-configuration endpoint beyond the profile's Adzuna search defaults — there is nothing to configure among multiple sources in MVP (ADR-004).
