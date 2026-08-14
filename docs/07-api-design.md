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
| `GET /job-sources` / `POST /job-sources` / `PATCH /job-sources/{id}` | Configure job source connectors. |
| `POST /discovery/run` | Trigger an on-demand discovery run (in addition to the scheduled cadence). |
| `GET /jobs?status=&min_score=` | List jobs, filterable by triage queue and score. |
| `GET /jobs/{id}` | Full job detail: canonical fields, deterministic match breakdown, latest AI analysis with Verified/Inferred/Unknown labels, evidence references. |
| `GET /jobs/{id}/evidence` | Raw evidence record(s) for a job. |
| `POST /jobs/{id}/review` | Record Approve / Save / Dismiss. |
| `POST /jobs/{id}/reanalyze` | Force a fresh AI analysis (e.g. after a profile change). |
| `GET /saved-jobs` | Saved queue. |
| `POST /applications` | Create an application from an approved job (moves to Preparing). |
| `GET /applications` / `GET /applications/{id}` | List/detail, including full `application_events` history. |
| `POST /applications/{id}/prepare` | Stage AI-drafted materials + (if available) start automation extraction of the application form. |
| `POST /applications/{id}/confirm-submission` | The explicit, user-only action that unlocks the final submit step (Stop→Show→Wait→Continue gate). |
| `PATCH /applications/{id}/status` | User-driven manual status update (e.g. marking Interview after a phone call not captured by email monitoring). |
| `GET /email/connection` / `POST /email/connection` | Manage mailbox connection (read-only scope). |
| `GET /email-events?confirmed=false` | Unconfirmed detected email events awaiting user action. |
| `POST /email-events/{id}/confirm` | User confirms/corrects a detected event and its proposed application link. |
| `GET /notifications` / `POST /notifications/{id}/dismiss` | "What needs attention" feed. |
| `GET /system/ai-status` | Ollama connectivity + configured model, for the honest "AI unavailable" UI state. |
| `GET /audit-logs?entity=&id=` | Read-only audit trail for a given entity, for transparency/debugging. |

## What the API deliberately does not expose

- No endpoint accepts a raw prompt or lets the frontend call the LLM directly — all AI orchestration, context-building, and verification happens server-side, so the untrusted-input handling in `08-security-and-prompt-injection.md` can't be bypassed by a client-crafted request.
- No endpoint performs an application submission by itself; submission is always a human-in-the-browser or human-click-confirmed action recorded through `confirm-submission`, never a single API call the frontend could fire unattended.
- No bulk "apply to all matches" endpoint — this would violate rule 9 (No Automatic Applications) even if gated by a single confirmation, since it collapses many individual irreversible decisions into one click; each application's submission is confirmed individually.
