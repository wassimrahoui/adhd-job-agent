# API Design

FastAPI, JSON over HTTPS, JWT bearer auth (the Supabase-issued JWT, verified by backend middleware on every request). REST-shaped, resource-oriented; no GraphQL layer (unnecessary complexity for a single client app with well-known query shapes).

## Conventions

- All endpoints scoped to the authenticated user implicitly — no user ID is ever accepted as a client-supplied parameter for "whose data to return"; it always comes from the verified JWT.
- Every response includes enough evidence/provenance references (not full payloads) for the frontend to link back to `job_evidence`/`ai_analyses` without a second round trip being required to know *that* evidence exists.
- Errors are structured (`error_code`, `message`, no stack traces).

## Surface (representative, not exhaustive)

| Method & Path | Purpose |
|---|---|
| `POST /auth/session` | Exchange Supabase auth result for backend session context (first-request bootstrap). |
| `GET /profile` / `PUT /profile` | Read/update user profile and matching preferences. |
| `POST /resumes` / `GET /resumes` / `PUT /resumes/{id}/activate` | Manage resume uploads and active resume. |
| `POST /discovery/run` | Trigger an on-demand Adzuna discovery run (in addition to the scheduled cadence). Adzuna is the sole source; there is no multi-source configuration endpoint. |
| `GET /jobs?min_score=&passed_prefilter=` | List jobs, filterable by score and pre-filter outcome. |
| `GET /jobs/{id}` | Full job detail: canonical fields (from Adzuna), deterministic match breakdown, latest AI analysis with per-claim FACT/INFERENCE/UNKNOWN labels, evidence references, original `redirect_url`. |
| `GET /jobs/{id}/evidence` | Raw evidence record(s) for a job. |
| `POST /jobs/{id}/save` | Bookmark a job into `saved_jobs`. |
| `DELETE /jobs/{id}/save` | Remove a bookmark. |
| `GET /saved-jobs` | List bookmarked jobs. |
| `POST /jobs/{id}/reanalyze` | Force a fresh AI analysis (e.g. after a profile change). |
| `GET /system/ai-status` | Ollama connectivity + whether the exact configured analysis-model tag (`14-model-evaluation.md`) is present locally, for the honest "AI unavailable" / "required model not installed" UI state — never auto-triggers a pull. |
| `GET /system/adzuna-status` | Remaining daily Adzuna quota / last successful discovery run, for the honest "discovery unavailable today" UI state. |
| `GET /audit-logs?entity=&id=` | Read-only audit trail for a given entity, for transparency/debugging. |

## What the API deliberately does not expose

- No endpoint accepts a raw prompt or lets the frontend call the analysis model directly — all AI orchestration, context-building, and verification happens server-side.
- No endpoint performs, prepares, or assists an application submission of any kind — there is no `/applications` resource, no `/assist-me` endpoint, no form-filling endpoint, no browser-automation trigger. The API's involvement with a job ends at surfacing its data and its original `redirect_url`; the user leaves the app to apply.
- No email endpoints of any kind — this project does not read, classify, or act on a mailbox.
- No `/notifications` resource beyond what `GET /jobs?min_score=` already gives the frontend to build its own "what's new" view — there is no separate always-on inbox to manage.
