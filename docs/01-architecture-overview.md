# Architecture Overview

## Component summary

| Component | Responsibility |
|---|---|
| Web Frontend | ADHD-friendly UI. React + TypeScript SPA. No business logic, no direct AI calls. |
| Auth | Login/session issuance. Self-hosted Supabase Auth (GoTrue) — email/password, JWT sessions. |
| API / Backend | All business logic: profile, jobs, matching, AI orchestration, applications, evidence, audit. Python (FastAPI). |
| User Profile & CV Ingestion | Stores structured profile + parsed resume content used by matching and AI. |
| Job Source Connector (Adzuna) | The sole, mandatory MVP job source. Deterministic Adzuna API queries built from the profile — the AI never searches for jobs. A pluggable adapter interface is retained for future sources, but only Adzuna ships in MVP. |
| Job Discovery | Orchestrates the Adzuna connector on a schedule / on demand. |
| Normalization | Maps Adzuna's fields into the canonical job schema. |
| Deduplication | Identifies the same job discovered more than once (by Adzuna id, then redirect_url, then composite key). |
| Deterministic Pre-Filter | Cheap, pure-code exclusion pass that runs before a job is ever eligible for LLM analysis, protecting the shared GPU/RAM budget on the target hardware. |
| Job Database | Canonical, deduplicated job records + evidence + AI analyses + matches. PostgreSQL. |
| Matching Engine | Deterministic scoring against the user profile. |
| AI Analysis Engine | Local Ollama calls (one exactly-pinned model, low/queued concurrency) for semantic analysis, always against a fixed FACT/INFERENCE/UNKNOWN schema. |
| Evidence & Verification Layer | Checks AI claims against Adzuna's structured fields (authoritative) and the description snippet; labels each claim FACT/INFERENCE/UNKNOWN; rejects unsupported claims. |
| Browser Automation | Playwright-driven subsystem for application preparation; never submits without approval. |
| Application Tracking | 11-state lifecycle state machine + audit history for each application. |
| Email Monitoring | Reads a connected mailbox, classifies job-related messages, links them to applications. |
| Notifications | Surfaces what needs attention; no separate always-on inbox to manage. |
| Audit Logging | Append-only record of AI calls, Adzuna calls, matches, state transitions, and automation actions. |
| Scheduler / Background Jobs | Runs discovery, matching, and email polling on a cadence. |

Every component in this list exists because a requirement in `00-vision-and-requirements.md` needs it. Nothing was added for its own sake — e.g. there is no message queue, no microservice mesh, and no multi-tenant abstraction, because a single-user local system doesn't need them.

## Overall architecture

```mermaid
flowchart TB
    subgraph Client
        UI["Web Frontend (React + TS)"]
    end

    subgraph Backend["Backend (FastAPI, Python)"]
        AUTHMW["Auth Middleware (verifies Supabase JWT)"]
        PROFILE["Profile & CV Service"]
        DISCOVERY["Job Discovery Orchestrator"]
        NORM["Normalization"]
        DEDUP["Deduplication"]
        PREFILTER["Deterministic Pre-Filter"]
        MATCH["Matching Engine (deterministic)"]
        AIORCH["AI Orchestration (queued, concurrency=1)"]
        EVID["Evidence & Verification Layer"]
        APPTRACK["Application Tracking"]
        EMAILSVC["Email Monitoring Service"]
        NOTIF["Notification Service"]
        AUDIT["Audit Logger"]
        SCHED["Scheduler / Background Jobs"]
    end

    subgraph Automation["Browser Automation Subsystem"]
        PW["Playwright Controller"]
    end

    subgraph AI["Local AI"]
        OLLAMA["Ollama Runtime"]
        MODEL["qwen2.5:14b-instruct-q4_K_M (pinned)"]
    end

    subgraph Data["Data Layer (self-hosted Supabase / PostgreSQL)"]
        AUTHDB["Auth (GoTrue)"]
        PG["PostgreSQL"]
        STORAGE["Object Storage (resumes)"]
    end

    subgraph External["External"]
        ADZUNA["Adzuna API"]
        MAILBOX["User's Mailbox (IMAP/API)"]
    end

    UI -->|HTTPS/JSON, JWT| AUTHMW
    UI -->|login| AUTHDB
    AUTHMW --> PROFILE
    AUTHMW --> APPTRACK
    AUTHMW --> NOTIF

    SCHED --> DISCOVERY
    DISCOVERY --> ADZUNA
    DISCOVERY --> NORM --> DEDUP --> PG
    DEDUP --> MATCH --> PREFILTER
    MATCH --> PROFILE
    PREFILTER -->|passes| AIORCH
    AIORCH --> OLLAMA --> MODEL
    AIORCH --> EVID
    EVID --> PG
    EVID --> AUDIT

    APPTRACK --> PW
    PW --> ADZUNA
    APPTRACK --> AUDIT
    APPTRACK --> PG

    SCHED --> EMAILSVC
    EMAILSVC --> MAILBOX
    EMAILSVC --> APPTRACK
    EMAILSVC --> AUDIT

    PROFILE --> STORAGE

    APPTRACK --> NOTIF
    MATCH --> NOTIF
```

