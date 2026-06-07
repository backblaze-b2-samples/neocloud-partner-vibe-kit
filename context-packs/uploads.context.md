---
status: context-pack
token_note: Short compressed context. Open full docs only when needed.
source_of_truth:
  - docs/upload-data-plane.md
  - docs/configuration-reference.md
  - docs/adr/004-multipart-upload-defaults.md
  - docs/s3-compatible-api.md
---

# Uploads Context

## Purpose
Parallel, resilient, high-throughput uploads.

## Core rules
- <100 MB: single upload.
- >=100 MB: multipart.
- 100 MB default part size.
- 5 MB minimum part except final.
- 5 GB max part.
- 10,000 part limit.
- File concurrency 3, per-file part concurrency 4, global in-flight 10.
- Retry transient failures; abort incomplete multipart uploads.
- Use shared B2 file-name builder.
- Avoid excessive tiny-object amplification when practical.

## Two API surfaces
- Platform-mediated uploads use the B2 Native Large File API; the platform records `usage_events` and `audit_events`.
- Tenants may also upload via the S3-compatible API directly (`s3.{region}.backblazeb2.com`, SigV4, same B2 application key). Same multipart part-size rules apply. The platform does not see these uploads — `usage_events` is incomplete; `usage_import_rows` from the daily B2 CSV is the billing source of truth.
- See `docs/s3-compatible-api.md` when the task touches S3 multipart, S3 presigned URLs, or tenant-facing S3 client config.

## Tests
Concurrency, retry, abort, thresholds, file-name builder, small-file policy. For S3: SigV4 auth, master key never used as S3 credential.
