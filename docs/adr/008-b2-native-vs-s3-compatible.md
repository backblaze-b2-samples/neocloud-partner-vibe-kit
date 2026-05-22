# ADR 008 — Tenants May Use Either the B2 Native or S3-Compatible API

**Status:** Accepted

**Date:** 2026-05-21

---

## Context

Backblaze B2 exposes two distinct HTTP API surfaces against the same data:

1. **B2 Native API** — Backblaze's purpose-built API (`b2_authorize_account`, `b2_upload_file`, `b2_start_large_file`, etc.) plus the Partner API operations for customer account management.
2. **S3-Compatible API** — A subset of the AWS S3 protocol with AWS SigV4 authentication, exposed at `https://s3.{region}.backblazeb2.com/`.

The neocloud platform's control plane and platform-mediated data plane need to use the B2 Native API because Partner API operations (provisioning, ejection, Group membership) are only available there, and because the Large File API offers more direct visibility for resumable uploads.

A separate question is: what should tenants use to read and write their own data? Many tenants arrive with existing S3-aware tooling (boto3 scripts, AWS CLI, Rclone, Cyberduck, S3-compatible analytics pipelines). Requiring them to rewrite against the B2 Native SDK would be a significant friction.

---

## Decision

**Tenants may use either the B2 Native API or the S3-compatible API against their provisioned customer account. The platform documents both as supported, with the same B2 application key working as the credential for both.**

Specifics:

- Each tenant's `storage_accounts` row stores `s3_endpoint` (the S3 host) and `region` (the Partner API region code). Both are returned in provisioning responses.
- The tenant's provider key works as a B2 native key and as an AWS-style access key/secret for SigV4 — no separate credential is provisioned.
- The platform's documentation (`docs/s3-compatible-api.md`) is the canonical reference for what S3 operations are and are not supported.
- The platform's control plane continues to use the B2 Native + Partner APIs exclusively.

---

## Rationale

- **Tenant onboarding velocity.** S3 client libraries are ubiquitous. Forcing every tenant to use B2-specific SDKs would reject a large fraction of potential workloads with no architectural benefit.
- **No additional credential complexity.** Backblaze's S3 implementation accepts B2 application keys directly as AWS access key/secret. No separate provisioning is required; we already create the right credential during tenant setup.
- **Same isolation model.** S3 access against a tenant's customer account is constrained by the same key scope that constrains B2 Native access. The account-per-tenant isolation boundary applies to both APIs equally.
- **Same metering substrate.** B2's daily usage CSV records account-level usage regardless of which API surfaced the operation. The platform's `usage_imports` / `billing_ledger` pipeline already attributes by account first, so S3 usage is billed correctly without changes.
- **Operator preference.** Workloads that need Backblaze-specific features (Partner API, finer Large File control, B2 Reserve trial workflows) can still use the B2 Native API — both are supported simultaneously.

---

## Consequences

### Positive

- Wider tenant compatibility — any S3 client works.
- Easier migration for tenants moving from another S3 provider (AWS, Wasabi, Storj, etc.).
- No additional credential lifecycle complexity.
- Inference and read-heavy workloads benefit from existing S3-aware caching tooling (CDNs, S3-aware libraries).

### Negative

- The platform's own `usage_events` table is incomplete for tenants who use S3 heavily. Reconciliation jobs show a persistent delta. Operators must understand this is expected behavior, not a bug.
- The platform's `objects` metadata table may lag reality if tenants upload via S3 without notifying the platform. Optional reconciliation can be added that lists objects via S3 and inserts missing rows.
- Operations specific to the B2 Native API (Partner API, certain Large File controls) are not available via S3. The platform must steer tenants to the right interface for those.
- S3 has surfaces Backblaze does not implement (SSE-KMS, object tagging, IAM roles, SigV2). Tenants whose workloads depend on those will hit limitations. The platform must document the unsupported list (`docs/s3-compatible-api.md` §Explicitly NOT Supported).

---

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| **S3-only, hide the B2 Native API from tenants** | Loses Backblaze-specific features (Partner API workflows for tenant-of-tenants patterns, Large File progress, fine-grained capabilities). Forces tenants who already use B2 Native to migrate. |
| **B2 Native-only, no S3 access for tenants** | Rejects tenants with existing S3 tooling. High onboarding friction. Backblaze documents S3-compatible as a supported interface — refusing to expose it to tenants is leaving value on the table. |
| **Platform-proxied S3 (the platform exposes its own S3-compatible endpoint, forwards to B2)** | High implementation cost. Adds a hop with no clear benefit since B2 already provides S3 directly. Tenants who want a single-tenant view can get it through scoped provider keys. |
| **Issue separate "S3 access" credentials in addition to B2 keys** | Backblaze does not require this — B2 application keys work as S3 credentials directly. Adding a parallel credential type would duplicate lifecycle work for no functional gain. |

---

## Cross-References

- `docs/s3-compatible-api.md` — canonical reference for the S3 surface (supported operations, auth, endpoints).
- `docs/provisioning-and-partner-api.md` — how `s3_endpoint` is captured at customer account creation.
- `docs/data-model.md` — `storage_accounts.s3_endpoint`.
- `docs/known-gaps.md` — Backblaze S3 limitations.
- `docs/adr/001-account-subaccount-tenant-isolation.md` — the isolation model that applies to both APIs.
