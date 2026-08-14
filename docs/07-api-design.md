# API Design

FastAPI, JSON over HTTP. No auth layer for the MVP — single local user, no login (`01-architecture-overview.md`). REST-shaped, resource-oriented; no GraphQL layer (unnecessary complexity for a single client app with well-known query shapes).

## Conventions

- There is exactly one profile; endpoints don't take a user ID.
- Errors are structured (`error_code`, `message`, no stack traces).

## Surface — the complete MVP API

| Method & Path | Purpose |
|---|---|
| `GET /health` | Liveness/readiness check. |
| `GET /profile` / `PUT /profile` | Read/update the single user profile, CV content, and preferences. |
| `POST /jobs/search` | Trigger the full pipeline: Adzuna search → normalize → dedup → deterministic pre-filter → Ollama analysis (sequential) → stored results. This is what the "Search Jobs" button calls. |
| `GET /jobs` | List jobs from the most recent search, with score/recommendation, sorted by score. |
| `GET /jobs/{id}` | Full job detail: original job information, matching skills, matching experience, missing requirements, unknown requirements, evidence, explanation, score, original `redirect_url`. |
| `POST /jobs/{id}/analyze` | Re-run AI analysis for a single job (e.g. after a profile change). |
| `GET /system/ollama-status` | Ollama connectivity + whether the exact configured analysis-model tag is installed locally — never triggers a pull. |

That's the whole surface. Nothing here is designed for a hypothetical future feature.

## What the API deliberately does not expose

- No `/auth` or `/session` endpoint — there's no login for the MVP.
- No `/applications`, `/assist-me`, form-filling, or browser-automation endpoint of any kind. The API's involvement with a job ends at surfacing its data and its original `redirect_url`.
- No email endpoints of any kind.
- No `/saved-jobs` endpoint for the MVP — see `06-database-design.md` and `05-adhd-ux.md` for why the bookmark feature isn't built yet.
- No scheduler-management endpoint — search is user-triggered only.
- No model-download or model-switching endpoint — the model is pinned in configuration and installed manually by the user (`14-model-evaluation.md`).
- No multi-agent/coordinator endpoint of any kind.
