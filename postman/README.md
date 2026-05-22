# Postman Collection

This folder contains Postman artifacts for Backblaze APIs.

## Backblaze API surfaces

Backblaze exposes three relevant API surfaces:

| API | Purpose | Coverage in this folder |
|---|---|---|
| **B2 Native API** | Authorization, buckets, keys, uploads, downloads, file metadata | Included in the v3 collection |
| **Partner API** | Customer account provisioning within Groups (`b2_create_group_member`, `b2_eject_group_member`, `b2_list_groups`, `b2_list_group_members`) | Included as a request group inside the same v3 collection (shares the B2 Native base URL) |
| **S3-compatible API** | S3 protocol access (`s3.{region}.backblazeb2.com`) — bucket and object operations using AWS SigV4 auth | Included as `Backblaze B2 Cloud Storage S3 Compatible API.postman_collection.json` |

For the target neocloud application API (the platform's own endpoints you are building), use `docs/api-contracts.md` — not this collection.

## B2 Native + Partner API collection

`Backblaze_B2_Postman_Collection_CORRECTED_v3.json`

Status: candidate corrected v3 reference collection pending live-environment review.

The collection is organized into request groups for Authentication, Bucket Management, File Operations, Large File Operations, Application Key Management, Event Notification Rules, and Partner API. Use it for B2 API familiarization, request-shape reference, and manual testing — not as the source of truth for the neocloud application API.

Use these environments with this collection:

- `b2-native-example.postman_environment.json`
- `b2-native-local.postman_environment.json`

These are placeholder templates. Never commit a populated environment with real credentials. For Partner API account creation, set `memberEmail` to the Neocloud alias value. For large-file part uploads, set `partSha1` to the precomputed SHA-1 for the current part and use the same checksum in `b2_finish_large_file`. For Object Lock examples, set `retainUntilTimestamp` to a future Unix timestamp in milliseconds.

## S3-compatible API collection

`Backblaze B2 Cloud Storage S3 Compatible API.postman_collection.json`

Covers the most commonly used S3 actions against B2's S3-compatible endpoint (`s3.{region}.backblazeb2.com`). Two top-level groups:

- **Bucket Operations** (22 requests) — create, delete, list, get bucket policy, versioning, encryption, lifecycle, etc.
- **Object Operations** (12 requests) — put, get, copy, delete, multipart upload, etc.

Auth type: **AWS SigV4**. The `applicationKeyId` becomes the AWS access key; the `applicationKey` becomes the AWS secret.

Use these environments with the S3 collection:

- `s3-example.postman_environment.json` — template for real credentials
- `s3-local.postman_environment.json` — placeholder values for local development

Variables used by the S3 collection:

| Variable | Purpose |
|---|---|
| `applicationKeyId` | Maps to AWS access key for SigV4 auth |
| `applicationKey` | Maps to AWS secret key for SigV4 auth |
| `region` | B2 S3 region (e.g., `us-west-004`); used in the host URL |
| `keyMd5` | Base64-encoded MD5 of the customer-managed key, for SSE-C requests |

Bucket and object names are passed as Postman path parameters (`:bucket`, `:key`) on individual requests — not via environment variables.

### Choosing between B2 Native and S3-compatible

The neocloud platform's control plane and platform-mediated data plane use the **B2 Native API** because Partner API operations and large-file uploads are first-class there. The **S3-compatible API** exists for tenants whose applications already speak S3 and want to point an existing S3 client at B2 directly. The `storage_accounts.s3_endpoint` column records the S3 endpoint per customer account for those tenants.

## Neocloud platform API environments

Use these for future neocloud platform API requests, not for the B2 Native API collection:

- `neocloud-example.postman_environment.json`
- `neocloud-local.postman_environment.json`

## Security

Do not commit real API keys, application keys, customer data, account IDs, bucket IDs, production URLs, private tokens, or cookies.
