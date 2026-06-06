---
last_verified: 2026-06-06
status: reference
load_when:
  - building the business case for a B2-backed offering
  - designing pricing, chargeback, or margin into the platform
source_of_truth_for:
  - partner cost model and TCO methodology
  - how kit design decisions affect B2 cost
---

# Cost & TCO for a B2-Backed Partner Platform

Partners adopt this kit to **resell or embed storage at a margin**. That only
works if you understand what Backblaze charges *you* and can attribute it to the
customers *you* charge. This doc gives the cost model, maps the kit's design
decisions to cost, and shows where the billing layer (PRs 5–7) closes the loop.

> **Pricing figures below were captured 2026-06-06.** They move — treat the
> live page as authoritative: <https://www.backblaze.com/cloud-storage/pricing>
> and <https://www.backblaze.com/cloud-storage/transaction-pricing>. The cost
> *model* and *levers* in this doc don't go stale; the dollar figures might.

## The partner economics, in one line

```
partner margin  =  (what you charge tenants)  −  (what Backblaze charges you)
                                                  └── storage + egress + transactions
```

Your job as the platform is to (a) keep the right-hand side low by design and
(b) **attribute it per tenant** so you can bill the left-hand side accurately.
The kit's account/sub-account isolation and provider-account-first usage
attribution exist precisely so B2's per-account usage maps cleanly to a tenant.

## The three B2 cost dimensions

| Dimension | Rate (as of 2026-06-06) | Notes |
|-----------|-------------------------|-------|
| **Storage** | **$0.005 / GB-month** (~$6 / TB-month) | Billed on byte-hours, so deleting/expiring data lowers it immediately |
| **Egress** | **Free up to 3× average monthly storage**, then **$0.01 / GB** | **Free, unlimited** egress to/through partner CDNs/compute (Fastly, Cloudflare, bunny.net, CacheFly, CoreWeave, Equinix Metal, Vultr, phoenixNAP) |
| **Transactions** | **Class A: free.** Class B: 2,500/day free, then $0.004/10,000. Class C: 2,500/day free, then $0.004/1,000 | Per-object operations — this is where **small-file workloads quietly cost money** |

High-volume options (via sales): **B2 Overdrive** (high-throughput) at $15/TB-month
with unlimited free egress; **B2 Reserve** capacity bundles (20 TB+, 1–3 yr,
all-inclusive) — relevant for committed partners and resale.

For context, this storage rate is roughly **1/5 of AWS S3 Standard**, and S3
charges ~$0.09/GB egress where B2's is free-to-3×-then-$0.01 — which is the core
of the migration value proposition (see `docs/migrating-from-aws-s3.md`).

## How the kit's design decisions map to cost

This is the part that's specific to *this* platform. Several kit invariants are
cost levers, not just correctness rules:

| Kit decision | Cost dimension | Effect |
|--------------|----------------|--------|
| **Small-file packing** (ADR 006, `small-file-and-throughput-guidance.md`) | Transactions | Packing many small files into larger segment objects collapses Class B/C transaction counts — the single biggest avoidable cost for small-object workloads |
| **Lifecycle expiration** (`migrating-from-aws-s3.md` §6b) | Storage | Expiring/deleting stale versions drops byte-hours immediately; pair `Expiration{Days}` with the delete-marker rule B2 requires |
| **Presigned download + CDN** | Egress | Route tenant downloads through a partner CDN (Cloudflare/Fastly/bunny.net/…) for **$0 egress** — decisive for serving/inference workloads |
| **Provider-account-first usage attribution** (ADR 003) | All | Maps B2's per-account usage CSV to a tenant, so each tenant's storage/egress/transactions can be costed and charged |
| **distribution_id naming** (ADR 002) | — | No cost impact (naming is free), but it's what lets high-write workloads scale without throttling |
| **B2 as high-throughput, not high-IOPS** (ADR 006) | Transactions | Designing for fewer, larger operations keeps you out of per-transaction cost and request-rate ceilings |

## Worked example (plug in your own numbers)

A partner tenant with **50 TB stored**, **30 TB egress/month**, **40M Class B +
5M Class C** transactions/month:

```
storage      50,000 GB × $0.005                         = $250.00
egress       free up to 3×50TB = 150TB; 30TB < 150TB     =   $0.00   (or $0 via CDN)
class B      ~40M − (2,500/day×30) free ≈ 40M billable
             40,000,000 / 10,000 × $0.004                = $16.00
class C      ~5M billable / 1,000 × $0.004               = $20.00
                                                          --------
B2 cost to the partner for this tenant                   ≈ $286 / month
```

If the partner charges this tenant, say, **$10/TB-month for 50 TB = $500**, the
gross margin is **~$214/tenant/month (~43%)** before the partner's own compute,
support, and platform costs. Note how **transactions, not storage, are the swing
factor** here — which is exactly why the packing guidance matters. (Numbers
illustrative; recompute against current rates.)

## Closing the loop: from cost to invoice

1. **PR 5 — usage event ledger:** durable records of upload/download/delete (not
   frontend counters) — the basis for any defensible bill.
2. **PR 6 — B2 CSV ingestion & reconciliation:** import Backblaze's per-account
   usage CSV and reconcile it against your ledger; provider-account-first
   attribution (ADR 003) assigns each row to a tenant.
3. **PR 7 — billing/reporting:** turn attributed usage into per-tenant,
   per-period reports and exports. Apply your markup/margin here.

Pricing policy, markup, and margin targets are **operator-defined** — a natural
fit for a `customer-overlays/` value (e.g., a `pricing` block) rather than a
hardcoded default.

## See also

- `docs/usage-reporting-and-billing.md` — attribution + CSV ingestion details
- `docs/small-file-and-throughput-guidance.md` — the packing patterns that cut transaction cost
- `docs/migrating-from-aws-s3.md` — egress/storage cost contrast vs S3
- `docs/adr/003-provider-account-first-usage-attribution.md` — why attribution starts at the provider account
