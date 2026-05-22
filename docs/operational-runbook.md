# Operational Runbook

This runbook covers recurring operational incidents on the neocloud platform. Each section follows the pattern: **Symptoms → Investigate → Remediate → Prevent**.

The runbook is task-oriented and assumes the target architecture from `docs/neocloud-architecture.md`. Specific table and column names refer to the canonical entities in `docs/data-model.md` and the canonical API surface in `docs/api-contracts.md`. Composite provider method names refer to the `NeocloudStorageProvider` layer in `docs/provisioning-and-partner-api.md`.

**When the system is in active production use, every remediation step that mutates platform state must be performed under an operator role and must emit an `audit_events` row. Never bypass audit logging during incidents.**

---

## Severity Classification

| Severity | Definition | Response time |
|---|---|---|
| SEV-1 | Tenant data plane down, or active data integrity risk | Page on-call; respond within 15 minutes |
| SEV-2 | Degraded data plane (high error rate, slow uploads), or billing integrity at risk | Respond within 1 business hour |
| SEV-3 | Single-tenant impact or operator-internal issue | Respond within 1 business day |
| SEV-4 | No customer impact; cleanup or hygiene work | Schedule normally |

---

## 1. Failed Uploads

**Symptoms**
- Tenant reports upload errors via portal, API client, or support channel.
- Spike in non-2xx responses on `POST /tenant/projects/:projectId/upload-sessions` or `PUT .../parts/:n`.
- `usage_events` rows with `event_type = 'upload'` stop appearing for a tenant that normally uploads.

**Investigate**
1. Resolve the tenant ID from the report. Look up `tenants.status` — confirm `active`.
2. Query `upload_sessions` for the affected tenant in the last hour. Group by `status`. Distinguish:
   - `failed` rows with a non-retryable error (4xx) — client-side issue.
   - `failed` rows after retries exhausted with 5xx — provider or network issue.
   - `pending` or `uploading` rows past their TTL — see Section 2 (Stuck Multipart Sessions).
3. If failures are concentrated on one tenant, check `provider_keys` for that tenant: any `revoked_at` set? Key in `rotation_pending_delete` status?
4. If failures are cross-tenant, check provider API status (Backblaze status page) and aggregate provider error rate metric.

**Remediate**
- **Client-side error (400, 413, SHA1 mismatch):** Surface a clear error to the tenant. Do not retry server-side. Document the cause.
- **Auth error (401, 403):** If the platform's master credentials are invalid, see Section 7 (Provider Key Revocation/Rotation). If the tenant's platform API key is revoked, surface 401 to the client.
- **Transient 5xx after retry exhaustion:** Confirm retry policy matches `CLAUDE.md` Upload Defaults (3 attempts, exponential backoff with jitter, retry on 408/425/429/500/502/503/504). If a tenant is hitting per-account rate limits, reduce that tenant's batch concurrency or stage uploads.
- **Suspended tenant:** Confirm with operator that suspension is intentional. If unintentional, run the reactivate flow (Section 5).

**Prevent**
- Ensure the dashboard exposes upload failure rate per tenant and per storage account.
- Alert when failure rate exceeds a configured threshold for any tenant over a 5-minute window.

---

## 2. Stuck Multipart Sessions

**Symptoms**
- `upload_sessions` rows with `status` in (`pending`, `uploading`) past their TTL.
- Tenant reports an upload that never completed.
- Storage charges accruing for unfinished large files on the provider side.

**Investigate**
1. Query `upload_sessions` where `status IN ('pending', 'uploading')` and the session's TTL has expired. Note count and tenants affected.
2. For each stuck session, look up `upload_parts` count and the most recent part timestamp.
3. Determine whether the cleanup job ran recently — check job logs and the `last_stale_upload_cleanup_run` metric.

