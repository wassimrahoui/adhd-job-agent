# ADHD-Friendly UX

## Principles

- **One clear next action per screen.** Every screen answers "what should I do right now" without the user having to infer it from a dashboard full of widgets.
- **Small, bounded decisions.** Save / Dismiss, not a form with a dozen fields to consider at once.
- **Visible progress, not open-ended lists.** "3 of 8 new matches reviewed today," not an infinite unsorted feed.
- **Status is always legible.** A job's state is shown as a short, plain-language label, never left implicit.
- **Explanations over scores.** A number alone ("87%") is meaningless and easy to distrust or obsess over; a short factor breakdown is both more useful and more calming.
- **Minimal simultaneous choices.** Secondary actions (view full posting, view evidence) are tucked behind a single "more" affordance, not laid out alongside the primary action.
- **No infinite scroll of undifferentiated jobs.** Jobs are triaged into small, prioritized queues (e.g., "Review today," "Saved for later") rather than one long list competing for attention.
- **Gentle, not naggy, notifications.** A small number of surfaced items, not a badge-count arms race.

## Core screens (intent, not pixel-level design)

1. **Home / Today** — "What needs my attention." New relevant matches to review, that's it. Each item has one obvious primary action.
2. **Job Review** — one job at a time. Title, company, location/salary/work-mode at a glance, deterministic factor breakdown, AI explanation with per-claim FACT/INFERENCE/UNKNOWN labels (matching skills, matching experience, missing requirements, unknown requirements), the original Adzuna application link, and two big actions: Save, Dismiss.
3. **Saved** — a short, filterable queue of jobs saved for later, not a growing backlog treated as a to-do guilt list; stale saved jobs are gently surfaced ("saved 3 weeks ago — still interested?") rather than silently forgotten or silently expired. This is a bookmark, not an application-status tracker — the system has no concept of "applied," "in progress," or "rejected."
4. **Job Search** — the search/preference form that drives the Adzuna query (keywords, location, salary floor, category, remote/hybrid/on-site).
5. **Profile / CV** — a guided, section-by-section editor (experience, skills, certifications, languages, preferences) rather than one giant form; changes are saved incrementally.
6. **Settings** — Adzuna connection status, analysis-model status (a plain "Ollama: connected / unavailable" indicator, naming the configured model and whether it's installed), relevance-threshold configuration.

## What is deliberately not built

- No dense enterprise-style multi-column dashboard with many simultaneous KPIs.
- No infinite customizable widgets/report builder.
- No gamified streaks or guilt-inducing pressure messaging — encouragement framing only, and always optional to dismiss.
- No screen that requires reading more than a short paragraph to know what to do next.
- No application-tracking screen, no application-history screen, no email-events screen — this project ends at showing the user a relevant job and its original application link.
