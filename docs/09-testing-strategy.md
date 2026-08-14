# Testing Strategy

Testing is designed before implementation and organized around the same layers as the architecture.

## Test categories

- **Unit tests**: canonical job model validation, normalization mapping, deduplication key logic, matching sub-score calculations, AI schema validation, evidence-verification claim checking, configuration loading.
- **Integration tests**: DB persistence round-trips, local Ollama call + response handling (against a real local Ollama instance in CI where available, else a recorded-fixture double), Adzuna adapter against fixture pages/API responses, end-to-end orchestrator run against fixtures, evidence recording.
- **Adzuna connector tests**: authentication, rate limits/quota handling, pagination, malformed responses, missing job fields — all run against saved fixture API responses so tests don't depend on the live third-party service; a small, explicitly-labeled live-smoke check (run manually / on a schedule, never blocking normal CI) exercises the real API to catch drift early, always kept clearly distinguished from fixture-based "proof."
- **Normalization & deduplication tests**: missing-field handling, duplicate-from-different-pages, malformed source data, near-duplicate titles that must *not* be merged (different roles at the same company).
- **Deterministic pre-filter tests**: title/keyword exclusion, skill-floor threshold, location/remote incompatibility, salary-floor rejection — each verified independently of the AI stage.
- **CV/matching tests**: deterministic sub-score calculations across all considered factors (skills, networking/cybersecurity/sysadmin experience, work experience, education, certifications, languages, role fit, location, remote/hybrid/on-site, employment type, experience level, salary).
- **AI schema tests**: valid responses accepted; missing required fields, wrong types, and extra fields all rejected; ambiguous/low-confidence responses correctly routed to `UNKNOWN`.
- **Hallucination / evidence tests**: fixture jobs and fixture CVs paired with known-correct expected extractions; assert the AI analysis never introduces a skill, certification, work-history entry, education credential, language, salary, or requirement absent from the fixture text, and that any such attempt is caught by verification and downgraded/rejected rather than shown as fact. Includes the canonical cases: a demonstrated skill scored as `matching_skills`/`FACT`, and an undemonstrated required skill correctly scored `missing_requirements` or `unknown_requirements`, never invented as a match.
- **Untrusted-input handling test (kept simple, not a dedicated suite)**: a handful of fixture job postings containing embedded text that reads like an instruction (e.g. "ignore previous instructions," "contact HR directly") assert no behavioral change results — output is still schema-valid and still evidence-checked. This is a small sanity check, not a large adversarial security test suite, consistent with the project's explicit choice not to build a dedicated prompt-injection subsystem.
- **Authorization tests**: user A cannot read, list, or mutate user B's profile, jobs, resumes, or saved jobs, through either the API layer or a direct-DB path exercising RLS.
- **Database tests**: constraint enforcement, RLS policy tests (per table, per CRUD verb), migration correctness.
- **Ollama-unavailable / model-missing tests**: assert the system reports an explicit degraded state (`AI_UNAVAILABLE`, naming the configured model and whether it's installed) rather than silently failing or fabricating output, and never auto-pulls or substitutes a different model.
- **Regression tests**: once a real bug is found and fixed, a regression test is added from that exact real-world evidence before the fix is considered complete.

## Explicit adversarial/edge cases

| Case | Expected behavior |
|---|---|
| AI invents a skill, certification, or work-history entry not in the CV | Verification finds no supporting text, claim rejected/downgraded to `UNKNOWN` |
| AI invents a salary | Same as above |
| AI invents remote status | Same as above |
| AI invents a job requirement not present in the Adzuna description | Same as above |
| Job description contains text resembling an instruction | No behavioral deviation; still schema-valid, still evidence-checked output only |
| Duplicate jobs from the same source | Merged into one job record with multiple evidence entries, not duplicated |
| Missing salary | Field stored as null, shown as "not specified" — never defaulted to a guessed value |
| Missing location | Same treatment |
| Adzuna field conflicts with an AI claim (e.g. AI states a different salary than Adzuna's `salary_min`/`salary_max`) | Adzuna's field wins; the AI's claim is rejected, never shown at equal confidence (`03-job-sources.md`, "Adzuna wins") |
| Adzuna daily quota exhausted mid-run | Discovery stops cleanly, run marked quota-exhausted (not a generic error), no partial/corrupt job records, user notified |
| Adzuna returns a malformed/incomplete job record | Normalization stores what's present, nulls the rest, never invents a value; job still gets evidence-recorded |
| Configured Ollama analysis model is missing locally | System reports "Required Ollama model is not installed," names the exact configured model tag and the exact `ollama pull` command; never auto-pulls, never substitutes a different installed model |
| Attempt to queue more than the configured LLM concurrency ceiling at once | Excess requests queue (FIFO, deterministic-score tiebreak) rather than firing in parallel against Ollama |
| Job fails the cheap deterministic pre-filter | Never dequeued for AI analysis at all; stored with `passed_prefilter=false`, visible in the low-priority view only |
| User attempts to access another user's data | 403/blocked at both the API-authorization layer and RLS |

## What "passing" means

A test suite pass is only ever reported alongside which of the categories above it covers, and fixture-based passes are never described as proof of live-system behavior. Any status report on this project must distinguish "unit/fixture tests pass" from "verified against the real live Adzuna API / real Ollama instance."
