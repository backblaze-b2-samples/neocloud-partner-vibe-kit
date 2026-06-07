<!-- last_verified: 2026-06-06 -->
# ADR 002 — B2 File-name Distribution

## Status
Accepted

## Context
B2 object keys are B2 file names. Slashes are part of the file name, not real directories. A constant leading component such as `objects/` does not distribute generated names across the leading lexicographical keyspace.

## Decision
Use `{distribution_id}/tenants/{tenant_id}/projects/{project_id}/objects/{object_id}/{safe_filename}` for generated physical B2 file names.

The first B2 file-name component is the hash-derived `distribution_id`. The `objects` component appears later for readability only; it is not a bucket, folder, partition, or authorization boundary.

## Specification (normative)

The physical file-name builder MUST be deterministic and interoperable, so the
inputs and algorithm are pinned. Reimplementations that follow this produce
identical names; ones that don't produce **unreadable** objects.

**`distribution_id`**
- **Input:** the object's stable `object_id` (the globally-unique id from the
  `objects` table). Do not hash the filename, logical path, or anything mutable.
- **Algorithm:** `SHA-256(object_id_utf8)`, lowercase hex, take the first `N`
  characters.
- **Length `N`:** `2` by default (256-way spread); `4` for extreme-scale
  workloads. Pick once per deployment and keep it stable.
- Reference: `distribution_id = sha256(object_id.encode("utf-8")).hexdigest()[:N]`.

**`safe_filename`** (display/suffix component only — never an authority)
- Use the original filename's final path segment (drop any `/`).
- Allowed characters: `A–Z a–z 0–9 . _ -`; replace every other character
  (including spaces and Unicode) with `_`.
- Trim surrounding whitespace; if the result is empty, use `file`.
- Cap length at 255 bytes. The pair (`object_id`, `safe_filename`) is unique
  because `object_id` is unique, so sanitization never needs collision handling.

**Determinism:** for fixed (`object_id`, `original_filename`, `N`) the builder
returns the same physical name every time; `tenant_id` and `project_id` are
substituted verbatim. This is what the PR 1 "deterministic file-name generation"
test verifies.

## Consequences
Logical browsing uses metadata. Authorization does not parse B2 file names. Normal application listing should query metadata rather than enumerating B2 file names across distribution IDs.
