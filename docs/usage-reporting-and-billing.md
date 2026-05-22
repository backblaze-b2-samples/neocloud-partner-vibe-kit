# Usage Reporting and Billing

## Goals

- Track usage by tenant, storage account, project, bucket, and object metadata.
- Ingest B2 usage CSVs.
- Reconcile internal usage events with provider reports.
- Generate deterministic chargeback/billing exports.

## Usage event ledger

Event types include:

- `object_upload_started`
- `object_upload_completed`
- `object_upload_failed`
- `object_downloaded`
- `object_deleted`
- `multipart_started`
- `multipart_part_uploaded`
- `multipart_completed`
- `multipart_aborted`
- `api_key_created`
- `api_key_revoked`
- `quota_exceeded`

Usage events are append-only. Do not use frontend or local JSON counters for billing.

## S3-compatible API usage in the CSV

B2's daily and monthly usage CSV records every operation regardless of which API surfaced it. Operations against the S3-compatible endpoint appear with the same Account ID and Bucket Name columns as B2 Native operations — there is no separate column distinguishing "S3" vs "Native" usage.

This means:

- `usage_import_rows` is the complete billing source of truth for both API surfaces.
- `usage_events` (platform-mediated) is incomplete for tenants who use S3 directly. Treat it as the platform's view, not the billing source.
- The reconciliation job will show a persistent delta for S3-heavy tenants. Document the expected delta in the customer overlay's `notes:`.

## Provider CSV attribution

Usage attribution starts with provider account/storage account first, then bucket ID or bucket name, then internal bucket/project/object metadata. Bucket name alone is not a reliable tenant identifier.

Attribution order:

1. Provider customer account ID / `storage_account_id`
2. Provider bucket ID or bucket name
3. Internal bucket metadata
4. Internal project/object metadata where available
5. Unattributed import row if mapping is missing

Unknown account/bucket combinations should be imported as unattributed rows for review.

## Ingestion flow

1. Upload/import CSV.
2. Validate headers.
3. Store raw import with checksum.
4. Normalize rows.
5. Map provider account ID to `storage_account`.
6. Map bucket ID/name to internal bucket metadata.
7. Store unattributed rows when mappings are missing.
8. Reconcile against internal usage events.
9. Generate tenant/project/billing-period reports.

## Reports

- tenant usage summary
- project usage summary
- daily usage report
- billing-period report
- discrepancy report
- raw usage export

## Tests

- parse and validate CSV
- account-first attribution
- bucket as secondary attribution
- missing mappings become unattributed
- idempotent import
- reconciliation drift is reported
- billing export is deterministic
