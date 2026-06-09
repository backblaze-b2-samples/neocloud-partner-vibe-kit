<!-- last_verified: 2026-06-06 -->
# Common Pitfalls

Recurring mistakes when implementing or reviewing the neocloud platform. Each pitfall lists the wrong pattern, why it's wrong, and the right pattern. Use this doc as a PR review aid alongside `docs/quality-gates.md`.

For the canonical "do" rules, see `CLAUDE.md` §Golden Rules. This doc captures the "don't" side.

---

## 1. Treating the Bucket as the Isolation Boundary

**Wrong**
- Routing tenants to a shared B2 account with one bucket each.
- Authorizing requests by checking which bucket they target.
- Designing for "bucket-per-tenant" because that scales (it doesn't — B2 accounts have a default 100-bucket limit).

**Why wrong**
- B2 accounts default to a 100-bucket limit. The neocloud isolation model must scale past 100 tenants.
- A compromised key with `listAllBucketNames` capability could enumerate other tenants' buckets.
- Bucket-name attribution in usage CSV is ambiguous when buckets are renamed or reassigned.

**Right**
- One provisioned B2 customer account/sub-account per tenant per region, via the Partner API.
- Buckets are child resources inside each customer account.
- Authorization uses the database's `tenant_id` lookups, not bucket name parsing.

**References:** `CLAUDE.md` §Scoped Object Paths, `docs/adr/001-account-subaccount-tenant-isolation.md`.

---

## 2. Authorizing by B2 File Name or Bucket Name

**Wrong**
```
// Authorize by parsing the requested path
const tenantId = req.path.split('/')[2]; // "tnt_42"
if (tenantId === session.tenantId) { ... }
```

**Why wrong**
- Client-supplied identifiers can be forged.
- A guessed B2 file name or bucket name must not grant access.
- Authorization should not depend on file-name structure changing.

**Right**
- Resolve the resource from a database lookup keyed by an opaque ID (not a name) and check ownership via the join to `tenant_id` server-side, using only the authenticated session's `tenant_id`.
- Never trust path components, bucket names, query parameters, or request body fields for authorization decisions.

**References:** `CLAUDE.md` §Golden Rules ("Authorization uses trusted metadata"), `docs/security-and-tenant-isolation.md`.

---

## 3. Using `usage_events` as the Billing Source of Truth

**Wrong**
- Computing monthly bills directly from `usage_events`.
- Trusting in-memory counters or frontend tallies.

**Why wrong**
- `usage_events` records platform-mediated activity. Anything that happens outside the platform (direct B2 access, multipart abort accounting, B2-internal counters) is invisible to it.
- B2 usage CSVs are the provider's authoritative record. Bills based on `usage_events` will drift from B2's own counters.

**Right**
- `billing_ledger` is derived from `usage_import_rows` (provider CSV-attributed rows).
- `usage_events` are used for the **reconciliation** job that detects drift, not for billing math directly.

**References:** `docs/adr/003-provider-account-first-usage-attribution.md`, `docs/usage-reporting-and-billing.md`.

---

## 4. Attributing CSV Rows by Bucket Name First

**Wrong**
- Joining B2 usage CSV rows to `buckets.bucket_name` and falling back to Account ID only on miss.

**Why wrong**
- In the account-per-tenant model, the provider Account ID is a 1:1 identifier; bucket name is a secondary attribute that can collide or be reassigned.
- Bucket-name-first attribution silently mis-attributes usage if a bucket is renamed.

**Right**
- Match the row's `Account ID` to `storage_accounts.provider_customer_account_id` first.
- Fall back to bucket name only if Account ID does not resolve.
- Drop to `usage_import_rows` flagged unattributed if neither matches.

**References:** `docs/adr/003-provider-account-first-usage-attribution.md`.

---

## 5. Returning a Provider Key Value More Than Once

**Wrong**
- Logging the `applicationKey` value during creation for debugging.
- Returning `applicationKey` in `GET /provider-keys/:id`.
- Storing the `applicationKey` value in `provider_keys.metadata`.

**Why wrong**
- B2 returns the application key value exactly once. Anywhere it lands after that is a credential leak.
- Logs are searchable, copied, replicated, and retained. A key value in a log is a permanent leak.

**Right**
- Return the key value once in the response to the key-creation API call.
- Store it in a secrets store (Vault, AWS Secrets Manager, etc.) — never in the application database.
- Store only the `provider_key_id` in `provider_keys`.
- Redact `applicationKey` and `authorizationToken` in all logs.

**References:** `CLAUDE.md` §Golden Rules, `docs/quality-gates.md` Gate 4.

---

## 6. Building a Custom `createGroup` Operation

**Wrong**
- Adding `provider.createGroup(...)` to the storage provider interface.
- Mocking Group creation in the mock provider.
- Calling a hypothetical Backblaze Group-creation API.

**Why wrong**
- Backblaze Groups can only be created in the Backblaze website after Groups are enabled by Backblaze. There is no Partner API to create a Group.
- A mocked `createGroup` would train the application toward a non-existent capability.

**Right**
- The thin Partner API adapter exposes `listGroups`, `listGroupMembers`, `createGroupMember`, `ejectGroupMember`. No `createGroup`.
- The composite provider exposes `linkExistingGroup` (local metadata only — links to a Group created via the Backblaze website).

**References:** `docs/provisioning-and-partner-api.md` §Partner API and Group enablement.

---

## 7. Treating Eject as Reversible Suspension

**Wrong**
- Calling `ejectGroupMember` when a tenant fails to pay, expecting to be able to add them back later.
- Conflating "suspend" and "eject" in the same code path.

**Why wrong**
- Ejecting a Group member is non-reversible through the Partner API. Backblaze support may be able to help in some cases, but it is not a normal reversible operation.
- Existing application keys can continue to function after ejection unless explicitly revoked. Ejection alone does not disable access.

**Right**
- Use `markTenantSuspendedLocal` and `markTenantReactivatedLocal` for normal access control. These are application-level state changes; the Backblaze account remains in the Group.
- Reserve `ejectStorageAccountFromProviderGroup` for permanent deprovisioning, with explicit operator confirmation and a documented key disposition policy.

**References:** `docs/operational-runbook.md` §5–6, `docs/provisioning-and-partner-api.md` §Eject, suspend, and reactivate semantics.

---

## 8. Storing B2 File Names With Timestamp or Tenant-ID Prefixes

**Wrong**
```
uploads/2026-05-21T14:00:00Z/dataset.tar.gz
customer-acme/run-2026-05-21/file.bin
```

**Why wrong**
- Sequential or timestamp prefixes cluster all writes into the same leading lexicographical area. At neocloud scale, this creates hot spots that reduce write throughput.
- Tenant-ID prefixes leak tenant identity into the physical key.

**Right**
- Use the distribution-first layout: `objects/{distribution_id}/tenants/{tenant_id}/projects/{project_id}/{object_id}/{safe_filename}`.
- `distribution_id` is `sha256(tenant_id:project_id:object_id).slice(0, 2)` — 256 possible leading values.

**References:** `CLAUDE.md` §B2 File-Name Distribution, `docs/adr/002-b2-file-name-distribution.md`.

---

## 9. Listing Tenant Objects via B2 Prefix Enumeration

**Wrong**
- Implementing `GET /tenant/projects/:projectId/objects` by calling `b2_list_file_names` with a prefix.

**Why wrong**
- With distribution-first names, listing a tenant's objects requires querying 256 possible distribution prefixes.
- B2 list operations are rate-limited and slower than a database query.
- A tenant's objects are described in the `objects` table, which is the source of truth for ownership and metadata.

**Right**
- Query the `objects` table filtered by `tenant_id` (and `project_id` if scoping further).
- Reserve B2 listing for reconciliation jobs that confirm DB-vs-B2 consistency, not for user-facing API responses.

**References:** `CLAUDE.md` §Golden Rules ("Direct B2 listing is not the primary tenant dashboard source").

---

## 10. Using Single-Part Upload for Large Files (or Multipart for Small Files)

**Wrong**
- Uploading a 10 GB file via `b2_upload_file` (single-part).
- Uploading a 5 MB file via `b2_start_large_file` → `b2_upload_part` → `b2_finish_large_file`.

**Why wrong**
- Single-part uploads cannot resume. A network blip on a 10 GB upload starts over.
- Multipart has fixed overhead per part. For a 5 MB file, the overhead dominates.

**Right**
- File ≥ 100 MB: multipart.
- File < 100 MB: single-part.
- Threshold is configurable via `UPLOAD_MULTIPART_THRESHOLD_BYTES`.

**References:** `CLAUDE.md` §Upload Defaults, `docs/upload-data-plane.md`, `docs/adr/004-multipart-upload-defaults.md`.

---

## 11. Caching Upload URLs or Part URLs

**Wrong**
- Calling `b2_get_upload_url` once and reusing the URL for many uploads.
- Saving a part upload URL and retrying with it after a failure.

**Why wrong**
- B2 upload URLs and part upload URLs are single-use. They expire quickly.
- Retrying with a stale URL produces 503 or 401 errors that look like provider failures but are client misuse.

**Right**
- Request a new `b2_get_upload_url` (or `b2_get_upload_part_url`) per file (or per part).
- On any failure, discard the URL and request a new one before retrying.

**References:** `docs/upload-data-plane.md` §Backend Behavior.

---

## 12. Building Multi-Cloud Abstractions Through the Provider Interface

**Wrong**
- Renaming `provider.createBucket` to `provider.createContainer` so it might work with Azure later.
- Adding an `s3Compatible` flag to the provider interface.

**Why wrong**
- The storage provider abstraction exists for **mock vs B2** in this kit, not for cross-cloud portability.
- Multi-cloud abstractions force lowest-common-denominator semantics; B2-specific features (Groups, Partner API, file-name distribution rules) get lost.

**Right**
- The provider interface reflects B2 concepts. The mock implementation mimics B2 semantics. Both implementations satisfy the interface; neither pretends to be a different provider.
- If multi-cloud is ever needed, that is a separate, future architecture decision — not a constraint on this kit.

**References:** `docs/known-gaps.md` §8.

---

## 13. Persisting Counters Locally for Billing or Quota

**Wrong**
- Maintaining an in-memory `bytesUploadedThisMonth` counter for quota checks.
- Storing a per-tenant running total in `tenants.bytes_used` that is incremented in code.

**Why wrong**
- In-memory counters are lost on restart.
- Per-row running totals are race-prone and drift from the authoritative source.
- Frontend counters can be manipulated by clients.

**Right**
- Compute quota and billing dynamically from `usage_events` (real-time) and `usage_import_rows` (provider-authoritative).
- Cache totals only with a short TTL and a clear invalidation path.

**References:** `CLAUDE.md` §Golden Rules ("Usage reporting must be based on durable records, not frontend counters").

---

## 14. Skipping Audit Entries Because "It's Just an Internal Operation"

**Wrong**
- Suspending a tenant from a CLI script and skipping the `audit_events` write because "no one will look."
- Rotating a key in a background job without an audit entry.
- Adjusting a project quota without recording who changed it and why.

**Why wrong**
- Audit logs are how incidents get investigated. Missing entries leave gaps that are worse than no logging.
- Compliance and SOC2-style controls require provenance for state changes.
- Future you (or future ops) will not remember what was done in the moment.

**Right**
- Every state-changing operation writes an `audit_events` row, regardless of trigger (CLI, scheduled job, UI, API).
- `audit_events` is append-only by schema constraint.

**References:** `CLAUDE.md` §Golden Rules ("All admin actions must be auditable"), `docs/quality-gates.md` Gate 5.

---

## 15. Storing Secrets in the Repo or Config Files

**Wrong**
- Committing `.env` with real B2 credentials.
- Hardcoding an `applicationKey` in a test fixture.
- Saving a token to `config/production.json`.

**Why wrong**
- Git history is forever. A leaked credential remains in the repo even after a delete commit.
- Test fixtures get copied. Hardcoded credentials propagate.

**Right**
- Use environment variables sourced from a secrets store.
- For tests, use the mock provider — it does not require credentials.
- `.gitignore` `.env*` files. Document that real credentials go through the secrets store only.

**References:** `CLAUDE.md` §Golden Rules ("Never hardcode production credentials"), `docs/configuration-reference.md` §16.

---

## 16. Treating the Postman Collection as Authoritative

**Wrong**
- Copying request shapes from Postman into application code without verifying against current docs.
- Assuming every Postman request is implemented in the platform.
- Updating Postman to "match" the implementation, drifting it from the architecture.

**Why wrong**
- The Postman collection is candidate reference material. It may be stale.
- Implementation should follow `docs/api-contracts.md`, not Postman.

**Right**
- Use Postman for B2 API familiarization and manual testing.
- Verify any Postman request against `docs/api-contracts.md` (for neocloud API) or the Backblaze docs (for B2 API) before implementing from it.
- If Postman and docs disagree, the docs win.

**References:** `docs/adr/005-postman-is-reference-not-source-of-truth.md`.

---

## 17. Adding Future-Phase Code to an Earlier PR

**Wrong**
- During PR 3 (uploads), also writing the usage event emission code "since I'm here already" (that's PR 5).
- During PR 1 (foundation), stubbing out an auth middleware "to prepare for PR 2."

**Why wrong**
- Phase boundaries exist to keep PRs reviewable and reversible.
- Half-finished code from a future phase clutters the current PR and leaves a half-implemented feature.

**Right**
- Implement exactly one phase per PR. No stubs for future phases.
- If a current-phase change needs a hook for a future phase, add the minimal hook and document it in the PR description.

**References:** `CLAUDE.md` §Golden Rules ("Do not combine unrelated roadmap phases"), `docs/quality-gates.md` Gate 1.

---

## 18. Designing for High-IOPS Tiny-Object Workloads

**Wrong**
- Storing millions of 100-byte event records as individual B2 objects.
- Using B2 as a metadata store for an active application.
- Using B2 as a message queue or cache.

**Why wrong**
- B2 is high-throughput object storage. Per-request overhead is non-trivial for very small objects.
- Rate-limit errors (429) and request-rate pressure increase as object size shrinks and frequency rises.

**Right**
- For records < 100 KB at high volume: pack them into segment objects with a manifest, retrieve via Range reads.
- Use a real database (Postgres, DynamoDB, etc.) for fast small-record access patterns.
- B2 is for objects that are large enough to amortize the per-request overhead.

**References:** `docs/small-file-and-throughput-guidance.md`, `docs/adr/006-high-throughput-not-high-iops.md`.

---

## 19. Using SigV2 Against B2's S3-Compatible API

**Wrong**
- Configuring an S3 client to sign requests with AWS Signature Version 2.
- Using legacy S3 tools that default to SigV2 without checking.

**Why wrong**
- Backblaze's S3-compatible API accepts SigV4 only. SigV2 requests are rejected.

**Right**
- Force SigV4 in the client (`signatureVersion: 's3v4'` in boto3; AWS SDK default in current versions).
- Verify with a test request before deploying.

**References:** `docs/s3-compatible-api.md` §Authentication.

---

## 20. Expecting SSE-KMS, Object Tagging, or IAM Roles on B2's S3 API

**Wrong**
- Designing a workflow that depends on `PutObjectTagging` / `GetObjectTagging`.
- Configuring a bucket with SSE-KMS via `PutBucketEncryption`.
- Using `AssumeRole` / STS to issue scoped S3 credentials.
- Setting object-level ACLs.

**Why wrong**
- Backblaze documents these as not supported:
  - SSE-KMS — use SSE-B2 or SSE-C instead.
  - Object Tagging — returns empty.
  - IAM roles / STS — no analog; use B2 application keys directly.
  - Object-level ACLs — return 403; objects inherit bucket ACL.

**Right**
- For encryption: use SSE-B2 (Backblaze-managed) or SSE-C (customer-managed).
- For credential scoping: provision a B2 application key with the minimum capability set.
- For access metadata: store in your own database, not as object tags.

**References:** `docs/s3-compatible-api.md` §Explicitly NOT Supported, `docs/known-gaps.md` §12.

---

## 21. Confusing Partner API Region Code with S3 Endpoint Label

**Wrong**
- Storing `us-west-004` in `storage_accounts.region` and sending it to `b2_create_group_member`.
- Storing `us-west` in `storage_accounts.s3_endpoint` and using it as a URL host.

**Why wrong**
- Partner API regions and S3 endpoint labels are different values:
  - Partner API region (in `b2_create_group_member`): `us-east`, `us-west`, `ca-east`, `eu-central`.
  - S3 endpoint label (in the URL): `us-east-005`, `us-west-004`, `eu-central-003`.
- Passing one where the other is expected produces hard-to-debug errors (provisioning fails or S3 requests go to the wrong host).

**Right**
- Use the Partner API region code in `storage_accounts.region` (sent to `b2_create_group_member`).
- Use the S3 endpoint label (or full URL) in `storage_accounts.s3_endpoint` (used by S3 clients).
- Capture both at provisioning time from the Partner API response; do not infer one from the other.

**References:** `docs/s3-compatible-api.md` §Region Values, `docs/provisioning-and-partner-api.md` §Regional customer accounts.

---

## 22. Computing Billing from `usage_events` When Tenants Use the S3 API Directly

**Wrong**
- Adding up `usage_events` rows for the period and calling that the tenant's bill.
- Assuming `usage_events` is complete for any tenant.

**Why wrong**
- `usage_events` records platform-mediated operations only. When a tenant uses the S3-compatible API directly against B2, those operations never touch the platform and never write `usage_events`.
- Bill the tenant from `usage_events` and you under-bill S3-heavy tenants.

**Right**
- Bill from `usage_import_rows` / `billing_ledger`, which derive from B2's daily CSV. The CSV covers every operation regardless of which API surfaced it.
- Use `usage_events` for reconciliation (detect drift) and for real-time tenant dashboards (best-effort live view), not for invoicing.

**References:** `docs/usage-reporting-and-billing.md`, `docs/s3-compatible-api.md` §Operational Considerations for S3 Tenants, `docs/adr/003-provider-account-first-usage-attribution.md`.

---

## 23. Using the Operator Master Key as an S3 Credential

**Wrong**
- Pasting the operator's master `applicationKeyId` / `applicationKey` into a boto3 config or `.aws/credentials` to "quickly test" an S3 workflow — which fails to authenticate anyway, but not before the key lands in shell history and local config.
- Letting an internal tool use the master key for S3 access because it's already loaded in the environment.
- Handing the master key to a tenant for "convenience" instead of provisioning a scoped tenant key.

**Why wrong**
- Backblaze's S3 API rejects the master key — it won't authenticate, so the "quick test" above fails outright (S3 requires a non-master application key). The deeper problem is scope: the master key has full account-level capabilities across every provisioned customer account, so a leak on S3 (config files, environment, CI logs) — even from a failed test that left the key on disk — exposes the entire platform.
- The master key is the only credential with Partner API access. Compromise of the master key means a third party can provision, eject, or modify any customer account.
- Even one-off testing leaves the key in shell history, system clipboards, or local config files.

**Right**
- The master key is loaded only by the platform's control plane, behind the `NeocloudStorageProvider` abstraction. No tenant code path and no ad-hoc script loads it.
- For operator-side S3 testing, provision a separate operator-scoped key (with the minimum capabilities needed for the test) and use that.
- For tenant workloads, provision a tenant-scoped provider key with the minimum capability set (`listFiles, readFiles, writeFiles, shareFiles`, plus `deleteFiles` only if needed).

**References:** `docs/security-and-tenant-isolation.md` §Operator master key, `docs/s3-compatible-api.md` §Never Use the Operator Master Key as an S3 Credential, `CLAUDE.md` §Golden rules.

---

## 24. Hard-Coding or Inferring Backblaze Endpoints

**Wrong**
- Putting a literal `apiNNN.backblazeb2.com`, `fNNN.backblazeb2.com`, or hand-built `s3.<region>.backblazeb2.com` host into client config or code.
- Deriving the region (and a URL from it) by parsing a bucket name, account ID, or application key.
- Caching a discovered URL once and reusing it forever, ignoring token expiry.

**Why wrong**
- Pod/region assignment is opaque and can change; a hand-built host can point at the wrong cluster.
- A region inferred from a name or key may not match the account's actual endpoints, so requests silently go to the wrong host.
- B2 authorization tokens expire (≈24h); a reused URL with a stale token starts failing mid-workload.

**Right**
- Platform/control-plane code authorizes once at the fixed endpoint `https://api.backblazeb2.com/b2api/v4/b2_authorize_account`, then reads `apiInfo.storageApi.{apiUrl, downloadUrl, s3ApiUrl}` and `authorizationToken` from the response. Re-authorize on token expiry or a `401`/authorization-invalid response.
- Tenant S3 tooling uses the provisioned `storage_accounts.s3_endpoint` value (captured at provisioning), never a hand-built host.
- Never infer region from bucket names, account IDs, application keys, or previously seen URLs — the authorize response is the source of truth.

**References:** `CLAUDE.md` §Golden rules, `docs/s3-compatible-api.md` §Endpoint discovery, `docs/provisioning-and-partner-api.md` §Regional customer accounts.

---

## Using This Doc in PR Review

When reviewing a PR, scan this list. If the PR pattern matches any **Wrong** example, request changes before approving. The **References** column tells you where the canonical guidance lives so you can quote it in the review comment.

When new pitfalls emerge (e.g., from a production incident or a code review finding), add them here so the next implementer doesn't repeat the mistake.
