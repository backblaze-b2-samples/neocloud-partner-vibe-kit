<!-- last_verified: 2026-06-06 -->
# ADR 003 — Provider Account-first Usage Attribution

## Status
Accepted

## Decision
Attribute provider usage by provider account/storage account first, bucket second, internal metadata third. Bucket name alone is not reliable. Unknown rows are imported as unattributed.
