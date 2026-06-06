<!-- last_verified: 2026-06-06 -->
# Quickstart — 5-minute concept demo

**This is not the platform.** The Neocloud / Partner Vibe Kit is an
implementation *guide* (see `known-gaps.md` §1 — no application code by design).
This `quickstart/` is a tiny, runnable demo so you can watch the kit's core
**invariants** work against a real Backblaze B2 bucket *before* you build the real
foundation.

## What it shows

One command exercises four hard invariants from `docs/source-of-truth.md` against
your bucket:

| Step | Invariant | Why it matters |
|------|-----------|----------------|
| Upload | **distribution_id-first B2 file names** (ADR 002) | High-scale generated names spread across the keyspace — no write hot spots |
| Browse | **metadata-based listing** | The tenant view comes from a durable ledger, not B2 prefix enumeration |
| Download | **presigned URL** | Tenants talk to B2 directly; the platform never proxies object bytes |
| Usage | **durable usage events** | Billing aggregates from records, not frontend/local counters |

It also models the credential rule: a **scoped** key via SigV4 — never the
operator master key.

## Run it

```bash
cp .env.example .env          # then fill in a THROWAWAY bucket's B2 key
pip install -r quickstart/requirements.txt
python quickstart/quickstart.py
```

The B2 key needs read + write + delete. Everything the demo writes goes under a
unique `quickstart-demo/<run>/` prefix and is **deleted at the end**; the usage
ledger is a temp SQLite file, also removed. Nothing persists.

Expected output ends with a per-event usage summary and `cleaned up …`.

## What it is NOT

- Not multi-tenant provisioning (that's the Partner API — PRs 8–9).
- Not auth/RBAC, not real billing, not the durable Postgres schema.
- The ledger is SQLite-in-a-tempfile purely to stay dependency-free.

## Next step

Build the real foundation: open `START_HERE.md`, then run
`prompts/pr1-foundation.md`. The demo's patterns (distribution_id naming, durable
usage, metadata browsing, presigned download) are exactly what PRs 1–4 implement
properly.
