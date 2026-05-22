# Customer Overlays

Per-deployment configuration files that override kit defaults. Overlays let one codebase serve multiple deployments with different region choices, bucket layouts, retention policies, attribution priorities, and workload characteristics.

## Files

| File | Purpose |
|---|---|
| `customer-profile.template.yaml` | Template with every configurable key, comments, and default values |
| `customer-profile.example-ai-training.yaml` | Worked example: AI training workload, multi-region, large files, soft quota, small-file packing enabled |
| `customer-profile.example-media-archive.yaml` | Worked example: long-term media archive, single-region, Object Lock + compliance retention, hard quota, no packing |
| `customer-profile.example-multi-workload.yaml` | Worked example: combined training + DR + inference. Multi-region, per-bucket policies (Object Lock on DR only, packing on training datasets only), mixed quota mode, application-layer DR replication |

## Compare the examples

The three examples are deliberately different so users can see how the same set of configurable keys responds to different workload characteristics:

| Dimension | AI Training | Media Archive | Multi-Workload (Training + DR + Inference) |
|---|---|---|---|
| Workload types | 3 | 3 | 5 |
| Regions | Multi (us-west + eu-central) | Single (us-east) | Multi (us-west + us-east — DR replica) |
| Quota mode | Soft | Hard | Per-project (soft for training/inference, hard for DR) |
| Object Lock | Not required | Required globally, compliance mode | Required on DR bucket only, governance mode |
| Small-file packing | Enabled | Disabled | Enabled, but bucket-scoped to training-datasets only |
| Upload concurrency | High | Lower (batch window) | Highest (sustained training ingest) |
| Default buckets per account | 2 | 3 (per retention class) | 4 in primary region, 2 in DR region (per workload class) |
| End-user file browser | No (programmatic) | Yes (archivist browsing) | No (programmatic — training jobs, inference servers) |
| Audit retention | 7 years (SOC2) | 10 years (broadcast regulation) | 7 years (SOC2) |
| Key rotation | 90 days | 180 days | 90 days |
| Cross-region replication | n/a (regions are independent) | n/a (single region) | Application-layer dual-write (kit does not automate this) |
| Caching tier | n/a | n/a | Required (operator-provided CDN or per-node cache) |

## When to use which as a starting point

- **AI training only** → start from `customer-profile.example-ai-training.yaml`.
- **Long-term archive or compliance backup** → start from `customer-profile.example-media-archive.yaml`.
- **Combined workloads (training + DR, training + inference, or all three)** → start from `customer-profile.example-multi-workload.yaml`. The combined example is the most complex; it shows per-bucket policies, mixed quota modes, and the explicit call-outs for what the kit does not solve automatically (cross-region replication, inference caching).

## Creating a new overlay

1. Copy `customer-profile.template.yaml` to `customer-profile.<customer-slug>.yaml`.
2. Fill in customer-specific values.
3. Read `docs/source-of-truth.md` §Hard invariants before changing anything labeled as a hard invariant — these must not be overridden without explicit review.
4. Read `docs/configuration-reference.md` for the canonical default for any value you are overriding.
5. Add a `notes:` block explaining non-default choices.

## What overlays can change

Overlays may set values in the **Configurable defaults** category of `docs/source-of-truth.md`:

- Portal workflow scope
- Report formats
- Quota policy mode and thresholds
- Bucket layout inside customer accounts
- Lifecycle and retention choices
- Upload concurrency and multipart thresholds (when justified)
- Billing export format
- Provisioning approval workflow
- Admin role names
- Customer account alias/memberEmail pattern
- Region/account mapping strategy
- Small-file packing strategy

## What overlays cannot change

Overlays may not override **Hard invariants** without explicit review (see `docs/source-of-truth.md` §Hard invariants):

- Account/sub-account-driven tenant isolation
- Backblaze Group creation is website-only (no Partner API `createGroup`)
- Alias maps to `memberEmail`
- Eject is non-reversible deprovisioning, not suspend/reactivate
- Partner API enablement is Backblaze-team-managed (not self-service)
- One customer account per region (multi-region = multiple accounts)
- Metadata-based authorization (no bucket-name parsing)
- B2 file-name distribution for high-scale generated names
- Durable usage events (no frontend counters for billing)
- No secrets in the repo
- Provider account first in usage attribution

## Secrets and overlays

Never put real credentials, real account IDs, or production secrets in an overlay file. Overlays describe configuration choices, not credentials. Use the secrets store referenced in `docs/configuration-reference.md` §16 for credentials.

## Validating an overlay

When implementing the platform, validate at startup that:

- All keys in the overlay are recognized.
- Hard-invariant keys, if present, match the canonical invariant.
- Required keys for the chosen workload (e.g., `regions_required` for multi-region) are populated.
- Unknown keys raise a warning, not a silent ignore.
