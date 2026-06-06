<!-- last_verified: 2026-06-06 -->
# Configuration Reference

All configurable settings for the neocloud platform target architecture. Defaults shown are the recommended values from `CLAUDE.md` §Upload Defaults and the customer overlay template; customer overlays may override values in the **Configurable defaults** category, but not in the **Hard invariant** category.

Every setting in this reference is read from environment variables, a config file, or a customer overlay YAML. Never commit secrets or credentials.

For the source-of-truth hierarchy that this reference defers to, see `docs/source-of-truth.md`.

---

## 1. Application Environment

| Key | Default | Purpose | Source |
|---|---|---|---|
| `NODE_ENV` | `development` | Runtime environment (`development`, `test`, `production`) | platform standard |
| `PORT` | `3000` | HTTP listen port | platform standard |
| `LOG_LEVEL` | `info` | Logging verbosity (`debug`, `info`, `warn`, `error`) | platform standard |
| `LOG_FORMAT` | `json` | Structured log output format | `CLAUDE.md` §Observability |

---

## 2. Database

| Key | Default | Purpose | Source |
|---|---|---|---|
| `DATABASE_URL` | (required) | Connection string for the metadata DB | platform standard |
| `DATABASE_POOL_SIZE` | `10` | Connection pool size | operator tuning |
| `DATABASE_MIGRATION_DIR` | `./migrations` | Path to migration files | platform standard |

---

## 3. Auth and Roles

| Key | Default | Purpose | Source |
|---|---|---|---|
| `AUTH_MODE` | `dev` | `dev` accepts static tokens; `production` requires real IdP | `CLAUDE.md` §PR 2 |
| `DEV_ADMIN_TOKEN` | `dev-token` | Static token accepted as platform-admin in dev mode only | PR 2 prompt |
| `DEV_TENANT_TOKEN` | `dev-tenant-token` | Static token accepted as tenant in dev mode only | PR 2 prompt |
| `ADMIN_ROLES` | `platform-admin` | Comma-separated list of roles with admin authority | customer overlay (`admin roles`) |

---

## 4. Storage Provider

| Key | Default | Purpose | Source |
|---|---|---|---|
| `STORAGE_PROVIDER` | `mock` | `mock` for local; `b2` for production | `docs/provisioning-and-partner-api.md` |
| `B2_APPLICATION_KEY_ID` | (required for `b2`) | Operator master key ID | secrets store only |
| `B2_APPLICATION_KEY` | (required for `b2`) | Operator master key value | secrets store only |
| `MOCK_SEED_GROUPS` | `true` | Mock provider seeds fake Groups | `docs/provisioning-and-partner-api.md` |

---

## 5. Partner API and Groups

These settings reflect environmental prerequisites that must be confirmed with Backblaze. The platform does not configure Backblaze; it consumes already-enabled capabilities.

| Key | Default | Purpose | Source |
|---|---|---|---|
| `PARTNER_API_ENABLED` | (operator confirmation) | Boolean flag indicating Backblaze has enabled Partner API on the operator account | hard invariant |
| `GROUPS_ENABLED` | (operator confirmation) | Boolean flag indicating Backblaze has enabled Groups on the operator account | hard invariant |
| `DEFAULT_GROUP_ID` | (operator-set) | Provider Group ID used for new tenant customer accounts | customer overlay (`group_strategy`) |
| `GROUP_STRATEGY` | `link_existing_website_created_groups_by_customer_cohort` | How tenant accounts are organized into Groups | customer overlay |

**Hard invariant:** Group creation via the Partner API is not supported. The platform must not implement, mock, or expose a `createGroup` operation. See ADR 007.

---

## 6. Customer Account Provisioning

| Key | Default | Purpose | Source |
|---|---|---|---|
| `CUSTOMER_ACCOUNT_ALIAS_PATTERN` | `<partner_customer_id>-<b2_partner_region>@<partner_storage_domain>` | Template for generating `memberEmail` values | customer overlay |
| `PARTNER_STORAGE_DOMAIN` | (operator-set) | Domain portion of the alias pattern | customer overlay |
| `ACCOUNT_REGION_MODEL` | `one_customer_account_per_required_region` | How multi-region tenants are mapped to accounts | customer overlay |
| `DEFAULT_BUCKETS_PER_CUSTOMER_ACCOUNT` | `1` | Starter bucket count at provisioning time | customer overlay |
| `BUCKET_NAMING_PATTERN` | `{platform_prefix}-{tenant_id}-{purpose}` | Bucket name generation pattern | `CLAUDE.md` §Bucket Name Rules |
| `BUCKET_STRATEGY` | `by_workload_policy_or_environment` | Multi-bucket organization within a customer account | customer overlay |
| `TENANT_KEY_CAPABILITIES` | `listFiles, readFiles, writeFiles, shareFiles` | Default capabilities for tenant provider keys | `CLAUDE.md` §Key Capabilities Reference |

