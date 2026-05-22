---
status: context-pack
token_note: Short compressed context. Open full docs only when needed.
source_of_truth:
  - docs/provisioning-and-partner-api.md
  - docs/data-model.md
  - docs/adr/007-partner-api-enablements-and-regional-accounts.md
---

# Provisioning Context

## Purpose

Provider abstraction, Partner API, existing Backblaze Groups, and B2 customer account/sub-account lifecycle.

## Core rules

- Partner API must be enabled by the Backblaze sales/team process.
- Customers cannot self-enable Partner API.
- Partner API is required for provisioning and ejecting B2 customer accounts/sub-accounts.
- Groups must be enabled by Backblaze before Group-based provisioning workflows are used.
- Backblaze Groups cannot be created through the Partner API.
- After Groups are enabled, required Groups must be created in the Backblaze website.
- The application may list, select, link, cache, and store mappings to existing Groups, but it must not implement provider Group creation.
- Keep the thin Backblaze Partner API adapter limited to documented Backblaze operations: authorize, list Groups, list Group members, create Group member, eject Group member, and optional B2 Reserve trial account creation.
- Label suspend, reactivate, link mapping, key lifecycle, and customer-account policy steps as Neocloud local/composite operations unless a verified Backblaze endpoint backs them.
- A tenant/customer should map to one or more provisioned B2 customer accounts/sub-accounts.
- Provision each customer account/sub-account with a Partner API `region` and deterministic partner-controlled alias that is sent to Backblaze as `memberEmail`.
- Use Partner API region codes such as `us-east`, `us-west`, `ca-east`, and `eu-central`; do not pass S3 endpoint/cluster labels such as `us-west-004` as Partner API `region` values.
- A B2 customer account lives in a pre-defined region.
- Multi-region customers require multiple B2 customer accounts/sub-accounts, one per required region.
- Buckets and provider keys are child workflows inside the provisioned customer account/sub-account.
- Tenant isolation is account/sub-account-driven, not bucket-driven.
- Eject is a high-friction deprovisioning operation, not reversible suspension: ejection removes the account from the Group but does not delete it, existing application keys continue to function unless handled separately, and the account cannot be re-added to a Group using the Partner API.

## Customer account alias / `memberEmail` format

Use a deterministic partner-controlled alias when provisioning B2 customer accounts/sub-accounts. Send that alias as Backblaze Partner API `memberEmail`.

Recommended format:

`<partner_customer_id>-<b2_partner_region>@<partner_storage_domain>`

Example:

`cust_12345-us-west@storage.example-neocloud.com`

Where:

- `partner_customer_id` is the neocloud/partner’s stable internal customer identifier, not the B2 account ID.
- `b2_partner_region` is the target Partner API region code for the provisioned customer account/sub-account.
- `partner_storage_domain` is a partner-controlled domain used for storage account aliases/member emails.
- The alias/memberEmail should be unique, stable, deterministic, email-shaped, and safe to store in provisioning metadata.
- The alias/memberEmail must not already be an existing Backblaze account email.
- The alias/memberEmail should be stored with the tenant, storage account, provider customer account ID, existing Group ID, region, and returned S3 endpoint/cluster metadata.
- Do not use a personal user email address as the provisioned customer account alias/memberEmail.

For multi-region customers, create one alias/memberEmail per provisioned regional account.

```text
cust_12345-us-west@storage.example-neocloud.com
cust_12345-eu-central@storage.example-neocloud.com
```

## Tests

- Provider contract does not expose `createGroup`.
- Thin Partner API adapter exposes only documented Backblaze operations; provider-side suspend/reactivate/reassign are not modeled as raw Backblaze calls.
- Mock provider seeds existing Groups and supports selection/linking.
- Mock provider provisions customer accounts/sub-accounts with region and alias/memberEmail.
- Alias/memberEmail generation is deterministic, email-shaped, and unique per customer-region pair.
- Region/account mapping is stored in metadata.
- Existing Group assignment is recorded.
- Multi-region customers map to multiple storage accounts.
- Buckets and provider keys are created inside the correct provisioned customer account/sub-account.
- Provisioning and eject flows emit audit events.
- Eject requires explicit confirmation and warns that ejected accounts cannot be re-added to a Group through the Partner API.
- Suspend/reactivate flows are local/composite access-control workflows and do not call Partner API eject.
