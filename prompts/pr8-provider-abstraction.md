# PR 8 - Provider abstraction

Use this prompt with Claude for PR 8.

## Low-token startup

1. Read `START_HERE.md`.
2. Read `CLAUDE.md`.
3. Read this prompt and `context-packs/provisioning.context.md`.
4. Load full docs only when necessary.

## Goal

Add a mockable provider layer with a thin Backblaze Partner API adapter plus Neocloud composite storage operations. Cover existing Group discovery/linking, customer accounts, buckets, keys, uploads, downloads, and usage reports without pretending that local/composite actions are raw Backblaze endpoints.

## Scope

Interface and mock provider only; no real Partner API implementation unless explicitly requested. Mock Groups should be seeded fixtures that represent Backblaze Groups already created in the website. Keep the thin Partner API adapter limited to documented operations such as listGroups, listGroupMembers, createGroupMember, ejectGroupMember, and optional reserveTrialCreateAccount.

## Non-goals

- Do not implement unrelated roadmap phases.
- Do not hardcode secrets or real provider IDs.
- Do not implement Backblaze Group creation; Groups are created in the Backblaze website after Groups are enabled.
- Preserve local developer experience.

## Before editing

- Inspect current architecture.
- Run baseline tests if code changes are planned.
- Identify expected files to change.
- Present a concise plan.

## Required tests

- mock provider implements contract
- mock provider lists/selects existing Groups
- provider contract does not expose `createGroup`
- provisionCustomerStorageAccount/createGroupMember accepts existing Group ID, region, and alias/memberEmail
- account/group methods are modeled around existing Groups
- alias is sent as Backblaze `memberEmail` and must be email-shaped
- suspend/reactivate are local/composite operations, not raw Backblaze Partner API calls
- eject requires explicit confirmation and warns that re-add through Partner API is not supported
- local tests do not require credentials

## After editing

- Run formatting/linting/tests relevant to the change.
- Validate JSON if touched.
- Summarize files changed, behavior changed, tests, risks, and follow-ups.

## Suggested PR title

Add storage provider abstraction

## Suggested PR description

Add a summary, what changed, testing, risks, and follow-ups.
