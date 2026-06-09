---
last_verified: 2026-06-09
status: reference
load_when:
  - a tenant or partner is bringing existing AWS S3 tooling or code to B2
  - converting an S3 client, SDK config, or pipeline to point at Backblaze B2
source_of_truth_for:
  - AWS S3 → B2 tooling conversion
  - S3-vs-B2 checksum / integrity differences
---

# Migrating from AWS S3 to Backblaze B2

This guide consolidates everything a team needs to repoint **existing AWS S3
tooling, SDKs, and code** at Backblaze B2 — the credential mapping, the
auth/endpoint changes, the object-key model shift, and the checksum gotchas that
trip up most migrations. It is for both the platform builder and the tenant who
already "speaks S3."

> **Scope.** This is about converting **tooling and access patterns**. It is
> *not* about copying existing data out of AWS into B2 — bulk data migration
> (bucket-to-bucket copy, rehydration, manifest reconciliation) is out of scope
> for the kit; see `docs/known-gaps.md` §9. Use `rclone`, `aws s3 sync`, or a
> per-engagement tool for the actual byte movement.

Backblaze exposes two relevant surfaces. Most AWS migrations target the
**S3-compatible API** (drop-in for S3 clients). The platform's own control/data
plane uses the **B2 Native API**. Both are valid against a tenant's customer
account — see `docs/adr/008-b2-native-vs-s3-compatible.md`.

## The five mental-model shifts

| AWS S3 assumption | Backblaze B2 reality |
|---|---|
| Global endpoint, region in the URL/SDK | One endpoint **per region**: `s3.<region>.backblazeb2.com`; an account lives in **one** region |
| IAM users/roles, access key + secret | The B2 **application key** *is* the S3 credential: `keyID` → access key, `applicationKey` → secret |
| SigV2 or SigV4 | **SigV4 only.** SigV2 is rejected |
| S3 auto-scales throughput per key prefix | **B2 does not repartition by prefix** — you distribute writes yourself (see §3) |
| `ETag == MD5`, IAM/KMS/tagging/ACLs available | ETag is *not* MD5 for multipart; **SSE-KMS, object tagging, IAM, object-ACLs, website config are unsupported** (§6). Lifecycle expiration & abort *are* supported but reshaped — current-version expiration needs a paired delete-marker rule; transitions/tag/size filters are rejected (§6b) |

## 1. Endpoint, region, and credentials

- **Endpoint:** `https://s3.<your-region>.backblazeb2.com`. Find the exact host
  on the bucket's details page; the platform records it on
  `storage_accounts.s3_endpoint`. Use that value — don't hand-build it.
- **Region label:** the middle segment of that host (read from your provisioned
  endpoint, not guessed). Use it verbatim as the SDK `region`. It is distinct
  from the Partner API region code.
- **Credentials:** the tenant's B2 application key pair maps directly —
  `applicationKeyId` is the AWS **access key id**, `applicationKey` is the AWS
  **secret access key**. No separate AWS-style credential is provisioned. The
  `applicationKey` is shown **once** at key creation.
- **Least privilege:** provision a tenant-scoped key with only the capabilities
  the workload needs (`listFiles, readFiles, writeFiles, shareFiles`; add
  `deleteFiles` only when required). **Never** configure the operator master key
  as an S3 credential (see §8 and `docs/security-and-tenant-isolation.md`).

## 2. Authentication: SigV4 only

Force SigV4 in every client. Backblaze does **not** support SigV2 *(verified: a
SigV2 request is rejected by B2 with `InvalidRequest`)*.

- boto3 / botocore: `Config(signature_version="s3v4")`
- AWS CLI: `aws configure set default.s3.signature_version s3v4`

Presigned URLs work normally under SigV4. Max presign TTL is 7 days (604800s),
the AWS SDK ceiling — see `docs/s3-compatible-api.md` §Presigned URLs.

## 3. Object keys: distribute writes yourself

This is the difference your team flagged, and it is the one most likely to cause
a silent performance regression.

