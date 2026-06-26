# Changelog

All notable changes to the Neocloud/Partner Vibe Kit are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This is a content product (guidance, prompts, reference docs), so entries describe
changes to the *guidance*, not to a running application.

## [Unreleased]

### Added
- Architecture and flow diagrams (mermaid) for the system layers, tenant isolation,
  the upload data plane, tenant provisioning, and the usage→billing pipeline.
- Community-health files: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, this changelog,
  issue/PR templates, and `CODEOWNERS`.
- README hero, badges, and an embedded architecture overview.

### Changed
- Removed the bundled Postman collection; references now point to Backblaze's public
  Postman workspace. (`docs/api-contracts.md`, `docs/s3-compatible-api.md`, others.)
- Corrected B2 master-key / S3-compatible behavior and added the endpoint-discovery
  rule, audited against backblaze.com.
- README getting-started rewritten with prerequisites and a step-by-step concept
  demo → PR 1 onboarding flow; `.env.example` is now tracked.

### Removed
- ADR 005 ("Postman is reference, not source of truth") — the bundled collection it
  governed is gone; the rule lives on in `docs/common-pitfalls.md` §16 and
  `docs/source-of-truth.md`.
