---
status: context-pack
token_note: Short compressed context. Open full docs only when needed.
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

## Tests
Concurrency, retry, abort, thresholds, file-name builder, small-file policy.
