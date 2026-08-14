# ADHD-Friendly UX

## Principles

- **One clear next action per screen.** Every screen answers "what should I do right now" without the user having to infer it from a dashboard full of widgets.
- **Visible progress, not open-ended lists.** A search's results are a bounded, understandable set, not an infinite unsorted feed.
- **Status is always legible.** A job's state (matched, not a match, AI unavailable) is shown as a short, plain-language label, never left implicit.
- **Explanations over scores.** A number alone ("87%") is meaningless and easy to distrust or obsess over; a short explanation is both more useful and more calming.
- **Minimal simultaneous choices.** The primary action on a result — open the details — is obvious; the original application link is the other clear action once on a job's page.
- **No infinite scroll of undifferentiated jobs.** Results from a search are shown together, sorted by score, not accumulated into a growing backlog.

## Core screens (intent, not pixel-level design)

The MVP has four screens. Nothing else is built until a real need shows up.

1. **Jobs / Search** — a "Search Jobs" button that triggers the pipeline (Adzuna → normalize → dedup → pre-filter → Ollama analysis), and, below it, the results list: title, company, location, salary when available, relevance score, recommendation, a short explanation, and the original application link, for each job. Sorted by score, highest first.
2. **Job Details** — one job, full picture: the original job information, matching skills, matching experience, missing requirements, unknown requirements, evidence, the AI's explanation, the score, and the original application URL.
3. **CV / Profile / Preferences** — a single editable form: work experience, technical skills, networking/cybersecurity/sysadmin experience, education, certifications, languages, desired roles, location preferences, salary requirements, remote/hybrid/on-site preference, experience level, and search keywords/exclusions. One place, saved as one profile.
4. **Settings / Status** — Adzuna connection status, Ollama status (a plain "connected / unavailable" indicator naming the configured model and whether it's installed), and the relevance-score threshold.

## What is deliberately not built

- No dense enterprise-style multi-column dashboard with many simultaneous KPIs.
- No infinite customizable widgets/report builder.
- No gamified streaks or guilt-inducing pressure messaging.
- No screen that requires reading more than a short paragraph to know what to do next.
- No application-tracking screen, no application-history screen, no email-events screen — this project ends at showing the user a relevant job and its original application link.
- No separate "saved jobs" / bookmark screen for the MVP — the results list from the last search is where jobs live; if a persistent bookmark list turns out to be genuinely needed later, it's a small, deliberate addition, not something built speculatively now.
- No "Home / Today" screen with overnight/scheduled activity — there's no scheduler in the MVP, so there's nothing to summarize before the user has run a search.
