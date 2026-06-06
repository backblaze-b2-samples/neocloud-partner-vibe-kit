<!-- last_verified: 2026-06-06 -->
# Provisioning and Partner API

> Term definitions (Partner API, Group, alias/memberEmail, eject, storage account, etc.) are in `docs/glossary.md`. The operator-side prerequisite steps (getting Partner API enabled by Backblaze, creating Groups in the website) are in `docs/first-time-operator-setup.md`.

## Goals

- Provision tenant storage.
- Select and use existing Backblaze Groups.
- Create/manage B2 customer accounts/sub-accounts through the documented Partner API flows.
- Create/manage buckets and provider keys inside customer accounts.
- Support local mock provider without real Partner API credentials.
- Keep Partner API integration behind an interface.

## Partner API and Group enablement

Partner API must be enabled by the Backblaze sales/team process. Customers cannot self-enable Partner API on their own. Partner API is required for provisioning and ejecting customer accounts.

Backblaze Groups must also be enabled. Backblaze Groups cannot be created through the Partner API. After Groups have been enabled, required Groups must be created in the Backblaze website. Neocloud may list, select, link, cache, and store mappings to existing Groups, but it must not expose or mock a real Backblaze `createGroup` operation.

## Regional customer accounts

A B2 customer account lives in a pre-defined Partner API region. If a customer needs multiple regions, create multiple B2 customer accounts/sub-accounts for that customer, one per required region. Store the mapping in `storage_accounts`.

Partner API region inputs should use Partner API region codes such as `us-east`, `us-west`, `ca-east`, and `eu-central`. Do not pass S3 endpoint/cluster labels such as `us-west-004` as Partner API `region` values. Store S3 endpoint or cluster metadata separately when needed.

The Partner API response for a successful customer account creation includes the S3 endpoint host for that account (e.g., `s3.us-west-004.backblazeb2.com`). Capture this in `storage_accounts.s3_endpoint` at provisioning time — it cannot be inferred reliably from the region code alone, and it is what tenants need to configure S3 clients. See `docs/s3-compatible-api.md` §Region Values.

## Customer account alias and `memberEmail`

The Neocloud customer account alias maps to the Backblaze Partner API `memberEmail` field used by `b2_create_group_member`. Treat the alias as the provider member email unless a customer overlay explicitly names a different internal field.

Recommended `memberEmail` / alias pattern:

```text
<partner_customer_id>-<b2_partner_region>@<partner_storage_domain>
```

Example:

```text
cust_12345-us-west@storage.example-neocloud.com
```

Rules:

- The value must be syntactically valid as an email address.
- The value must not already be an existing Backblaze account email.
- The value can be a partner-controlled non-human/fake email when the workflow allows it.
- If the managed Group uses SSO, validate whether the email must belong to the SSO domain before provisioning.
- Store the generated alias/member email with the tenant, storage account, provider customer account ID, existing Group ID, region, and returned S3 endpoint metadata.

Validate current region identifiers and Group/SSO restrictions with Backblaze before production provisioning.

## Recommended provisioning flow

1. Confirm Partner API is enabled by Backblaze.
2. Confirm Groups are enabled by Backblaze.
3. Create the required Group in the Backblaze website. This is an external prerequisite, not an application or Partner API operation.
4. Link/select the existing Group in Neocloud and store the provider Group mapping.
5. Generate a deterministic partner-controlled alias and send it as Backblaze `memberEmail`.
6. Call the documented Partner API account creation flow for the existing Group with `adminAccountId`, `groupId`, `memberEmail`, and `region`.
7. Store tenant to provider account and Group mapping, including returned account ID, Group ID, region, S3 endpoint, and initial provider credentials in the approved secret store.
8. Create one or more buckets inside the customer account.
9. Create scoped B2 application keys inside the customer account.
10. Emit audit events for Group linking, account, bucket, and key creation.
11. Emit usage/billing mapping records.

A starter workflow may create a default bucket inside the customer account for demo simplicity. This is not the isolation boundary.

## Eject, suspend, and reactivate semantics

Use application-level tenant/storage-account suspension for reversible access control. Do not model Partner API eject as a normal reversible suspend.

