---
last_verified: 2026-06-06
status: reference
source_of_truth_for:
  - S3-compatible API surface
  - When tenants use S3 vs B2 Native
  - S3 endpoint format, auth, and supported operations
---

# S3-Compatible API

Backblaze B2 exposes an S3-compatible API alongside the B2 Native API. The S3-compatible API lets tenants point existing S3 clients (AWS SDKs, S3 CLI, S3-aware tools like Cyberduck, Rclone, MinIO clients) directly at their B2 buckets.

The platform itself uses the **B2 Native API + Partner API** for control-plane and platform-mediated data-plane operations. The S3-compatible API is offered to **tenants** as an alternative interface to their own data — they read and write through their own customer account using their own provider key.

> Entity references (`storage_accounts`, `provider_keys`, `buckets`) are defined in `docs/data-model.md`. Term definitions (SigV4, SSE-B2, SSE-C, path-style, etc.) are in `docs/glossary.md`. For precedence when this doc conflicts with another, see `docs/source-of-truth.md`.

---

## When Tenants Use S3 vs B2 Native

| Use case | Recommended interface |
|---|---|
| Generic S3 SDK code (boto3, aws-sdk-js, AWS CLI) | S3-compatible |
| Existing tools that speak S3 (Rclone, Cyberduck, MinIO mc) | S3-compatible |
| Inference servers loading model artifacts | S3-compatible (better cache/CDN integration) |
| Application-layer dual-write to another S3 provider | S3-compatible (uniform client) |
| Backblaze-specific workflows (Partner API, B2 Reserve, Large File API with progress reporting) | B2 Native |
| Workflows that need every B2 feature on day one | B2 Native |
| Maximum throughput for very large files using B2-specific tuning | Either; B2 Native gives finer-grained control |

Tenants may use **both** simultaneously against the same buckets — the data is shared.

The platform's control plane (`POST /admin/tenants`, suspend, eject, key rotation) always goes through the B2 Native and Partner APIs via the `NeocloudStorageProvider` abstraction. Tenants never call the platform's S3 endpoint — they use S3 against B2 directly.

---

## Endpoint Format

```
https://s3.{region}.backblazeb2.com/{bucket}/{key}          (path-style)
https://{bucket}.s3.{region}.backblazeb2.com/{key}          (virtual-hosted-style)
```

- **HTTPS only.** Plain HTTP is not accepted.
- **Both URL styles are supported.** Most modern SDKs default to virtual-hosted-style.
- `{region}` is the S3 endpoint label, e.g., `us-west-004`, `us-east-005`, `eu-central-003`. This is **different** from the Partner API region code — see "Region values" below.

The endpoint per customer account is recorded in `storage_accounts.s3_endpoint` at provisioning time. Clients can also discover it from the `s3ApiUrl` returned by `b2_authorize_account`.

---

## Region Values

Two related but distinct values exist for regions and they are **not interchangeable**:

| Value | Where it appears | Example | Used by |
|---|---|---|---|
| Partner API region code | `b2_create_group_member` `region` parameter; `storage_accounts.region` column | `us-east`, `us-west`, `ca-east`, `eu-central` | Customer account creation |
| S3 endpoint label | URL in S3 requests; `storage_accounts.s3_endpoint` column | `us-east-005`, `us-west-004`, `eu-central-003` | S3 client connections |

When a customer account is provisioned, Backblaze returns the specific S3 endpoint for that account. Store both values. Do not infer one from the other.

---

## Authentication

**Only AWS Signature Version 4 (SigV4) is supported. SigV2 is not accepted.**

The B2 application key works directly as an S3 credential:

| AWS field | B2 field | Notes |
|---|---|---|
| AWS Access Key ID | `applicationKeyId` | Same value, no conversion |
| AWS Secret Access Key | `applicationKey` | Same value, no conversion |
| AWS Region | Partner API region (e.g., `us-west`) or S3 endpoint label (e.g., `us-west-004`) — depends on the SDK; most accept the endpoint label | Used in the signing string |
| AWS Service | `s3` | Standard for S3 calls |

No separate "AWS-style" credential needs to be provisioned. Any B2 application key with the required capabilities works as an S3 credential.

### Never Use the Operator Master Key as an S3 Credential

Backblaze does not technically restrict which keys can use the S3 API — the master application key works as an S3 credential just like any other B2 key. **The platform must not allow this in practice.** The master key has full Partner API access and account-level scope across every customer account. Using it as an S3 credential — even for testing — creates a credential with the broadest possible blast radius on the easiest-to-leak surface (S3 client config files, environment variables, CI logs).

Rules:

- The master key is loaded only by the platform's control plane, behind the `NeocloudStorageProvider` abstraction.
- No tenant ever receives the master key in any form.
- No platform code path that runs in a tenant context loads the master key.
- S3 client configurations (boto3 config, AWS CLI profile, `.aws/credentials`) used by tenants reference a tenant-scoped provider key, never the master key.
- For operator-side S3 testing (e.g., verifying SSE behavior), provision a dedicated operator-scoped key with the minimum capabilities for the test — do not reuse the master.

