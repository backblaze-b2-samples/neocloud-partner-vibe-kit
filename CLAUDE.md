# CLAUDE.md — Neocloud Vibe Kit

## Purpose

This kit helps build a B2-backed neocloud storage control plane and data plane. It is a Claude-ready implementation guide and reference package, not a finished production platform and not a consumer file upload demo.

## Minimal Context Mode

When the user asks to save tokens:

1. Read `START_HERE.md` first.
2. Read only the relevant prompt and context pack.
3. Prefer context packs over full docs.
4. Do not load Postman unless the task is API/Postman-specific.
5. Do not load the original Vibe Coding Starter Kit unless the task is reuse/dev-experience-specific.
6. Ask before loading additional large files.

## Source-of-truth order

Use `docs/source-of-truth.md` to resolve conflicts. In short: golden rules here, then source-of-truth, API contracts, data model, task-specific docs, roadmap, prompts, Postman, then original starter kit.

## Golden rules

- Use the 12-PR roadmap as the canonical implementation sequence.
- Prompt files in `prompts/` must match the canonical PR numbers.
- Do not treat this as a consumer file upload app.
- Do not combine unrelated roadmap phases into one PR unless explicitly asked.
- Preserve local developer experience.
- Keep every PR reviewable.
- Add tests for every new behavior.
- Neocloud tenant isolation is account/sub-account-driven, not bucket-driven.
- A tenant/customer maps to a provisioned B2 customer account/sub-account where possible.
- Groups should be enabled and used to organize customer accounts.
- A Group can hold up to 5,000 accounts.
- B2 has a default limit of 100 buckets per account.
- Buckets are resources inside a customer account, not the primary tenant isolation boundary.
- A starter workflow may create a default bucket inside a customer account for demo simplicity; this is not an architectural requirement.
- Use metadata to map tenant IDs to provider customer account IDs, Group IDs, buckets, provider keys, objects, B2 file names, usage records, and audit events.
- Authorization must use trusted metadata and auth context, not bucket names, B2 file-name parsing, or frontend-provided IDs.
- Backblaze B2 object keys are B2 file names. `objects` is not a bucket or directory; slashes are part of the B2 file name. For high-scale generated names, the first file-name component should be the hash-derived `distribution_id`, not a constant string.
- Do not describe B2 object naming as AWS-style prefix partitioning.
- Generated B2 file names for high-scale workloads must be distributed across the lexicographical keyspace.
- Usage attribution starts with provider account/storage account, then bucket ID/name, then internal metadata. Bucket name alone is not a reliable tenant attribution key.
- Usage reporting must use durable records, not frontend counters or local JSON counters.
- Backblaze B2 should be treated as high-throughput object storage, not high-IOPS tiny-object database storage.
- Prefer objects of at least 1 MB when practical, but do not globally reject smaller objects.
- When a workload can concatenate, pack, batch, or aggregate small files into larger objects, prefer that pattern. Use manifests or indexes plus range reads to retrieve individual logical files or records; this can lower request rate, reduce per-object overhead, and increase potential throughput.
- Small files are allowed when the workflow needs them.
- Partner API must be enabled by the Backblaze sales/team process. Customers cannot self-enable it.
- Groups must be enabled and created in the Backblaze website before the app links/selects them. Do not implement Backblaze Group creation through an API.
- Partner API is required for provisioning and ejecting customer accounts.
- Recommended customer account alias/memberEmail pattern: `<partner_customer_id>-<b2_partner_region>@<partner_storage_domain>`. The Neocloud alias maps to Backblaze `memberEmail`.
- Do not use Partner API eject for normal suspend/reactivate. Eject removes the account from the Group but does not delete it, existing application keys can continue to function unless separately handled, and the account cannot be re-added to a Group through the Partner API.
- A customer account lives in a pre-defined region. Multi-region customers require multiple B2 customer accounts/sub-accounts.
- Partner API integration must be abstracted so local development can use a mock provider.
- Never hardcode production credentials, account IDs, customer data, bucket IDs, tokens, or secrets.
- The platform's own control plane and platform-mediated data plane use the B2 Native API and Partner API. The S3-compatible API is offered to tenants as an alternative interface to their own data — tenants use the same B2 application key as an AWS-style access key/secret via SigV4. See `docs/s3-compatible-api.md` and `docs/adr/008-b2-native-vs-s3-compatible.md`.
- Backblaze's S3-compatible API supports SigV4 only (not SigV2), SSE-B2 and SSE-C (not SSE-KMS), and no object tagging / no IAM roles / no website configuration / no object-level ACLs. Do not design workflows that depend on the unsupported features.
- **Least privilege everywhere.** Every credential is scoped to the minimum capabilities required for its workload. Default tenant capabilities: `listFiles, readFiles, writeFiles, shareFiles` (add `deleteFiles` only when needed).
- **The operator master application key is for the platform's control plane only.** It must never be used as a tenant credential or configured into any S3 client. Backblaze does not restrict the master key from the S3 API at the protocol level — the restriction is a platform policy you enforce. A leaked master key in an S3 config file compromises every provisioned customer account.

