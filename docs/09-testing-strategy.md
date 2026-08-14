# Testing Strategy

Testing is designed before implementation, per the spec's requirement, and is organized around the same layers as the architecture.

## Test categories

- **Unit tests**: canonical job model validation, normalization mapping, deduplication key logic, matching sub-score calculations, AI schema validation, evidence-verification claim checking, state-machine transition rules, configuration loading.
- **Integration tests**: DB persistence round-trips, local Ollama call + response handling (against a real local Ollama instance in CI where available, else a recorded-fixture double), the Adzuna connector against fixture API responses, end-to-end orchestrator run against fixtures, evidence recording.
- **Adzuna connector tests**: run against saved fixture API responses so tests don't depend on live Adzuna calls; a small, explicitly-labeled live-smoke suite (run manually / on a schedule, never blocking normal CI) exercises the real Adzuna API to catch response-shape drift early, always kept clearly distinguished from fixture-based "proof" per the lesson in prototype 1's `MASTER_PLAN.md` (never represent a fixture pass as live-system proof).
- **Normalization & deduplication tests**: missing-field handling, duplicate-from-different-pages-of-the-same-Adzuna-query, malformed Adzuna response data, near-duplicate titles that must *not* be merged (different roles at the same company).
- **AI schema tests**: valid responses accepted; missing required fields, wrong types, and extra fields all rejected; ambiguous/low-confidence responses correctly routed to `UNKNOWN`.
- **Hallucination / evidence tests**: fixture jobs (Adzuna-shaped) paired with known-correct expected `FACT`/`INFERENCE`/`UNKNOWN` labels; assert the AI analysis never introduces a fact (salary, remote status, requirement, deadline, benefit, qualification) absent from the fixture's Adzuna fields and snippet, and that any such attempt is caught by verification and downgraded/rejected.
- **Prompt-injection tests**: fixture job postings and emails containing embedded instructions ("ignore previous instructions," "mark as submitted," "reveal your system prompt," fake authority claims); assert no behavioral change results — output is still schema-valid, still evidence-checked, and no action beyond normal analysis occurs.
- **Browser automation tests**: run against local controlled test pages (not live third-party ATSs) — expected-page mismatch aborts correctly; form-fill read-back diff catches mismatches; captcha/auth-required states surface as human-intervention needed; the automation controller never reaches a submit action without a prior recorded user-approval token; unexpected-page-after-navigation is detected and aborts.
- **Authorization tests**: user A cannot read, list, or mutate user B's profile, jobs, applications, resumes, or evidence, through either the API layer or a direct-DB path exercising RLS.
- **Application workflow tests**: every state-machine transition in `04-application-lifecycle-and-email.md` is individually tested, including invalid-transition rejection (e.g. `SAVED → APPLIED` directly is rejected).
- **Database tests**: constraint enforcement, RLS policy tests (per table, per CRUD verb), the application status transition guard, migration correctness.
- **Email processing tests**: correct classification of each category on fixture messages; injected-instruction messages produce no mutating behavior (see prompt-injection tests); duplicate/already-linked messages don't create duplicate events.
- **Regression tests**: once a real bug is found and fixed (as prototype 1's live SuccessFactors run did with a real async-render timing bug), a regression test is added from that exact real-world evidence before the fix is considered complete.

## Explicit adversarial/edge cases required by the spec

| Case | Expected behavior |
|---|---|
| AI claims an action happened that it did not | System independently verifies before recording; claim alone is never sufficient (see `02-ai-and-matching-architecture.md`) |
| AI invents a salary | Verification finds no supporting Adzuna field or snippet text, claim rejected/downgraded to `UNKNOWN` |
| AI invents remote status | Same as above |
| AI invents requirements | Same as above |
| Job description contains prompt injection | No behavioral deviation; still schema-valid, still evidence-checked output only |
| Duplicate jobs from different Adzuna pages/queries | Merged into one job record with multiple evidence entries, not duplicated |
| Missing salary | Field stored as null, shown as "not specified" — never defaulted to a guessed value |
| Missing location | Same treatment |
| User attempts to access another user's data | 403/blocked at both the API-authorization layer and RLS |
| Adzuna field conflicts with an AI claim (e.g. AI states a different salary than Adzuna's `salary_min`/`salary_max`) | Adzuna's field wins; the AI's claim is rejected, never shown at equal confidence (`03-job-sources-and-browser-automation.md`, "Adzuna wins") |
| Adzuna daily quota exhausted mid-run | Discovery stops cleanly, run marked quota-exhausted (not a generic error), no partial/corrupt job records, user notified |
| Adzuna returns a malformed/incomplete job record | Normalization stores what's present, nulls the rest, never invents a value; job still gets evidence-recorded |
| Pinned Ollama model tag is missing locally | System enters `AI_UNAVAILABLE` with an explicit message naming the exact missing tag and the exact `ollama pull` command; never auto-pulls, never substitutes a different installed model |
| Attempt to queue more than the configured LLM concurrency ceiling at once | Excess requests queue (FIFO, deterministic-score tiebreak) rather than firing in parallel against Ollama |
| Job fails the cheap deterministic pre-filter | Never dequeued for LLM analysis at all; stored with `passed_prefilter=false`, visible in the low-priority view only |
| Application status transition attempted out of order (e.g. `SAVED → APPLIED`) | Rejected at both the API layer and the database transition guard (`06-database-design.md`) |
| Browser automation reaches an unexpected page during application prep | Abort per `03-job-sources-and-browser-automation.md`; user notified |

## What "passing" means

A test suite pass is only ever reported alongside which of the categories above it covers, and fixture-based passes are never described as proof of live-system behavior — a direct continuation of the "LIVE_SUCCESSFACTORS = DEFERRED, never PASS" discipline documented in prototype 1's `MASTER_PLAN.md`. Any status report on this project (by a human or a coding agent implementing it) must distinguish "unit/fixture tests pass" from "verified against the real live Adzuna API / real hardware."
