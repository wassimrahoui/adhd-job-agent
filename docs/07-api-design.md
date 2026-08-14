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
| `GET /profile` / `PUT /profile` | Read/update user profile and matching preferences. |
| `POST /resumes` / `GET /resumes` / `PUT /resumes/{id}/activate` | Manage resume uploads and active resume. |
| `POST /discovery/run` | Trigger an on-demand Adzuna discovery run (in addition to the scheduled cadence). Adzuna is the sole MVP source; there is no multi-source configuration endpoint. |
| `GET /jobs?status=&min_score=&passed_prefilter=` | List jobs, filterable by pipeline status, score, and pre-filter outcome. |
| `GET /jobs/{id}` | Full job detail: canonical fields (from Adzuna), deterministic match breakdown, latest AI analysis with per-claim FACT/INFERENCE/UNKNOWN labels, evidence references. |
| `GET /jobs/{id}/evidence` | Raw evidence record(s) for a job. |
| `POST /jobs/{id}/save` | Create an `applications` row in `SAVED` status for a `MATCHED` job — the only way an application comes into existence. |
| `POST /jobs/{id}/reanalyze` | Force a fresh AI analysis (e.g. after a profile change). |
| `GET /applications?status=SAVED` | Saved queue (no separate saved-jobs resource; see `06-database-design.md`). |
| `GET /applications` / `GET /applications/{id}` | List/detail, including full `application_events` history. |
| `POST /applications/{id}/review` | Move `SAVED → REVIEWED` (user opened full detail). |
| `POST /applications/{id}/approve` | Move `REVIEWED → APPROVED`. |
| `POST /applications/{id}/dismiss` | Move to `WITHDRAWN` from `REVIEWED` (dismiss before ever approving). |
| `POST /applications/{id}/prepare` | Move `APPROVED → PREPARING`; stage optional AI-drafted reference materials (CV excerpt highlights, cover-letter draft), landing in `READY_FOR_USER`. No form-filling or automation happens here — this only stages materials for the user to read. |
| `POST /applications/{id}/start-application` | Move `READY_FOR_USER → APPLYING`: records that the user clicked through to the original `redirect_url` and is now applying on the employer/ATS site in their own browser, outside the app. |
| `POST /applications/{id}/assist-me` | **Post-MVP, not implemented in MVP.** Explicit, user-triggered request to activate the opt-in "Assist Me" field-filling helper for the current application (`03-job-sources-and-browser-automation.md`). Verifies page identity, returns only verified `FACT`-level CV/profile values for known fields, flags the rest `UNKNOWN`. Never calls or simulates a submit action. |
| `POST /applications/{id}/mark-applied` | Move `APPLYING → APPLIED`: the user's own self-attestation that they manually applied and submitted on the real page. Recorded as a `user`-actor event, not a system-verified fact. |
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
- No endpoint performs an application submission, or anything resembling one, on the user's behalf — there is no code path from any endpoint to a Submit/Apply click on an employer/ATS page. `start-application` only records that the user left the app to apply themselves; `mark-applied` only records their self-attestation afterward. Neither one, nor any combination of the two, causes an application to be submitted.
- No bulk "apply to all matches" endpoint — this would violate rule 9 (No Automatic Applications) regardless of any confirmation step, since real submission always happens on the employer's own page, one at a time, by the user's own hand.
- `assist-me` (post-MVP) never returns or triggers a submit action; it only returns verified field values for the frontend/extension to help populate, with every value traceable to a `FACT`-labeled CV/profile claim.
