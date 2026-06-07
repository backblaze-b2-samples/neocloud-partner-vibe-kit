---
last_verified: 2026-06-06
status: reference
source_of_truth_for:
  - target entities
  - ownership metadata
  - provider account mapping
---

# Data Model

This is the target data model for the neocloud control plane. It is not a statement about what the current starter app already implements.

> Term definitions for the entities below are in `docs/glossary.md`. For the precedence order when this doc conflicts with another, see `docs/source-of-truth.md`.

## Core relationships

```text
tenant 1--many storage_accounts
storage_account 1--many buckets
project many--1 tenant
object many--1 project
object many--1 bucket
provider_key many--1 storage_account
service_account 1--many api_keys
usage_event many--1 tenant/project/object
```

Tenant isolation is account/sub-account-driven. A tenant may have multiple storage accounts when the customer needs multiple regions.

### Cross-table ownership invariant (normative)

Several child tables (`buckets`, `objects`, `provider_keys`, `usage_events`,
`upload_sessions`, …) carry a denormalized `tenant_id` **in addition to** a
foreign key to a parent that also has a tenant. This is a query-scoping
convenience, **not** an independent source of truth.

- The **parent chain is authoritative.** A row's `tenant_id` MUST equal the
  `tenant_id` of every parent it references. For example, a `bucket`'s
  `tenant_id` must equal its `storage_account`'s `tenant_id`; an `object`'s must
  equal its `project`'s, `bucket`'s, and `storage_account`'s.
- This invariant MUST be enforced on write — by the repository layer, a DB
  trigger, or composite foreign keys — because plain single-column FKs do **not**
  prevent a mismatched `tenant_id`. A mismatch is an isolation bug, not a valid
  state; creating such a row is an error.
- Authorization and tenant scoping read the denormalized `tenant_id` for
  performance, which is safe only because the write-time invariant holds.

## Canonical entities

### groups

- `id`
- `provider`
- `provider_group_id`
- `name`
- `region_strategy`
- `created_at`

A Group organizes customer accounts. In this data model, `groups` records link/cache existing Backblaze Groups created in the Backblaze website; `created_at` is the local mapping timestamp, not provider Group creation time.

### tenants

- `id`
- `name`
- `status`
- `provider_customer_account_id` (default/primary if one exists)
- `provider_group_id`
- `billing_account_id`
- `created_at`
- `suspended_at`

A tenant/customer maps to one or more provisioned B2 customer accounts/sub-accounts through `storage_accounts`.

### storage_accounts

- `id`
- `tenant_id`
- `provider`
- `provider_customer_account_id`
- `provider_group_id`
- `region`
- `alias`
- `provider_member_email`
- `s3_endpoint`
- `status`
- `created_at`
- `suspended_at`
- `ejected_at`

A storage account represents the provider-side B2 customer account/sub-account relationship. It is the primary provider isolation mapping. For Backblaze Partner API provisioning, `alias` should match the `memberEmail` sent to `b2_create_group_member`; keep `provider_member_email` for explicit traceability when needed. `status = suspended` is a local/composite Neocloud access state and must not imply Partner API eject. `ejected_at` records high-friction provider Group ejection; ejected accounts cannot be re-added to a Group through the Partner API and existing provider application keys must be handled separately.

### buckets

- `id`
- `tenant_id`
- `storage_account_id`
- `provider_bucket_id`
- `bucket_name`
- `purpose`
- `region`
- `lifecycle_policy`
- `retention_policy`
- `created_at`

Buckets are child resources inside a storage account. They are not the root tenant isolation model.

### provider_keys

- `id`
- `tenant_id`
- `storage_account_id`
- `bucket_id`
- `provider`
- `provider_key_id`
- `name`
- `scope`
- `capabilities`
- `file_name_prefix_or_scope`
- `status`
- `created_at`
- `revoked_at`
- `last_used_at`

Provider keys are B2 application keys created inside a provisioned B2 customer account/sub-account. They are distinct from platform API keys.

