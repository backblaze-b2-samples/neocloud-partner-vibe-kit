---
status: context-pack
token_note: Short compressed context. Open full docs only when needed.
---

# Usage Reporting Context

Usage attribution starts with provider account/storage account, then bucket ID/name, then internal metadata. Bucket name alone is not reliable. Unknown rows become unattributed. Use durable usage events and reconciled provider imports; do not use local/frontend counters.
