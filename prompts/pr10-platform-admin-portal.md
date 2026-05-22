# PR 10 — Platform admin portal

Use this prompt with Claude for PR 10.

## Low-token startup

1. Read `START_HERE.md`.
2. Read `CLAUDE.md`.
3. Read this prompt and `context-packs/portal.context.md`.
4. Load full docs only when necessary.

## Goal

Add operator-facing portal workflows.

## Scope

Tenants, storage accounts, Groups, provisioning status, usage, reports, audit logs.

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

- admin route auth
- dashboard from metadata
- no direct B2 listing as state
- audit visibility

## After editing

- Run formatting/linting/tests relevant to the change.
- Validate JSON if touched.
- Summarize files changed, behavior changed, tests, risks, and follow-ups.

## Suggested PR title

Add platform admin portal

## Suggested PR description

Add a summary, what changed, testing, risks, and follow-ups.