### Required Capabilities

The B2 capability model maps to S3 operations as follows. Provision tenant keys with only the capabilities the tenant's workload needs:

| S3 operation class | Required B2 capabilities |
|---|---|
| GetObject, HeadObject, ListBucket, ListObjects | `readFiles`, `listFiles` |
| PutObject, multipart upload | `writeFiles` |
| DeleteObject | `deleteFiles` |
| GetBucketAcl, GetBucketLocation, GetBucketVersioning | `listFiles` (typically already present) |
| Presigned URL generation by tenant (CreatePresignedUrl) | `shareFiles` |
| PutBucketLifecycleConfiguration, PutBucketEncryption | Master / control-plane capabilities only — do not grant to tenants |

Default tenant capability set: `listFiles, readFiles, writeFiles, shareFiles` (and optionally `deleteFiles`). See `CLAUDE.md` §Key Capabilities Reference.

---

## Supported S3 Operations

Validated against Backblaze documentation. The list reflects the most commonly used S3 operations; consult the live Backblaze docs for the authoritative current list.

### Bucket operations

- ListBuckets
- CreateBucket
- DeleteBucket
- HeadBucket
- GetBucketLocation
- GetBucketAcl / PutBucketAcl (limited — canned values only)
- GetBucketVersioning / PutBucketVersioning (versioning is on by default for B2)
- GetBucketLifecycleConfiguration / PutBucketLifecycleConfiguration / DeleteBucketLifecycle (current-version `Expiration{Days}` **must be paired with an `ExpiredObjectDeleteMarker` rule of the same prefix** or B2 returns MalformedXML; noncurrent-version expiration + incomplete-multipart cleanup work alone; **no** storage-class transitions, tag/size filters, `And`, or disabled rules; versioned buckets only. See `docs/migrating-from-aws-s3.md` §6b)
- GetBucketEncryption / PutBucketEncryption / DeleteBucketEncryption (SSE-B2 / SSE-C only)
- GetBucketCORS / PutBucketCORS / DeleteBucketCORS
- GetObjectLockConfiguration / PutObjectLockConfiguration
- GetBucketPolicy / PutBucketPolicy / DeleteBucketPolicy (limited subset)

### Object operations

- GetObject
- PutObject
- HeadObject
- DeleteObject
- DeleteObjects (batch delete)
- CopyObject
- ListObjects (v1)
- ListObjectsV2
- ListObjectVersions
- GetObjectAcl (returns based on bucket ACL — object ACLs are not supported)
- GetObjectRetention / PutObjectRetention
- GetObjectLegalHold / PutObjectLegalHold

### Multipart upload operations

- CreateMultipartUpload
- UploadPart
- UploadPartCopy
- CompleteMultipartUpload
- AbortMultipartUpload
- ListMultipartUploads
- ListParts

Multipart part-size requirements:
- Minimum part size: 5 MB (except final part)
- Maximum part size: 5 GB
- Maximum parts: 10,000
- Recommended part size: 100 MB (matches B2 Native multipart defaults)

### Encryption

- **SSE-B2** — Backblaze-managed keys, enabled per-bucket via PutBucketEncryption or per-request.
- **SSE-C** — Customer-managed keys, supplied per-request via `x-amz-server-side-encryption-customer-*` headers. The `keyMd5` variable in the Postman environment is the base64-encoded MD5 of the customer key.
- **SSE-KMS** — **Not supported.** Do not design workflows that depend on SSE-KMS.

### Versioning

- B2 buckets have versioning **on by default**.
- ListObjectVersions, GetObject with `versionId`, DeleteObject with `versionId` all work.
- "Hide" versions in B2 correspond to S3 delete markers.

---

## Explicitly NOT Supported

These S3 features are documented by Backblaze as not currently supported. The platform must not present them as available to tenants:

- **IAM roles / STS** — There is no `AssumeRole` analog. Use B2 application keys directly.
- **Object Tagging** — `PutObjectTagging` and `GetObjectTagging` either fail or return empty.
- **Website Configuration** — Static website hosting via S3 is not supported.
- **Bucket Logging** — S3 server access logging (`PutBucketLogging`) is not supported.
- **Browser-based POST uploads to presigned URLs** — Standard S3 POST policy uploads do not work.
- **Object-level ACLs** — Setting per-object ACLs returns 403; objects inherit their bucket's ACL.
- **SSE-KMS encryption** — Use SSE-B2 or SSE-C instead.
- **SigV2** — Use SigV4 only.

If a tenant's workload depends on any of these, document the limitation in their customer overlay and recommend the B2 Native API or an alternative workflow.

---

## Bucket Naming for S3 Use

B2 bucket names are global and follow B2's naming rules (6–50 chars, lowercase letters/digits/hyphens, no leading/trailing hyphen). Bucket names in the S3 API URL must comply with these same B2 rules. The platform's standard bucket naming pattern `{platform_prefix}-{tenantId}-{purpose}` produces valid S3 bucket names.

