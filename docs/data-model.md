---
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
usage_event many--1 tenant/project/object
```

Tenant isolation is account/sub-account-driven. A tenant may have multiple storage accounts when the customer needs multiple regions.

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
- `tenant_id`
- `project_id`
- `service_account_id`
- `name`
- `scopes`
- `status`
- `created_at`
- `revoked_at`

Application-level service API keys for the neocloud platform.

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

Object ownership comes from metadata. The physical B2 file name is internal and uses `distribution_id` for high-scale generated names.

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
