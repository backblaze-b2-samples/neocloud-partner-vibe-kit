<!-- last_verified: 2026-06-06 -->
# Demo Script

A walkthrough for demonstrating the Neocloud/Partner Vibe Kit and a reference implementation built from it. The flow takes ~20–30 minutes and is intended for technical audiences (architects, engineers, solution engineers, prospective neocloud operators).

The script assumes:
- A reference implementation built from PRs 1–9 is running locally with `STORAGE_PROVIDER=mock`.
- The audience understands basic object storage concepts.
- No real B2 credentials are needed for the demo.

If the implementation is not built, the script still functions as an architecture walkthrough using the docs alone — skip the live commands and narrate the slides only.

---

## Setup (Before the Demo)

1. Pull the latest reference implementation from the project repo.
2. Confirm `STORAGE_PROVIDER=mock` is set in the environment.
3. Run database migrations and seed demo data: a `tnt_demo` tenant, `prj_demo` project, two seed Groups, and one storage account in `us-west`.
4. Start the server. Confirm `GET /health/ready` returns 200.
5. Open three browser tabs: admin portal, tenant portal, and the API documentation.
6. Have `docs/neocloud-architecture.md` and `docs/provisioning-and-partner-api.md` open in another monitor for reference.

---

## Step 1 — Frame the Problem

**Show:** The README and `docs/neocloud-requirements.md`.

**Say:** The original Backblaze B2 starter kit demonstrates basic upload, list, and download. That is sufficient for one developer demoing one bucket. It does not scale to a neocloud operator who needs to provision dozens of tenants, isolate their data, attribute usage for billing, and operate the platform reliably.

The Neocloud/Partner Vibe Kit is the architecture and implementation guide for that next step. It is not a finished product — it is the blueprint and the prompts to build the platform incrementally.

**Takeaway:** Two distinct problems, two distinct kits. The starter kit is for B2 API familiarity. The Neocloud/Partner Vibe Kit is for building a multi-tenant storage platform on top of B2.

---

## Step 2 — Walk the Architecture

**Show:** `docs/neocloud-architecture.md` and `docs/source-of-truth.md`.

**Say:** The architecture has two planes:
- **Control plane** — tenants, storage accounts, Groups, buckets, keys, audit. Infrequent operations, always mediated by the platform.
- **Data plane** — uploads, downloads, deletes, presigned URLs. High throughput, also mediated.

Tenant isolation is driven by **account/sub-account-per-tenant via the Backblaze Partner API**. Each tenant maps to one or more provisioned B2 customer accounts. Buckets live inside those customer accounts, not at the operator account level.

Highlight the hard invariants in `docs/source-of-truth.md`. These cannot be overridden by customer overlays.

**Takeaway:** Isolation lives at the account boundary, not the bucket boundary. Backblaze Groups organize customer accounts. The Partner API does the provisioning.

---

## Step 3 — Provision a Tenant

**Show:** Admin portal → "Create Tenant" flow. Use the API directly via `curl` for a clearer trace.

**Run:**
```
curl -X POST http://localhost:3000/admin/tenants \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "external_id": "acme-001",
    "region": "us-west"
  }'
```

**Say:** Behind that single API call, the platform:
1. Selects an existing Backblaze Group (created in the Backblaze website — Group creation is not a Partner API operation).
2. Generates a deterministic alias: `cust_acme-001-us-west@storage.example-neocloud.com`. This alias is sent to Backblaze as `memberEmail` via `b2_create_group_member`.
3. Stores the returned provider account ID, Group ID, region, and S3 endpoint on a `storage_accounts` row.
4. Creates one starter bucket inside the new customer account using the naming convention `{platform_prefix}-{tenantId}-primary`.
5. Creates a scoped B2 application key for that bucket with minimum capabilities: `listFiles, readFiles, writeFiles, shareFiles`.
6. Emits audit events for the Group link, account, bucket, and key creation.

**Show:** Query the resulting database state:
- `tenants` row with `status = 'active'`.
- `storage_accounts` row with `region`, `alias`, `provider_member_email`, `provider_customer_account_id`.
- `buckets` row scoped to the storage account.
- `provider_keys` row with `status = 'active'` (no key value stored in the DB).
- `audit_events` rows for each step.

**Takeaway:** One API call → one new tenant with one provisioned customer account, one bucket, one scoped key, and a full audit trail. All keys are scoped within the tenant's customer account.

---

## Step 4 — Upload via Distribution-First B2 File Names

**Show:** Tenant portal → upload page. Run a multipart upload of a 500 MB file.

**Talking points while the upload runs:**

- The platform decided this is a multipart upload because the file exceeds the 100 MB threshold from `CLAUDE.md` §Upload Defaults.
- Part size is 100 MB; concurrency is 4 parts per file, capped at 10 global in-flight requests.
- Each part is uploaded with a fresh part URL — B2 part URLs are single-use.
- The physical B2 file name uses the **distribution-first layout**:
  ```
  objects/{distribution_id}/tenants/{tenant_id}/projects/{project_id}/{object_id}/{safe_filename}
  ```
  where `distribution_id` is the first 2 hex chars of `sha256(tenant:project:object)`.
- This distributes generated names across 256 leading prefixes (`00`–`ff`), avoiding the hot-spot pattern of timestamp- or tenant-ID-prefixed file names.

**Show:** The `objects.physical_b2_file_name` value in the database. Point out the leading `distribution_id`.

