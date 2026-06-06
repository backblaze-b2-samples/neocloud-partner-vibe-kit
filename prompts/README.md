# PR Prompts

One canonical prompt per roadmap PR. Each prompt is self-contained: it states the goal, the scope, the non-goals, the required reading, the test expectations, and the acceptance criteria.

Use a prompt by copying its contents into a fresh Claude session along with the files it directs you to read.

After running a prompt, check the result against `examples/expected-pr-outputs.md` — the "what good looks like" reference (files, a golden output, and the acceptance signal) for each PR.

## PR sequence

Implement in order. Do not skip steps.

| PR | Prompt | Phase |
|---|---|---|
| 1 | `pr1-foundation.md` | Foundation — data model, demo mode, B2 file-name builder |
| 2 | `pr2-auth-rbac-api-keys.md` | Auth, RBAC, platform API keys, audit events |
| 3 | `pr3-parallel-resilient-uploads.md` | Multipart upload, retry, concurrency, abort |
| 4 | `pr4-download-presigned-urls.md` | Download, range requests, presigned URLs |
| 5 | `pr5-usage-event-ledger.md` | Usage event ledger, delete endpoint, usage summaries |
| 6 | `pr6-b2-csv-ingestion-reconciliation.md` | B2 usage CSV ingestion, attribution, reconciliation |
| 7 | `pr7-billing-reporting-foundation.md` | Billing calculation, draft/finalize, export |
| 8 | `pr8-provider-abstraction.md` | Provider interface, mock provider, B2 provider |
| 9 | `pr9-tenant-provisioning.md` | Tenant lifecycle via Partner API, multi-region |
| 10 | `pr10-platform-admin-portal.md` | Admin views: tenants, usage, audit, billing |
| 11 | `pr11-tenant-portal.md` | Tenant self-service: projects, keys, uploads, usage |
| 12 | `pr12-operational-hardening.md` | Health, metrics, jobs, structured logging |

## How a prompt is structured

Each prompt block contains:

1. **Required reading** at the top — `START_HERE.md`, the matching context pack, `CLAUDE.md` §Golden Rules, the source-of-truth doc(s) for the phase.
2. **Goal** — what this PR accomplishes.
3. **Changes to implement** — the scope, including specific tables, endpoints, or behaviors.
4. **What NOT to implement** — explicit non-goals to prevent scope creep into future PRs.
5. **Required tests** — minimum test coverage for this PR.
6. **Acceptance criteria** — checklist before the PR can be considered done.
7. **Post-implementation** — what to run (lint, type checks, tests) and how to summarize.

## Before starting a PR

Confirm the previous PR is complete (acceptance criteria all pass, tests pass, schema migrations applied). PRs build on each other. Skipping a phase or combining phases breaks the dependency chain.

## After a prompt is implemented

Update the PR description with the post-implementation summary the prompt asks for. If the implementation reveals that a source-of-truth doc needs to change, update the doc in the same PR. Drift between docs and code creates more bugs than the time saved by skipping doc updates.

## Token efficiency

Each prompt directs you to a context pack (`context-packs/*.context.md`) and explicitly does not require reading every reference doc. Trust the prompt — if it doesn't tell you to read a file, you probably don't need it.
