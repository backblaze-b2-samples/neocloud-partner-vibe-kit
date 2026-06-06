<!-- last_verified: 2026-06-06 -->
# Glossary

Terms used across the Neocloud / Partner Vibe Kit. When a term has both a Neocloud-specific meaning and a Backblaze-side meaning, both are listed.

For canonical entity definitions (columns, relationships), see `docs/data-model.md`. For the Partner API surface and composite operations, see `docs/provisioning-and-partner-api.md`.

---

## A

- **Adapter (thin Partner API adapter)** — A code layer that exposes only operations corresponding to documented Backblaze Partner API calls. Distinct from the Neocloud composite provider. See `BackblazePartnerApiClient` in `docs/provisioning-and-partner-api.md`.
- **Alias** — Partner-controlled email-shaped identifier for a provisioned Backblaze customer account. Stored on `storage_accounts.alias` and sent to Backblaze as `memberEmail`. Pattern: `<partner_customer_id>-<b2_partner_region>@<partner_storage_domain>`.
- **API key** — Platform service credential issued by the neocloud platform to a tenant. Distinct from a provider key. Stored as a hash in `api_keys.scopes`; never stored in plaintext.
- **Append-only** — Property of `audit_events`, `usage_events`, and `usage_import_rows` tables: rows are inserted but never updated or deleted. Enforced at the schema/permission layer.
- **Attribution (usage attribution)** — Mapping a row in a B2 usage CSV to a tenant. Order: provider customer account ID → storage account → bucket ID/name → internal metadata → unattributed row for review.
- **Audit event** — Row in the `audit_events` table recording a state-changing operation. Columns include `event_type`, `actor_id`, `resource_type`, `resource_id`, `occurred_at`, and `metadata`.
- **AWS SigV4** — AWS Signature Version 4 authentication. The only auth scheme Backblaze's S3-compatible API accepts. The tenant's B2 `applicationKeyId` becomes the access key; `applicationKey` becomes the secret. SigV2 is not supported.

## B

- **B2 file name** — A B2 object key. The path-shaped string that identifies an object within a bucket. Not a filesystem path. See also **physical B2 file name** and **logical path**.
- **B2 Native API** — The Backblaze-native HTTP API for B2 (distinct from the S3-compatible API). All provisioning and most data plane operations in the kit use the B2 Native API.
- **B2 Reserve trial** — A separate Backblaze workflow for short-term trial accounts, surfaced as `reserveTrialCreateAccount` on the thin adapter. Not the default managed-Group provisioning flow.
- **Backfill** — Inserting a database row to repair a missed record, typically a `storage_accounts` entry for an orphaned provider account discovered during reconciliation.
- **Billing ledger** — `billing_ledger` table holding per-period, per-tenant billing computations. Derived deterministically from `usage_import_rows`. Not a payment record.
- **Billing period** — `billing_periods` table row representing a closed accounting window (typically a calendar month). Has `draft` and `finalized` states.
- **Bucket** — B2 container for objects, created inside a customer account. In neocloud, buckets are child resources of a storage account, not the primary tenant isolation boundary.

## C

- **Composite operation** — A `NeocloudStorageProvider` method that combines one or more Backblaze API calls with local metadata writes, audit logging, and policy enforcement. Examples: `markTenantSuspendedLocal`, `ejectStorageAccountFromProviderGroup`.
- **Context pack** — A short summary document in `context-packs/` that provides just enough context for one phase of the implementation. Used to reduce token usage versus loading full reference docs.
- **Control plane** — The slice of the platform that manages tenants, storage accounts, Groups, buckets, keys, and configuration. Contrast with **data plane**.
- **Customer account** — A Backblaze account provisioned via the Partner API and added to a Backblaze Group. Maps 1:1 (per region) to a neocloud `storage_accounts` row.
- **Customer overlay** — YAML file in `customer-overlays/` describing per-deployment configuration choices (regions, bucket layout, retention policy, attribution priorities). Overlays may set configurable defaults but cannot override hard invariants.

## D

- **Data plane** — The slice of the platform that handles uploads, downloads, deletes, and presigned URL generation. Contrast with **control plane**.
- **distribution_id** — Hash-derived leading component of a physical B2 file name. Computed as the first 2 hex characters of `sha256(tenant_id : project_id : object_id)`. Distributes generated B2 file names across the lexicographical keyspace.

## E