- **AWS S3** automatically scales request throughput **per key prefix** and
  re-partitions hot prefixes behind the scenes. The old "randomize a prefix"
  advice exists *because* prefix is the partition unit.
- **B2** does **not** transparently re-partition by prefix. A constant or
  monotonically-increasing leading component (a timestamp, a sequential ID, a
  shared `objects/` root, or a per-tenant prefix) concentrates high-volume
  writes into one region of the lexicographical keyspace and creates a write
  **hot spot**.

**What to do:** put a stable, hash-derived `distribution_id` as the **first**
component of generated B2 file names, so writes spread across the keyspace:

```text
{distribution_id}/tenants/{tenant_id}/projects/{project_id}/objects/{object_id}/{safe_filename}
```

`distribution_id` is 2 hex chars by default (4 for extreme scale). The later
`objects/` segment is for readability only — it is **not** a folder, partition,
or authorization boundary. See `docs/adr/002-b2-file-name-distribution.md` and
the upload data plane (`docs/upload-data-plane.md`).

**Listing changes too.** Don't port `ListObjects(prefix=…)`-as-application-state
patterns: with distribution-first names, a tenant's objects are spread across
many leading prefixes. Query the **metadata DB** for logical browsing, not B2
prefix enumeration (`docs/common-pitfalls.md` §8 hot spots, §9 listing).

## 4. Checksums and integrity (the part most migrations miss)

AWS tooling routinely treats **`ETag` as the object's MD5** — an assumption that
breaks for multipart/encrypted objects on B2 *and* on AWS. The behavior below was
**verified live against Backblaze B2 `us-west-004` on 2026-06-06** (boto3/botocore
1.43).

**ETag**
- **Single-part, unencrypted `PutObject`:** ETag **is** the hex MD5 of the body.
  *(verified)*
- **Multipart:** ETag is `md5(concat(part_md5s))-<partCount>` (e.g. `…-2`) — **not**
  the whole-object MD5. *(verified — the formula matched exactly.)* With SSE-C it is
  not an MD5 at all. **Never** use ETag as a content hash across multipart objects.

**S3 additional checksums (`x-amz-checksum-*`) — supported on B2.** B2's S3
endpoint **accepts and returns CRC32, CRC32C, SHA1, and SHA256** *(all four
verified: accepted on `PutObject(ChecksumAlgorithm=…)`, returned on
`HeadObject(ChecksumMode='ENABLED')`)*. Practical consequences:

- Modern boto3 / AWS CLI default to attaching a **CRC32** checksum
  (`request_checksum_calculation = when_supported`). **This works against B2
  as-is** — B2 accepts and stores it; no `when_required` workaround is needed.
  *(verified: a default `PutObject` stored `ChecksumCRC32`.)*
- **CRC32C** needs the `botocore[crt]` extra installed **client-side** (to compute
  the digest locally) — a client dependency, not a B2 limitation.
- For explicit end-to-end integrity, pass `ChecksumAlgorithm='SHA256'` (or CRC32)
  on PUT and read it back with `ChecksumMode='ENABLED'`. **`Content-MD5`** on PUT
  is also accepted *(verified)* and is the most portable single-part option.

**B2 Native API** verifies integrity with **SHA-1** (`X-Bz-Content-Sha1` per file;
per-part SHA-1 plus an array at `b2_finish_large_file`). *(Verified: a correct
`X-Bz-Content-Sha1` is accepted; a wrong one is rejected `400 bad_request:
Checksum did not match data received`.)* The platform's own data
plane (PR 3) uses this — store the checksum in metadata, not by reading back the
ETag.

## 5. Multipart tuning

The thresholds match across surfaces (`docs/adr/004-multipart-upload-defaults.md`):

- Multipart at **≥100 MB**; min part **5 MB** (except final), max part **5 GB**,
  max **10,000** parts.
- AWS SDKs often default to an **8 MB** multipart chunk. For large sustained
  transfers, raise the client's multipart threshold/part size to reduce request
  count (boto3 `TransferConfig(multipart_chunksize=…, multipart_threshold=…)`;
  AWS CLI `s3.multipart_chunksize` / `s3.multipart_threshold`).
