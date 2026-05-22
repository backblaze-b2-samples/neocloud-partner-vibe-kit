# First-Time Operator Setup

A step-by-step checklist for an organization standing up the neocloud platform for the first time. This is the operations-side companion to the developer-facing PR prompts in `prompts/`.

Read this doc end-to-end before starting. Several steps involve outside parties (Backblaze sales, IT for DNS, security for secrets storage) and have lead times that should be initiated in parallel.

**Audience:** Platform operator, ops lead, or solution engineer responsible for deploying the neocloud platform to production for their organization.

**Local development does not require any of this.** With `STORAGE_PROVIDER=mock`, the kit runs without Backblaze access. This doc applies when you are preparing for a real B2-backed deployment.

---

## Critical Path

These steps have external dependencies and should start as early as possible:

1. **Backblaze Partner API enablement** — lead time depends on Backblaze sales process.
2. **Backblaze Groups enablement** — lead time depends on Backblaze sales process.
3. **Secrets store provisioning** — depends on your security team's standard process.
4. **Domain setup for customer account alias** — depends on your IT/DNS team.

Start all four in parallel on day 1. Everything else can wait until these are in flight.

---

## Step 1 — Engage Backblaze

Contact your Backblaze account team. If you do not have an account team yet, request one through the Backblaze sales contact form. Tell them:

1. You are building a neocloud reseller platform on B2.
2. You need **Partner API enabled** on your operator account.
3. You need **Groups enabled** on your operator account.

Backblaze enables both via their internal process. Neither is self-service via dashboard or API. Confirm enablement in writing before proceeding.

**Output of this step:**
- Confirmation email that Partner API is enabled.
- Confirmation email that Groups are enabled.
- (Optional) Sandbox access for testing if Backblaze offers it.

**References:** `CLAUDE.md` §Golden rules, `docs/provisioning-and-partner-api.md` §Partner API and Group enablement, `docs/adr/007-partner-api-enablements-and-regional-accounts.md`.

---

## Step 2 — Choose and Reserve Your Identifiers

Lock in three identifiers before any provisioning code runs. Changing them later is painful.

| Identifier | What it is | Example | Where it appears |
|---|---|---|---|
| `platform_prefix` | Short slug used in bucket names | `nc` | `nc-{tenantId}-primary` |
| `partner_storage_domain` | Domain used in customer account alias emails | `storage.acme-neocloud.com` | `cust_abc-us-west@storage.acme-neocloud.com` |
| Operator account email | The B2 account that holds Partner API access | `partner-ops@acme-neocloud.com` | Backblaze account record |

**Rules for `platform_prefix`:** lowercase letters, digits, hyphens. Short (2–6 chars). Stable forever — bucket names are global and you cannot rename them.

**Rules for `partner_storage_domain`:** must be a domain you control. The MX record does not need to receive mail; the alias emails are identifiers, not inboxes. But the domain itself must be valid and yours.

**Output:** Three identifier values written down. Add them to the customer overlay template you'll use as your default (`customer-overlays/customer-profile.template.yaml`).

---

## Step 3 — Provision Your Operator B2 Account

If you do not yet have an operator B2 account, create one:

1. Sign up for B2 at https://www.backblaze.com/b2/ using the operator account email.
2. Use a strong, non-personal email (e.g., `partner-ops@acme-neocloud.com`) so the account does not depend on one person.
3. Enable two-factor authentication on the account immediately.
4. Pass the account email to your Backblaze account team so they can enable Partner API and Groups on it (Step 1).

**Do not use a personal B2 account for production.** The operator account is the root of trust for your entire neocloud platform.

---

## Step 4 — Set Up Your Secrets Store

The platform needs a secrets store for:
- The operator master B2 application key (used to authenticate Partner API calls)
- Per-tenant provider key values returned by `b2_create_key`
- Any platform-level secrets (database credentials, signing keys)

Choose one and provision it:
- HashiCorp Vault
- AWS Secrets Manager
- Google Secret Manager
- Azure Key Vault
- Other enterprise standard you already use

