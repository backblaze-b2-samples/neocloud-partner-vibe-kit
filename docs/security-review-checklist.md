<!-- last_verified: 2026-06-06 -->
# Security Review Checklist

Pre-production security review for a neocloud platform built from this kit. Use this checklist before exposing the platform to any real tenant or production data.

This document materializes the review scope referenced in `docs/known-gaps.md` §5. It is a structured checklist, not a substitute for hands-on penetration testing or a formal security audit.

**Who runs this:** A reviewer independent from the implementation team. Ideally a dedicated security engineer; minimum, a senior engineer who did not write the code being reviewed.

**When to run this:** Before first production deployment. After any change that touches authentication, authorization, secrets handling, or audit logging. Annually thereafter.

**Outcome:** A signed-off report listing every checked item, every finding, and the remediation plan for any failures.

---

## 1. Authentication and Authorization

### Auth model

- [ ] Production environment uses a real identity provider (not the dev token mode).
- [ ] Dev tokens (`dev-token`, `dev-tenant-token`) are rejected when `NODE_ENV=production` or `AUTH_MODE=production`.
- [ ] All platform API endpoints require an authenticated session. No public/anonymous endpoints except `/health` and `/health/ready`.
- [ ] Authentication failures return `401`, not `403`, and do not leak whether a tenant or user exists.

### Role enforcement

- [ ] Every endpoint declares its required role (`platform-admin`, `tenant-admin`, `developer`).
- [ ] Middleware enforces the declared role before the handler executes — no in-handler "if role" checks.
- [ ] Role mismatch returns `403`, with no information disclosure beyond "forbidden."
- [ ] `platform-admin` endpoints cannot be reached by tenant-scoped tokens.
- [ ] Cross-tenant access from a tenant-scoped token returns `403` (verified by an explicit test).

### Platform API keys

- [ ] API key secret values are returned exactly once at creation and never persisted.
- [ ] The secret is stored only as a one-way hash in `api_keys.key_hash` — never in plaintext, and never in `api_keys.scopes` (which is for permission-narrowing, not secrets).
- [ ] Authentication presents the key id plus secret; the platform compares a hash of the secret against `api_keys.key_hash` (the id alone is not a credential).
- [ ] Revoked API keys return `401` on the next use — no lag.
- [ ] API key creation, revocation, and `last_used_at` updates are audited.

---

## 2. Tenant Isolation Enforcement

### Authorization source

- [ ] Authorization decisions use the database's `tenant_id` resolved from the authenticated session.
- [ ] Authorization never depends on URL path components, bucket names, B2 file names, query parameters, or request body fields.
- [ ] A guessed B2 file name does not grant access (verified by test).
- [ ] A guessed bucket name does not grant access (verified by test).
- [ ] A guessed `provider_customer_account_id` does not grant access (verified by test).

### Account isolation

- [ ] Each tenant is provisioned in its own B2 customer account/sub-account via the Partner API.
- [ ] Tenant provider keys are scoped within the tenant's customer account.
- [ ] Tenant provider keys never have `listBuckets`, `listAllBucketNames`, `deleteBuckets`, `writeBuckets`, `readAccountInfo`, or `bypassGovernance` capabilities.
- [ ] A compromised tenant provider key cannot reach another tenant's customer account (verified by inspecting key scope).

### Cross-tenant API tests

- [ ] Tenant A's token cannot list, read, write, or delete Tenant B's objects (returns `403`).
- [ ] Tenant A's token cannot query Tenant B's usage data (returns `403`).
- [ ] Tenant A's token cannot retrieve Tenant B's API key list (returns `403`).
- [ ] Tenant A's token cannot access admin endpoints (returns `403`).

---

## 3. Secret Storage and Credential Hygiene

### Storage