**Remediate**
- **Cleanup job is healthy and the sessions just predate it:** Wait for the next scheduled run, or trigger it manually if the affected tenant needs space reclaimed now. The job calls `provider.abortMultipartUpload(provider_upload_id)` for each session, marks the row `aborted` with `aborted_at = now()`, and emits an audit event.
- **Cleanup job is broken:** Restart the worker. If the failure is in the job itself, fall back to manual cleanup: for each stuck session, call `provider.abortMultipartUpload(provider_upload_id)`, set `upload_sessions.status = 'aborted'`, `aborted_at = now()`, and emit an `audit_events` row with `event_type = 'manual_session_abort'` and `resource_type = 'upload_session'`.
- **`abortMultipartUpload` returns "file not found":** The session was already finalized or aborted on the provider side. Mark the session `aborted` in the database and log the divergence for review.

**Prevent**
- The stale upload cleanup job must run on a fixed schedule (default: hourly). Add a metric for last-run-age and alert if it exceeds 2x the schedule.
- Surface unfinished-large-files count per storage account in the operator dashboard.

---

## 3. Usage Import Failures (B2 CSV)

**Symptoms**
- `usage_imports` row marked `failed`, or no new `usage_imports` rows for a recent period.
- Billing job blocked because `billing_ledger` has no data for a period.
- Operator alerted to a missing daily CSV.

**Investigate**
1. Look up the most recent `usage_imports` rows. Check import status, error message, and whether the raw CSV was archived.
2. Confirm the raw CSV was archived to the control bucket before any DB writes. If not, the ingest was aborted before transformation — this is the correct behavior; re-fetch and re-ingest.
3. Common failure modes:
   - **Missing required column:** Schema drift in the B2 CSV format. Inspect headers in the archived raw file. Update the parser only after confirming the change is intentional.
   - **Unparseable row:** Single corrupt row. The parser should isolate and log the row; the rest of the file should still ingest.
   - **Unattributed rows:** Rows where neither the provider Account ID nor the Bucket Name matches a `storage_accounts` or `buckets` record. These should land in `usage_import_rows` flagged as unattributed, not fail the ingest.

**Remediate**
- **Schema drift:** Patch the parser. Re-ingest the affected file. The import checksum recorded on `usage_imports` enforces idempotency so re-ingest does not duplicate `usage_import_rows`.
- **Corrupt row:** Investigate with Backblaze if needed. Re-ingest after the row is fixed or excluded.
- **Unattributed rows in volume:** Investigate the `storage_accounts` table. A provisioning failure may have left an account un-registered. Backfill the missing `storage_accounts` row (with correct `provider_customer_account_id`, `region`, and `alias`) if you find an orphaned account.

**Prevent**
- Alert on any `usage_imports` row marked failed.
- Alert on unattributed `usage_import_rows` count exceeding a threshold per ingest.
- Run reconciliation (Section 4) on a schedule and surface drift.

---

## 4. Reconciliation Discrepancies

**Symptoms**
- Reconciliation job reports a delta between `usage_events` totals (platform-mediated) and `usage_import_rows` totals (provider CSV) for the same period and tenant.
- Tenant disputes their billing amount.

**Investigate**
1. Pull both totals for the period and tenant from `usage_events` and the attributed `usage_import_rows`.
2. Compute the delta by `event_type` (upload, download, delete).
3. Common explanations:
   - **Direct B2 access:** The tenant has a provider key with scope outside the platform-mediated paths and is using B2 directly. The provider sees activity the platform did not record. This should be impossible with correctly-scoped tenant keys — investigate `provider_keys.capabilities` and `provider_keys.scope`.
   - **CSV lag:** B2 CSV exports trail real-time usage. Small deltas at month boundaries are expected. Compare against the next period's ingest to see if the missing usage appears.
   - **Failed-but-billable operations:** Provider may count partial transfers (e.g., aborted multipart parts) that the platform did not record. Verify with provider documentation for the period in question.
   - **Bug in usage event emission:** A code path that performs B2 operations is missing the `usage_events` write. Audit all data plane code paths.

**Remediate**
- **Reconciliation is informational only.** Do not modify `usage_import_rows`, `usage_events`, or `billing_ledger` data based on a discrepancy without explicit operator approval and an `audit_events` row.
- If the discrepancy is real and not explained: file a bug for the missing usage event emission. Backfill is generally not appropriate — `usage_import_rows` (provider-reported) is the billing source of truth.
- If the tenant is using direct B2 access via an overly-scoped key, immediately rotate to a properly-scoped key (Section 7).