When a Group member is ejected through the Partner API, the Backblaze account is removed from the Group but is not deleted. Existing application keys created inside the Group member account continue to function unless Neocloud revokes or rotates them separately. An ejected Group member cannot be re-added to any Group using the Partner API. Treat eject as a high-friction deprovisioning/offboarding operation that requires explicit operator confirmation and audit logging.

## Provider interfaces

Do not couple product logic directly to raw API calls. Keep a thin Backblaze Partner API adapter separate from Neocloud composite operations. The provider contract intentionally excludes Group creation because Backblaze Groups are website-created resources.

### Thin Backblaze Partner API adapter

Only expose operations that correspond to documented Backblaze API calls or returned API endpoints.

```text
BackblazePartnerApiClient
  authorizeAccount
  listGroups
  listGroupMembers
  createGroupMember({ adminAccountId, groupId, memberEmail, region })
  ejectGroupMember({ adminAccountId, groupId, memberAccountId, email? })
  reserveTrialCreateAccount({ email, region, termDays, storageTb })  # optional B2 Reserve trial workflow only
```

`createGroupMember` creates the Backblaze customer account and adds it to an existing managed Group. It does not create the Group. `reserveTrialCreateAccount` is for the separate B2 Reserve trial workflow and should not be confused with the default managed-Group provisioning flow.

### Neocloud composite storage provider

Composite operations may combine Backblaze calls with local metadata, audit, key lifecycle, and policy checks. Label these as Neocloud operations, not raw Backblaze Partner API operations.

```text
NeocloudStorageProvider
  verifyPartnerApiEnabled
  verifyGroupsConfigured
  listExistingGroups
  linkExistingGroup({ providerGroupId, displayName, metadata })  # local metadata only
  listExistingGroupMembers
  provisionCustomerStorageAccount({ tenantId, existingGroupId, region, alias, memberEmail, displayName, contactEmail, metadata })
  markTenantSuspendedLocal
  markTenantReactivatedLocal
  ejectStorageAccountFromProviderGroup({ storageAccountId, memberAccountId, explicitConfirmation })
  createBucket
  listBuckets
  getBucket
  deleteBucket
  createApplicationKey
  revokeApplicationKey
  listApplicationKeys
  createMultipartUpload
  signUploadPart
  completeMultipartUpload
  abortMultipartUpload
  getDownloadUrl
  deleteObject
  getUsageReport
  validateCredentials
```

`linkExistingGroup`, `markTenantSuspendedLocal`, and `markTenantReactivatedLocal` are local/composite Neocloud operations. `ejectStorageAccountFromProviderGroup` wraps Partner API ejection but must also handle Neocloud-specific confirmation, key revocation/rotation policy, audit logging, and follow-up operator guidance.

## Local development

Use `MockStorageProvider` with deterministic fake IDs. The mock provider should seed existing fake Groups and support listing/selecting/linking those Groups. It must not implement a provider `createGroup` capability because that would train the application toward a non-existent Backblaze API workflow.

The mock provider should make the alias/memberEmail mapping explicit and should require an explicit confirmation flag for eject-style flows. Local suspend/reactivate tests should not call eject.

## Tests

- Partner API enablement prerequisite is documented.
- Group enablement prerequisite is documented.
- Group creation is documented as website-only after Groups are enabled.
- Provider contract does not contain `createGroup`.
- Thin Partner API adapter does not expose fake Backblaze operations such as provider-side suspend, reactivate, or arbitrary reassignment.
- Mock provider seeds existing Groups and supports selection/linking.
- Alias/memberEmail is generated deterministically, is email-shaped, and is stored on `storage_accounts`.
- Region and alias/memberEmail are stored on `storage_accounts`.
- Partner API region codes are stored separately from S3 endpoint/cluster labels.
- Tenant can map to multiple storage accounts for multi-region workflows.
- Customer account creation and existing-Group assignment are audited.
- Eject flow requires explicit confirmation, emits audit events, and warns that ejection is not reversible through the Partner API.
- Local suspend/reactivate does not call Partner API eject.
- Buckets are created as child resources inside a storage account.
- Provider keys are scoped inside the customer account/sub-account and, where appropriate, to specific buckets or B2 file-name scopes.