For the "don't" side of these rules — concrete wrong patterns, why they're wrong, and what to do instead — see `docs/common-pitfalls.md`. Use it as a PR review aid alongside `docs/quality-gates.md`.

## Generic-by-default rule

The kit provides safe defaults without forcing one customer workflow.

Hardcode only invariants: account/sub-account isolation, website-created Groups, Partner API enablement assumptions, alias-to-memberEmail mapping, regional account rules, eject-not-suspend semantics, metadata-based authorization, B2 file-name distribution, durable usage events, no secrets, no local counters for billing, and no direct B2 listing as the primary tenant dashboard source.

Make these configurable: portal workflow, report format, quota policy, bucket layout inside customer accounts, lifecycle/retention choices, upload concurrency, billing export format, provisioning approval flow, admin roles, customer account alias/memberEmail pattern, region/account mapping, and small-file packing strategy.

## Canonical roadmap

1. PR 1 — Foundation and data model
2. PR 2 — Auth, RBAC, and API keys
3. PR 3 — Parallel and resilient uploads
4. PR 4 — Download and presigned URL flows
5. PR 5 — Usage event ledger
6. PR 6 — B2 usage CSV ingestion and reconciliation
7. PR 7 — Billing and reporting foundation
8. PR 8 — Provider abstraction
9. PR 9 — Tenant provisioning with Groups and customer accounts/sub-accounts
10. PR 10 — Platform admin portal
11. PR 11 — Tenant portal
12. PR 12 — Operational hardening

## Upload defaults

- Normal single-object upload for files smaller than 100 MB.
- Multipart upload for files >= 100 MB.
- Default multipart part size: 100 MB.
- Minimum multipart part size: 5 MB except final part.
- Maximum part size: 5 GB.
- Maximum parts: 10,000.
- Adaptive part size for very large files, rounded up to nearest 5 MB.
- Per-file part concurrency: 4.
- Batch file concurrency: 3.
- Global in-flight upload requests: 10.
- Retry transient failures up to 3 times with exponential backoff and jitter.
- Retry 408, 425, 429, 500, 502, 503, 504, and network errors.
- Do not retry 400, 401, 403, 404, or 413.
- Abort incomplete multipart uploads on cancellation or final failure.

Do not confuse these concepts:

- 1 MB: preferred minimum object-size guideline when practical.
- 5 MB: minimum multipart part size except final part.
- 100 MB: multipart threshold and default part-size guideline.

## B2 file-name distribution

Default physical B2 file-name layout:

```text
{distribution_id}/tenants/{tenant_id}/projects/{project_id}/objects/{object_id}/{safe_filename}
```

`distribution_id` is a stable hash-derived value near the beginning of the B2 file name. Use 2 hex characters by default and allow 4 for extreme-scale workloads. Store the physical B2 file name in metadata. Show logical names to users.

## Before editing code

1. Read `START_HERE.md`.
2. Load only the relevant prompt and context pack.
3. Inspect current architecture.
4. Run baseline tests if code changes are planned.
5. Report baseline failures separately.
6. Identify exact files expected to change.
7. Present an implementation plan.

## After editing code

1. Run formatting, linting, type checks, and relevant tests.
2. Validate JSON artifacts if touched.
3. Smoke test the changed flow when possible.
4. Summarize files changed, behavior changed, tests added, commands run, risks, assumptions, and follow-ups.
5. Review against `docs/common-pitfalls.md` and `docs/quality-gates.md` before opening the PR.
6. Provide PR title and description.

## Postman guidance

The corrected B2 Native API Postman collection lives at `postman/Backblaze_B2_Postman_Collection_CORRECTED_v3.json`. It is a candidate reference, not the target neocloud application API contract. Use `docs/api-contracts.md` for target platform APIs. Do not implement from Postman blindly.

## Reusing the original Vibe Coding Starter Kit

Reuse local setup clarity, environment examples, B2 client examples, upload/list/download/delete examples, drag-and-drop UX, validation, dashboard patterns, health/metrics/logging, and test conventions. Do not reuse one-bucket/one-key/no-database assumptions, direct bucket listing as app state, original filenames as durable identity, sequential-only uploads, local counters for usage, CORS as authorization, or object-name parsing as authorization.
