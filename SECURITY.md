# Security Policy

The Neocloud/Partner Vibe Kit is an implementation **guide** — documentation,
prompts, and context packs. It contains no running service. Even so, we take the
security of the kit's *guidance* seriously, because teams build real multi-tenant
storage platforms from it.

## Reporting a vulnerability or unsafe guidance

Please report either of the following privately — **do not open a public issue**:

- A security flaw in the kit's recommended patterns (e.g., guidance that would
  weaken tenant isolation, leak credentials, or bypass authorization).
- A secret, real credential, or customer data accidentally committed to the repo.

Email **security@backblaze.com** with "Neocloud Vibe Kit" in the subject, or use
Backblaze's coordinated disclosure process at
<https://www.backblaze.com/company/policy.html>. We aim to acknowledge within
3 business days.

## Scope

In scope:
- Insecure patterns in `docs/`, `prompts/`, `context-packs/`, or
  `customer-overlays/` that would lead an implementer to a vulnerable design.
- Committed secrets or credentials (see also the hard invariant: **no secrets in
  the repo**).

Out of scope:
- Vulnerabilities in a platform *you build* from the kit — review those against
  `docs/security-review-checklist.md` before production.
- The Backblaze B2 service itself — report via the link above.

## For implementers

Before taking a kit-derived platform to production, complete
`docs/security-review-checklist.md` (it is referenced from `docs/known-gaps.md`
§5, "No Production Security Review"). Key invariants the kit must preserve:
account/sub-account tenant isolation, metadata-based authorization, least-privilege
provider keys, durable usage records, and **never using the operator master key as
a tenant or S3 credential**.