**Decide the path convention now:**

```
neocloud/operator/master_key
neocloud/tenants/{tenant_id}/provider_keys/{provider_key_id}
neocloud/platform/{secret_name}
```

Document the convention in `docs/configuration-reference.md` §16.

**Do not store provider key values in your application database.** Store only `provider_key_id` in `provider_keys`. The value goes to the secrets store, period.

---

## Step 5 — Create Your Operator Master Application Key

After Partner API is enabled (Step 1) and the operator account exists (Step 3):

1. Sign in to the operator B2 account in the Backblaze website.
2. Create a master application key with the capabilities needed for Partner API operations and platform-level B2 calls.
3. **Copy the `applicationKey` value immediately** — B2 returns it exactly once.
4. Store the value in your secrets store at `neocloud/operator/master_key`.
5. Note the `applicationKeyId` separately (this is safe to record).

**The master key is the highest-privilege credential in your platform.** Limit who has access to the secrets store path. Rotate the master key on a defined schedule (default: 90 days).

---

## Step 6 — Create Your Initial Group(s) in the Backblaze Website

Backblaze Groups can only be created in the Backblaze website. Plan your Group strategy before you create them.

**Group strategies:**

| Strategy | When to use |
|---|---|
| One Group total | Small deployments (< 1000 tenants), single-region, simple customer model |
| One Group per region | Multi-region deployments — keeps regional accounts organized |
| One Group per compliance tier | Regulated workloads where tenant cohorts have different retention/policy requirements |
| One Group per customer cohort | Reseller-of-resellers patterns where tenants are themselves segmented |

Each Group can hold up to 5,000 customer accounts. Don't over-engineer — start with one Group per region. You can add more Groups later.

**To create a Group:**
1. Sign in to the operator account.
2. Navigate to the Groups section (visible only after Backblaze enables Groups).
3. Create the Group(s) per your strategy. Note each Group's ID.
4. Record the Group IDs in your customer overlay under `groups:`.

---

## Step 7 — Set Up DNS for the Alias Domain

The customer account alias pattern is `{partner_customer_id}-{b2_partner_region}@{partner_storage_domain}`. Backblaze must be able to receive provisioning requests with these alias values.

**Requirements:**
- The domain in `partner_storage_domain` must resolve. An A record or CNAME for the apex domain is sufficient.
- The aliases themselves do not need to receive real mail. However, Backblaze may verify the domain is valid before accepting it as a `memberEmail` value.
- If Backblaze requires a verification record (TXT, SPF, MX), follow their instructions.

Confirm with your Backblaze account team whether they require any domain verification before they will accept your alias pattern.

---

## Step 8 — Provision the Platform Database

The neocloud platform needs a metadata database. Provision it per your organization's standard:

| Component | Choice |
|---|---|
| Engine | PostgreSQL recommended; the schema in `docs/data-model.md` is written for relational stores |
| Hosting | RDS, Cloud SQL, self-hosted, etc. |
| Connection | Set `DATABASE_URL` in the platform environment |
| Backups | Per your standard recovery objective |
| Encryption | At rest and in transit |

Run the migrations from PR 1 once the database is reachable. Verify with `GET /health/ready`.

---

## Step 9 — Local Development Setup (Confirm Before Production)

Before deploying to production, confirm the platform runs end-to-end against the mock provider locally:

1. Clone the implementation repo.
2. Set `STORAGE_PROVIDER=mock` and `NODE_ENV=development`.
3. Run migrations.
4. Seed demo data (`tnt_demo` tenant, `prj_demo` project).
5. Start the server.
6. Run the full test suite — it should pass without any Backblaze credentials.
7. Walk through the demo script (`docs/demo-script.md`) using the mock provider.

If any of these fail, fix the implementation before continuing. Production setup is not the time to discover implementation gaps.

---

## Step 10 — Production Environment Variables

Set these in the production environment (via your secrets manager or environment-variable system — never in source):

