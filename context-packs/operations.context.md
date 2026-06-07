---
status: context-pack
token_note: Short compressed context. Open full docs only when needed.
source_of_truth:
  - docs/operational-runbook.md
  - docs/configuration-reference.md
  - docs/quality-gates.md
  - docs/s3-compatible-api.md
---

# Operations Context

Cover health, metrics, logs, audit events, failed upload investigation, stuck multipart cleanup, provider API failures, usage reconciliation drift, tenant suspension, provider key revocation, quota exceeded, and multi-region reporting checks.

## Don't reinvent — operational defaults live in full docs

Operational-job intervals and alert thresholds are already specified in
`docs/configuration-reference.md` §15 (Operational Jobs) and §10:
`STALE_UPLOAD_CLEANUP_INTERVAL`=3600s, `RECONCILIATION_INTERVAL`=86400s,
`KEY_ROTATION_INTERVAL_DAYS`=90, `UNATTRIBUTED_ROW_ALERT_THRESHOLD`=100.
Incident procedures are in `docs/operational-runbook.md`; reconciliation
drift for S3-direct tenants is expected (see `docs/s3-compatible-api.md`).
