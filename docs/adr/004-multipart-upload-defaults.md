<!-- last_verified: 2026-06-26 -->
# ADR 004 — Multipart Upload Defaults

## Status
Accepted

## Context
Backblaze imposes exactly one threshold here: a single `b2_upload_file` (or S3 `PutObject`) accepts up to **5 GB**, and a file **larger than 5 GB must** use the Large File / multipart API. Below 5 GB, choosing single vs multipart is an implementation decision, not a Backblaze rule. Backblaze separately *recommends* a 100 MB part size and exposes `recommendedPartSize` from `b2_authorize_account`. See [Backblaze: Create Large Files with the Native API](https://www.backblaze.com/docs/cloud-storage-create-large-files-with-the-native-api).

## Decision
- **Default multipart threshold: 100 MB** — a tunable kit default, not a Backblaze requirement. Single upload below it, multipart at or above it. Chosen to gain resumability and parallelism well before the 5 GB ceiling; configurable per deployment (`UPLOAD_MULTIPART_THRESHOLD_BYTES`).
- **Above 5 GB, multipart is mandatory** (Backblaze hard limit).
- **Part size: default 100 MB, but prefer `recommendedPartSize` from `b2_authorize_account`** rather than hardcoding. Minimum 5 MB except the final part, maximum 5 GB, maximum 10,000 parts.
- Adaptive part size for very large files (rounded to the nearest 5 MB); a large file needs at least 2 parts, so lowering the threshold below the part size should also shrink the part size.
- Retry/backoff on transient failures; abort incomplete multipart uploads on cancellation or final failure.

## Consequences
The threshold and part size are configurable, so deployments can tune for their workload (e.g., many medium files vs few huge files). The 5 GB single-upload ceiling and the 5 MB / 5 GB / 10,000-part bounds are fixed by Backblaze and must not be overridden.
