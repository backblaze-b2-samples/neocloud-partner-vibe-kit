# Examples

Reference artifacts for B2 API behavior and the canonical B2 usage CSV format. Examples are illustrative — they are not the source of truth for the neocloud application API.

## Files

| File or directory | Purpose |
|---|---|
| `expected-pr-outputs.md` | Per-PR "what good looks like" — files, a golden output, and the acceptance signal for each of the 12 PRs |
| `api-payloads.md` | Manually curated B2 Native API request and response shapes with notes |
| `sample-usage-csv/README.md` | CSV column reference and ingestion test guide |
| `sample-usage-csv/sample-b2-usage.csv` | 30-day sample CSV across two tenants and one operator account |

## When to use these examples

- **`expected-pr-outputs.md`** — After running a PR prompt, compare the result against the per-PR golden output and acceptance signal. Use it as a review aid alongside `docs/quality-gates.md`.
- **`api-payloads.md`** — When implementing B2 API calls, refer to this file for the exact request/response shape. For the target neocloud platform API, use `docs/api-contracts.md` instead.
- **`sample-usage-csv/`** — When implementing CSV ingestion (PR 6), use the sample as a fixture for integration tests. Verify attribution by account ID and bucket name against the documented mapping.

## What examples are NOT

- Not the source of truth. If `api-payloads.md` conflicts with the current Backblaze API behavior, the Backblaze docs win.
- Not real customer data. The sample CSV uses fabricated account IDs and bucket names.
- Not a complete API surface. Only the requests/responses most relevant to neocloud workflows are included.

## Adding examples

When a new B2 API call becomes relevant to the kit (e.g., a new Partner API operation), add its request and response shape to `api-payloads.md` with a brief note explaining when to use it.

When the canonical B2 usage CSV format changes, update both `sample-usage-csv/sample-b2-usage.csv` and its `README.md`. Mark the date of the change in the README so implementers know which format their parser must support.
