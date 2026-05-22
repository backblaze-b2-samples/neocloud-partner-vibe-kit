# ADR 001 — Account/Sub-account Tenant Isolation

## Status
Accepted

## Context
Neocloud customers need strong tenant boundaries and provisioning workflows.

## Decision
Use provisioned B2 customer accounts/sub-accounts organized with Groups as the primary tenant isolation model. Buckets are child resources.

## Consequences
Metadata must map tenants to storage accounts, Groups, buckets, keys, objects, and usage records.
