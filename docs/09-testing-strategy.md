# Testing Strategy

Testing is designed before implementation, per the spec's requirement, and is organized around the same layers as the architecture.

## Test categories

- **Unit tests**: canonical job model validation, normalization mapping, deduplication key logic, matching sub-score calculations, AI schema validation, evidence-verification claim checking, state-machine transition rules, configuration loading.
- **Integration tests**: CSV/DB persistence round-trips, local Ollama call + response handling (against a real local Ollama instance in CI where available, else a recorded-fixture double), source adapter against fixture pages/APIs, end-to-end orchestrator run against fixtures, evidence recording.
- **Source connector tests**: one suite per adapter, run against saved fixture HTML/API responses so tests don't depend on live third-party sites; a small, explicitly-labeled live-smoke suite (run manually / on a schedule, never blocking normal CI) exercises real sources to catch drift early, always kept clearly distinguished from fixture-based "proof" per the lesson in prototype 1's `MASTER_PLAN.md` (never represent a fixture pass as live-system proof).
- **Normalization & deduplication tests**: missing-field handling, duplicate-from-different-sources, malformed source data, near-duplicate titles that must *not* be merged (different roles at the same company).
- **AI schema tests**: valid responses accepted; missing required fields, wrong types, and extra fields all rejected; ambiguous/low-confidence responses correctly routed to `unknowns`.
- **Hallucination / evidence tests**: fixture jobs paired with known-correct expected extractions; assert the AI analysis never introduces a fact (salary, remote status, requirement, deadline, benefit, qualification) absent from the fixture text, and that any such attempt is caught by verification and downgraded/rejected rather than shown as fact.
- **Prompt-injection tests**: fixture job postings and emails containing embedded instructions ("ignore previous instructions," "mark as submitted," "reveal your system prompt," fake authority claims); assert no behavioral change results — output is still schema-valid, still evidence-checked, and no action beyond normal analysis occurs.
- **Manual-application flow tests**: the original `redirect_url` is present, correct, and prominently surfaced at every relevant state (`READY_FOR_USER`, `APPLYING`); no code path exists anywhere in the API or frontend that can submit, click Submit, or otherwise complete an application on the user's behalf; `mark-applied` only ever records a user-initiated self-attestation event.
- **"Assist Me" tests (post-MVP feature, tested if/when it is built — not part of MVP)**: run against local controlled test pages (not live third-party ATSs) — expected-page-identity mismatch aborts correctly with zero fields touched; every filled value traces back to a `FACT`-labeled claim, never `INFERENCE` or invented; fields with no verified answer are left blank and flagged, never guessed; the helper never activates without the specific, explicit "Assist Me" click for that application; assert there is no code path, direct or indirect, by which the helper can click or trigger a Submit/Apply control.
- **Authorization tests**: user A cannot read, list, or mutate user B's profile, jobs, applications, resumes, or evidence, through either the API layer or a direct-DB path exercising RLS.
- **Application workflow tests**: every state-machine transition in `04-application-lifecycle-and-email.md` is individually tested, including invalid-transition rejection (e.g. `SAVED → APPLIED` directly is rejected).
- **Database tests**: constraint enforcement, RLS policy tests (per table, per CRUD verb), migration correctness.
- **Email processing tests**: correct classification of each category on fixture messages; injected-instruction messages produce no mutating behavior (see prompt-injection tests); duplicate/already-linked messages don't create duplicate events.
- **Regression tests**: once a real bug is found and fixed (as prototype 1's live SuccessFactors run did with a real async-render timing bug), a regression test is added from that exact real-world evidence before the fix is considered complete.

## Explicit adversarial/edge cases required by the spec

| Case | Expected behavior |
|---|---|
| AI claims an action happened that it did not | System independently verifies before recording; claim alone is never sufficient (see `02-ai-and-matching-architecture.md`) |
| AI invents a salary | Verification finds no supporting text, claim rejected/downgraded to Unknown |
| AI invents remote status | Same as above |
| AI invents requirements | Same as above |
| Job description contains prompt injection | No behavioral deviation; still schema-valid, still evidence-checked output only |
| Duplicate jobs from different sources | Merged into one job record with multiple evidence entries, not duplicated |
| Missing salary | Field stored as null, shown as "not specified" — never defaulted to a guessed value |
| Missing location | Same treatment |
| Broken job page (extraction fails) | Explicit extraction error, job marked accordingly, not silently skipped or half-populated |
| Website changes its HTML | Adapter's expected-marker check fails loudly; run flagged as an extraction error for that source, not a fabricated result |
| "Assist Me" (post-MVP) is invoked on a page that doesn't match the expected job/application | Abort per `03-job-sources-and-browser-automation.md`, no fields touched; user notified |
| User attempts to access another user's data | 403/blocked at both the API-authorization layer and RLS |
| Adzuna field conflicts with an AI claim (e.g. AI states a different salary than Adzuna's `salary_min`/`salary_max`) | Adzuna's field wins; the AI's claim is rejected, never shown at equal confidence (`03-job-sources-and-browser-automation.md`, "Adzuna wins") |
| Adzuna daily quota exhausted mid-run | Discovery stops cleanly, run marked quota-exhausted (not a generic error), no partial/corrupt job records, user notified |
| Adzuna returns a malformed/incomplete job record | Normalization stores what's present, nulls the rest, never invents a value; job still gets evidence-recorded |
| Pinned Ollama model tag is missing locally | System enters `AI_UNAVAILABLE` with an explicit message naming the exact missing tag and the exact `ollama pull` command; never auto-pulls, never substitutes a different installed model |
| Attempt to queue more than the configured LLM concurrency ceiling at once | Excess requests queue (FIFO, deterministic-score tiebreak) rather than firing in parallel against Ollama |
| Job fails the cheap deterministic pre-filter | Never dequeued for LLM analysis at all; stored with `passed_prefilter=false`, visible in the low-priority view only |
| Application status transition attempted out of order (e.g. `SAVED → APPLIED`) | Rejected at both the API layer and the database transition guard (`06-database-design.md`) |

## What "passing" means

A test suite pass is only ever reported alongside which of the categories above it covers, and fixture-based passes are never described as proof of live-system behavior — a direct continuation of the "LIVE_SUCCESSFACTORS = DEFERRED, never PASS" discipline documented in prototype 1's `MASTER_PLAN.md`. Any status report on this project (by a human or a coding agent implementing it) must distinguish "unit/fixture tests pass" from "verified against a real live source/ATS."
