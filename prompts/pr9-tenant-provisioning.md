# PR 9 — Tenant provisioning

Use this prompt with Claude for PR 9.

## Low-token startup

1. Read `START_HERE.md`.
2. Read `CLAUDE.md`.
3. Read this prompt and `context-packs/provisioning.context.md`.
4. Load full docs only when necessary.

## Goal

Implement Group-aware tenant provisioning with existing Backblaze Groups, customer accounts/sub-accounts, aliases/memberEmail values, regions, buckets, and provider keys.

## Scope

Partner API enablement prerequisite, Groups website prerequisite, existing Group selection/linking, account create/eject, alias-to-memberEmail mapping, bucket/key child workflows, audited provisioning, and explicit eject warnings.

## Non-goals

- Do not implement unrelated roadmap phases.
- Do not implement Backblaze Group creation; Groups are created in the Backblaze website after Groups are enabled.
- Do not hardcode secrets or real provider IDs.
- Preserve local developer experience.

## Before editing

- Inspect current architecture.
- Run baseline tests if code changes are planned.
- Identify expected files to change.
- Present a concise plan.

## Required tests

- Partner API enablement documented
- Group enablement and website-only Group creation documented
- provider contract excludes `createGroup`
- mock provider seeds existing Groups and supports selection/linking
- region and alias/memberEmail stored
- alias/memberEmail is email-shaped and deterministic
- multi-region tenant supported
- existing Group assignment recorded
- Partner API eject is not used for normal suspend/reactivate
- eject requires explicit operator confirmation and warns that Partner API re-add is not supported
- provisioning audited

## After editing

- Run formatting/linting/tests relevant to the change.
- Validate JSON if touched.
- Summarize files changed, behavior changed, tests, risks, and follow-ups.

## Suggested PR title

Add tenant provisioning with existing Groups

## Suggested PR description

Add a summary, what changed, testing, risks, and follow-ups.
