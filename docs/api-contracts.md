---
last_verified: 2026-06-06
status: reference
source_of_truth_for:
  - target neocloud application APIs
---

# Neocloud API Contracts

This document describes target neocloud application APIs. It is separate from the B2 Native API, which Backblaze documents in its public Postman workspace.

> Entity references (`tenants`, `projects`, `storage_accounts`, `usage_events`, etc.) are defined in `docs/data-model.md`. Term definitions are in `docs/glossary.md`. For the precedence order when this doc conflicts with another, see `docs/source-of-truth.md`.

## API principles

- Auth is required except health/dev routes.
- Tenant/project context is resolved from auth context and trusted metadata.
- Headers are not trusted alone.
- Physical B2 file names are internal implementation details.
- APIs should be idempotent where appropriate.
- Errors should be structured and stable.
- Admin actions emit audit events.
- Usage-affecting operations emit usage events.

## Common headers

```text
Authorization: Bearer <token>
X-Request-Id: req_123
X-Tenant-Id: tnt_123
X-Project-Id: prj_456
```

Tenant/project headers must match auth context and metadata.

## Standard error shape

```json
{
  "error": {
    "code": "tenant_not_found",
    "message": "Tenant not found",
    "request_id": "req_123",
    "details": {}
  }
}
```

## Platform/admin APIs

- `POST /admin/tenants`
- `GET /admin/tenants`
- `GET /admin/tenants/:tenantId`
- `PATCH /admin/tenants/:tenantId`
- `POST /admin/tenants/:tenantId/suspend`
- `POST /admin/tenants/:tenantId/reactivate`
- `POST /admin/provider-groups/link`
- `GET /admin/provider-groups`
- `POST /admin/tenants/:tenantId/storage-accounts`
- `GET /admin/tenants/:tenantId/storage-accounts`
- `POST /admin/storage-accounts/:storageAccountId/eject-from-provider-group`
- `POST /admin/storage-accounts/:storageAccountId/buckets`
- `GET /admin/storage-accounts/:storageAccountId/buckets`
- `POST /admin/storage-accounts/:storageAccountId/provider-keys`
- `POST /admin/provider-keys/:providerKeyId/revoke`
- `GET /admin/audit/events`

`POST /admin/tenants` creates the application tenant record. `POST /admin/provider-groups/link` stores an application mapping to an existing Backblaze Group; it does not create a Backblaze Group. Backblaze Groups are created in the Backblaze website after Groups are enabled. Storage-account provisioning creates or links the provider customer account/sub-account. The storage account `alias` is sent to Backblaze as Partner API `memberEmail` by default. Bucket creation happens after storage-account provisioning. Tenant suspend/reactivate APIs are local Neocloud access-control workflows; they must not silently call Partner API eject.

### Storage account provisioning example

```json
{
  "region": "us-west",
  "alias": "cust_12345-us-west@storage.example-neocloud.com",
  "group_id": "grp_123",
  "display_name": "Acme US West Storage Account"
}
```

`group_id` must reference an existing Backblaze Group that was created in the Backblaze website and linked/discovered by neocloud. It is not created by the storage-account provisioning API. `alias` must be email-shaped because it maps to Backblaze `memberEmail`, and it must not already belong to a Backblaze account.


### Storage account ejection example

```json
{
  "confirm_eject": true,
  "acknowledge_not_readdable_via_partner_api": true,
  "key_policy": "revoke_tracked_provider_keys",
  "notes": "Customer offboarded by support ticket SUP-123"
}
```

`POST /admin/storage-accounts/:storageAccountId/eject-from-provider-group` is a high-risk deprovisioning workflow, not normal suspension. It must warn the operator that Partner API eject does not delete the Backblaze account, existing provider application keys can continue to function unless handled separately, and the ejected account cannot be re-added to a Group through the Partner API.

## Tenant/project upload APIs

- `POST /tenant/projects/:projectId/upload-sessions`
- `GET /tenant/projects/:projectId/upload-sessions/:sessionId`
- `PUT /tenant/projects/:projectId/upload-sessions/:sessionId/parts/:partNumber`
- `POST /tenant/projects/:projectId/upload-sessions/:sessionId/complete`
- `DELETE /tenant/projects/:projectId/upload-sessions/:sessionId`

Files smaller than 100 MB use normal upload. Files >= 100 MB use multipart. The server assigns the physical B2 file name using the shared file-name builder.

## Tenant/project object APIs

- `GET /tenant/projects/:projectId/objects`
- `GET /tenant/projects/:projectId/objects/:objectId`
- `POST /tenant/projects/:projectId/objects/:objectId/download-url`
- `DELETE /tenant/projects/:projectId/objects/:objectId`

## Usage and reporting APIs

- `GET /tenant/projects/:projectId/usage`
- `GET /admin/tenants/:tenantId/usage`
- `GET /admin/usage/events`
- `POST /admin/usage/imports/b2-csv`
- `POST /admin/reports/billing-periods`
- `GET /admin/reports/:reportId`
- `POST /admin/reports/:reportId/export`

## Optional packed-object APIs

These are optional workflow APIs for small-file-heavy customers:

- `POST /tenant/projects/:projectId/packed-objects`
- `GET /tenant/projects/:projectId/packed-objects/:packedObjectId/manifest`
- `POST /tenant/projects/:projectId/packed-objects/:packedObjectId/range-url`

## Relationship to Postman

Backblaze's public Postman workspace (<https://www.postman.com/backblaze/backblaze/overview>) is a B2 Native API reference artifact. This API contract doc is the source for target neocloud application APIs.