- [ ] No credentials, account IDs, key values, or tokens are committed to source control.
- [ ] No credentials in config files in the repo. Config files reference environment variables or secret store paths only.
- [ ] `.env`, `.env.*`, and similar files are in `.gitignore`.
- [ ] Operator master key value lives only in the secrets store (e.g., Vault, AWS Secrets Manager).
- [ ] Operator master key is **never** used as an S3 credential by any tenant or tool. Backblaze rejects the master key at the S3 protocol level (S3 auth with the master key fails); regardless, it must never appear in any S3 client config or tenant-facing artifact given its Partner API/native scope. Verified by `grep` over CI configs, deployment manifests, and S3 client config files.
- [ ] Tenant S3 client configurations reference a tenant-scoped provider key only. The master key never appears in tenant-facing artifacts.
- [ ] Per-tenant provider key values live only in the secrets store, keyed by `provider_key_id`.
- [ ] The platform database has no plaintext credential columns (only IDs and hashes).

### Transmission

- [ ] Provider key values are returned only in the immediate response to the key-creation API call.
- [ ] `GET /admin/provider-keys/:id` and similar endpoints never return the key value.
- [ ] Notification channels (email, Slack, ticket systems) never carry key values. Tenants are directed to the portal to retrieve new key values.

### Log redaction

- [ ] Log entries never contain `applicationKey`, `authorizationToken`, or other credential values.
- [ ] Verified by `grep -i "applicationKey\|authorizationToken" $(production logs from last 24h)` returning empty.
- [ ] Error responses do not include stack traces or internal state that could leak credentials in production.

---

## 4. Audit Log Integrity

- [ ] `audit_events` table has no UPDATE or DELETE endpoint, route handler, or stored procedure.
- [ ] Database-level permissions deny UPDATE and DELETE on `audit_events` to the application's database role.
- [ ] Every state-changing operation writes an `audit_events` row. Verified by code review of all admin endpoints, provisioning flows, key lifecycle operations, and billing actions.
- [ ] `audit_events` rows contain `event_type`, `actor_id`, `resource_type`, `resource_id`, `occurred_at`, and structured `metadata` — never a credential value.
- [ ] Audit log retention meets compliance requirements (`AUDIT_RETENTION_DAYS`, default 2555 / 7 years).
- [ ] Audit log export is available to authorized operators.

---

## 5. Key Lifecycle

### Provider key creation

- [ ] Provider keys are created with minimum capabilities for the use case.
- [ ] Default tenant key capabilities are `listFiles, readFiles, writeFiles, shareFiles`. `deleteFiles` only when the tenant's workflow requires it.
- [ ] Key scope includes the specific `bucket_id` (and `file_name_prefix_or_scope` when applicable).

### Provider key rotation

