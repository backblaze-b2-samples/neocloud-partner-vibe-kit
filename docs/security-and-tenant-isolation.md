# Security and Tenant Isolation

## Principles

- Tenant isolation is account/sub-account-driven.
- Buckets are child resources inside customer accounts.
- Authorization uses trusted metadata and auth context.
- B2 file-name distribution is not an authorization mechanism.
- Admin actions are audited.
- Denied access is logged without leaking sensitive details.

## Roles

- `platform_admin`
- `tenant_admin`
- `developer`
- `viewer`
- `billing_viewer`
- `support_operator`

## Account-driven isolation

A tenant/customer maps to one or more provisioned B2 customer accounts/sub-accounts. The metadata database maps tenant IDs to storage accounts, provider customer account IDs, Group IDs, buckets, provider keys, objects, usage rows, and audit events.

Cross-tenant access must fail even if an attacker guesses bucket names, object IDs, physical B2 file names, provider IDs, or account IDs.

## B2 file names

Physical B2 file names may contain tenant and project IDs for traceability. They must not be parsed as the source of truth for authorization.

Default layout:

```text
{distribution_id}/tenants/{tenant_id}/projects/{project_id}/objects/{object_id}/{safe_filename}
```

## Key scoping

Create B2 application keys inside the tenant's provisioned B2 customer account/sub-account and, where appropriate, scope them to specific buckets or B2 file-name scopes required by the workload. Store provider key metadata; store secrets only in an approved secret store.

## Required audit events

- successful auth
- failed auth
- access denied
- tenant created/suspended/reactivated
- storage account provisioned/suspended/reactivated/ejected
- Partner API eject warning acknowledged
- Group assignment changed
- bucket created/deleted
- provider key created/revoked
- API key created/revoked
- upload completed/failed/aborted
- retention/lifecycle policy changed
- billing report finalized/exported

## Eject safety

Tenant suspension/reactivation is a local Neocloud access-control workflow. Partner API eject must require explicit operator confirmation, provider key handling, and audit logging because ejected Backblaze accounts cannot be re-added to a Group through the Partner API and existing provider application keys can continue to function unless revoked or rotated separately.