- Always **abort** incomplete multipart uploads on cancel/failure; the platform
  reaps orphans (PR 12). See `docs/small-file-and-throughput-guidance.md`.

Small files: the 1 MB-preferred / pack-and-range-read guidance is identical over
S3 — see `docs/small-file-and-throughput-guidance.md` §S3 small-file
considerations.

## 6. Unsupported S3 features — do not design around them

Backblaze's S3 implementation does **not** support: **SSE-KMS** (SSE-B2 and
SSE-C are supported), **object tagging**, **IAM roles/policies**, **object-level
ACLs** (bucket-level canned `private`/`public-read` only), **website
configuration**, and **bucket logging**. SigV2 is unsupported. If incoming
tooling depends on any of these, redesign that dependency before migrating.
(Lifecycle rules **are** supported — see §6b.) Full surface:
`docs/s3-compatible-api.md` §Explicitly NOT Supported.

*Verified live (2026-06-06):* a SigV2 request → `InvalidRequest`; object ACL →
`NotImplemented`; SSE-KMS → `InvalidArgument`; `PutBucketWebsite` →
`NotImplemented`. **Tagging is a silent trap:** `PutObjectTagging` returns **200
but discards the tags** (`GetObjectTagging` comes back empty), and `PutObject`
with a `Tagging` header is rejected `InvalidArgument` — so a migrating app gets no
error but loses its tags. Treat tagging as unavailable.

## 6b. Lifecycle rules — supported, but reshaped for B2

Lifecycle rules **are supported on B2** through the S3 API
(`PutBucketLifecycleConfiguration`), the B2 Native API (`lifecycleRules`), or the
web console. But a lifecycle config exported from AWS rarely applies to B2
unchanged. Behavior below was **verified live against B2 `us-west-004`
(2026-06-06)**.

**1. Current-version expiration must be paired with delete-marker cleanup.**
Because every B2 bucket is versioned, a bare `Expiration { Days: N }` rule is
**rejected**:

> `MalformedXML: …has an Expiration rule but there is no ExpiredObjectDeleteMarker
> rule with the exact same prefix`

You must add a second rule, **same prefix**, with
`Expiration { ExpiredObjectDeleteMarker: true }`. The requirement is mutual — an
`ExpiredObjectDeleteMarker` rule alone is likewise rejected. Verified-accepted
shape:

```json
{ "Rules": [
  { "ID": "expire",  "Filter": {"Prefix": "tmp/"}, "Status": "Enabled",
    "Expiration": {"Days": 30} },
  { "ID": "cleanup", "Filter": {"Prefix": "tmp/"}, "Status": "Enabled",
    "Expiration": {"ExpiredObjectDeleteMarker": true} }
]}
```

`NoncurrentVersionExpiration { NoncurrentDays: N }` and
`AbortIncompleteMultipartUpload { DaysAfterInitiation: N }` are each accepted on
their own. Prefix filters map to B2 file-name prefixes.

**2. Storage-class transitions don't apply.** B2 has a single storage class, so S3
`Transition` actions (Glacier/IA/Intelligent-Tiering) are rejected
(`MalformedXML: …unsupported elements …Rule.Transition`). Drop them.

**Also rejected (verified):** tag-based filters (`Tag`), object-size filters
(`ObjectSizeGreaterThan` / `ObjectSizeLessThan`), `And` filter combinations, and
disabled rules (`Status: Disabled`). Versioned buckets only — which is every B2
bucket.

See `docs/s3-compatible-api.md` for the operation list.

## 7. Tool conversion cheat-sheet

Every client needs the same three changes: **endpoint override**, **SigV4**, and
**B2 key as access key/secret**.

