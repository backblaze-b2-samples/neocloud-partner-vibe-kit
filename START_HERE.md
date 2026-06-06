---
status: routing
token_note: Read this first. It tells Claude which minimal files to load for each workflow.
---

# START_HERE.md

Use this file to reduce token usage. Do **not** load the entire Neocloud / Partner Vibe Kit by default.

Start with:

1. `CLAUDE.md`
2. The one canonical prompt for the PR you are implementing
3. The matching context pack
4. One or two source-of-truth docs only when the task needs them

Only open Postman when the task is specifically about B2 API requests, Postman, or API validation. Only open the original Vibe Coding Starter Kit when the task is specifically about developer experience or reuse guidance.

## Minimal Context Mode

When the user asks to save tokens:

1. Read only `START_HERE.md`, `CLAUDE.md`, and the relevant prompt file.
2. Prefer a context pack over full reference docs.
3. Do not open full reference docs unless needed.
4. Summarize assumptions before editing.
5. Ask before loading additional large files.
6. Do not load Postman unless the task is API/Postman-specific.
7. Do not load the original Vibe Coding Starter Kit unless the task is reuse/dev-experience-specific.
8. Do not load more than one task-specific doc unless required.

## What to read for each task

| Task | Prompt | Context pack | Source-of-truth docs |
|---|---|---|---|
| Foundation / data model | `prompts/pr1-foundation.md` | `context-packs/foundation.context.md` | `docs/data-model.md`, `docs/security-and-tenant-isolation.md` |
| Auth / RBAC | `prompts/pr2-auth-rbac-api-keys.md` | `context-packs/foundation.context.md` | `docs/security-and-tenant-isolation.md`, `docs/api-contracts.md` |
| Uploads | `prompts/pr3-parallel-resilient-uploads.md` | `context-packs/uploads.context.md` | `docs/upload-data-plane.md`, `docs/small-file-and-throughput-guidance.md`, `docs/api-contracts.md` |
| Downloads / presigned URLs | `prompts/pr4-download-presigned-urls.md` | `context-packs/uploads.context.md` | `docs/api-contracts.md` |
| Usage event ledger | `prompts/pr5-usage-event-ledger.md` | `context-packs/usage-reporting.context.md` | `docs/usage-reporting-and-billing.md`, `docs/data-model.md` |
| B2 CSV ingestion / reconciliation | `prompts/pr6-b2-csv-ingestion-reconciliation.md` | `context-packs/usage-reporting.context.md` | `docs/usage-reporting-and-billing.md`, `examples/sample-usage-csv/README.md` |
| Billing | `prompts/pr7-billing-reporting-foundation.md` | `context-packs/billing.context.md` | `docs/usage-reporting-and-billing.md` |
| Provider abstraction | `prompts/pr8-provider-abstraction.md` | `context-packs/provisioning.context.md` | `docs/provisioning-and-partner-api.md`, `docs/data-model.md` |
| Tenant provisioning | `prompts/pr9-tenant-provisioning.md` | `context-packs/provisioning.context.md` | `docs/provisioning-and-partner-api.md`, `docs/adr/007-partner-api-enablements-and-regional-accounts.md` |
| Platform admin portal | `prompts/pr10-platform-admin-portal.md` | `context-packs/portal.context.md` | `docs/api-contracts.md`, `docs/data-model.md` |
| Tenant portal | `prompts/pr11-tenant-portal.md` | `context-packs/portal.context.md` | `docs/api-contracts.md`, `docs/security-and-tenant-isolation.md` |
| Operations | `prompts/pr12-operational-hardening.md` | `context-packs/operations.context.md` | `docs/operational-runbook.md`, `docs/quality-gates.md` |
| Small-file workloads | PR-specific prompt | `context-packs/small-files.context.md` | `docs/small-file-and-throughput-guidance.md`, `docs/upload-data-plane.md` |

## Cross-cutting reference docs

These docs are not tied to one PR. Read them when the task calls for them.

| When you need... | Read |
|---|---|
| A term definition | `docs/glossary.md` |
| A configurable setting (env var, overlay key) | `docs/configuration-reference.md` |
| Incident response procedure (failed uploads, stuck sessions, ejection, key rotation, etc.) | `docs/operational-runbook.md` |
| To know what the kit does NOT cover | `docs/known-gaps.md` |
| A narrative walkthrough of the platform | `docs/demo-script.md` |
| A PR review checklist | `docs/quality-gates.md` |
| Common mistakes to avoid | `docs/common-pitfalls.md` |
| Setting up the platform for the first time | `docs/first-time-operator-setup.md` |
| Pre-production security review | `docs/security-review-checklist.md` |
| S3-compatible API surface (supported ops, auth, endpoints) | `docs/s3-compatible-api.md` |
| Why both B2 Native and S3 are supported | `docs/adr/008-b2-native-vs-s3-compatible.md` |
| A step-by-step recipe for a common task | `docs/workflow-recipes.md` |
| A rationale for a major design decision | `docs/adr/` |

## Hard invariants

Customer overlays and workflow recipes can change configurable choices, but they must not override these invariants:

- Tenant isolation is account/sub-account-driven, not bucket-driven.
- Tenant/customer records map to provisioned B2 customer accounts/sub-accounts.
- Groups are used to organize customer accounts, but Groups are created in the Backblaze website after Groups are enabled, not through the Partner API.
- Partner API enablement is handled through the Backblaze sales/team process; customers cannot self-enable it.
- A B2 customer account lives in a pre-defined region; multi-region customers require multiple accounts.
- Authorization uses trusted metadata and auth context.
- B2 file names for high-scale generated object workloads are distributed across the lexicographical keyspace.
- Usage and billing are based on durable records, not local/frontend counters.
- Postman is reference material, not the source of truth for the target neocloud application API.
