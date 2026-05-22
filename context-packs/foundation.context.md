---
status: context-pack
token_note: Short compressed context. Open full docs only when needed.
---

# Foundation Context

## Purpose
Foundation, metadata, and ownership model.

## Read this when
Implementing PR 1 or checking tenant/account/object ownership.

## Source-of-truth docs
`docs/data-model.md`, `docs/security-and-tenant-isolation.md`, `docs/source-of-truth.md`.

## Core rules
- Tenant maps to B2 customer account/sub-account through `storage_accounts`.
- Groups organize customer accounts; a Group can hold up to 5,000 accounts.
- B2 has a default 100-bucket-per-account planning constraint.
- Buckets are child resources.
- Storage accounts include region and alias/memberEmail metadata for provider account mapping.
- Metadata DB is the application source of truth.
- Physical B2 file names start with `{distribution_id}/...`.

## Required tests
Metadata ownership, B2 file-name generation/distribution, cross-tenant denial.

## Common mistakes
Bucket-driven isolation, direct B2 listing as state, parsing B2 file names for auth.
