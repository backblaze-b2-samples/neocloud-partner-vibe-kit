<!-- last_verified: 2026-06-09 -->
# Expected PR Outputs

A "what good looks like" reference for each of the 12 roadmap PRs. Use it to
de-risk execution: after running a prompt, compare the result against the
**files you should see**, the **golden output**, and the **acceptance signal**
below.

These are illustrative. The authoritative contracts are `docs/api-contracts.md`
(APIs), `docs/data-model.md` (entities/columns), and each PR's prompt
(`prompts/prN-*.md`). When this doc and those disagree, those win.

> Payloads here are *target* application shapes, not implemented promises — the
> platform is unbuilt (`docs/known-gaps.md` §1). The IDs are illustrative.

---

## PR 1 — Foundation and data model

**Files you should see:** schema/migrations for the core entities (`groups`,
`tenants`, `storage_accounts`, `buckets`, `provider_keys`, `api_keys`,
`projects`, `objects`, `upload_sessions`, `upload_parts`, `usage_events`,
`audit_events`); the shared **B2 file-name builder**; deterministic-naming tests.

**Golden output** — a generated physical B2 file name (distribution_id first):
```text
7f/tenants/tnt_123/projects/prj_456/objects/obj_abc/checkpoint-00042.safetensors
```
`objects` rows store `physical_b2_file_name` + `logical_path`; ownership is by
metadata, never by parsing the key.

**Acceptance signal:** deterministic file-name tests pass (same input → same
name); the name starts with a hash-derived `distribution_id`; a tenant maps to
`storage_accounts`; buckets are child resources.

## PR 2 — Auth, RBAC, and API keys

**Files you should see:** auth middleware, role/permission checks on routes,
`api_keys` usage, `audit_events` writes on admin actions.

**Golden output** — a cross-tenant access attempt is denied with the standard
error shape:
```json
{ "error": { "code": "forbidden", "message": "Cross-tenant access denied",
             "request_id": "req_123", "details": {} } }
```
plus an `audit_events` row for the admin action that triggered it.

**Acceptance signal:** route-level permissions enforced; guessed-ID cross-tenant
access denied; audit events written; CORS is not used as authorization.

## PR 3 — Parallel and resilient uploads

**Files you should see:** upload-session routes
(`POST /tenant/projects/:projectId/upload-sessions` …), multipart orchestration
(bounded concurrency, retry/backoff, abort), `upload_sessions` / `upload_parts`.

**Golden output** — create session for a 5 GB file → multipart:
```json
// request
{ "filename": "checkpoint-00042.safetensors", "size_bytes": 5368709120,
  "content_type": "application/octet-stream" }
// response (mode is "multipart" because size >= 100 MB)
{ "session_id": "ups_789", "mode": "multipart", "part_size_bytes": 104857600,
  "physical_b2_file_name": "7f/tenants/tnt_123/projects/prj_456/objects/obj_abc/checkpoint-00042.safetensors" }
```

**Acceptance signal:** <100 MB → single upload; ≥100 MB → multipart; transient
part failures retry with backoff; cancellation calls multipart abort.

## PR 4 — Download and presigned URL flows

**Files you should see:** `POST /tenant/projects/:projectId/objects/:objectId/download-url`,
metadata-ownership check **before** signing, optional range support.

**Golden output:**
```json
{ "url": "https://s3.{region}.backblazeb2.com/bucket/7f/tenants/…?X-Amz-…",
  "expires_at": "2026-05-21T12:05:00Z" }
```
The platform returns a presigned URL; tenants fetch bytes directly from B2 (no
proxy). A `usage_events` row of `event_type=download` is recorded.

**Acceptance signal:** ownership verified from metadata before any URL is signed;
optional range URL; audit/usage events emitted.

## PR 5 — Usage event ledger

**Files you should see:** append-only `usage_events` writes on
upload/download/delete/admin actions.

**Golden output** — a usage event row:
```json
{ "id": "evt_001", "tenant_id": "tnt_123", "project_id": "prj_456",
  "storage_account_id": "sa_001", "bucket_id": "bkt_1", "object_id": "obj_abc",
  "event_type": "upload", "bytes": 5368709120, "request_id": "req_123",
  "occurred_at": "2026-05-21T12:00:00Z" }
```

**Acceptance signal:** upload/download/delete/admin events recorded durably; **no
local or frontend counters** feed billing.

## PR 6 — B2 CSV ingestion and reconciliation

**Files you should see:** `POST /admin/usage/imports/b2-csv`, CSV parser,
`usage_imports` / `usage_import_rows`, attribution logic. See
`examples/sample-usage-csv/`.

