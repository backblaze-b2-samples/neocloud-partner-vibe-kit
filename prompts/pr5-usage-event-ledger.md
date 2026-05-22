# PR 5 — Usage event ledger

Use this prompt with Claude for PR 5.

## Low-token startup

1. Read `START_HERE.md`.
2. Read `CLAUDE.md`.
3. Read this prompt and `context-packs/usage-reporting.context.md`.
4. Load full docs only when necessary.

## Goal

Add append-only durable usage events for data-plane and key/admin operations.

## Scope

Usage event schema, write paths, immutable events, real-time summaries.

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

- upload/download/delete events
- key events
- immutable append-only behavior
- no local counters

## After editing

- Run formatting/linting/tests relevant to the change.
- Validate JSON if touched.
- Summarize files changed, behavior changed, tests, risks, and follow-ups.

## Suggested PR title

Add usage event ledger

## Suggested PR description

Add a summary, what changed, testing, risks, and follow-ups.
