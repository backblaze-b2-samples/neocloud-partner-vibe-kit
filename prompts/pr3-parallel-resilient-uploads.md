# PR 3 — Parallel and resilient uploads

Use this prompt with Claude for PR 3.

## Low-token startup

1. Read `START_HERE.md`.
2. Read `CLAUDE.md`.
3. Read this prompt and `context-packs/uploads.context.md`.
4. Load full docs only when necessary.

## Goal

Add bounded parallel uploads, multipart uploads, retry/backoff, abort handling, progress, and B2 file-name builder integration.

## Scope

Upload sessions, concurrency, multipart threshold, retry policy, small-file recommendations/warnings. Do not implement billing or provisioning.

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

- <100 MB single upload
- >=100 MB multipart
- retry transient failures
- do not retry auth/validation errors
- abort incomplete multipart
- small files accepted by default

## After editing

- Run formatting/linting/tests relevant to the change.
- Validate JSON if touched.
- Summarize files changed, behavior changed, tests, risks, and follow-ups.

## Suggested PR title

Add parallel and resilient uploads

## Suggested PR description

Add a summary, what changed, testing, risks, and follow-ups.
