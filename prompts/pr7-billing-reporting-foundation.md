# PR 7 — Billing and reporting foundation

Use this prompt with Claude for PR 7.

## Low-token startup

1. Read `START_HERE.md`.
2. Read `CLAUDE.md`.
3. Read this prompt and `context-packs/billing.context.md`.
4. Load full docs only when necessary.

## Goal

Add deterministic billing-period reports and exports from usage ledger/reconciled imports.

## Scope

Billing periods, rollups, CSV/JSON exports, draft/final report states.

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

- deterministic rollups
- export CSV/JSON
- reports by tenant/project/storage account
- no frontend/local counters

## After editing

- Run formatting/linting/tests relevant to the change.
- Validate JSON if touched.
- Summarize files changed, behavior changed, tests, risks, and follow-ups.

## Suggested PR title

Add billing reporting foundation

## Suggested PR description

Add a summary, what changed, testing, risks, and follow-ups.