**Prevent**
- Reconciliation runs on a schedule (daily or weekly). Threshold alerts surface discrepancies that exceed configured tolerance.
- Tenant keys must follow the minimum-capability list in `CLAUDE.md` §Key Capabilities Reference. Audit `provider_keys.capabilities` periodically.

---

## 5. Tenant Suspension and Reactivation

**Symptoms / Triggers**
- Operator decision (non-payment, abuse, support request).
- Compromise indicators (anomalous traffic, leaked credentials).

This is a local/composite Neocloud state change. It does **not** call Partner API eject. See `docs/provisioning-and-partner-api.md` §Eject, suspend, and reactivate semantics.

**Suspend procedure**
1. Confirm the operator action is authorized (record ticket reference).
2. Call `provider.markTenantSuspendedLocal(tenantId)`. This sets `tenants.status = 'suspended'` and `tenants.suspended_at = now()`.
3. For each active row in `provider_keys` for this tenant: call `provider.revokeApplicationKey(provider_key_id)`. Mark `provider_keys.status = 'revoked'`, set `provider_keys.revoked_at = now()`.
4. Emit `audit_events` row: `event_type = 'tenant_suspended'`, `resource_type = 'tenant'`, `resource_id = tenant_id`, with metadata including the list of revoked `provider_key_id` values and the suspension reason.
5. Verify: any subsequent platform API call from the tenant returns 403. Any direct provider call with the revoked key returns 401 from the provider.

**Reactivate procedure**
1. Confirm authorization.
2. Verify `tenants.status = 'suspended'`. Do not reactivate a tenant whose storage account has been ejected (`storage_accounts.ejected_at IS NOT NULL`); ejection is non-reversible through the Partner API.
3. For each `storage_accounts` row for the tenant, call `provider.createApplicationKey(...)` with the canonical minimum-capability set and the canonical bucket scope. Insert a new `provider_keys` row with `status = 'active'`. Store the key value in the secrets store only.
4. Call `provider.markTenantReactivatedLocal(tenantId)`. This sets `tenants.status = 'active'` and clears `tenants.suspended_at`.
5. Emit `audit_events` row: `event_type = 'tenant_reactivated'`, `resource_type = 'tenant'`, `resource_id = tenant_id`, with metadata including the new `provider_key_id` values.

**Notes**
- Suspension does not delete tenant data. Buckets and objects remain. Provider account is not ejected from its Group.
- Old key values from before suspension are not recoverable. The tenant must update any external clients with the new key value.

---

## 6. Provider Group Ejection

Before ejecting a storage account from a provider Group, confirm this is deprovisioning rather than temporary suspension. Eject is the Partner API mechanism for permanently removing a customer account from a Group. It is not reversible through the Partner API.

**Pre-eject checklist**
1. Record explicit operator confirmation that this is intentional deprovisioning.
2. Warn the operator: the account cannot be re-added to any Group through the Partner API.
3. Warn the operator: existing application keys on the ejected account can continue to function unless explicitly revoked.
4. Decide and record the key disposition policy:
   - **Revoke all keys first** (recommended for security-sensitive deprovisioning). Run Section 7 procedures for each active `provider_keys` row tied to the storage account.
   - **Rotate keys to operator-controlled values** (for forensic preservation while denying tenant access).
   - **Leave keys intact** (only for hand-off scenarios where tenant retains direct access to their data).
5. If this eject is part of post-retention purge of a deleted tenant, confirm that the configured retention window has passed before proceeding. Record the retention check outcome in the audit metadata. (The exact retention bookkeeping schema is operator-defined; `tenants.status` reflects lifecycle state.)