Caveat: virtual-hosted-style URLs (`https://{bucket}.s3.{region}.backblazeb2.com/...`) require DNS-compatible bucket names. The kit's naming pattern is DNS-compatible by construction, so this is satisfied.

---

## Multipart Upload Considerations

The S3 multipart API and the B2 Native Large File API are equivalent in capability. Choose based on the client:

- **S3 client (boto3, aws-sdk):** Use S3 `CreateMultipartUpload` → `UploadPart` → `CompleteMultipartUpload`.
- **B2 Native client:** Use `b2_start_large_file` → `b2_upload_part` → `b2_finish_large_file`.

Both produce the same underlying B2 object. A multipart upload started via S3 can theoretically be queried via B2 Native `b2_list_unfinished_large_files`, but mixing APIs mid-upload is not recommended and not part of the platform's tested paths.

Apply the same defaults as the B2 Native flow:
- Multipart threshold: 100 MB
- Default part size: 100 MB
- Concurrency: 4 parts per file, 3 files concurrently, 10 in-flight global
- Retry: SigV4 errors (403) are usually clock skew or wrong region — do not retry blindly

---

## Presigned URLs via S3

The S3 API supports presigned URLs natively via the SDK's `generate_presigned_url` (or equivalent). The signing uses the tenant's B2 application key. The URL embeds the `applicationKeyId` (visible) and the SigV4 signature (visible but time-limited).

Presigned URL TTL:
- Minimum: 1 second
- Maximum: 7 days (604800 seconds) — AWS SDK enforces this

The platform's own presigned URL endpoint (`POST /tenant/projects/:projectId/objects/:objectId/presign`) returns a B2 Native API presigned URL via `b2_get_download_authorization`. Tenants who want S3-style presigned URLs generate them client-side using their own provider key.

---

## Server-Side Encryption Details

### SSE-B2 (recommended default for encryption-at-rest)

Set at bucket creation or via `PutBucketEncryption` after creation. Once enabled, all uploads to that bucket are encrypted with Backblaze-managed keys transparently. No additional client config needed.

### SSE-C (customer-managed keys)

Provided per-request via headers:
- `x-amz-server-side-encryption-customer-algorithm: AES256`
- `x-amz-server-side-encryption-customer-key: <base64 of the 256-bit key>`
- `x-amz-server-side-encryption-customer-key-MD5: <base64 of MD5 of the raw key>`

The `keyMd5` variable in the S3 Postman environment corresponds to the third header. The customer is responsible for retaining the key; lose the key and the object is unreadable.

### Mixed encryption in the same bucket

A bucket can hold objects with different encryption modes (some SSE-B2, some SSE-C, some unencrypted) as long as the operator allows it. For compliance-driven workloads, enforce a single mode at the bucket level via PutBucketEncryption.

---

## Operational Considerations for S3 Tenants

### Direct B2 access bypasses the platform's data plane

When a tenant uses S3 directly:
- The platform's `usage_events` table does NOT record the operation. Only `usage_imports` (from the daily B2 CSV) sees it.
- The platform's `objects` metadata table may not reflect the new object until a reconciliation job runs (or until the tenant uses the platform's API to register the object).
- Authorization is enforced by B2 against the tenant's application key scope — not by the platform's middleware.

This is acceptable if the customer overlay's `attribution_priority` lists `provider_customer_account_id` first (which it does by default), because per-account usage attribution still works.

If the operator wants the `objects` table to track every object regardless of which API created it, run a periodic reconciliation job that calls `ListObjectsV2` per bucket and inserts missing rows.

### Logging and audit gaps

S3 direct access does not write `audit_events` rows (the platform never sees the request). For compliance-driven workloads, enable B2 access logging (write API logs to a separate bucket) and ingest those logs into the platform's audit trail as an extension. See `docs/known-gaps.md`.

### Reconciliation under direct S3 access

The reconciliation job (compare `usage_events` vs `usage_import_rows`) will show a permanent delta if a tenant uses S3 heavily. Document this in the overlay's `notes:` so operators expect the delta and don't treat it as a bug.

---

## Cross-References

- `docs/data-model.md` — `storage_accounts.s3_endpoint` column.
- `docs/provisioning-and-partner-api.md` — `s3_endpoint` is returned at customer account creation.
- `docs/configuration-reference.md` §S3 settings — configurable env vars.
- `docs/operational-runbook.md` §S3 Direct Access Troubleshooting — incident response.
- `docs/security-and-tenant-isolation.md` — S3 credential scoping is the same B2 key scope.
- `docs/common-pitfalls.md` — S3-specific pitfalls (SigV2, SSE-KMS, object tagging).
- `docs/adr/008-b2-native-vs-s3-compatible.md` — decision rationale.
- `postman/Backblaze B2 Cloud Storage S3 Compatible API.postman_collection.json` — request/response examples.
- `postman/s3-example.postman_environment.json`, `postman/s3-local.postman_environment.json` — environment templates.