## Layering and data flow: facts vs. calculation vs. interpretation vs. decision

This separation is the backbone of the whole system (detailed further in `02-ai-and-matching-architecture.md`):

```mermaid
flowchart LR
    A["A. FACTS\nAdzuna structured fields + snippet, CV, profile\n(authoritative, immutable once captured)"] --> B["B. DETERMINISTIC CALCULATIONS\nSkills match, salary compare,\nlocation match, dedup, pre-filter, scoring rules"]
    B --> C["C. LLM INTERPRETATION\nSemantic analysis, explanations,\ntransferable-skill reasoning"]
    C --> D["D. USER DECISION\nApprove / save / dismiss / apply"]
    A -.->|evidence checked against, Adzuna wins| C
```

The LLM never sits in path A or B. It only ever consumes facts and deterministic results and produces an interpretation that is itself checked back against A before reaching the user.

## Security boundaries

```mermaid
flowchart TB
    subgraph Untrusted["Untrusted zone"]
        JOBTEXT["Adzuna description snippet"]
        EMAILTEXT["Inbound email content"]
        PAGE["Live web pages during automation"]
    end

    subgraph Trusted["Trusted zone (backend)"]
        SANITIZE["Sanitization / extraction\n(treats all of the above as data only)"]
        PROMPTCTX["Prompt Context Builder\n(only verified fields injected, never raw untrusted text as instructions)"]
        LLMCALL["LLM Call (local Ollama, queued)"]
        VALIDATE["Schema Validation"]
        VERIFY["Evidence Verification (Adzuna wins)"]
        AUTHZ["Authorization Layer\n(row-level user ownership checks)"]
        DB[("PostgreSQL — user-scoped data")]
    end

    subgraph UserZone["User-controlled zone"]
        USER["User (approval, credentials, submission)"]
    end

    JOBTEXT --> SANITIZE
    EMAILTEXT --> SANITIZE
    PAGE --> SANITIZE
    SANITIZE --> PROMPTCTX --> LLMCALL --> VALIDATE --> VERIFY --> DB
    AUTHZ --> DB
    USER -->|explicit approval only| AUTHZ
    LLMCALL -.->|no tool access, no system control, output-only| VALIDATE
```

Key rule: nothing under `Untrusted` zone can directly cause an action; it can only become *data* that trusted, code-controlled steps process. See `08-security-and-prompt-injection.md` for the full threat model.

## Why this shape and not something else

- **One backend service, not microservices.** A single user does not need independent scaling of components; splitting into services would only add operational overhead (more containers, more network hops, more failure modes) with no corresponding benefit — doubly true given the shared-hardware constraint in `14-model-evaluation.md`. The backend is modular internally (clear module boundaries mirroring the component table) so it could be split later if ever needed, but starts as one deployable.
- **Postgres, not a heavier data platform.** All data here is relational and modestly sized (one user's jobs and applications, not internet-scale). Postgres also gives row-level security, JSONB for flexible AI-analysis payloads, and full-text search — enough for this system without adding a search cluster or NoSQL store.
- **A dedicated Evidence & Verification Layer, not "trust the JSON schema and move on."** Schema validity only proves the AI produced well-formed output, not that the content is true. Verification — with Adzuna's structured fields as the top authority — is what stops confident-sounding hallucinations from reaching the user.
- **Browser automation as an isolated subsystem**, not scattered Playwright calls throughout the codebase, so its safety rules (stop-show-wait) are enforced in one place and are easy to audit.
