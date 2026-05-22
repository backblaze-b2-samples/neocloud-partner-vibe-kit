# ADR 002 — B2 File-name Distribution

## Status
Accepted

## Context
B2 object keys are B2 file names. Slashes are part of the file name, not real directories. A constant leading component such as `objects/` does not distribute generated names across the leading lexicographical keyspace.

## Decision
Use `{distribution_id}/tenants/{tenant_id}/projects/{project_id}/objects/{object_id}/{safe_filename}` for generated physical B2 file names.

The first B2 file-name component is the hash-derived `distribution_id`. The `objects` component appears later for readability only; it is not a bucket, folder, partition, or authorization boundary.

## Consequences
Logical browsing uses metadata. Authorization does not parse B2 file names. Normal application listing should query metadata rather than enumerating B2 file names across distribution IDs.
