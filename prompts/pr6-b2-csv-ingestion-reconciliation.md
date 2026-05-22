# PR 6 — B2 usage CSV ingestion and reconciliation

Use this prompt with Claude for PR 6.

## Low-token startup

1. Read `START_HERE.md`.
2. Read `CLAUDE.md`.
3. Read this prompt and `context-packs/usage-reporting.context.md`.
4. Load full docs only when necessary.

## Goal

Import B2 usage CSVs, normalize rows, attribute account-first, reconcile with internal events, and store unattributed rows.

## Scope

CSV import, checksum idempotency, attribution, discrepancy reports.

## Non-goals

- Do not implement unrelated roadmap phases.
- Do not hardcode secrets or real provider IDs.
- Preserve local developer experience.

## Before editing

- Inspect current architecture.
- Run baseline tests if code changes are planned.
- Identify expected files to change.
- Present a concise plan.

## Required tests

- account-first attribution
- bucket secondary attribution
- unknown rows unattributed
- idempotent import
- reconciliation drift report

## After editing

- Run formatting/linting/tests relevant to the change.
- Validate JSON if touched.
- Summarize files changed, behavior changed, tests, risks, and follow-ups.

## Suggested PR title

Add B2 usage CSV ingestion

## Suggested PR description

Add a summary, what changed, testing, risks, and follow-ups.