```
NODE_ENV=production
DATABASE_URL=<production database URL>
STORAGE_PROVIDER=b2
B2_APPLICATION_KEY_ID=<operator master key ID>
B2_APPLICATION_KEY=<from secrets store>
PARTNER_API_ENABLED=true
GROUPS_ENABLED=true
DEFAULT_GROUP_ID=<your initial Group ID from Step 6>
PARTNER_STORAGE_DOMAIN=<from Step 2>
SECRETS_STORE=<your secrets store identifier>
```

Plus all the upload defaults, usage import defaults, etc. from `docs/configuration-reference.md`. The reference doc is the source of truth for what each variable does.

---

## Step 11 — Provision Your First Real Tenant

After all the steps above are complete:

1. From the admin portal or API: `POST /admin/tenants` with a real tenant name and region.
2. Watch the logs as the provisioning flow runs.
3. Verify the resulting state in the database:
   - One `tenants` row with `status = 'active'`.
   - One `storage_accounts` row per region with `region`, `alias`, `provider_member_email`, `provider_customer_account_id` all populated.
   - One or more `buckets` rows tied to the storage account.
   - One or more `provider_keys` rows with `status = 'active'`.
   - `audit_events` rows for each provisioning step.
4. Verify in the Backblaze website:
   - The customer account appears in your Group with the alias email.
   - The buckets exist in the customer account.
   - The application key(s) exist in the customer account.

If any step fails, do **not** retry blindly. Follow `docs/operational-runbook.md` §6 for partial-failure recovery.

---

## Step 12 — Verification Checklist

Before you let real tenants use the platform, confirm every line:

- [ ] Partner API enablement confirmed in writing from Backblaze.
- [ ] Groups enablement confirmed in writing from Backblaze.
- [ ] Operator B2 account has 2FA enabled.
- [ ] Master key value is in the secrets store and not in any logs.
- [ ] At least one Group exists in the operator account and its ID is in the platform config.
- [ ] The alias domain resolves.
- [ ] Database migrations have run; `/health/ready` returns 200.
- [ ] Local mock-provider test suite passes.
- [ ] First test tenant provisioned successfully and verified end-to-end.
- [ ] Audit log shows entries for every provisioning step on the test tenant.
- [ ] All env vars from `docs/configuration-reference.md` are set or explicitly defaulted.
- [ ] Secrets store paths are documented.
- [ ] Backup and restore procedure for the metadata database is tested.
- [ ] Operational runbook (`docs/operational-runbook.md`) has been reviewed by the on-call team.
- [ ] Security review (`docs/security-review-checklist.md`) has been completed or formally scheduled.
- [ ] Monitoring is wired up: `/admin/metrics`, structured logs flowing to your aggregator, alerts configured.

---

## Operational Handoff

Once Step 12 is complete, hand off to operations:

1. **On-call team** reads `docs/operational-runbook.md` end-to-end.
2. **Security team** completes `docs/security-review-checklist.md`.
3. **Customer-facing team** reads `docs/demo-script.md` and is ready to demo the platform.
4. **Finance/billing team** reads `docs/usage-reporting-and-billing.md` and confirms the billing pipeline integrates with their system of record.

Set a 30-day post-launch review to revisit any gaps in this checklist.

---

## What This Document Does Not Cover

Per `docs/known-gaps.md`, the kit explicitly does not include:

- Payment processing or invoicing.
- Customer self-signup or contract management.
- Identity provider integration beyond dev tokens.
- A production observability stack (the platform emits signals; you wire them up).
- Migration from another storage provider to B2.

If any of these are required for your deployment, they are operator-side work and must be planned separately.

---

## Cross-References

- `docs/provisioning-and-partner-api.md` — full Partner API flow detail.
- `docs/configuration-reference.md` — every configurable setting with defaults.
- `docs/operational-runbook.md` — incident response after launch.
- `docs/security-review-checklist.md` — pre-launch security gate.
- `docs/known-gaps.md` — what the kit does not cover.
- `customer-overlays/README.md` — choosing or creating a customer overlay.
- `CLAUDE.md` §Golden rules — non-negotiable invariants.
