---
last_verified: 2026-06-26
status: reference
source_of_truth_for:
  - upload thresholds
  - multipart defaults
  - retry behavior
  - B2 file-name generation during upload
---

# Upload Data Plane

## Goals

- High throughput.
- Safe retries.
- Bounded concurrency.
- Clear progress reporting.
- Safe cleanup.
- Metadata-based authorization.

## Two API surfaces for uploads

Tenants may upload through either the platform's data plane (which uses the B2 Native Large File API under the hood) or directly to B2 via the S3-compatible API (using S3 multipart). Both produce the same underlying B2 object. The platform-mediated flow gives the platform durable visibility into upload sessions and writes `usage_events` rows; direct S3 access bypasses both.

See `docs/s3-compatible-api.md` for the S3 alternative, including the equivalent S3 multipart operations and their part-size requirements (5 MB minimum, 5 GB max, 10,000 max parts — identical to B2 Native). The defaults below describe the platform-mediated flow.

## Decision tree

- **Hard limit (Backblaze):** a single `b2_upload_file` (or S3 `PutObject`) accepts **up to 5 GB**. Files **larger than 5 GB must** use the Large File / multipart API — this is the only Backblaze-imposed threshold. See [Backblaze: Create Large Files with the Native API](https://www.backblaze.com/docs/cloud-storage-create-large-files-with-the-native-api).
- **Kit default (tunable):** switch to multipart at **100 MB**. Files smaller than 100 MB use a single-object upload; files at or above 100 MB use multipart. This is a chosen default that favors resumability and parallelism well before the 5 GB ceiling — **not** a Backblaze requirement. It is configurable per deployment (`UPLOAD_MULTIPART_THRESHOLD_BYTES`; see `docs/configuration-reference.md`).
- Prefer objects of at least 1 MB when practical, but do not reject smaller files globally.

Do not confuse:

- 1 MB: preferred minimum object-size guideline when practical.
- 5 MB: minimum multipart part size except final part.
- 100 MB: the kit's **default** multipart threshold and default part size (tunable).
- 5 GB: Backblaze's **hard** maximum for a single (non-multipart) upload, and the maximum size of one part.

## Multipart defaults

- Default part size: 100 MB. Prefer the `recommendedPartSize` value returned by `b2_authorize_account` over hardcoding 100 MB; Backblaze recommends 100 MB as the value that balances throughput against parallelism, but the authorize response is the source of truth and may change.
- Minimum part size: 5 MB except final part.
- Maximum part size: 5 GB.
- Maximum parts: 10,000.
- Adaptive part size for very large files, rounded to nearest 5 MB. (A large file has at least 2 parts, so a deployment that lowers the threshold below the part size should also shrink the part size to keep multipart meaningful.)
- Per-file part concurrency: 4.
- Batch file concurrency: 3.
- Global in-flight upload requests: 10.
- Retry transient failures up to 3 times with exponential backoff and jitter.
- Retry 408, 425, 429, 500, 502, 503, 504, and network errors.
- Do not retry 400, 401, 403, 404, or 413.
- Abort incomplete multipart uploads on cancellation or final failure.

## Canonical APIs

- `POST /tenant/projects/:projectId/upload-sessions`
- `GET /tenant/projects/:projectId/upload-sessions/:sessionId`
- `PUT /tenant/projects/:projectId/upload-sessions/:sessionId/parts/:partNumber`
- `POST /tenant/projects/:projectId/upload-sessions/:sessionId/complete`
- `DELETE /tenant/projects/:projectId/upload-sessions/:sessionId`

## B2 file-name generation

The upload data plane must call the shared B2 file-name builder. Multipart and single uploads use the same naming model. The first B2 file-name component must be `distribution_id`; do not place a constant component such as `objects/` before it.

```text
{distribution_id}/tenants/{tenant_id}/projects/{project_id}/objects/{object_id}/{safe_filename}
```

## Object creation flow

1. Generate durable `object_id`.
2. Sanitize original filename to `safe_filename`.
3. Compute `distribution_id` from tenant/project/object IDs.
4. Build physical B2 file name.
5. Store tenant/project/storage account/bucket/object metadata.
6. Create upload session.
7. Upload single object or multipart parts.
8. Complete or abort.
9. Emit usage and audit events.

## Small-file strategy

For small-file-heavy workloads, prefer batching, packing, or concatenating logical records into larger objects with manifests/indexes and range reads. This is optional and workflow-specific. Do not force it on human document upload workflows.

## Tests

- Multiple files upload with bounded concurrency.
- Multipart triggers at the configured threshold (default 100 MB) and is mandatory above 5 GB.
- Part size respects min/max/10,000-part rules.
- Retry/backoff handles transient failures.
- Validation/auth errors are not retried.
- One failed file does not block others.
- Aborted multipart uploads are cleaned up.
- B2 file-name builder is used for single and multipart flows.
- Small files are accepted unless customer policy blocks them.
- Packed-object range-read workflows validate ownership when enabled.
