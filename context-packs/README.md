# Context Packs

Narrow, token-efficient summaries for each phase of the implementation. Read the relevant pack instead of loading the full reference docs.

A context pack contains:
- The core concept for the phase.
- Key tables, endpoints, or flows referenced in that phase.
- Defaults and thresholds the implementer needs to know.
- Test expectations summarized.
- A "files to read next" list for when the pack is not enough.

## Which pack to read

| For PR | Pack |
|---|---|
| PR 1 (foundation), PR 2 (auth) | `foundation.context.md` |
| PR 3 (uploads), PR 4 (downloads, presigned URLs) | `uploads.context.md` |
| PR 5 (usage events), PR 6 (CSV ingestion) | `usage-reporting.context.md` |
| PR 7 (billing) | `billing.context.md` |
| PR 8 (provider abstraction), PR 9 (tenant provisioning) | `provisioning.context.md` |
| PR 10 (admin portal), PR 11 (tenant portal) | `portal.context.md` |
| PR 12 (operational hardening) | `operations.context.md` |
| Any PR touching small-file workloads | `small-files.context.md` |

## When a pack is not enough

Each pack ends with a "files to read next" list. Open those files only when the pack does not answer the implementer's question. Loading the full reference docs by default wastes tokens.

## Maintaining packs

When a source-of-truth doc changes in a way that affects a pack (e.g., a default value changes, an endpoint is renamed), update the pack to match. The pack must never contradict its source-of-truth doc; if it would, fix the pack.
