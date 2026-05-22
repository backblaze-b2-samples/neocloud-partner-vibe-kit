# Implementation Roadmap

Use this canonical 12-PR roadmap. Do not combine unrelated PRs unless explicitly asked.

| PR | Title | Goal | Key acceptance criteria |
|---:|---|---|---|
| 1 | Foundation and data model | Add metadata DB and core entities. | Tenant maps to storage accounts; storage account includes region and alias/memberEmail; buckets are child resources; shared B2 file-name builder exists; deterministic B2 file-name tests pass. |
| 2 | Auth, RBAC, and API keys | Add dev auth, roles, service API keys. | Route-level permissions; cross-tenant denial; audit events; no CORS-as-auth. |
| 3 | Parallel and resilient uploads | Add bounded concurrency, multipart, retry. | <100 MB single upload; >=100 MB multipart; retry/backoff; abort cleanup; small-file policy is warning/configurable, not hard rejection. |
| 4 | Download and presigned URL flows | Add authorized download/range flows. | Metadata auth before signing; optional range URL support; audit/usage events. |
| 5 | Usage event ledger | Add durable append-only events. | Upload/download/delete/admin events recorded; no local counters. |
| 6 | B2 CSV ingestion and reconciliation | Import provider usage data. | Attribution by provider account/storage account first; unknown rows marked unattributed; idempotent imports. |
| 7 | Billing and reporting foundation | Generate reports/exports. | Deterministic tenant/project/billing-period reports; CSV/JSON exports. |
| 8 | Provider abstraction | Add mockable provider layer. | Existing Groups are listed/linked; thin Partner API adapter only exposes documented operations; alias maps to memberEmail; composite suspend/reactivate/eject semantics are explicit. |
| 9 | Tenant provisioning with Groups and customer accounts/sub-accounts | Implement provisioning flow. | Partner API and Group enablement prerequisites documented; existing Group selection/linking; account alias/memberEmail and region mapping; eject warning/confirmation; buckets/keys inside customer account. |
| 10 | Platform admin portal | Add operator workflows. | Tenants, storage accounts, usage, reports, audits, provisioning status. |
| 11 | Tenant portal | Add tenant workflows. | Projects, uploads, objects, API keys, usage, reports; logical paths only. |
| 12 | Operational hardening | Add production-readiness checks. | Metrics, alerts, runbooks, stuck multipart cleanup, provider error monitoring, reconciliation drift monitoring. |

## Reuse guidance

Use the original Vibe Coding Starter Kit for developer experience and implementation examples, not as architecture. See `docs/reuse-from-original-vibe-kit.md`.

## Prompt files

The `prompts/` directory contains one canonical prompt per PR. Do not use deprecated phase prompts.
