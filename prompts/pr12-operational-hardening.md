# PR 12 — Operational hardening

Use this prompt with Claude for PR 12.

## Low-token startup

1. Read `START_HERE.md`.
2. Read `CLAUDE.md`.
3. Read this prompt and `context-packs/operations.context.md`.
4. Load full docs only when necessary.

## Goal

Add production-readiness checks, metrics, alerts, runbooks, and cleanup jobs.

## Scope

Health, metrics, stuck multipart cleanup, provider errors, reconciliation drift, key revocation, small-file amplification monitoring.

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

- stuck multipart cleanup
- provider error metrics
- reconciliation drift alert
- regional usage aggregation
- runbook coverage

## After editing

- Run formatting/linting/tests relevant to the change.
- Validate JSON if touched.
- Summarize files changed, behavior changed, tests, risks, and follow-ups.

## Suggested PR title

Add operational hardening

## Suggested PR description

Add a summary, what changed, testing, risks, and follow-ups.