**Eject procedure**
1. For each `buckets` row tied to the storage account (per the key disposition policy and any compliance-driven data deletion requirements): enumerate file versions, delete each version, then delete the bucket. Skip this step if the policy is to leave data intact for hand-off.
2. Call `provider.ejectStorageAccountFromProviderGroup({ storageAccountId, memberAccountId, explicitConfirmation: true })`. This wraps the thin Partner API `ejectGroupMember` call with the required local handling.
3. Set `storage_accounts.ejected_at = now()` and `storage_accounts.status` to an operator-defined post-eject value (e.g., `ejected`).
4. Emit `audit_events` row: `event_type = 'storage_account_ejected'`, `resource_type = 'storage_account'`, `resource_id = storage_account_id`, with metadata including the provider Group ID, the provider customer account ID, the bucket deletion summary, and the key disposition policy that was applied.

**Recovery**
- There is no Partner API recovery path. If eject was performed in error, contact Backblaze through normal support channels. Expect that re-establishing the account in a Group may require manual Backblaze intervention.

---

## 7. Provider Key Revocation and Rotation

**When to revoke immediately**
- Key value leaked (committed to source, posted in chat, exposed in logs).
- Tenant compromise indicator.
- Operator policy violation.

**When to rotate on schedule**
- Per the configured key rotation interval (default: 90 days).
- After any operator with provisioning access leaves the team.

**Emergency revocation**
1. Identify the affected `provider_keys` row(s) by `provider_key_id`.
2. Call `provider.revokeApplicationKey(provider_key_id)` for each. Set `provider_keys.status = 'revoked'` and `provider_keys.revoked_at = now()`.
3. Immediately create a replacement key (if the tenant is still active): call `provider.createApplicationKey(...)` with the same `storage_account_id`, `bucket_id`, and capability scope. Insert a new `provider_keys` row with `status = 'active'`. Store the new value in the secrets store.
4. Notify the tenant through the agreed-upon support channel that they must rotate to the new key value. Do not send the key value over the notification channel — direct them to the portal or a secure delivery mechanism.
5. Emit `audit_events` row: `event_type = 'provider_key_emergency_revoked'`, `resource_type = 'provider_key'`, `resource_id = old_provider_key_id`, with metadata including the new `provider_key_id` (if a replacement was issued) and the reason.

**Scheduled rotation**
1. Look up the active key in `provider_keys`.
2. Call `provider.createApplicationKey(...)` with the same `storage_account_id`, `bucket_id`, and capability scope. Insert a new `provider_keys` row with `status = 'active'`. Store the value in the secrets store.
3. Mark the old key `rotation_pending_delete`.
4. Call `provider.revokeApplicationKey(old_provider_key_id)`. On success, set the old key's `status = 'revoked'` and `revoked_at = now()`.
5. **If step 4 fails:** the new key is already active; do not roll back. Log the orphaned old `provider_key_id`. Alert ops to delete it manually. The tenant is in a safe state.
6. Emit `audit_events` row: `event_type = 'provider_key_rotated'`, `resource_type = 'provider_key'`, `resource_id = new_provider_key_id`, with metadata including the old `provider_key_id`.

**Prevent**
- Never log the provider application key value at any log level.
- Never return the provider application key value in any API response after the initial creation response.
- Verify with `grep` over recent logs that no provider application key strings appear.

---

## 8. Provider API Failures

**Symptoms**
- Spike in provider error responses across multiple tenants.
- Health check `/health/ready` returns non-200 because `provider.authorizeAccount` is failing.
- Background jobs (cleanup, ingestion) reporting connection errors.

**Investigate**
1. Check the Backblaze status page first.
2. Aggregate provider error rate by error code in metrics:
   - `401`: platform auth token invalid or expired. Re-authorize.
   - `403`: capability or scope issue. Audit the platform's master credentials.
   - `429`: rate limited. Check whether traffic spike is real (legitimate burst) or a bug (retry storm).
   - `503`: provider unavailable. Backoff and retry.
3. Check whether failures are concentrated on a single storage account or spread across many. Account-specific failures are usually a credentials issue.

**Remediate**
- **401 / token expired:** Force re-authorize. Token cache should be cleared. If repeated, investigate clock skew or stored credential corruption.
- **403:** Confirm the platform master credentials have all required capabilities. If a tenant-specific call returns 403, the tenant's key scope may be insufficient — review against the minimum-capability list.
- **429:** Reduce concurrency. If retry storm is suspected, check that retry logic respects `Retry-After`. The global in-flight limit (`UPLOAD_MAX_INFLIGHT`, default 10) should prevent runaway.
- **503:** Let exponential backoff handle it. If persistent for > 15 minutes, page Backblaze support.