**boto3**
```python
import boto3
from botocore.config import Config

s3 = boto3.client(
    "s3",
    endpoint_url="https://s3.<your-region>.backblazeb2.com",  # from storage_accounts.s3_endpoint
    region_name="<your-region>",                              # the endpoint label, not guessed
    aws_access_key_id=APPLICATION_KEY_ID,      # B2 keyID
    aws_secret_access_key=APPLICATION_KEY,     # B2 applicationKey
    config=Config(signature_version="s3v4"),   # SigV4 is the only required override
)
# B2 supports the default CRC32 integrity checksum (§4) — no checksum config
# needed. CRC32C additionally requires `pip install botocore[crt]` client-side.
```

**AWS CLI**
```bash
aws configure set default.s3.signature_version s3v4
aws --endpoint-url https://s3.<your-region>.backblazeb2.com \
    s3 ls s3://my-bucket/
```

**rclone** — either the S3 backend (`provider = Other`,
`endpoint = s3.<your-region>.backblazeb2.com`, SigV4) or rclone's **native `b2`
backend** (uses keyID/applicationKey directly).

**MinIO `mc`**
```bash
mc alias set b2 https://s3.<your-region>.backblazeb2.com KEYID APPKEY --api S3v4
```

**Cyberduck / S3-aware analytics tools** — set the S3 endpoint host to the
region endpoint and the key pair as access key/secret; ensure SigV4.

Provisioning a tenant for S3 access is a standard flow — see
`docs/workflow-recipes.md` §"tenants whose tooling already speaks S3."

## 8. What NOT to do (migration edition)

- **Don't paste the operator master key** into a boto3 config or
  `~/.aws/credentials` to "quickly test." Backblaze's S3 API rejects it, so the
  test fails to authenticate; and regardless, a master-key leak compromises every
  customer account via the Partner/native API
  (`docs/common-pitfalls.md` §23, `CLAUDE.md` golden rules).
- **Don't trust ETag as MD5** for integrity (see §4).
- **Don't carry over timestamp/sequential/tenant-prefixed keys** — they create
  B2 write hot spots (§3).
- **Don't implement tenant listing via S3 prefix enumeration** — use metadata
  (§3).
- **Don't depend on SSE-KMS, tagging, IAM, ACLs, or website config** (§6).
- **Don't expect an AWS lifecycle config to apply unchanged** — a bare
  `Expiration{Days}` rule is rejected (needs a paired `ExpiredObjectDeleteMarker`
  rule), and storage-class transitions/tag/size filters aren't supported (§6b).

## Cross-references

- `docs/s3-compatible-api.md` — full S3 surface, auth, supported/unsupported ops
- `docs/adr/008-b2-native-vs-s3-compatible.md` — why both surfaces exist
- `docs/adr/002-b2-file-name-distribution.md` — the distribution-id key model
- `docs/small-file-and-throughput-guidance.md` — small files, multipart, packing
- `docs/common-pitfalls.md` — §8/§9 prefix hot spots & listing, §23 master key
- `docs/workflow-recipes.md` — provisioning an S3-speaking tenant
- `docs/known-gaps.md` §9 — bulk data migration is out of scope

## Validation checklist

- [ ] Client uses `s3.<region>.backblazeb2.com` and SigV4; SigV2 attempt is rejected.
- [ ] Tenant key (not the master key) is the S3 credential; capabilities are least-privilege.
- [ ] Generated keys are `distribution_id`-first; no timestamp/tenant prefix on high-volume writes.
- [ ] Integrity verification does not assume `ETag == MD5`; uses an `x-amz-checksum-*` algorithm (CRC32/CRC32C/SHA1/SHA256 — all supported by B2), `Content-MD5`, or B2-Native SHA-1.
- [ ] If using CRC32C, the client has `botocore[crt]` installed (B2 supports it; the digest is computed client-side).
- [ ] No code path depends on SSE-KMS, object tagging, IAM, object ACLs, or website config.
- [ ] Lifecycle: each current-version `Expiration{Days}` rule is paired with an `ExpiredObjectDeleteMarker` rule (same prefix); transitions, tag/size filters, `And`, and disabled rules removed.
- [ ] Multipart part size tuned above the 8 MB SDK default for large transfers; aborts on failure.
