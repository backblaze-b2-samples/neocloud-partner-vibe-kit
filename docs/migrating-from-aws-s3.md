---
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
| `ETag == MD5`, IAM/KMS/tagging/ACLs available | ETag is *not* MD5 for multipart; **SSE-KMS, object tagging, IAM, object-ACLs, website config, lifecycle are unsupported** (see §6) |

## 1. Endpoint, region, and credentials

- **Endpoint:** `https://s3.<region>.backblazeb2.com`, e.g.
  `https://s3.us-west-004.backblazeb2.com`. Find the exact host on the bucket's
  details page; the platform records it on `storage_accounts.s3_endpoint`.
- **Region label:** the middle segment, e.g. `us-west-004`. Use it verbatim as
  the SDK `region`. It is distinct from the Partner API region code.
- **Credentials:** the tenant's B2 application key pair maps directly —
  `applicationKeyId` is the AWS **access key id**, `applicationKey` is the AWS
  **secret access key**. No separate AWS-style credential is provisioned. The
  `applicationKey` is shown **once** at key creation.
- **Least privilege:** provision a tenant-scoped key with only the capabilities
  the workload needs (`listFiles, readFiles, writeFiles, shareFiles`; add
  `deleteFiles` only when required). **Never** configure the operator master key
  as an S3 credential (see §8 and `docs/security-and-tenant-isolation.md`).

## 2. Authentication: SigV4 only

Force SigV4 in every client. Backblaze does **not** support SigV2.

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

AWS tooling routinely treats **`ETag` as the object's MD5**. That assumption
breaks on B2 (and on AWS itself for multipart/encrypted objects):

- **ETag is MD5 only** for a single-part, unencrypted `PutObject`. For a
  **multipart** upload the ETag is `md5(concat(part_md5s))-<partCount>` — not the
  object's MD5. With SSE-C it is not an MD5 at all. **Do not** use ETag as a
  content hash for integrity verification across multipart objects.
- **B2 Native API** verifies object integrity with **SHA-1**
  (`X-Bz-Content-Sha1` per file; per-part SHA-1 plus an array at
  `b2_finish_large_file`). The platform's own data plane (PR 3) uses this — store
  the checksum in metadata, not by reading back the ETag.
- **S3-compatible PUT** integrity: send **`Content-MD5`** (base64 MD5) for
  single-part end-to-end verification. For multipart, validate **per part**, not
  via the final ETag.

**Modern AWS SDK gotcha (call this out in onboarding).** Recent AWS SDKs and the
AWS CLI enable **automatic data-integrity checksums** by default (CRC32 via
`x-amz-checksum-*` trailers, `request_checksum_calculation = when_supported`).
Against a non-AWS S3 endpoint this can surface as signature or
`x-amz-content-sha256` / checksum errors after an SDK upgrade. If you see those:

- boto3 / AWS CLI v2: set `request_checksum_calculation = when_required` and
  `response_checksum_validation = when_required` (in `~/.aws/config`, or env
  `AWS_REQUEST_CHECKSUM_CALCULATION=when_required` /
  `AWS_RESPONSE_CHECKSUM_VALIDATION=when_required`).

Confirm which `x-amz-checksum-*` algorithms Backblaze's S3 endpoint honors
against your region before relying on them; **`Content-MD5` + per-part
validation is the portable baseline.** (Postman/live-validation status is
tracked per `docs/adr/005-postman-is-reference-not-source-of-truth.md`.)

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
configuration**, **bucket logging**, and **lifecycle rules** via the S3 API.
SigV2 is unsupported. If incoming tooling depends on any of these, redesign that
dependency before migrating. Full surface: `docs/s3-compatible-api.md`
§Explicitly NOT Supported.

## 7. Tool conversion cheat-sheet

Every client needs the same three changes: **endpoint override**, **SigV4**, and
**B2 key as access key/secret**.

**boto3**
```python
import boto3
from botocore.config import Config

s3 = boto3.client(
    "s3",
    endpoint_url="https://s3.us-west-004.backblazeb2.com",
    region_name="us-west-004",
    aws_access_key_id=APPLICATION_KEY_ID,      # B2 keyID
    aws_secret_access_key=APPLICATION_KEY,     # B2 applicationKey
    config=Config(
        signature_version="s3v4",
        request_checksum_calculation="when_required",   # avoid CRC-trailer surprises
        response_checksum_validation="when_required",
    ),
)
```

**AWS CLI**
```bash
aws configure set default.s3.signature_version s3v4
export AWS_REQUEST_CHECKSUM_CALCULATION=when_required
aws --endpoint-url https://s3.us-west-004.backblazeb2.com \
    s3 ls s3://my-bucket/
```

**rclone** — either the S3 backend (`provider = Other`,
`endpoint = s3.us-west-004.backblazeb2.com`, SigV4) or rclone's **native `b2`
backend** (uses keyID/applicationKey directly; often simpler and avoids the S3
checksum-trailer issue entirely).

**MinIO `mc`**
```bash
mc alias set b2 https://s3.us-west-004.backblazeb2.com KEYID APPKEY --api S3v4
```

**Cyberduck / S3-aware analytics tools** — set the S3 endpoint host to the
region endpoint and the key pair as access key/secret; ensure SigV4.

Provisioning a tenant for S3 access is a standard flow — see
`docs/workflow-recipes.md` §"tenants whose tooling already speaks S3."

## 8. What NOT to do (migration edition)

- **Don't paste the operator master key** into a boto3 config or
  `~/.aws/credentials` to "quickly test." It is not restricted from S3 at the
  protocol level, so a leak compromises every customer account
  (`docs/common-pitfalls.md` §23, `CLAUDE.md` golden rules).
- **Don't trust ETag as MD5** for integrity (see §4).
- **Don't carry over timestamp/sequential/tenant-prefixed keys** — they create
  B2 write hot spots (§3).
- **Don't implement tenant listing via S3 prefix enumeration** — use metadata
  (§3).
- **Don't depend on SSE-KMS, tagging, IAM, ACLs, or lifecycle** (§6).

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
- [ ] Integrity verification does not assume `ETag == MD5`; uses `Content-MD5`/per-part or B2-Native SHA-1.
- [ ] SDK auto-checksum behavior is set to `when_required` (or validated against the endpoint).
- [ ] No code path depends on SSE-KMS, object tagging, IAM, object ACLs, website config, or lifecycle.
- [ ] Multipart part size tuned above the 8 MB SDK default for large transfers; aborts on failure.