- **Eject** — Partner API operation (`ejectGroupMember`) that removes a customer account from its Group. Non-reversible through the Partner API. Existing provider keys can continue to function unless explicitly revoked. Treat as deprovisioning, not suspension.
- **event_type** — Column in `audit_events` and `usage_events` identifying the kind of event. Examples for audit: `tenant_suspended`, `provider_key_rotated`, `storage_account_ejected`. Examples for usage: `upload`, `download`, `delete`.

## G

- **Generic-by-default** — Kit principle: do not assume a specific customer, industry, or workload unless a `customer-overlays/*.yaml` file is present. Without an overlay, prompts and docs describe the generic neocloud target.
- **Golden rule** — A non-negotiable invariant from `CLAUDE.md` §Golden Rules. Customer overlays cannot override these.
- **Group** — Backblaze Partner API construct that organizes customer accounts. Up to 5,000 accounts per Group. Created only in the Backblaze website (not via the Partner API), after Groups are enabled by Backblaze.

## H

- **Hard invariant** — An architectural rule from `docs/source-of-truth.md` §Hard invariants that customer overlays may not override without explicit review. Examples: account-driven isolation, metadata-based authorization, B2 file-name distribution.

## L

- **Logical path** — Tenant-facing object path used by API clients (e.g., `/projects/p_42/datasets/q4.parquet`). Stored in `objects.logical_path`. Distinct from the physical B2 file name and from the bucket name.

## M

- **Manifest (packed object manifest)** — `packed_object_manifests` row describing a B2 object that packs multiple logical records together. Combined with `packed_object_entries` byte offsets, it allows individual records to be retrieved by Range read.
- **`memberEmail`** — Backblaze Partner API field on `b2_create_group_member`. The neocloud alias maps directly to this field.
- **Metadata-based authorization** — Authorization decisions are made from trusted database metadata (e.g., `tenant_id`, `project_id`, ownership joins) and the authenticated session — never from bucket names, B2 file-name parsing, or client-supplied identifiers.
- **Mock provider** — In-memory implementation of `NeocloudStorageProvider` used in local development and tests. Selected when `STORAGE_PROVIDER=mock` or `NODE_ENV=test`. Does not call Backblaze.
- **Multipart upload** — B2 Large File API flow: `b2_start_large_file` → many `b2_upload_part` → `b2_finish_large_file`. Required for files ≥ 100 MB. State persisted in `upload_sessions` and `upload_parts`.

## N

- **Neocloud** — The platform pattern this kit describes: a multi-tenant storage product built on top of B2, with the operator acting as a Backblaze partner reseller of storage.
- **NeocloudStorageProvider** — Composite provider interface that combines Backblaze calls with local metadata, audit, and policy. See `docs/provisioning-and-partner-api.md`.

## O

- **Object** — Logical content item stored by a tenant. Represented in `objects` with metadata including `logical_path`, `physical_b2_file_name`, `size_bytes`, and ownership. Distinct from the underlying B2 file.
- **Operator** — The organization or team running the neocloud platform. The operator holds Backblaze partner credentials and provisions storage accounts on behalf of tenants.

## P

