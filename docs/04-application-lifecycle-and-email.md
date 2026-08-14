# Application Lifecycle and Email Monitoring

## Two separate state machines, not one overloaded one

This revision separates two things that the first version of this spec conflated into one job-status enum: the **deterministic ingestion pipeline status** (owned entirely by code, never by the user) and the **application lifecycle** (owned by the user's journey with a specific job they've taken an interest in).

- **`jobs.status`** — deterministic pipeline state, set only by ingestion/normalization/dedup/matching code: `DISCOVERED → NORMALIZED → (DUPLICATE | MATCHED) → (ERROR on failure)`. A job never moves through these because of anything the user or the LLM does; it moves because Adzuna returned it and code processed it.
- **`applications.status`** — the user-facing lifecycle, created the moment a user takes a first interest action ("Save") on a `MATCHED` job. This is the exact 11-state list:

```
SAVED, REVIEWED, APPROVED, PREPARING, READY_FOR_USER, APPLYING, APPLIED, INTERVIEW, OFFER, REJECTED, WITHDRAWN
```

This split removes the redundancy the first version had (a `saved_jobs` table plus overlapping job-status values) — saving a job *is* creating an application row in `SAVED` status; there is no separate saved-jobs concept anymore.

```mermaid
stateDiagram-v2
    [*] --> SAVED: user saves a MATCHED job
    SAVED --> REVIEWED: user opens full detail
    REVIEWED --> APPROVED: user approves
    REVIEWED --> WITHDRAWN: user dismisses
    APPROVED --> PREPARING: prep starts (AI drafts + optional automation fill)
    PREPARING --> READY_FOR_USER: materials staged, form filled if automated
    READY_FOR_USER --> APPLYING: user gives explicit submit approval\n(Stop/Show/Wait/Continue gate)
    READY_FOR_USER --> APPROVED: user cancels prep, goes back
    APPLYING --> APPLIED: submission independently verified
    APPLIED --> INTERVIEW: email/user signal
    APPLIED --> REJECTED: email/user signal
    INTERVIEW --> OFFER: user signal
    INTERVIEW --> REJECTED: email/user signal
    OFFER --> WITHDRAWN: user declines offer
    OFFER --> [*]: user accepts (outside system scope)
    APPLIED --> WITHDRAWN: user withdraws
    INTERVIEW --> WITHDRAWN: user withdraws
    REJECTED --> [*]
    WITHDRAWN --> [*]
```

- **`READY_FOR_USER` is the Stop→Show→Wait→Continue gate materialized as a real, queryable state**, not just a UI modal — an application can sit in `READY_FOR_USER` indefinitely (e.g. the user gets distracted, closes the app, comes back tomorrow) and the system's database is the source of truth for "this is staged and waiting for you," which fits the ADHD-friendly "resume where I left off" need directly.
- Every arrow above is a recorded `application_events` row (see `06-database-design.md`), whether triggered by the user, an automation step, or a detected email — nothing changes status silently.
- Invalid transitions (e.g. `SAVED → APPLIED` directly) are rejected at the database and application layer alike (see `09-testing-strategy.md`).

## Application preparation and submission flow

```mermaid
flowchart TD
    APPROVED["APPROVED"] --> STAGE["Stage application materials\n(CV excerpt selection, cover letter draft,\nform-field mapping)"]
    STAGE --> AIPREP["AI drafts prep material\n(schema-validated, evidence-checked\nagainst Adzuna fields + CV)"]
    AIPREP --> USERREVIEW["User reviews staged materials"]
    USERREVIEW -->|edits| STAGE
    USERREVIEW -->|approves prep| AUTOFILL{"Automation available\nfor this application URL?"}
    AUTOFILL -->|yes| PWFILL["Playwright fills form\n(see 03-job-sources-and-browser-automation.md)"]
    AUTOFILL -->|no| MANUAL["Staged materials shown as\nreference for manual application"]
    PWFILL --> READY["Status: READY_FOR_USER"]
    MANUAL --> READY
    READY --> CONFIRM["Stop / Show / Wait for explicit submit approval"]
    CONFIRM -->|approved| APPLYING["Status: APPLYING"]
    APPLYING --> SUBMIT["Submission occurs\n(user-initiated click, or user does it manually)"]
    SUBMIT --> VERIFYSUBMIT["Independently verify submission\n(confirmation page/DOM state, or user attestation\nrecorded distinctly from an AI/automation claim)"]
    VERIFYSUBMIT --> APPLIED["Status: APPLIED"]
```

A "submitted successfully" message from the automation layer is never, by itself, sufficient to flip status to `APPLIED`. The system requires an independent signal (a confirmation page element, a confirmation email later matched by email monitoring, or an explicit user attestation click logged as a *user* action, not inferred from automation output) — same rule as `02-ai-and-matching-architecture.md`, applied here.

## Email monitoring

Unchanged in shape from the first version, retargeted to the new state names: a narrowly-scoped subsystem that reads a connected mailbox (read-only/minimal scope), classifies messages, and proposes linking them to an existing `applications` row — never auto-transitioning status without user confirmation.

```mermaid
sequenceDiagram
    participant Sched as Scheduler
    participant Email as Email Monitoring Service
    participant Mailbox as User's Mailbox
    participant AI as Local AI (classification)
    participant App as Application Tracking
    participant User as User

    Sched->>Email: poll (interval)
    Email->>Mailbox: fetch new messages (read-only scope)
    Email->>Email: pre-filter (sender/subject heuristics)
    Email->>AI: classify candidate messages (structured schema)
    AI-->>Email: {category, confidence, extracted_fields, evidence, verification_status}
    Email->>Email: verify extracted fields against message text
    Email->>App: propose linking message to application\n(never auto-applied silently)
    App->>User: surfaced as a detected event awaiting acknowledgement
    User->>App: confirms / corrects the link and resulting status suggestion\n(e.g. APPLIED -> INTERVIEW)
```

- **Categories detected**: application confirmation, interview invitation, rejection, request for more information, recruiter outreach, general hiring-process update.
- **Never deletes email.** Read and label/tag only, if the provider supports non-destructive tagging.
- **Never acts on instructions inside an email.** Same untrusted-input treatment as job postings — see `08-security-and-prompt-injection.md`.
- **Association, not auto-transition.** A detected event proposes a status change (e.g. suggesting `APPLIED → INTERVIEW`); the user confirms or corrects it.
- **Evidence preserved**: the original message reference and the exact excerpt that triggered classification are stored.

## Notifications

Unchanged: a thin surface over `application_events`, new `MATCHED` jobs above the score threshold, and unconfirmed `email_events` — no second source of truth, no general-purpose alerting ambition.
