# PR 1 — Foundation and data model

Use this prompt with Claude for PR 1.

## Low-token startup

1. Read `START_HERE.md`.
2. Read `CLAUDE.md`.
3. Read this prompt and `context-packs/foundation.context.md`.
4. Load full docs only when necessary.

## Goal

Add metadata DB, tenants, storage accounts, projects, buckets, objects, provider keys, B2 file-name builder, seeded demo data, and local mock-friendly foundations. Include `region`, `alias`, and `provider_member_email` on storage accounts and support tenant-to-many-storage-accounts.

## Scope

Metadata model, migrations, shared B2 file-name builder, demo tenant/project/storage account, account/sub-account isolation metadata. Do not implement Partner API calls yet.

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

- deterministic B2 file-name generation
- distribution_id appears near beginning
- storage_account belongs to tenant
- bucket belongs to storage_account
- cross-tenant metadata access denied

## After editing

- Run formatting/linting/tests relevant to the change.
- Validate JSON if touched.
- Summarize files changed, behavior changed, tests, risks, and follow-ups.

## Suggested PR title

Add neocloud foundation and data model

## Suggested PR description

Add a summary, what changed, testing, risks, and follow-ups.
