<!-- last_verified: 2026-06-06 -->
# Security and Tenant Isolation

## Principles

- Tenant isolation is account/sub-account-driven.
- Buckets are child resources inside customer accounts.
- Authorization uses trusted metadata and auth context.
- B2 file-name distribution is not an authorization mechanism.
- Admin actions are audited.
- Denied access is logged without leaking sensitive details.
- **Least privilege everywhere.** Every credential — platform API key, provider key, tenant-facing S3 access — is scoped to the minimum capabilities required for its workload.
- **The operator master application key is for the platform's control plane only.** It must never be used as a tenant credential, exposed to tenants, or configured into a tenant's S3 client. The isolation boundary is the same for B2 Native and S3-compatible APIs.

## Roles and permissions

Platform authorization is **role-based (RBAC)**. Every neocloud application API
request resolves to a principal whose `role` comes from its platform API key (see
`docs/data-model.md` `api_keys` / `service_accounts`). These roles gate the
neocloud *application* API and are distinct from B2 provider-key *capabilities*
(§Key scoping), which gate access to B2 itself.

### Permission matrix (normative)

| Role | object:read | object:write / object:delete | tenant:manage | admin | billing:read |
|------|:-:|:-:|:-:|:-:|:-:|
| `platform_admin` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `tenant_admin` | ✓ | ✓ | ✓ |  |  |
| `developer` | ✓ | ✓ |  |  |  |
| `viewer` | ✓ |  |  |  |  |
| `billing_viewer` |  |  |  |  | ✓ |
| `support_operator` | ✓ |  |  |  |  |

Permission meanings:
- `object:read` / `object:write` / `object:delete` — tenant data-plane object operations.
- `tenant:manage` — manage resources **within a tenant**: projects, buckets, tenant API keys, provider keys.
- `admin` — platform/operator routes: tenant provisioning, storage-account lifecycle, cross-tenant views.
- `billing:read` — read usage and billing reports.

### Tenant scoping

A non-`admin` permission is confined to the principal's own `tenant_id`. A
`developer` or `tenant_admin` for tenant A may never read or mutate tenant B's
resources — even with the right role, and even if they guess IDs. Only
`platform_admin` (the holder of `admin`) may act across tenants, and only on
`/admin/*` routes. Every cross-tenant attempt is denied and audited.

### Dev auth mode

In local/dev, a request authenticates with a platform API key whose id maps to an
`api_keys` row; the principal's `tenant_id`, optional `project_id`, and `role`
are read from that row. Production replaces the token **issuer** with the
operator's identity provider (operator-defined — see `docs/known-gaps.md`), but
the resolved principal shape (`tenant_id`, `project_id`, `role`) is unchanged.
Invalid or revoked keys fail closed with a logged `failed auth` / `access denied`
audit event.

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

### Operator master key

The operator master key has full Partner API access and account-level capabilities across every provisioned customer account. It must be treated as the highest-privilege credential in the platform:

- **Used by the platform's control plane only.** No tenant-facing code path may load or invoke the master key.
- **Never used as an S3 credential.** Backblaze's S3 API rejects the master key outright (enforced by B2, not just platform policy), so it cannot serve as an S3 credential. It must still never appear in any S3 client configuration given its full Partner API/account-level scope.
- **Stored in the secrets store only.** Never in source, config files, environment files committed to the repo, or anywhere a tenant could reach it.
- **Rotated on a defined schedule** (default: 90 days; see `docs/configuration-reference.md` §15).
- **Used only over HTTPS** against B2 endpoints. No direct API access from tenant-network code paths.

If you are tempted to use the master key for an ad-hoc operation, that operation belongs in the platform's control plane (under `provider.*` methods that wrap the master credential), not in a script.

### Tenant provider keys

Tenant provider keys are created inside the tenant's customer account with the minimum capability set for the workload. The default capability set is:

```
listFiles, readFiles, writeFiles, shareFiles
```

Add `deleteFiles` only if the workload requires tenant-initiated deletion. Never grant tenant keys: `listBuckets`, `listAllBucketNames`, `deleteBuckets`, `writeBuckets`, `readAccountInfo`, `bypassGovernance`.

The same provider key works for both B2 Native and S3-compatible API access — `applicationKeyId` becomes the AWS access key and `applicationKey` becomes the AWS secret. The capabilities granted constrain both surfaces identically.

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
