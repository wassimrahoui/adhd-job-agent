# ADHD-Friendly UX

## Principles

- **One clear next action per screen.** Every screen answers "what should I do right now" without the user having to infer it from a dashboard full of widgets.
- **Small, bounded decisions.** Approve / Save / Dismiss, not a form with a dozen fields to consider at once.
- **Visible progress, not open-ended lists.** "3 of 8 new matches reviewed today," not an infinite unsorted feed.
- **Status is always legible.** A job or application's state is shown as a short, plain-language label plus a one-line "what happens next," never left implicit.
- **Explanations over scores.** A number alone ("87%") is meaningless and easy to distrust or obsess over; a short factor breakdown is both more useful and more calming.
- **Minimal simultaneous choices.** Secondary actions (edit, view full posting, view evidence) are tucked behind a single "more" affordance, not laid out alongside the primary action.
- **No infinite scroll of undifferentiated jobs.** Jobs are triaged into small, prioritized queues (e.g., "Review today," "Saved for later") rather than one long list competing for attention.
- **Gentle, not naggy, notifications.** A small number of surfaced items, not a badge-count arms race.

## Core screens (intent, not pixel-level design)

1. **Home / Today** — "What needs my attention." Three sections at most: new strong matches to review, applications needing a follow-up, unconfirmed email events. Each item has one obvious primary action.
2. **Job Review** — one job at a time. Title, company, location/salary/work-mode at a glance, deterministic factor breakdown, AI explanation with per-claim FACT/INFERENCE/UNKNOWN labels, and three big actions: Approve, Save, Dismiss. A secondary "view original posting" link for anyone who wants to double-check (rarely needed, precisely because the system already shows its evidence).
3. **Saved** — a short, filterable queue of jobs saved for later, not a growing backlog treated as a to-do guilt list; stale saved jobs are gently surfaced ("saved 3 weeks ago — still interested?") rather than silently forgotten or silently expired.
4. **Application Prep** — shows optional AI-drafted staged materials (CV excerpt highlights, cover-letter draft) for the user to review or skip, then one clear "Go apply" action that opens the original job's source URL for the user to apply manually themselves. There is no automated form-fill or submit action in MVP. Post-MVP, once the user has clicked through and is on the employer/ATS page, an optional "Assist Me" action may appear (opt-in, verified-CV-data-only field suggestions, never a Submit action of its own — `03-job-sources-and-browser-automation.md`).
5. **Applications** — grouped by status (Applied, Interview, Offer, etc.) with the next suggested action per item ("Follow up? It's been 10 days since you applied.").
6. **Profile / CV** — a guided, section-by-section editor (experience, skills, preferences) rather than one giant form; changes are saved incrementally.
7. **Settings** — source configuration, AI model status (including a plain "Ollama: connected / unavailable" indicator), notification preferences, mailbox connection.

## What is deliberately not built

- No dense enterprise-style multi-column dashboard with many simultaneous KPIs.
- No infinite customizable widgets/report builder.
- No gamified streaks or guilt-inducing "you haven't applied in X days" pressure messaging — encouragement framing only, and always optional to dismiss.
- No screen that requires reading more than a short paragraph to know what to do next.
