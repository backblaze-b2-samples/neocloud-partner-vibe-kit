---
last_verified: 2026-06-06
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

## S3-compatible client workflow

For tenants whose tooling already speaks S3 (boto3, AWS CLI, Rclone, Cyberduck, MinIO mc, S3-aware analytics pipelines), provision the tenant as normal (`POST /admin/tenants`) and then expose three values to the tenant: the `s3_endpoint` host (e.g., `s3.us-west-004.backblazeb2.com`), the `applicationKeyId` (used as the AWS access key), and the `applicationKey` (used as the AWS secret, returned exactly once at key creation). The tenant configures their S3 client with these values using SigV4 auth. Do not provision a separate AWS-style credential — the same B2 provider key works for both API surfaces. Document the unsupported S3 features (SSE-KMS, object tagging, IAM roles, object-level ACLs) in the tenant's onboarding materials. The operator master key must never appear in a tenant's S3 config. See `docs/s3-compatible-api.md`.

## Inference serving with S3 + CDN cache

For workloads that load model artifacts at inference time: use S3-compatible API for the model retrieval path (most ML serving frameworks expect S3 semantics) and place a CDN or per-node cache in front of B2 to handle first-byte latency. The platform records the per-account `s3_endpoint` so inference servers can be configured directly. Cache hit rate becomes a separate operational concern outside the kit. See `customer-overlays/customer-profile.example-multi-workload.yaml` for a complete worked example.