**Show:** Interrupt the upload mid-stream. Restart the client. Hit `GET /tenant/projects/:projectId/upload-sessions/:sessionId` and show the uploaded parts list. Resume — verify the remaining parts upload and the session finishes.

**Takeaway:** Distribution-first file names scale. Multipart uploads are resumable. None of this requires the client to know about `b2_start_large_file` or `b2_get_upload_part_url` — the platform mediates.

---

## Step 5 — Usage Events and B2 CSV Import

**Show:** `usage_events` table after a few uploads and downloads.

**Say:** Every platform-mediated data plane operation writes a durable `usage_events` row. This is the platform's own record. It is append-only.

Independent of that, B2 produces usage CSVs (daily and monthly). Those CSVs are the billing source of truth. We ingest them on a schedule.

**Run:**
```
curl -X POST http://localhost:3000/admin/usage/import \
  -H "Authorization: Bearer dev-token" \
  -F "file=@examples/sample-usage-csv/sample-b2-usage.csv"
```

**Show:** The new rows in `usage_imports` (one per CSV) and `usage_import_rows` (one per CSV row). Point out:
- Attribution priority: provider account ID first → storage account → bucket name → unattributed.
- The raw CSV was archived to a control bucket **before** any DB writes.
- Re-running the same import is a no-op (idempotency via `usage_imports.checksum`).

**Show:** The reconciliation job output, comparing `usage_events` totals against `usage_import_rows`. Small deltas at month boundaries are expected (CSV lag). Large deltas would indicate a missing usage_events write or out-of-band B2 access.

**Takeaway:** Two independent ledgers. Both are durable. Provider CSV is the billing source of truth; reconciliation tells us if our internal counters diverge.

---

## Step 6 — Billing Export

**Show:** Admin portal → billing view for `tnt_demo`. Or run:

```
curl -X POST http://localhost:3000/admin/tenants/tnt_demo/billing/2026-05/calculate \
  -H "Authorization: Bearer dev-token"

curl http://localhost:3000/admin/tenants/tnt_demo/billing/2026-05/export?format=csv \
  -H "Authorization: Bearer dev-token"
```

**Say:** Billing is a deterministic projection from `usage_import_rows` and the `billing_rates` configuration in effect at the period start. Given the same inputs, it always produces the same output. There are no local counters, no frontend math, no race conditions.

The export comes in CSV and JSON. Same data, both formats. This is a billing **export**, not a payment system — invoicing and collection happen downstream in the operator's billing-of-record system.

**Show:** The `billing_ledger` row with status `draft`. Run finalize. Re-run calculate — show that finalized periods require explicit override.

**Takeaway:** Billing is reference architecture. The platform produces clean export artifacts. Payment, invoicing, and tax calculation are downstream concerns.

---

## Step 7 — Audit and Operations

**Show:** Admin portal → audit view filtered by `tnt_demo`.

**Say:** Every state-changing operation in the last 30 minutes is here: the create-tenant flow, the application key creation, the upload session creation, the cancel, the resume, the import, the billing finalize. Audit is append-only by schema design — there is no UPDATE or DELETE endpoint on `audit_events`.

**Show:** Suspend the tenant and reactivate it.

**Run:**
```
curl -X POST http://localhost:3000/admin/tenants/tnt_demo/suspend \
  -H "Authorization: Bearer dev-token" -d '{"reason": "demo"}'

# Upload now returns 403:
curl -X POST http://localhost:3000/tenant/projects/prj_demo/upload-sessions ...

curl -X POST http://localhost:3000/admin/tenants/tnt_demo/reactivate \
  -H "Authorization: Bearer dev-token"
```

Note that suspend revoked the tenant's provider key and reactivate created a new one. The old key value is unrecoverable; the tenant must update its client. Highlight that this is **local/composite suspension** — not Partner API eject. Eject is a high-friction, non-reversible deprovisioning action documented separately in `docs/operational-runbook.md` §6.

**Show:** `/admin/metrics` returning active tenant count, stale upload count, last ingest time, and per-code provider error rates.

**Takeaway:** Audit is immutable. Suspension and reactivation are reversible. Eject is permanent. The platform produces operational signals that any observability stack can consume.

---

## Wrap-Up

**Summary points:**
- Account-per-tenant isolation via Partner API.
- Distribution-first B2 file names.
- Provider-CSV-driven billing with internal reconciliation.
- Append-only audit.
- All Partner API operations behind a thin adapter; all composite logic in a Neocloud provider layer; mock provider for local development.
- Customer overlays let one codebase serve multiple deployments with different region, bucket, and reporting choices.

**What the kit does not include:**
- Payment processing, invoicing, dunning.
- Production observability stack (the platform emits signals; you wire them up).
- Multi-cloud abstraction.
- Real customer migration tooling.

See `docs/known-gaps.md` for the full inventory.

**Next steps for the audience:**
- Read `START_HERE.md` and pick the PR most relevant to their context.
- Open the matching context pack for token-efficient implementation.
- Bring in the customer overlay template (`customer-overlays/customer-profile.template.yaml`) when planning a real deployment.

---

## Time Budget

| Step | Time |
|---|---|
| 1 — Frame | 2 min |
| 2 — Architecture | 4 min |
| 3 — Provision | 5 min |
| 4 — Upload | 5 min |
| 5 — Usage and CSV import | 4 min |
| 6 — Billing | 3 min |
| 7 — Audit and ops | 3 min |
| Wrap-up | 2 min |
| **Total** | **~28 min** |

Allow 10 minutes for Q&A.