- [ ] Scheduled rotation creates the new key before deleting the old key (atomic from the tenant's perspective).
- [ ] If revoking the old key fails after the new key is active, the failure is logged with the orphaned `provider_key_id` and an alert fires.
- [ ] Rotation interval is configured per `KEY_ROTATION_INTERVAL_DAYS` (default 90).
- [ ] Rotation writes an `audit_events` row with `event_type = 'provider_key_rotated'`.

### Provider key revocation

- [ ] Emergency revocation immediately disables the key value at the provider.
- [ ] Revoked keys are marked `status = 'revoked'` and `revoked_at = now()` in `provider_keys`.
- [ ] Revocation writes an `audit_events` row.

### Tenant suspension and ejection

- [ ] `markTenantSuspendedLocal` revokes all active provider keys for the tenant.
- [ ] `ejectStorageAccountFromProviderGroup` requires explicit operator confirmation.
- [ ] Eject is documented as non-reversible through the Partner API.
- [ ] Eject does not silently leave provider keys active — a key disposition policy is recorded.

---

## 6. Data Plane Authorization

### Upload

- [ ] `POST /tenant/projects/:projectId/upload-sessions` resolves the tenant from the authenticated session, not from the URL.
- [ ] The handler verifies the project belongs to the authenticated tenant before any B2 call.
- [ ] Suspended tenants receive `403` (verified by test).
- [ ] Quota check runs before the B2 `b2_start_large_file` or `b2_get_upload_url` call.
- [ ] Part SHA1 verification runs before the bytes are forwarded to B2.

### Download

- [ ] `GET /tenant/projects/:projectId/objects/:objectId/download` verifies ownership through the database (object → project → tenant) before any B2 call.
- [ ] Tenant A cannot download Tenant B's object (verified by test).
- [ ] Range requests are forwarded correctly (`206 Partial Content` with valid `Content-Range`).
- [ ] Download writes a `usage_events` row with `event_type = 'download'`.

### Delete

- [ ] `DELETE /tenant/projects/:projectId/objects/:objectId` verifies ownership before any B2 call.
- [ ] Delete writes a `usage_events` row with `event_type = 'delete'`.
- [ ] Delete does not allow soft-undelete that exposes data to another tenant.

---

## 7. Presigned URL Scoping

- [ ] Presigned URLs are generated via `b2_get_download_authorization` with a tenant-scoped `fileNamePrefix`.
- [ ] The prefix is restricted to the specific object's physical B2 file name, not a wider prefix that would expose siblings.
- [ ] Presigned URL TTL respects `PRESIGNED_URL_DEFAULT_TTL_SECONDS` and `PRESIGNED_URL_MAX_TTL_SECONDS` (default 1 hour / 24 hours).
- [ ] Presigned URLs do not expose the physical B2 file name structure in the URL response body (the URL itself may include it, but the API response should not duplicate it).
- [ ] Presigned URL issuance writes a `usage_events` row (operator-configurable per `presigned_url_metering`).
- [ ] Expired presigned URLs return `401` from B2 — verified by waiting past TTL and retrying.
- [ ] Cross-tenant presigned URL generation is impossible (the URL prefix is tied to the requesting tenant's object).

---

## 8. CSV Ingestion Idempotency

- [ ] `usage_imports` records each ingest with a checksum of the raw CSV.
- [ ] Re-ingesting the same CSV (same checksum) does not create duplicate `usage_import_rows`.
- [ ] Re-ingesting does not create a duplicate `usage_imports` row.
- [ ] Raw CSV is archived to the control bucket **before** any DB writes — the archive is verified by an integration test.
- [ ] CSV with a missing required column errors out before any DB write.
- [ ] CSV with one corrupt row isolates the bad row to an error log; the rest of the file ingests.
- [ ] Unattributed rows land in `usage_import_rows` flagged as unattributed; they do not silently disappear and they do not fail the ingest.
- [ ] Attribution order is: provider account ID → storage account → bucket name → unattributed.

---

## 9. Operational Practices

### Local dev safety

- [ ] Tests use the mock provider exclusively. No tests require real B2 credentials.
- [ ] CI does not have access to production B2 credentials.
- [ ] Demo mode never connects to a real production B2 account.

### Production deployment

- [ ] Production environment is isolated from staging and dev (separate databases, separate Backblaze operator accounts).
- [ ] Production secrets are managed by the secrets store; not present in environment variables checked into infra-as-code.
- [ ] CI/CD pipelines that touch production require approval steps.
- [ ] Pre-production smoke tests verify provider connectivity (`provider.authorizeAccount` or `provider.validateCredentials`).

### Monitoring and alerting

- [ ] `/admin/metrics` is exposed only to platform-admin role.
- [ ] Alert thresholds are configured for: provider error rate, stale upload count, unattributed `usage_import_rows` growth, reconciliation drift, audit log gap.
- [ ] Alert destinations route to the on-call team, not just to a log file.

### Incident response

- [ ] Operations team has read `docs/operational-runbook.md`.
- [ ] Provider key emergency revocation has been practiced in a non-production environment.
- [ ] Tenant suspension and reactivation have been practiced.
- [ ] Tenant ejection has been practiced in a non-production environment (since real ejection is non-reversible).

---

## 10. Backups and Recovery

- [ ] Metadata database is backed up per the operator's recovery objective.
- [ ] Backup integrity is verified by periodic restore tests.
- [ ] `audit_events` and `usage_import_rows` retention meets compliance requirements.
- [ ] B2 objects themselves are not backed up by this kit; the operator's customer overlay documents the durability assumptions and any cross-region replication strategy (`customer-profile.example-multi-workload.yaml` shows the pattern).

---

## 10a. S3-Compatible API Surface

- [ ] If tenant-facing S3 access is enabled (`S3_ACCESS_FOR_TENANTS=true`), tenants understand that B2's S3 implementation does not support SSE-KMS, object tagging, IAM roles, object-level ACLs, or browser POST uploads (per `docs/s3-compatible-api.md` §Explicitly NOT Supported).
- [ ] SigV2 client configurations are rejected by SDK config (`signatureVersion: 's3v4'` or equivalent). Verified by a test request from a tenant fixture client.
- [ ] Provider key capabilities granted to tenants are the minimum needed for their S3 workload. Default set: `listFiles, readFiles, writeFiles, shareFiles` (and optionally `deleteFiles`).
- [ ] No tenant provider key has `listAllBucketNames`, `listBuckets`, `readAccountInfo`, `writeBuckets`, `deleteBuckets`, or `bypassGovernance`.
- [ ] `storage_accounts.s3_endpoint` is captured at provisioning time from the Partner API response — never inferred from the region code.
- [ ] If SSE policy is enforced (e.g., SSE-B2 default), bucket-level encryption is set at bucket creation, not at first object upload.
- [ ] If the workload uses SSE-C, the key MD5 is verified server-side (Backblaze does this by default) and the customer is responsible for key retention.
- [ ] S3-direct access by tenants is documented as expected for that tenant's overlay; reconciliation drift is not treated as a bug.
- [ ] If compliance requires per-request access logs, B2 access logging is enabled to a separate audit bucket and ingested into the platform's audit trail.
- [ ] Tenants using S3 cannot trigger Partner API operations through it. The Partner API is not exposed on the S3 endpoint.

## 11. Compliance-Specific Items

Only required for deployments under specific regulatory regimes. Skip items that do not apply.

### SOC2 / ISO 27001

- [ ] Access reviews are scheduled for the platform admin role.
- [ ] Change management process applies to production deployments.
- [ ] Audit log export is available on demand.

### HIPAA

- [ ] Customer overlay sets `object_lock_required = true` and `audit_export_required = true`.
- [ ] Business Associate Agreement (BAA) with Backblaze is in place if PHI is stored.
- [ ] Tenant overlay documents the PHI classification of the data.

### GDPR / data residency

- [ ] Multi-region accounts are configured per `customer-profile.example-multi-workload.yaml` or equivalent.
- [ ] Data subject access requests (DSAR) are supported by the audit log and object metadata queries.
- [ ] Data deletion requests are handled by the soft-delete + retention purge flow.

### Object Lock and retention

- [ ] If `object_lock_required = true`, the platform creates buckets with Object Lock enabled at provisioning time.
- [ ] Soft-delete and purge operations check Object Lock state before any destructive call.

---

## Reporting Findings

For each item that fails:

1. Record the finding with: severity (critical / high / medium / low), the failing item, the evidence (commit, log line, test output), and the proposed remediation.
2. Critical and high findings block production launch.
3. Medium findings require a remediation plan with target date.
4. Low findings are tracked but do not block.

Sign-off requires:
- Reviewer signature (the security engineer or designated reviewer).
- Implementation lead acknowledgment of findings and remediation plan.
- Operator approval to proceed (for critical/high items: approval after remediation; for medium/low: approval with tracking).

---

## Cross-References

- `docs/known-gaps.md` §5 — original scope of this checklist.
- `docs/common-pitfalls.md` — the "wrong patterns" that this checklist verifies are absent.
- `docs/quality-gates.md` — per-PR gates that prevent regressions before they reach review.
- `docs/operational-runbook.md` — incident response procedures referenced from §9.
- `CLAUDE.md` §Golden rules — non-negotiable invariants this checklist enforces.
- `docs/data-model.md` — canonical entity names referenced throughout.
- `docs/provisioning-and-partner-api.md` — Partner API surface referenced in §5 (key lifecycle) and §1 (auth).
