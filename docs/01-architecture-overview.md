# Architecture Overview

## Component summary

| Component | Responsibility |
|---|---|
| Web Frontend | ADHD-friendly UI. React + TypeScript SPA. No business logic, no direct AI calls. |
| Auth | Login/session issuance. Self-hosted Supabase Auth (GoTrue) — email/password, JWT sessions. |
| API / Backend | All business logic: profile, jobs, matching, AI orchestration, applications, evidence, audit. Python (FastAPI). |
| User Profile & CV Ingestion | Stores structured profile + parsed resume content used by matching and AI. |
| Job Source Connectors | Pluggable adapters (API-based or browser-based) that each produce the same canonical job shape. |
| Job Discovery | Orchestrates connectors on a schedule / on demand. |
| Job Extraction | Pulls full posting content + evidence (text, source URL, optional DOM snapshot) for a discovered job. |
| Normalization | Maps source-specific fields into the canonical job schema. |
| Deduplication | Identifies the same job discovered more than once. |
| Job Database | Canonical, deduplicated job records + evidence + AI analyses + matches. PostgreSQL. |
| Matching Engine | Deterministic scoring against the user profile. |
| AI Analysis Engine | Local Ollama calls for semantic analysis, always against a fixed schema. |
| Evidence & Verification Layer | Checks AI claims against stored evidence; assigns Verified/Inferred/Unknown; rejects unsupported claims. |
| Browser Automation | Playwright-driven subsystem for extraction and application preparation; never submits without approval. |
| Application Tracking | Lifecycle state machine + audit history for each application. |
| Email Monitoring | Reads a connected mailbox, classifies job-related messages, links them to applications. |
| Notifications | Surfaces what needs attention; no separate always-on inbox to manage. |
| Audit Logging | Append-only record of AI calls, matches, state transitions, and automation actions. |
| Scheduler / Background Jobs | Runs discovery, extraction, matching, and email polling on a cadence. |

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
        MATCH["Matching Engine (deterministic)"]
        AIORCH["AI Orchestration"]
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
        MODEL["Configured Local Model"]
    end

    subgraph Data["Data Layer (self-hosted Supabase / PostgreSQL)"]
        AUTHDB["Auth (GoTrue)"]
        PG["PostgreSQL"]
        STORAGE["Object Storage (resumes, evidence snapshots)"]
    end

    subgraph External["External, Untrusted"]
        SOURCES["Job Sources / ATS pages"]
        MAILBOX["User's Mailbox (IMAP/API)"]
    end

    UI -->|HTTPS/JSON, JWT| AUTHMW
    UI -->|login| AUTHDB
    AUTHMW --> PROFILE
    AUTHMW --> APPTRACK
    AUTHMW --> NOTIF

    SCHED --> DISCOVERY
    DISCOVERY --> SOURCES
    DISCOVERY --> NORM --> DEDUP --> PG
    DEDUP --> MATCH
    MATCH --> PROFILE
    MATCH --> AIORCH
    AIORCH --> OLLAMA --> MODEL
    AIORCH --> EVID
    EVID --> PG
    EVID --> AUDIT

    APPTRACK --> PW
    PW --> SOURCES
    APPTRACK --> AUDIT
    APPTRACK --> PG

    SCHED --> EMAILSVC
    EMAILSVC --> MAILBOX
    EMAILSVC --> APPTRACK
    EMAILSVC --> AUDIT

    PROFILE --> STORAGE
    EVID --> STORAGE

    APPTRACK --> NOTIF
    MATCH --> NOTIF
```

## Layering and data flow: facts vs. calculation vs. interpretation vs. decision

This separation is the backbone of the whole system (detailed further in `02-ai-and-matching-architecture.md`):

```mermaid
flowchart LR
    A["A. FACTS\nOriginal job text, CV, profile\n(authoritative, immutable once captured)"] --> B["B. DETERMINISTIC CALCULATIONS\nSkills match, salary compare,\nlocation distance, dedup, scoring rules"]
    B --> C["C. LLM INTERPRETATION\nSemantic analysis, explanations,\ntransferable-skill reasoning"]
    C --> D["D. USER DECISION\nApprove / save / dismiss / apply"]
    A -.->|evidence checked against| C
```

The LLM never sits in path A or B. It only ever consumes facts and deterministic results and produces an interpretation that is itself checked back against A before reaching the user.

## Security boundaries

```mermaid
flowchart TB
    subgraph Untrusted["Untrusted zone"]
        JOBTEXT["Job posting text/HTML"]
        EMAILTEXT["Inbound email content"]
        PAGE["Live web pages during automation"]
    end

    subgraph Trusted["Trusted zone (backend)"]
        SANITIZE["Sanitization / extraction\n(treats all of the above as data only)"]
        PROMPTCTX["Prompt Context Builder\n(only verified fields injected, never raw untrusted text as instructions)"]
        LLMCALL["LLM Call (local Ollama)"]
        VALIDATE["Schema Validation"]
        VERIFY["Evidence Verification"]
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

- **One backend service, not microservices.** A single user does not need independent scaling of components; splitting into services would only add operational overhead (more containers, more network hops, more failure modes) with no corresponding benefit. The backend is modular internally (clear module boundaries mirroring the component table) so it could be split later if ever needed, but starts as one deployable.
- **Postgres, not a heavier data platform.** All data here is relational and modestly sized (one user's jobs and applications, not internet-scale). Postgres also gives row-level security, JSONB for flexible AI-analysis payloads, and full-text search — enough for this system without adding a search cluster or NoSQL store.
- **A dedicated Evidence & Verification Layer, not "trust the JSON schema and move on."** Schema validity only proves the AI produced well-formed output, not that the content is true. Verification is what stops confident-sounding hallucinations from reaching the user.
- **Browser automation as an isolated subsystem**, not scattered Playwright calls throughout the codebase, so its safety rules (stop-show-wait) are enforced in one place and are easy to audit.