**Prevent**
- Health check must exercise a real provider call (e.g., `provider.authorizeAccount` or `provider.validateCredentials`), not just DB connectivity.
- Metric `provider_error_rate` with per-code breakdown.
- Alert when error rate exceeds threshold for 5 minutes.

---

## 9. Audit Investigations

**When to investigate**
- Operator action review (post-incident).
- Tenant security inquiry (was their account accessed when?).
- Compliance request (data residency, access logs).

**Investigation flow**
1. Identify the scope: tenant ID, time range, event types.
2. Query `audit_events`:
   ```sql
   SELECT *
   FROM audit_events
   WHERE tenant_id = :tenant_id
     AND occurred_at BETWEEN :start AND :end
     AND event_type IN (:event_type_list)
   ORDER BY occurred_at ASC;
   ```
3. Correlate with `usage_events` for data plane activity in the same window.
4. Correlate with `provider_keys` lifecycle (created, revoked, rotated) for credential changes.
5. If the investigation involves an external actor: filter on `audit_events.actor_id` and pull network identifiers (e.g., IP) from `audit_events.metadata`. Correlate with auth provider logs.

**Data preservation**
- `audit_events` is append-only by schema design. There must be no UPDATE or DELETE endpoint. Confirm the constraint is still in place.
- Export findings to a separate, immutable store for incident files. Do not modify `audit_events` rows.
- Hold required data per retention policy before scheduled deletion.

**Common patterns**
- "Who suspended this tenant?" → filter `event_type = 'tenant_suspended'`, look at `actor_id`.
- "When did this key get created?" → filter on `metadata->>'provider_key_id'`.
- "What did this admin do in the last day?" → filter `actor_id` over time range, group by `event_type`.

---

## 10. Quota Exceeded

Quota policy is configured at the project level (`projects.quota_policy`) in the canonical data model. Tenant-level aggregate quotas, if needed, are an operator-defined extension.

**Symptoms**
- Upload session creation fails with 429 (or 403) for a specific project.
- Tenant reports inability to upload.

**Investigate**
1. Look up the affected project. Read `projects.quota_policy` to determine the configured quota (hard or soft, byte limit, period) for that project.
2. Compute current usage for the project from `usage_import_rows` (the durable provider-reported source) for the current period.
3. Distinguish hard quota vs soft quota:
   - **Hard quota:** Upload session creation rejects. No data is written.
   - **Soft quota:** Warning surfaced; upload proceeds. Verify the configured mode.
4. If `usage_import_rows` lags real-time, also check `usage_events` for in-period upload bytes that have not yet been reconciled.

**Remediate**
- **Legitimate quota exhaustion:** Tenant must delete data or operator must raise the project's quota. Adjust `projects.quota_policy` and emit `audit_events`: `event_type = 'project_quota_adjusted'`, `resource_type = 'project'`, `resource_id = project_id`, with metadata including the prior and new policy.
- **Stale usage data:** If `usage_import_rows` is behind real-time, the quota check should also consider `usage_events`. Confirm the quota check logic accounts for both sources, or document the lag.
- **Mis-attribution:** If quota is exceeded but the project did not upload the volume in question, run reconciliation (Section 4).

**Prevent**
- Surface usage vs quota in the tenant portal so tenants see the approaching threshold.
- Alert tenants at 80% and 95% of project quota.
- Document quota policy clearly in the customer overlay's notes field.

---

## 11. Small-File Amplification

**Symptoms**
- A tenant is producing tens or hundreds of thousands of objects smaller than 100 KB.
- Per-tenant `usage_events` row count where `event_type = 'upload'` is orders of magnitude higher than other tenants.
- Provider 429 errors concentrated on a single tenant.
- Object count metric growing rapidly while bytes-stored grows slowly.