---

## 7. Region Codes

The Partner API region code (`storage_accounts.region`) is **not** an S3 endpoint label.

| Setting | Example Value | Purpose |
|---|---|---|
| Partner API region | `us-east`, `us-west`, `ca-east`, `eu-central` | Used in `b2_create_group_member` |
| S3 endpoint host | `s3.us-west-004.backblazeb2.com` | Stored on `storage_accounts.s3_endpoint`; used by S3-compatible clients |
| S3 endpoint label | `us-west-004`, `us-east-005`, `eu-central-003` | The middle component of the host; passed to S3 SDKs as the AWS region |

Validate current region identifiers with Backblaze before production use (`docs/known-gaps.md` §3).

## 7a. S3-Compatible API Settings

The platform's control plane uses the B2 Native API. The S3-compatible API is offered to tenants as an alternative interface to their own data — they connect directly to B2 using their provider key as an AWS-style credential.

| Key | Default | Purpose |
|---|---|---|
| `S3_ACCESS_FOR_TENANTS` | `true` | Whether tenant-facing documentation and provisioning surfaces include S3 endpoint info |
| `S3_DEFAULT_ENCRYPTION_MODE` | `none` | Default bucket encryption applied at provisioning: `none`, `sse-b2`, or `sse-c` (per overlay) |
| `S3_PRESIGNED_URL_MAX_TTL_SECONDS` | `604800` | Max TTL the platform documents to tenants for S3-style presigned URLs (AWS SDK enforces 7 days) |
| `S3_RECONCILIATION_LIST_OBJECTS_ENABLED` | `false` | If true, the reconciliation job calls `ListObjectsV2` per bucket to detect S3-direct uploads missing from the `objects` table |

See `docs/s3-compatible-api.md` for the full S3 surface, supported operations, and limitations.

---

## 8. Upload Defaults

All values configurable via environment variables. See `CLAUDE.md` §Upload Defaults for the authoritative table.

| Key | Default |
|---|---|
| `UPLOAD_MULTIPART_THRESHOLD_BYTES` | `104857600` (100 MB) |
| `UPLOAD_DEFAULT_PART_SIZE_BYTES` | `104857600` (100 MB) |
| `UPLOAD_MIN_PART_SIZE_BYTES` | `5242880` (5 MB) |
| `UPLOAD_MAX_PART_SIZE_BYTES` | `5368709120` (5 GB) |
| `UPLOAD_MAX_PARTS` | `10000` (B2 fixed) |
| `UPLOAD_PART_CONCURRENCY` | `4` |
| `UPLOAD_FILE_CONCURRENCY` | `3` |
| `UPLOAD_MAX_INFLIGHT` | `10` |
| `UPLOAD_MAX_RETRIES` | `3` |
| `UPLOAD_BACKOFF_BASE_MS` | `1000` |
| `UPLOAD_BACKOFF_MAX_MS` | `30000` |
| `UPLOAD_SESSION_TTL_HOURS` | `24` |

---

## 9. Small-File Strategy

| Key | Default | Purpose |
|---|---|---|
| `SMALL_FILE_PREFER_MIN_SIZE_MB` | `1` | Soft guidance threshold |
| `SMALL_FILE_ENFORCE_MIN_SIZE` | `false` | Whether to reject objects below the threshold |
| `PACK_SMALL_FILES_WHEN_PRACTICAL` | `true` | Enable packed-object manifests when applicable |
| `PACK_SEGMENT_MAX_BYTES` | `10485760` (10 MB) | Max packed segment size before flush |
| `PACK_SEGMENT_MAX_RECORDS` | `10000` | Max records per packed segment |
| `PACK_FLUSH_INTERVAL_MS` | `60000` | Max time before flushing partial segment |

See `docs/small-file-and-throughput-guidance.md` for the full packing pattern.

---

## 10. Usage Import

