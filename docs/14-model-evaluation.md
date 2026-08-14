# Local Analysis Model Evaluation and Selection

This document is about the **analysis model** only — the large local Ollama model the finished application uses at runtime to compare jobs against a CV/profile. It is not about, and is not selected based on, any model used by a coding agent to help build this project; that is a completely separate, independently-configured role (`02-ai-and-matching-architecture.md`, "Analysis model vs. coding model").

## Target hardware and budget

The Job Agent runs on Wassim's actual machine, shared with other active software (Docker, browser, coding tools, OS, etc.) — the model choice is constrained by that reality, not by an idealized dedicated-server assumption.

| Resource | Spec | Budget for this app |
|---|---|---|
| CPU | Ryzen 9 9950X | Not a binding constraint for inference; matters for the FastAPI/scheduler processes, which are lightweight relative to LLM inference |
| GPU | RTX 5070 Ti, 16GB VRAM | The model **must fit primarily in VRAM** without excessive CPU offloading — offloading layers to system RAM/CPU on every job analysis would defeat the "low concurrency, fast enough to be usable" requirement and compete with everything else on the box |
| System RAM | 32GB total, shared with other running software | **12–16GB preferred, ~20GB hard ceiling** for the Job Agent's own footprint (backend, Postgres, scheduler, and Ollama's non-VRAM overhead combined) — this is not "32GB available," it's "32GB shared," so the app must be a considerate tenant |

## Selection criteria, in order — not hard-coded to an arbitrary popular model

The analysis model is not chosen because it's popular or well-known; it is selected and benchmarked against this project's actual requirements and actual hardware:

1. Reliable structured JSON output under the schema in `02-ai-and-matching-architecture.md` (this is a job-fit reasoning and evidence-labeling task, not a coding task).
2. Instruction-following / rule adherence — must reliably answer `UNKNOWN`/not-demonstrated rather than guess when the schema calls for it.
3. CV/job matching accuracy and hallucination resistance on job-description-style and CV-style text — measured against fixtures with known-correct expected matches, not assumed from general benchmarks.
4. Fits primarily in 16GB VRAM at a quantization level that doesn't meaningfully degrade instruction-following, with headroom left for context and for the fact the GPU isn't dedicated to this app alone.
5. Response speed fast enough that a low-concurrency (effectively serial) queue is still usable — this app deliberately never parallelizes LLM calls (`02-ai-and-matching-architecture.md`), so single-request latency matters more than raw throughput.
6. Multilingual reasoning quality (at minimum English, German, French) to the extent the user's job search spans those languages.
7. **Coding ability is explicitly not a selection factor.** This model never writes or reviews code for this project; a coder-tuned variant is the wrong shape of model for job/CV analysis even if it benchmarks well on coding leaderboards. Coding-agent model selection (if any) is an entirely separate, unrelated decision made for development tooling, not documented here.

## Models considered

| Model | Why considered | Why not selected |
|---|---|---|
| `qwen2.5-coder:14b` | A coder-tuned variant sometimes used for development tooling | Wrong shape of model for this role — coder-tuned, not instruct/reasoning-tuned for general natural-language judgment. Coding-agent model choice and analysis-model choice are unrelated decisions; this entry exists only to make clear a coder model was considered and rejected specifically *for the analysis role* |
| `llama3.1:8b-instruct` | Smaller, faster, very safe VRAM margin | Weaker structured-output and instruction-adherence reliability than Qwen2.5 14B in this size class; kept as a documented lower-hardware fallback, not the primary pick, since the target GPU comfortably supports the 14B tier |
| `qwen2.5:32b-instruct` | Stronger reasoning | Does not fit primarily in 16GB VRAM at a quantization level worth trusting for structured output (would require substantial offload) — violates the "fits primarily in VRAM" hardware rule outright |
| **`qwen2.5:14b-instruct-q4_K_M`** | Strong instruction-following and structured/JSON output, 14.8B parameters at Q4_K_M is a 9.0GB weights footprint — comfortably primary-VRAM-resident on a 16GB card with room left for context and the fact the GPU isn't dedicated solely to this app, general instruct-tuned (not coder-tuned, correct shape for this task), Apache 2.0 licensed, a genuinely "large" model for a single consumer GPU rather than an arbitrary small default | **Current leading candidate — see "Candidate model" below** |

## Candidate model, pending real-hardware benchmark validation

This is the current leading candidate chosen against the selection criteria and hardware budget above — it is not yet a finalized decision. It becomes the configured production model in practice only after passing the benchmark and evidence-suite validation in "Verification before trust" below on Wassim's real machine, measuring VRAM usage, RAM usage, response speed, structured-output reliability, CV/job matching accuracy, hallucination rate, and correct `UNKNOWN`-handling directly, not assumed from spec sheets. Until then, treat every VRAM/RAM/quality figure in this document as an on-paper estimate to be confirmed, not a settled fact.

```
qwen2.5:14b-instruct-q4_K_M
```

- **Exact Ollama tag**: `qwen2.5:14b-instruct-q4_K_M` (verified to resolve on Ollama's library; 14.8B parameters, Q4_K_M quantization, ~9.0GB model weight blob).
- **VRAM fit**: ~9.0GB of weights leaves roughly 7GB of the 16GB card for KV cache/context and for the fact other software may be using the GPU concurrently — comfortably within budget without relying on CPU offload for normal operation.
- **RAM fit**: Ollama's non-VRAM overhead for a model this size, plus the FastAPI backend, Postgres, and scheduler, is expected to land within the 12–16GB preferred range and stay well under the ~20GB ceiling; this must be confirmed empirically once implemented (see Verification below) rather than assumed from spec alone.
- **License**: Apache 2.0 — no restriction relevant to private, non-commercial-adjacent single-user use.

## The model is pinned, not auto-managed

- The application **never** calls `ollama pull` itself, at startup, on first run, or as a "helpful" recovery action. Model management is entirely Wassim's, performed manually via `ollama pull qwen2.5:14b-instruct-q4_K_M`.
- On startup and before any AI call, the backend checks that the exact configured tag is present in the local Ollama instance (via Ollama's model-list API). If it is missing, the system reports "Required Ollama model is not installed," naming the exact configured model and the exact command to fix it — it does not fall back to a different installed model, does not guess at a "close enough" substitute, and does not silently disable AI features without telling the user why.
- **No silent substitution, ever.** If a different model happens to be installed under a similar name, the system does not use it in place of the configured tag. The tag string is compared exactly.
- **No automatic downloads, updates, or model-switching.** Changing the configured model in the future is a deliberate, documented decision (an update to this file plus the relevant ADR), never an automatic upgrade path, and any change must re-pass the verification step below before being wired into the live pipeline.

## Verification before trust, applied to the model itself

Before this model (or any future replacement) is adopted for real use, it must be run against the hallucination/evidence test suite (`09-testing-strategy.md`) using real Adzuna-shaped fixture jobs and fixture CVs with known-correct expected `FACT`/`INFERENCE`/`UNKNOWN` labels, and its actual VRAM/RAM footprint and response speed on the real target machine must be measured (not estimated from vendor figures alone) before being treated as "fits the budget" in practice. Spec-sheet VRAM numbers are a starting point for selection, not a substitute for measuring the real thing on Wassim's actual hardware once implementation begins.