- **Partner API** — Backblaze API surface for provisioning customer accounts within Groups (`b2_create_group_member`, `b2_eject_group_member`, etc.). Must be enabled by Backblaze on the operator account; not self-service.
- **Path-style URL** — S3 URL form `https://s3.{region}.backblazeb2.com/{bucket}/{key}`. Supported by Backblaze. Contrast with virtual-hosted-style.
- **Physical B2 file name** — The actual B2 file name written to a bucket. Generated using the distribution-first layout: `objects/{distribution_id}/tenants/{tenant_id}/projects/{project_id}/{object_id}/{safe_filename}`. Stored in `objects.physical_b2_file_name`.
- **Presigned URL** — Time-limited download URL. Two flavors: B2 Native (produced via `b2_get_download_authorization`, used by the platform's `POST .../presign` endpoint) and S3-style (produced client-side via the AWS SDK's `generate_presigned_url` using the tenant's B2 key as the AWS credential).
- **Project** — Tenant-internal grouping of objects, with its own `quota_policy` and `storage_policy`. Not a B2 concept; an application-level metadata boundary.
- **Provider error** — HTTP error response from B2. Categorized in metrics by status code (401, 403, 429, 503, etc.) for alerting.
- **Provider key** — B2 application key created inside a provisioned customer account. Distinct from a platform API key. Stored in `provider_keys` with metadata (no key value).
- **Provider Group** — Synonym for Backblaze Group.

## Q

- **Quota policy** — JSON value on `projects.quota_policy` describing storage limits for a project. Operator-defined shape. Enforced at upload time.

## R

- **Range read** — HTTP `Range:` request to B2 returning a byte slice of an object. Used for partial reads of packed-object manifests.
- **Reactivate** — Local/composite operation that re-enables a suspended tenant. Issues new provider keys and sets `tenants.status = 'active'`. Distinct from un-ejecting; ejected accounts cannot be reactivated through the Partner API.
- **Region (Partner API region code)** — Backblaze partner-API value such as `us-east`, `us-west`, `ca-east`, `eu-central`. Stored in `storage_accounts.region`. Distinct from **S3 endpoint label**.
- **Reconciliation** — Job that compares `usage_events` totals (platform-mediated) against `usage_import_rows` totals (provider CSV). Informational only; never modifies data.

## S

- **S3-compatible API** — Backblaze's AWS S3-protocol-compatible endpoint, exposed at `https://s3.{region}.backblazeb2.com/`. Authenticated via AWS SigV4 using B2 application keys directly. See `docs/s3-compatible-api.md` for supported operations and limitations.
- **S3 endpoint (label)** — B2 S3-compatible host such as `s3.us-west-004.backblazeb2.com`. The full URL including the host. Stored in `storage_accounts.s3_endpoint`. Do not confuse with the Partner API region code.
- **S3 endpoint label (region)** — The middle component of an S3 endpoint URL (e.g., `us-west-004`, `us-east-005`, `eu-central-003`). Distinct from the Partner API region code (e.g., `us-west`).
- **Safe filename** — Sanitized version of the user-supplied filename, suitable for inclusion as the last component of a physical B2 file name. Stored in `objects.safe_filename`.
- **Service account** — Programmatic identity inside a tenant. Holds platform API keys, not provider keys.
- **SigV2** — Older AWS Signature Version 2. **Not supported** by Backblaze's S3-compatible API. Use SigV4 only.
- **Source of truth** — The canonical authority for a given topic. Defined in `docs/source-of-truth.md`. Postman and the original starter kit are not sources of truth.
- **SSE-B2** — Server-side encryption with Backblaze-managed keys. Set per-bucket or per-request. The default recommendation when encryption at rest is required without customer key management.
- **SSE-C** — Server-side encryption with customer-managed keys. The customer supplies the key per request via `x-amz-server-side-encryption-customer-*` headers. The `keyMd5` variable in the S3 Postman environment maps to the MD5 header.
- **SSE-KMS** — AWS KMS-managed server-side encryption. **Not supported** by Backblaze. Workloads requiring SSE-KMS must use SSE-B2 or SSE-C instead.
- **Storage account** — `storage_accounts` row. Represents one Backblaze customer account/sub-account in one region for one tenant. A tenant may have multiple storage accounts for multi-region needs.
- **Suspend (tenant suspension)** — Local/composite operation that disables tenant access and revokes tenant provider keys. Reversible via reactivate. Does not call Partner API eject.

## T

- **Tenant** — Application customer record (`tenants` row). The primary identity for billing, quota, and authorization purposes. Each tenant maps to one or more storage accounts.
- **Token (B2 authorization token)** — Short-lived (24-hour) token returned by `b2_authorize_account`. Used as the `Authorization` header for subsequent calls. Refreshed before expiry.
- **Token (platform API token)** — Bearer token presented by API clients to the neocloud platform. Validated against `api_keys`.

## U

- **Unattributed row** — A `usage_import_rows` row whose provider Account ID and Bucket Name do not match any known `storage_accounts` or `buckets`. Stored for operator review; does not block ingest.
- **Upload session** — `upload_sessions` row tracking an in-progress upload. Modes: `single` (regular) or `multipart`. Persisted state allows resume after interruption.
- **Usage event** — Row in `usage_events` recording a platform-mediated data plane action (`upload`, `download`, `delete`). Append-only.
- **Usage import** — Row in `usage_imports` recording the ingestion of one B2 usage CSV file. The corresponding rows land in `usage_import_rows`.

## V

- **Vibe Coding Starter Kit (original)** — The simple B2 upload/list/download starter referenced in `docs/reuse-from-original-vibe-kit.md`. Useful for developer-experience reference only. Not the source of truth for neocloud architecture.
- **Virtual-hosted-style URL** — S3 URL form `https://{bucket}.s3.{region}.backblazeb2.com/{key}`. Supported by Backblaze. The default for most modern AWS SDKs. Requires a DNS-compatible bucket name (the kit's bucket naming pattern is DNS-compatible by construction).
