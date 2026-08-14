# AI Architecture, Matching, and Hallucination Control

## Conceptual pipeline

```mermaid
flowchart TD
    RAW["Raw job (Adzuna)"] --> NORMALIZE["Normalize into canonical job schema"]
    NORMALIZE --> STORE["Store canonical job + evidence"]
    STORE --> PROFILE["Retrieve user profile"]
    PROFILE --> DETMATCH["Deterministic matching"]
    DETMATCH --> PREFILTER{"Passes cheap\ndeterministic pre-filter?"}
    PREFILTER -->|no| SKIP["Never sent to the LLM.\nStored as low/no match."]
    PREFILTER -->|yes| QUEUE["Enter bounded, low-concurrency\nanalysis queue"]
    QUEUE --> CONTEXT["Build verified-facts context for LLM\n(Adzuna structured fields + snippet + CV)"]
    CONTEXT --> LLM["LLM analysis (local Ollama, one job at a time)"]
    LLM --> SCHEMA["Schema validation"]
    SCHEMA -->|invalid| REJECT["Reject / retry once / mark AI_UNAVAILABLE"]
    SCHEMA -->|valid| VERIFY["Evidence verification\n(Adzuna fields win over any conflicting claim)"]
    VERIFY --> LABEL["Label every claim FACT / INFERENCE / UNKNOWN"]
    LABEL --> FINAL["Final recommendation\n(relevance score + matching_skills +\nmatching_experience + missing_requirements + explanation)"]
    FINAL --> THRESHOLD{"Relevance score meets the\nconfigurable threshold?"}
    THRESHOLD -->|no| LOWPRI["Stored, visible only in the\nlow-priority / 'not a match' view"]
    THRESHOLD -->|yes| REVIEW["Shown to the user as a relevant match"]
```

## A/B/C/D separation

- **A. Facts** — the immutable source record: Adzuna's structured fields and description snippet, the user's CV/profile as entered. Adzuna's structured fields are the highest tier of fact in this system (see `03-job-sources-and-browser-automation.md`, "Adzuna wins"). Nothing downstream may alter these.
- **B. Deterministic calculations** — plain code, no LLM: salary range comparison, location/remote compatibility, skill-list intersection, employment-type match, duplicate detection, required-field completeness, the deterministic pre-filter (below), and the numeric deterministic sub-scores that feed the final score.
- **C. LLM interpretation** — semantic judgment where language understanding earns its keep: comparing the job against the user's CV/profile, transferable-skill reasoning, summarizing nuanced requirements from the description snippet, flagging concerns, writing the human-readable explanation. This is a real, active role in the AI Job Agent's search-to-relevance loop (see `03-job-sources-and-browser-automation.md`) — what's fixed is narrower than "the LLM has no role": the LLM component itself never searches, never queries Adzuna, and never decides what jobs exist; it only ever compares jobs Adzuna already returned against the CV/profile it's given.
- **D. User decision** — approve, save, dismiss, or apply. The AI's output is always a recommendation, never an action.

**Rule of thumb:** if a normal `if`/comparison/lookup can compute it reliably from Adzuna's structured fields, it is computed in B, not asked of the LLM.

## Cheap deterministic pre-filter — before anything reaches the LLM

Every job that passes normalization and dedup goes through a fast, pure-code pre-filter *before* it is eligible for LLM analysis at all:

- Hard exclusion keywords present (title/description) → excluded, never queued.
- Required-skill floor not met (e.g. zero overlap with the profile's required skills) → excluded, never queued.
- Location/remote-mode incompatible with the profile's acceptance settings → excluded, never queued.
- Salary (where Adzuna states it, accounting for `salary_is_predicted`) below the profile's stated minimum → excluded, never queued.

Jobs that fail this pre-filter are still stored (visible to the user in a low-priority/"not a match" view if they want to look) but are **never sent to Ollama**. This exists for two reasons at once: it keeps the transparent-score promise honest (a job with zero required skills shouldn't need an LLM to tell the user it's not a fit), and — just as importantly given the target hardware (see `14-model-evaluation.md`) — it keeps GPU/RAM load down by only ever running the LLM on jobs worth the cost.

## Relevance-threshold cutoff — after scoring, before the user ever sees it

Passing the pre-filter and getting an LLM analysis does not by itself make a job "relevant" to the user. After the six-layer defense (below) produces a verified `relevance_score`, that score is compared against a configurable threshold (a profile-level setting, sensible default provided): jobs at or above the threshold are surfaced in the normal review queues; jobs below it are stored and reachable in a low-priority view, but do not compete for the user's attention on the Home/Today screen or Job Review queue. This threshold is what actually implements "the user only sees relevant jobs" — the pre-filter alone only removes obvious non-matches, it doesn't rank the ones that remain.

## LLM concurrency: low and queued, never parallel-blasted

The AI Analysis Engine processes jobs through a **bounded, low-concurrency queue** — the default and recommended configuration is **concurrency = 1** (exactly one job in flight against Ollama at a time); a configuration ceiling exists but is not expected to be raised above a small number (2–3) even on capable hardware, and must never be set high enough to fire many simultaneous requests at Ollama. This is a hard architectural rule, not a performance nice-to-have: the target machine (`14-model-evaluation.md`) runs Ollama alongside other active software sharing the same 32GB system RAM and 16GB GPU, and uncontrolled concurrent inference is the single fastest way to exhaust either budget or starve the rest of the machine. The queue is FIFO by default, with the deterministic score used as a tiebreaker so the strongest candidate jobs are analyzed first if the queue backs up.

```mermaid
flowchart LR
    Q["Analysis Queue\n(FIFO, deterministic-score tiebreak)"] --> WORKER["Single analysis worker\n(concurrency=1 default)"]
    WORKER --> OLLAMA["Ollama\n(one request in flight)"]
    OLLAMA --> WORKER
    WORKER --> NEXT["Next job dequeued\nonly after this one completes"]
```

## Hybrid matching and scoring

```mermaid
flowchart LR
    subgraph Deterministic
        LOC["Location / remote-mode match"]
        SAL["Salary range overlap (Adzuna fields)"]
        SKILL["Required skill coverage"]
        TITLE["Title / seniority compatibility"]
        TYPE["Employment type match"]
        EXCL["Exclusion keywords"]
    end
    subgraph Semantic["LLM semantic layer"]
        TRANS["Transferable skills"]
        NUANCE["Nuanced requirement reading (snippet)"]
        GAPS["Gaps / concerns"]
        EXPLAIN["Plain-language explanation"]
    end
    Deterministic --> DETSCORE["Deterministic sub-score (0-100, weighted)"]
    DETSCORE --> FINAL["Final transparent score"]
    Semantic --> FINAL
    FINAL --> BREAKDOWN["Factor breakdown shown to user\n(never a bare number)"]
```

The deterministic sub-score is computed first and is never overridden by the LLM. The score shown to the user is always accompanied by its factor breakdown. Weighting of deterministic factors is user-configurable in the profile.

## Structured AI output and the evidence-claim schema

Every AI call has a fixed Pydantic contract. Conceptual schema for the core "analyze job fit" call — every retained/relevant job must be able to show all of these fields to the user, each evidence-based:

```json
{
  "relevance_score": "integer 0-100, the score the threshold cutoff is applied to",
  "overall_recommendation": "strong_match | possible_match | weak_match | not_enough_information",
  "confidence": "high | medium | low",
  "matching_skills": [
    {
      "claim": "string naming the matched skill and how it applies",
      "claim_type": "skill",
      "verification_status": "FACT | INFERENCE | UNKNOWN",
      "source_excerpt": "string quoting the exact CV/profile and/or job text supporting this match, or null if UNKNOWN",
      "confidence": "high | medium | low"
    }
  ],
  "matching_experience": [
    {
      "claim": "string naming the matched experience (work history, cybersecurity/networking experience, education, certifications, etc.) and how it applies",
      "claim_type": "requirement | qualification | transferable_skill | other",
      "verification_status": "FACT | INFERENCE | UNKNOWN",
      "source_excerpt": "string, or null if UNKNOWN",
      "confidence": "high | medium | low"
    }
  ],
  "missing_requirements": [
    {
      "claim": "string naming a stated job requirement the CV/profile does not demonstrate",
      "claim_type": "requirement | qualification | skill | other",
      "verification_status": "FACT | INFERENCE | UNKNOWN",
      "source_excerpt": "string quoting the job text stating the requirement, or null if UNKNOWN",
      "confidence": "high | medium | low"
    }
  ],
  "claims": [
    {
      "claim": "string, any other factual or semantic statement not covered above (salary, location, remote_status, benefit, deadline, etc.)",
      "claim_type": "salary | location | remote_status | benefit | deadline | other",
      "verification_status": "FACT | INFERENCE | UNKNOWN",
      "source_excerpt": "string quoting the exact Adzuna field or description snippet text supporting this claim, or null if UNKNOWN",
      "confidence": "high | medium | low"
    }
  ],
  "concerns": ["string"],
  "explanation": "string, 2-4 sentences, plain language"
}
```

`matching_skills`, `matching_experience`, and `missing_requirements` are the named categories the UI surfaces directly for every retained job, alongside `relevance_score`, `overall_recommendation`, `concerns`, and `explanation` — this is what "every retained job shows relevance score, recommendation, matching skills, matching experience, missing requirements, concerns, and explanation" means concretely. They share the same evidence-item shape as the general `claims` array, so the FACT/INFERENCE/UNKNOWN discipline below applies uniformly across all four arrays.

Every individual claim the model makes — not just the response as a whole — carries its own `verification_status`:

- **`FACT`** — directly stated in an Adzuna structured field or located verbatim/near-verbatim in the description snippet, and confirmed by the deterministic verifier (below) against that exact source, not just asserted by the model. `source_excerpt` is mandatory and must be a real substring of the evidence, not a paraphrase.
- **`INFERENCE`** — a reasonable semantic judgment the LLM is allowed to make (transferable skills, "this role likely involves X given the description's phrasing") that is not directly stated. Always shown to the user distinctly from `FACT`, always carries a `source_excerpt` showing what it was inferred *from*, and is never used to satisfy a deterministic hard filter — inferences inform the narrative, never the pass/fail gates in section "Cheap deterministic pre-filter" above.
- **`UNKNOWN`** — the model correctly identifies that neither Adzuna's structured fields nor the description snippet specify something (e.g. remote policy, benefits, exact seniority). `source_excerpt` is `null`. This is a rewarded, correct answer, not a failure — a model that says `UNKNOWN` where information genuinely isn't present is doing its job.

Any claim with `claim_type` covering a field Adzuna states structurally (`salary`, `location`, `remote_status` where derivable, `deadline` if Adzuna provides one) is checked directly against that Adzuna field, not the free-text snippet — and if the claim conflicts with Adzuna's value, the claim is rejected outright regardless of its self-reported `verification_status` (per "Adzuna wins," `03-job-sources-and-browser-automation.md`).

## The six-layer defense against hallucination

1. **Layer 1 — Minimal, verified context.** The LLM receives only the normalized job (Adzuna fields + snippet), the relevant CV/profile fields — work experience, technical skills, cybersecurity/networking experience, education, certifications, languages, desired roles, location/salary/remote preferences, experience level (`00-vision-and-requirements.md` requirement 5) — and the deterministic match results — nothing else, and never other users' or system data. Any field absent from the CV/profile is simply not present in the context; the model is never handed a placeholder or assumed value for it.
2. **Layer 2 — Structured output required.** Every meaningful AI call returns the fixed schema above. Free-text-only responses are never accepted for anything the system will act on or display as fact.
3. **Layer 3 — Schema validation.** Pydantic validation on every response; wrong types, missing required fields, or extra hallucinated fields cause outright rejection, not coercion.
4. **Layer 4 — Evidence verification.** Every claim is checked: Adzuna-structural claims against the Adzuna field directly; snippet-derived claims against the stored description text via deterministic substring/similarity matching (not another LLM call).
5. **Layer 5 — Reject unsupported claims.** Anything that fails verification is removed or its `verification_status` is force-corrected to `UNKNOWN`/rejected — never silently kept at its self-reported status.
6. **Layer 6 — FACT / INFERENCE / UNKNOWN labeling in the UI.** Every claim the user sees carries its label visibly. This is the user-facing enforcement of the whole pipeline's honesty.

```mermaid
flowchart TD
    L1["Layer 1: Minimal verified context"] --> L2["Layer 2: Structured output required"]
    L2 --> L3["Layer 3: Schema validation"]
    L3 -->|fail| REJECT["Reject response,\nmark AI step failed"]
    L3 -->|pass| L4["Layer 4: Evidence verification\n(Adzuna fields checked first)"]
    L4 --> L5["Layer 5: Reject/downgrade unsupported claims"]
    L5 --> L6["Layer 6: FACT/INFERENCE/UNKNOWN labels in UI"]
```

## Never trust the AI's report that something happened

Carried forward as a permanent architectural law (see ADR-002), with one clarification: this governs *machine* self-reports, not direct user actions. If the AI says a claim is a `FACT`, the system re-derives/verifies it against Adzuna's fields or the snippet before treating it as one. If the post-MVP "Assist Me" helper reports "field filled," the system independently re-reads the live page/DOM state before treating that field as populated — but no component in this system ever reports "application submitted," because no component ever submits one; submission is always the user's own click on the real page, and "Applied" is recorded only from the user's own self-attestation, which is authoritative by definition rather than something requiring re-verification (see ADR-002 addendum, `12-architecture-decisions.md`). Audit log entries distinguish "action attempted," "self-reported as complete" (machine actions only), and "independently verified as complete" / "user-attested" as separate states, never collapsed into one.

## LLM / model strategy

- **Runtime**: local Ollama only. No cloud LLM API, no cloud fallback. If Ollama is unreachable or the configured model is missing, AI-dependent fields are marked `AI_UNAVAILABLE` and the deterministic match result is still shown (ADR-006) — no fabricated "demo" analysis is ever generated.
- **Exactly one model at a time, pinned by exact tag.** The current leading candidate, chosen against the real target hardware and pending real-hardware benchmark validation, is `qwen2.5:14b-instruct-q4_K_M` — see `14-model-evaluation.md` for the selection criteria, the full hardware budget it was chosen against, its candidate status, and the manual-pull/no-auto-download/no-silent-substitution contract, which applies regardless of which exact tag ends up pinned.
- **Model adapter layer**: the AI Analysis Engine talks to an internal `LocalModelAdapter` interface (model name/tag, endpoint, prompt templates, and schema per task are configuration, not hard-coded call sites) so a future model change is a config change, not a code change — but changing the pinned model is still a deliberate, documented decision (see `14-model-evaluation.md`), never an automatic upgrade.
