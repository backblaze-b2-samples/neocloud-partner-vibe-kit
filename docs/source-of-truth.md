---
last_verified: 2026-06-09
status: reference
source_of_truth_for:
  - conflict resolution
  - hard invariants
  - configurable defaults
---

# Source of Truth

When docs conflict, use this order:

1. `CLAUDE.md` golden rules
2. `docs/source-of-truth.md`
3. `docs/api-contracts.md` for target neocloud application APIs
4. `docs/data-model.md` for entities
5. `docs/provisioning-and-partner-api.md` for Partner API and provider account guidance
5a. `docs/s3-compatible-api.md` for the S3-compatible API surface, supported operations, and tenant-facing usage
5b. `docs/adr/008-b2-native-vs-s3-compatible.md` for the decision rationale behind supporting both API surfaces
5c. `docs/migrating-from-aws-s3.md` for converting existing AWS S3 tooling/code to B2 (defers to `s3-compatible-api.md` for the surface and ADR 002 for keys)
6. `docs/upload-data-plane.md` for upload defaults
7. `docs/small-file-and-throughput-guidance.md` for high-throughput and small-file guidance
8. `docs/usage-reporting-and-billing.md` for usage attribution and billing
8a. `docs/cost-and-tco.md` for the cost model and partner margin (defers to the live Backblaze pricing page for rates)
9. `docs/security-and-tenant-isolation.md` for isolation enforcement
10. `docs/configuration-reference.md` for configurable settings (defers to upstream docs for the actual values)
11. `docs/operational-runbook.md` for incident response procedures
12. `docs/quality-gates.md` for PR review gates
13. `docs/common-pitfalls.md` for known mistakes to avoid
13a. `docs/first-time-operator-setup.md` for operator-side prerequisites and onboarding
13b. `docs/security-review-checklist.md` for pre-production security review
14. `docs/workflow-recipes.md` for step-by-step common tasks
15. `docs/glossary.md` for term definitions
16. `docs/known-gaps.md` for what is intentionally missing
17. task-specific docs not listed above
18. `docs/implementation-roadmap.md`
19. `docs/testing-matrix.md`
20. prompt files for execution
21. `docs/demo-script.md` for narrative/walkthrough only
22. Backblaze's public Postman workspace as reference only
23. original Vibe Coding Starter Kit as developer-experience reference only

Postman does not override the target architecture. The original starter kit does not override neocloud requirements.

## Hard invariants

Customer overlays may not override these without explicit review:

- Account/sub-account-driven tenant isolation.
- Groups organize customer accounts, but Backblaze Group creation is website-only after Groups are enabled.
- Neocloud customer account alias maps to Backblaze Partner API `memberEmail`.
- Partner API eject is a high-friction deprovisioning action, not normal suspend/reactivate; ejected accounts cannot be re-added to a Group through the Partner API and existing provider keys must be handled separately.
- Partner API enablement is handled through Backblaze sales/team process.
- Customers cannot self-enable Partner API.
- A customer account lives in a pre-defined region.
- Multi-region customers require multiple customer accounts/sub-accounts.
- Backblaze endpoints (api / download / S3) are discovered from the `b2_authorize_account` response (or the stored per-account `s3_endpoint`), never hard-coded or inferred from region codes.
- Metadata-based authorization.
- B2 file-name distribution for high-scale generated names.
- Durable usage events.
- No secrets in repo.
- No local/frontend counters for billing.
- Direct B2 listing is not the primary tenant dashboard source.
- Usage attribution starts with provider account/storage account.
- Tenants may use the B2 Native API or the S3-compatible API; both are valid against the tenant's customer account. SigV4 only; SSE-KMS, object tagging, IAM roles, and object-level ACLs are not supported by Backblaze's S3 implementation (only the bucket-level canned `private`/`public-read` ACLs exist).

## Configurable defaults

Customer overlays may configure:

- portal workflow
- report formats
- quota policy
- bucket layout inside customer accounts
- lifecycle and retention choices
- upload concurrency
- multipart thresholds when justified
- billing export format
- provisioning approval workflow
- admin roles
- customer account alias/memberEmail pattern
- region/account mapping strategy
- small-file packing strategy
