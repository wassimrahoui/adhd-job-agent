# Testing Strategy

Testing is designed before implementation and organized around the same layers as the architecture.

## Test categories

- **Unit tests**: canonical job model validation, normalization mapping, deduplication key logic, deterministic pre-filter checks, AI schema validation, the evidence-verification containment check, configuration loading.
- **Integration tests**: SQLite persistence round-trips, a local Ollama call + response handling (against a real local Ollama instance in CI where available, else a recorded-fixture double), Adzuna adapter against fixture pages/API responses, end-to-end `POST /jobs/search` run against fixtures.
- **Adzuna connector tests**: authentication, rate limits/quota handling, pagination, malformed responses, missing job fields — run against saved fixture API responses so tests don't depend on the live third-party service; a small, explicitly-labeled live-smoke check (run manually, never blocking normal CI) exercises the real API to catch drift early.
- **Normalization & deduplication tests**: missing-field handling, duplicate-from-different-pages, malformed source data, near-duplicate titles that must *not* be merged (different roles at the same company).
- **Deterministic pre-filter tests**: location, salary, employment type, experience level, excluded keywords, required skills — each verified independently of the AI stage, against the fixed set of checks (not a weighted scoring system).
- **AI schema tests**: valid responses accepted; missing required fields, wrong types, and extra fields all rejected and trigger the single retry; a still-invalid response after retry is marked `AI_UNAVAILABLE`.
- **Evidence tests**: fixture jobs and fixture CVs paired with known-correct expected extractions; assert the AI analysis never introduces a skill, certification, work-history entry, education credential, language, salary, or requirement absent from the compact context actually sent to the model, and that any such attempt is caught by the containment check and downgraded to `UNKNOWN`/`NOT_DEMONSTRATED` rather than shown as fact. Includes the canonical cases: a demonstrated skill scored as `matching_skills`, and an undemonstrated required skill correctly scored `missing_requirements` or `unknown_requirements`, never invented as a match.
- **Untrusted-input handling test (kept simple, not a dedicated suite)**: a handful of fixture job postings containing embedded text that reads like an instruction (e.g. "ignore previous instructions") assert no behavioral change results — output is still schema-valid and still evidence-checked. This is a small sanity check, not a large adversarial security test suite.
- **Database tests**: SQLite constraint enforcement, migration correctness against a fresh file.
- **Ollama-unavailable / model-missing tests**: assert the system reports an explicit `AI_UNAVAILABLE`/"model not installed" state (naming the configured model) rather than silently failing or fabricating output, and never auto-pulls or substitutes a different model.
- **Regression tests**: once a real bug is found and fixed, a regression test is added from that exact real-world evidence before the fix is considered complete.

## Explicit adversarial/edge cases

| Case | Expected behavior |
|---|---|
| AI invents a skill, certification, or work-history entry not in the CV | Evidence check finds no matching text in the supplied context, claim downgraded to `UNKNOWN`/`NOT_DEMONSTRATED` |
| AI invents a salary, remote status, or requirement not present in the job data sent | Same as above |
| Job description contains text resembling an instruction | No behavioral deviation; still schema-valid, still evidence-checked output only |
| Duplicate jobs from the same source | Merged into one job row, not duplicated |
| Missing salary or location | Field stored as null, shown as "not specified" — never defaulted to a guessed value |
| Adzuna field conflicts with an AI claim (e.g. AI states a different salary than `salary_min`/`salary_max`) | Adzuna's field wins; the AI's claim is discarded (`03-job-sources.md`, "Adzuna wins") |
| Adzuna daily quota exhausted mid-search | Search stops cleanly, marked quota-exhausted (not a generic error), no partial/corrupt job rows, user notified |
| Adzuna returns a malformed/incomplete job record | Normalization stores what's present, nulls the rest, never invents a value |
| Configured Ollama analysis model is missing locally | System reports "Required Ollama model is not installed," names the exact configured model tag and the exact `ollama pull` command; never auto-pulls, never substitutes |
| Model response is malformed | One retry; if the retry is also malformed, that job is marked `AI_UNAVAILABLE` and the pre-filter result is still shown |
| Job fails the cheap deterministic pre-filter | Never sent to Ollama at all; stored with `passed_prefilter=false`, visible in the low-priority view only |
| A search is triggered while a previous search's analysis loop is still running | The second request either waits or is rejected with a clear "a search is already in progress" message — there is never more than one Ollama request in flight |

## What "passing" means

A test suite pass is only ever reported alongside which of the categories above it covers, and fixture-based passes are never described as proof of live-system behavior. Any status report on this project must distinguish "unit/fixture tests pass" from "verified against the real live Adzuna API / real Ollama instance."