**Golden output** — a raw B2 usage row resolves to an attributed row, or is
flagged for review:
```json
{ "raw_account_id": "0001abcd", "bucket": "acme-uswest-uploads",
  "byte_hours": 3869835264000, "attributed_storage_account_id": "sa_001",
  "attributed_tenant_id": "tnt_123", "status": "attributed" }
// unknown account/bucket → { … "status": "unattributed" }
```

**Acceptance signal:** attribution is provider-account/storage-account **first**;
unknown account/bucket → `unattributed`; re-importing the same file is idempotent.

## PR 7 — Billing and reporting foundation

**Files you should see:** `billing_periods`, `billing_ledger`, report generation +
`POST /admin/reports/:reportId/export`.

**Golden output** — export request and a report line:
```json
// request: POST /admin/reports/billing-periods then export
{ "period": "2026-05", "format": "csv", "tenant_id": "tnt_acme" }
// a per-tenant report line (illustrative)
{ "tenant_id": "tnt_acme", "period": "2026-05", "storage_gb_month": 50000,
  "egress_gb": 30000, "class_b_txns": 40000000, "class_c_txns": 5000000 }
```
Markup/margin is applied here (operator-defined — see `docs/cost-and-tco.md`).

**Acceptance signal:** deterministic tenant/project/period reports; CSV and JSON
exports; figures trace back to `usage_events` + reconciled imports.

## PR 8 — Provider abstraction

**Files you should see:** a provider interface + a **mock** provider for local
dev + a thin Partner API adapter exposing only documented operations.

**Golden output** — the adapter surface (maps 1:1 to documented Partner API ops):
```text
list_groups()                       → b2_list_groups
list_group_members(group_id)        → b2_list_group_members
create_group_member(group_id, memberEmail, …)  → b2_create_group_member
eject_group_member(group_id, accountId)        → b2_eject_group_member   (high-friction)
```
Composite suspend/reactivate/eject are explicit Neocloud operations, not raw
Partner API calls.

**Acceptance signal:** existing Groups listed/linked (no Group *creation* via
API); mock provider works offline; alias maps to `memberEmail`.

## PR 9 — Tenant provisioning with Groups and customer accounts

**Files you should see:** provisioning flow over the provider abstraction;
`POST /admin/tenants/:tenantId/storage-accounts`.

**Golden output** — provision request → `storage_accounts` row:
```json
// request
{ "region": "us-west", "alias": "cust_12345-us-west@storage.example-neocloud.com",
  "group_id": "grp_123", "display_name": "Acme US West Storage Account" }
// resulting storage_accounts row (key fields)
{ "id": "sa_001", "tenant_id": "tnt_123", "region": "us-west",
  "alias": "cust_12345-us-west@storage.example-neocloud.com",
  "provider_member_email": "cust_12345-us-west@storage.example-neocloud.com",
  "s3_endpoint": "s3.{region}.backblazeb2.com", "status": "active" }
```

**Acceptance signal:** Partner API + Group prerequisites documented; existing
Group selected/linked; `alias` sent as `memberEmail`; `s3_endpoint` captured;
eject requires explicit confirmation; multi-region tenant → multiple
`storage_accounts`.

## PR 10 — Platform admin portal

**Files you should see:** operator UI consuming the `/admin/*` APIs.

**Golden output** — views backed by metadata (never direct B2 listing): tenants,
storage accounts, usage (`GET /admin/tenants/:id/usage`), reports, audit events
(`GET /admin/audit/events`), provisioning status.

**Acceptance signal:** operator can manage tenants, storage accounts, usage,
reports, audits, and provisioning status; lists come from the metadata DB.

## PR 11 — Tenant portal

**Files you should see:** tenant self-service UI consuming the `/tenant/*` APIs.

**Golden output** — projects, uploads, objects
(`GET /tenant/projects/:projectId/objects`), API keys, usage, reports. The file
browser shows **logical paths** from metadata; physical B2 names are never
exposed.

**Acceptance signal:** logical paths only; the file browser uses metadata, not
direct B2 prefix enumeration.

## PR 12 — Operational hardening

**Files you should see:** metrics endpoint, alerts, a **stuck-multipart cleanup**
job, **reconciliation drift** monitoring, runbook updates
(`docs/operational-runbook.md`).

**Golden output** — examples:
```text
GET /metrics  → uploads_total, upload_errors_total, reconciliation_drift_bytes …
stuck-multipart cleanup → aborts upload_sessions with status=in_progress older than N hours
reconciliation drift → reports a non-zero delta for S3-direct workloads (not error)
```

**Acceptance signal:** metrics + alerts present; orphaned multipart uploads are
reaped; reconciliation drift is monitored and reported.