| Key | Default | Purpose |
|---|---|---|
| `USAGE_IMPORT_FREQUENCY` | `daily` | Cadence for fetching B2 usage CSVs | customer overlay |
| `USAGE_IMPORT_ARCHIVE_BUCKET` | (operator-set) | Control bucket where raw CSVs are archived before ingest |
| `USAGE_IMPORT_ATTRIBUTION_PRIORITY` | `provider_customer_account_id, storage_account_id, bucket_id, object_metadata` | Ordered attribution match strategy | customer overlay |
| `USAGE_IMPORT_RETENTION_DAYS` | `365` | How long archived raw CSVs are retained |
| `UNATTRIBUTED_ROW_ALERT_THRESHOLD` | `100` | Alert threshold for unattributed rows per ingest |

---

## 11. Billing and Reporting

| Key | Default | Purpose |
|---|---|---|
| `BILLING_PERIOD` | `month` | Billing window granularity |
| `BILLING_CURRENCY` | `USD` | Reporting currency |
| `BILLING_EXPORT_FORMATS` | `csv,json` | Supported export formats | customer overlay |
| `BILLING_FINALIZATION_REQUIRES_OVERRIDE` | `true` | Whether finalized periods require explicit override to recalculate |
| `REPORT_EXPORT_PATH` | (operator-set) | Destination for report export artifacts |

---

## 12. Quota Policy

| Key | Default | Purpose |
|---|---|---|
| `QUOTA_MODE` | `soft` | `soft` (warn) or `hard` (reject upload) | customer overlay |
| `QUOTA_WARN_AT_PERCENT` | `80` | Warning threshold |
| `QUOTA_BLOCK_AT_PERCENT` | `100` | Hard-block threshold (for `hard` mode) |

Quotas are configured per project in `projects.quota_policy` (JSON column). The shape of that JSON is operator-defined.

---

## 13. Portal Scope

| Key | Default | Purpose |
|---|---|---|
| `PORTAL_ADMIN_ENABLED` | `true` | Whether the platform admin portal is mounted | customer overlay |
| `PORTAL_TENANT_ENABLED` | `true` | Whether the tenant portal is mounted | customer overlay |
| `PORTAL_END_USER_FILE_BROWSER` | `false` | Whether a per-end-user object browser is mounted | customer overlay |

---

## 14. Compliance and Audit

| Key | Default | Purpose |
|---|---|---|
| `OBJECT_LOCK_REQUIRED` | `false` | Whether B2 Object Lock must be enabled on buckets | customer overlay |
| `RETENTION_REQUIRED` | `false` | Whether retention policies are enforced | customer overlay |
| `AUDIT_EXPORT_REQUIRED` | `true` | Whether audit_events can be exported on demand | customer overlay |
| `AUDIT_RETENTION_DAYS` | `2555` (7 years) | How long audit_events are retained |

---

## 15. Operational Jobs

| Key | Default | Purpose |
|---|---|---|
| `STALE_UPLOAD_CLEANUP_INTERVAL` | `3600` (1 hour) | How often the stale upload cleanup job runs |
| `RECONCILIATION_INTERVAL` | `86400` (24 hours) | How often the reconciliation job runs |
| `RETENTION_PURGE_INTERVAL` | `86400` (24 hours) | How often the retention purge job runs |
| `KEY_ROTATION_INTERVAL_DAYS` | `90` | Scheduled provider key rotation interval |

---

## 16. Security

| Key | Default | Purpose |
|---|---|---|
| `SECRETS_STORE` | (required for `b2`) | Secrets backend identifier (e.g., HashiCorp Vault, AWS Secrets Manager) |
| `SECRETS_STORE_PROVIDER_KEY_PATH` | (operator-set) | Path template for storing provider key values |
| `REDACT_LOG_FIELDS` | `applicationKey, authorizationToken` | Log fields that must never appear in output |

**Hard invariant:** Provider application key values must never be logged or returned in any API response after the initial creation response. Verified by quality gate.

---

## 17. Source-of-Truth Map

This reference assembles values from multiple authoritative documents. When a value differs across docs, the source-of-truth wins:

| Topic | Authoritative document |
|---|---|
| Upload defaults | `CLAUDE.md` §Upload Defaults |
| Key capabilities | `CLAUDE.md` §Key Capabilities Reference |
| Region codes and Partner API behavior | `docs/provisioning-and-partner-api.md` |
| Customer overlay configurable keys | `customer-overlays/customer-profile.template.yaml` |
| Hard invariants | `docs/source-of-truth.md` §Hard invariants |
| Configurable defaults | `docs/source-of-truth.md` §Configurable defaults |
| Schema column names | `docs/data-model.md` |

If a setting appears here but not in any source-of-truth doc, treat it as an operator-defined extension. Document it in a customer overlay before relying on it.
