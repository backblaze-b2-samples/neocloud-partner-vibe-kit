---
status: context-pack
token_note: Short compressed context. Open full docs only when needed.
source_of_truth:
  - docs/usage-reporting-and-billing.md
  - docs/configuration-reference.md
  - docs/data-model.md
  - docs/adr/003-provider-account-first-usage-attribution.md
---

# Usage Reporting Context

Usage attribution starts with provider account/storage account, then bucket ID/name, then internal metadata. Bucket name alone is not reliable. Unknown rows become unattributed. Use durable usage events and reconciled provider imports; do not use local/frontend counters.

## S3 vs B2 Native usage

B2's daily CSV records every operation regardless of API surface. The CSV does not distinguish "S3" vs "Native" — both appear under the same Account ID / Bucket Name columns. Implications:

- `usage_import_rows` (from the CSV) is the complete billing source of truth for both API surfaces.
- `usage_events` is incomplete for tenants who use the S3-compatible API directly against B2 — those requests never reach the platform.
- Expect a persistent reconciliation delta for S3-heavy tenants; this is documented, not a bug. See `docs/s3-compatible-api.md` §Operational Considerations.

## Idempotent import

Imports are idempotent: store each raw import with a **checksum** and skip
re-ingesting identical content (see `docs/usage-reporting-and-billing.md`
§Ingestion flow, and `docs/configuration-reference.md` §10 Usage Import).
