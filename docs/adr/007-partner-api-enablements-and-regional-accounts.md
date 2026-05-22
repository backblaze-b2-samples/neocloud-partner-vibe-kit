# ADR 007 — Partner API Enablement and Regional Customer Accounts

## Status
Accepted

## Decision
Partner API must be enabled by Backblaze sales/team process; customers cannot self-enable it. Groups must be enabled and created in the Backblaze website; the application uses existing Groups and must not create Backblaze Groups through an API. Use existing Groups and provision customer accounts/sub-accounts. Recommend aliases like `<partner_customer_id>-<b2_partner_region>@<partner_storage_domain>` and send the alias to Backblaze as `memberEmail`. A customer account lives in a pre-defined region, so multi-region customers require multiple accounts. Partner API eject is not normal suspension: it removes the account from the Group, does not delete it, existing application keys must be handled separately, and the account cannot be re-added to a Group through the Partner API.

## Consequences
Metadata must support one tenant to many storage accounts, alias/memberEmail traceability, eject status, and reporting across accounts.
