---
status: reference
source_of_truth_for:
  - PR review gates
---

# Quality Gates

## Before editing

- Read `START_HERE.md`.
- Load only the relevant prompt and context pack.
- Inspect current architecture.
- Run baseline tests if code changes are planned.
- Identify exact files expected to change.
- Summarize assumptions.

## During implementation

- Scope to one PR.
- Do not mix roadmap phases.
- Preserve local developer experience.
- Use existing test style.
- Avoid unrelated refactors.
- Do not hardcode secrets.
- Use customer overlays for workflow-specific variation.

## Before review

- Run formatting.
- Run linting.
- Run tests relevant to changed area.
- Validate JSON artifacts.
- Run the kit validator: `python scripts/validate_kit.py` (enforces the static/doc gates in `docs/testing-matrix.md`; also runs in CI via `.github/workflows/kit-qa.yml`).
- Update docs if contracts changed.
- Summarize files, behavior, tests, commands, risks, and follow-ups.

## Neocloud-specific gates

- Tenant isolation remains account/sub-account-driven.
- Authorization uses metadata and auth context.
- B2 file names use `distribution_id` for high-scale generated names.
- Usage attribution starts with provider account/storage account.
- Partner API enablement is documented as Backblaze sales/team enabled.
- Regional account mapping and alias/memberEmail mapping are documented and tested when used.
- Partner API eject is not used for normal suspend/reactivate and requires explicit confirmation when exposed.
- Small-file policy is documented when workloads are small-object-heavy.
- Customer overlay does not override hard invariants.
- B2-native Postman environments match collection variables.
- No deprecated prompt files are used.
- Direct B2 listing is not primary tenant dashboard source.
- Billing/reporting does not use local/frontend counters.
