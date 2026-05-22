# Reuse Guidance from the Original Vibe Coding Starter Kit

Source: https://github.com/backblaze-b2-samples/vibe-coding-starter-kit

The original kit is a developer-experience and implementation-example reference, not the final neocloud architecture reference.

## Executive summary

Reuse polish, local setup patterns, B2 examples, upload UX, validation, logging, and test conventions. Do not reuse one-bucket/one-key/no-database assumptions, bucket-driven tenant isolation, local counters for billing, direct bucket listing as app state, sequential-only uploads, or object-name parsing for authorization.

## Reuse table

| Area | Reuse as-is? | Adapt for neocloud? | Why | Original repo reference |
|---|---:|---:|---|---|
| README/local setup | partly | yes | Preserve easy onboarding | `README.md` |
| Environment variables | partly | yes | Good dev pattern; add account/provisioning config | `.env.example` |
| B2 client setup | partly | yes | Wrap in provider interface | `services/api/app/repo/b2_client.py` |
| Upload UI | partly | yes | Keep UX, add concurrency/multipart | `apps/web/src/components/upload` |
| File browser UI | partly | yes | Use metadata instead of direct listing | frontend components |
| Validation/sanitization | yes | yes | Keep hygiene | `docs/security-and-tenant-isolation.md` |
| Health/metrics/logging | yes | yes | Add tenant/project dimensions | `services/api/main.py` |
| Tests | yes | yes | Reuse conventions | test config |

## Claude guardrails

- Steal polish and examples, not simple-app architecture.
- Preserve the fast local demo experience.
- Do not preserve one-bucket/one-key/no-database assumptions.
- Do not use B2 as the only source of application state.
- Do not use original filenames as durable identity.
- Do not rely on direct bucket listing for dashboards.
- Do not use local counters for reporting or billing.
- Keep changes small, reviewable, and tested.