**Investigate**
1. Compute the median object size for the tenant from `objects.size_bytes` or `usage_events.bytes`.
2. Count objects created per minute for the tenant. Compare against other tenants.
3. Determine whether the workload would benefit from packing (see `docs/small-file-and-throughput-guidance.md`).

**Remediate**
- **Tenant has not been offered packing:** Engage the tenant. Document the recommendation to use the packing pattern (`packed_object_manifests` + `packed_object_entries`). The platform supports both individual objects and packed manifests; the choice is the tenant's.
- **Tenant insists on individual small objects:** This is allowed by `docs/adr/006-high-throughput-not-high-iops.md`. The platform should not refuse small objects. Surface throughput cost in the tenant's billing view so the tradeoff is visible.
- **Runaway script or bug on the tenant side:** Coordinate with the tenant to throttle. Temporary rate limiting via concurrency reduction may be appropriate; emit `audit_events`: `event_type = 'tenant_concurrency_throttled'` with metadata including the throttling parameters and reason.

**Prevent**
- Add a "median object size" metric per tenant to the operator dashboard.
- Alert when median object size for a tenant drops below 10 KB sustained over 1 hour.
- Document the packing pattern in the tenant onboarding guide.

---

## 12. Regional Account Reporting Issues

**Symptoms**
- A tenant with multiple regions sees totals that match only one region.
- Reconciliation discrepancy concentrated on one region.
- Per-region usage view shows zero for a region that should have data.

**Investigate**
1. Query `storage_accounts` for the tenant. Confirm one row per expected region, each with `region`, `alias`, and `provider_member_email` populated. Verify region values use Partner API region codes (e.g., `us-east`, `us-west`, `eu-central`) — not S3 endpoint labels (e.g., `us-west-004`).
2. For each `storage_accounts` row, check the most recent `usage_imports` entry tagged to that account. If a region is missing from ingestion, the CSV for that region was never imported or failed.
3. Confirm the CSV ingestion pipeline is fetching CSVs per `storage_accounts` row separately. Per-account CSVs are not merged automatically — the pipeline must enumerate `storage_accounts` and ingest each.

**Remediate**
- **Missing region in `storage_accounts`:** Provisioning bug. Re-run the regional provisioning flow to backfill the missing account row. If the provider account exists but the row is missing, insert the row with the correct `region`, `alias`, `provider_member_email`, and `provider_customer_account_id`. Emit `audit_events`: `event_type = 'storage_account_backfilled'`.
- **Missing ingest for a region:** Re-fetch the regional CSV and re-ingest. Idempotency on `usage_imports.checksum` prevents duplicates.
- **Aggregation bug in the reporting query:** Confirm reports sum across all `storage_accounts` rows for a tenant, not just one.

**Prevent**
- Alert when a tenant's expected region count (from customer overlay) does not match the count of active `storage_accounts` rows.
- Alert when any region's most recent successful ingest is older than 48 hours.
- Test the multi-region path in CI with a fixture tenant that has accounts in two regions.

---

## Cross-References

- `docs/data-model.md` — canonical schema and column names referenced throughout this runbook.
- `docs/api-contracts.md` — canonical endpoints referenced for tenant lifecycle and data plane operations.
- `docs/provisioning-and-partner-api.md` — full Partner API flow detail, including the `NeocloudStorageProvider` composite layer whose methods are referenced here (`markTenantSuspendedLocal`, `markTenantReactivatedLocal`, `ejectStorageAccountFromProviderGroup`, `createApplicationKey`, `revokeApplicationKey`, `abortMultipartUpload`).
- `docs/usage-reporting-and-billing.md` — attribution order and reconciliation logic.
- `docs/quality-gates.md` — gates that prevent runbook scenarios from being needed (e.g., audit append-only enforcement, key-value redaction).
- `CLAUDE.md` §Upload Defaults — retry and concurrency configuration referenced in Section 1 and Section 8.
- `docs/small-file-and-throughput-guidance.md` — full small-file packing pattern referenced in Section 11.
- `docs/adr/006-high-throughput-not-high-iops.md` — small-file policy rationale referenced in Section 11.
