# PR 4 — Download and presigned URL flows

Use this prompt with Claude for PR 4.

## Low-token startup

1. Read `START_HERE.md`.
2. Read `CLAUDE.md`.
3. Read this prompt and `context-packs/uploads.context.md`.
4. Load full docs only when necessary.

## Goal

Add authorized download URLs, optional range URLs, and usage/audit events for downloads.

## Scope

Metadata auth before signing, logical object IDs, optional packed-object range support.

Two presigned URL paths exist and the PR must distinguish them:

1. **Platform-issued presigned URL** (this PR): the platform's `POST /tenant/projects/:projectId/objects/:objectId/presign` endpoint, backed by B2 Native `b2_get_download_authorization`. The platform writes a `usage_events` row on issuance and the URL is scoped to the requested object.
2. **Tenant-generated S3 presigned URL** (NOT this PR): the tenant uses an AWS SDK against the S3-compatible API to generate presigned URLs client-side using their own provider key. The platform does not see these. Document the S3 alternative in tenant-facing materials but do not implement an in-platform analog.

See `docs/s3-compatible-api.md` §Presigned URLs via S3.

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

- auth required before signing
- cross-tenant download denied
- range URL validates ownership
- usage event emitted
- platform-issued presigned URL does NOT use the operator master key (uses a scoped key for the issuing call where applicable)
- tenant-generated S3 presigned URLs are documented in tenant materials but not implemented as a platform endpoint

## After editing

- Run formatting/linting/tests relevant to the change.
- Validate JSON if touched.
- Summarize files changed, behavior changed, tests, risks, and follow-ups.

## Suggested PR title

Add authorized download URL flows

## Suggested PR description

Add a summary, what changed, testing, risks, and follow-ups.
