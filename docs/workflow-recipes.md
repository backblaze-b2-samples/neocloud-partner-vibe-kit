---
status: reference
load_when:
  - choosing customer workflow shape
---

# Workflow Recipes

Recipes help customers build the workflow they need without forcing one architecture beyond core invariants.

## AI training checkpoint storage

Use when large model checkpoints and artifacts dominate. Read `context-packs/uploads.context.md` and use PRs 3, 4, 5, and 7. Avoid excessive checkpoint fragmentation; use multipart uploads and usage reporting by tenant/project/storage account.

## Dataset ingest

Use for large datasets and batch ingest. Use manifests, metadata indexing, multipart uploads, and small-record batching where practical.

## Billions of small records

Do not create one tiny object per record unless required. Pack records into larger objects, maintain manifests/indexes, and use range reads. Prefer 1 MB+ objects when practical; this is not a hard requirement.

## Backup/archive workload

Prefer larger segment files, lifecycle/retention policies, Object Lock where needed, and restore workflows. Use PRs 3, 4, 5, 7, and 12.

## Media pipeline

Use multipart upload for large assets, metadata for derived objects, preview/download URLs, and logical paths in the UI.

## Tenant self-service storage portal

Use PRs 10 and 11. Include projects, API keys, upload sessions, usage reports, and metadata-driven browsing.

## Internal chargeback reporting

Use PRs 5, 6, and 7. Build from durable usage events, B2 CSV import, reconciliation, and billing exports.

## API-driven account provisioning with pre-created Groups

Use PRs 8 and 9. No portal is required. Include existing Group selection/linking, account aliases that map to Backblaze `memberEmail`, regional account mapping, and mock provider support. Do not implement Backblaze Group creation through an API; Groups are created in the Backblaze website after Groups are enabled. Treat eject as explicit deprovisioning, not reversible suspension.

## Multi-region customer

Create multiple B2 customer accounts/sub-accounts for the customer, one per required pre-defined region. Metadata maps the tenant to multiple storage accounts. Reporting aggregates across storage accounts when needed.