### api_keys

- `id`
- `tenant_id` (NULL for platform-scoped keys, e.g. a `platform_admin` key)
- `project_id`
- `service_account_id` (the machine principal that owns the key — see `service_accounts`)
- `name`
- `role` (the RBAC role — see `docs/security-and-tenant-isolation.md` §Roles and permissions)
- `scopes` (optional finer-grained narrowing *within* the role; the `role` is the primary authority)
- `key_hash` (a one-way hash of the secret key value; see below)
- `status` (`active` | `revoked`)
- `created_at`
- `last_used_at`
- `revoked_at`

Application-level platform API keys. Authorization is **role-based**: the `role`
gates the neocloud application API. These are distinct from `provider_keys`,
which are B2 application keys that gate access to B2 itself.

The `id` is the public identifier. The **secret value is shown exactly once at
creation and is never persisted** — only its hash is stored in `key_hash`, and
authentication compares a hash of the presented secret against it. `scopes` is
*not* a secret store. Update `last_used_at` on successful auth.

### service_accounts

- `id`
- `tenant_id` (NULL for platform/operator service accounts)
- `name`
- `default_role`
- `status`
- `created_at`

A non-human principal (a service or integration) that owns one or more
`api_keys`, referenced by `api_keys.service_account_id`. Human identities are
operator-defined (see `docs/known-gaps.md`).

### projects

- `id`
- `tenant_id`
- `name`
- `status`
- `quota_policy`
- `storage_policy`
- `created_at`

Projects are application-level metadata boundaries. They are not isolated by path alone.

### objects

- `id`
- `tenant_id`
- `project_id`
- `storage_account_id`
- `bucket_id`
- `physical_b2_file_name`
- `logical_path`
- `original_filename`
- `safe_filename`
- `size_bytes`
- `checksum`
- `content_type`
- `created_at`
- `deleted_at`

Object ownership comes from metadata. The physical B2 file name is internal and uses `distribution_id` for high-scale generated names; the exact builder (input, algorithm, length, and `safe_filename` rules) is pinned in `docs/adr/002-b2-file-name-distribution.md` §Specification.

### upload_sessions

- `id`
- `tenant_id`
- `project_id`
- `storage_account_id`
- `bucket_id`
- `object_id`
- `physical_b2_file_name`
- `mode` (`single`, `multipart`)
- `status`
- `provider_upload_id`
- `part_size_bytes`
- `created_at`
- `completed_at`
- `aborted_at`

### upload_parts

- `id`
- `upload_session_id`
- `part_number`
- `offset`
- `size_bytes`
- `checksum`
- `provider_part_id`
- `status`

### usage_events

- `id`
- `tenant_id`
- `project_id`
- `storage_account_id`
- `bucket_id`
- `object_id`
- `actor_id`
- `api_key_id`
- `event_type`
- `bytes`
- `request_id`
- `provider_request_id`
- `occurred_at`
- `metadata`

Usage events are append-only.

### usage_imports and usage_import_rows

Use these to store raw B2 usage CSV imports and normalized rows. Attribution starts with provider account/storage account, then bucket ID/name, then internal metadata. Unknown mappings become unattributed rows for review.

### billing_periods, billing_ledger, report_exports

Billing-period and export entities should be deterministic projections from usage events and reconciled provider imports. They are not payment processing records.

### audit_events

- `id`
- `tenant_id`
- `actor_id`
- `event_type`
- `resource_type`
- `resource_id`
- `request_id`
- `occurred_at`
- `metadata`

Audit events are append-only.

## Optional packed-object entities

For small-file-heavy workflows, add:

### packed_object_manifests

- `id`
- `tenant_id`
- `project_id`
- `object_id`
- `physical_b2_file_name`
- `manifest_version`
- `created_at`

### packed_object_entries

- `id`
- `manifest_id`
- `logical_name`
- `offset`
- `length`
- `checksum`
- `content_type`
- `metadata`
