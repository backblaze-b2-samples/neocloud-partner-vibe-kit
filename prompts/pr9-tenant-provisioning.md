# PR 9 — Tenant provisioning

Use this prompt with Claude for PR 9.

## Low-token startup

1. Read `START_HERE.md`.
2. Read `CLAUDE.md`.
3. Read this prompt and `context-packs/provisioning.context.md`.
4. Load full docs only when necessary.

## Goal

Implement Group-aware tenant provisioning with existing Backblaze Groups, customer accounts/sub-accounts, aliases/memberEmail values, regions, buckets, and provider keys.

## Scope

Partner API enablement prerequisite, Groups website prerequisite, existing Group selection/linking, account create/eject, alias-to-memberEmail mapping, bucket/key child workflows, audited provisioning, and explicit eject warnings.

The provisioning response must capture and persist the S3 endpoint host returned by the Partner API on each `storage_accounts` row (column: `s3_endpoint`). This value is what tenants need to configure S3 clients. The Partner API region code and the S3 endpoint label are different values — store both. See `docs/s3-compatible-api.md` §Region Values.

Tenants receive a single provider key per workload that works for both B2 Native and S3-compatible API access. Do not provision a separate AWS-style credential. The provider key capability set follows the minimum-privilege list in `CLAUDE.md` §Key Capabilities Reference. The operator master key must not be exposed in any tenant-facing response or used as a tenant's S3 credential.

## Non-goals

- Do not implement unrelated roadmap phases.
- Do not implement Backblaze Group creation; Groups are created in the Backblaze website after Groups are enabled.
- Do not hardcode secrets or real provider IDs.
- Preserve local developer experience.

## Before editing

- Inspect current architecture.
- Run baseline tests if code changes are planned.
- Identify expected files to change.
- Present a concise plan.

## Required tests

- Partner API enablement documented
- Group enablement and website-only Group creation documented
- provider contract excludes `createGroup`
- mock provider seeds existing Groups and supports selection/linking
- region and alias/memberEmail stored
- alias/memberEmail is email-shaped and deterministic
- multi-region tenant supported
- existing Group assignment recorded
- Partner API eject is not used for normal suspend/reactivate
- eject requires explicit operator confirmation and warns that Partner API re-add is not supported
- provisioning audited
- `storage_accounts.s3_endpoint` is captured at provisioning time and distinguishable from the Partner API region code
- tenant provisioning response surfaces the S3 endpoint along with the B2 Native API URL — tenant is informed of both API surfaces
- the operator master key is not returned in any provisioning response and is not stored on any tenant-facing record

## After editing

- Run formatting/linting/tests relevant to the change.
- Validate JSON if touched.
- Summarize files changed, behavior changed, tests, risks, and follow-ups.

## Suggested PR title

Add tenant provisioning with existing Groups

## Suggested PR description

Add a summary, what changed, testing, risks, and follow-ups.
