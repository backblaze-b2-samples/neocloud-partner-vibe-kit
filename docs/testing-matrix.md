# Testing Matrix

The `static` / `doc` rows below — kit consistency rather than generated-app
behavior — are enforced mechanically by `scripts/validate_kit.py` (run in CI via
`.github/workflows/kit-qa.yml`). Run `python scripts/validate_kit.py` before
opening a PR. The `unit` / `integration` rows describe tests for the platform
you build with the kit.

| Category | Scenario | Expected result | Test type | Priority |
|---|---|---|---|---|
| Roadmap | README, CLAUDE.md, roadmap, and prompts use the 12-PR sequence | Consistent PR numbering | static/doc test | P0 |
| Context | START_HERE routes each task to one prompt and one context pack | Minimal context path is clear | doc test | P0 |
| Data model | storage_account belongs to one tenant | Ownership enforced | unit/integration | P0 |
| Data model | bucket belongs to storage_account | Bucket is child resource | unit | P0 |
| Data model | provider_key belongs to storage_account and optional bucket/scope | Key scoping modeled | unit | P0 |
| Isolation | tenant maps to provider customer account/sub-account metadata | Account-driven isolation | integration | P0 |
| Isolation | cross-tenant access with guessed IDs | Denied | integration/security | P0 |
| Authorization | object access uses metadata and auth context | No B2 file-name parsing as authority | integration/security | P0 |
| B2 file names | deterministic generation | Same input produces same file name | unit | P0 |
| B2 file names | distribution_id near beginning | Name starts with `{distribution_id}/` | unit | P0 |
| B2 file names | high-volume generated names spread across distribution IDs | Multiple leading values used | property/unit | P1 |
| Uploads | <100 MB upload | single-object flow | integration | P0 |
| Uploads | >=100 MB upload | multipart flow | integration | P0 |
| Uploads | transient part failure | retry/backoff | unit/integration | P0 |
| Uploads | cancel upload | multipart abort called | integration | P0 |
| Small files | <1 MB file with default policy | accepted, optional warning | unit/integration | P1 |
| Small files | packed manifest range read | ownership checked, byte range correct | integration | P1 |
| Partner API | enablement prerequisite documented | Cannot self-enable in docs | doc/static | P0 |
| Provisioning | create storage account with region and alias/memberEmail | mapping stored and alias sent as memberEmail | integration/mock | P0 |
| Provisioning | multi-region tenant | multiple storage_accounts | integration/mock | P1 |
| Provisioning | eject storage account | explicit confirmation required; warning shown; not used for normal suspend/reactivate | integration/mock | P0 |
| Usage | provider account-first attribution | mapped to storage_account first | unit | P0 |
| Usage | unknown account/bucket | unattributed row | unit | P0 |
| Billing | export from ledger | deterministic | unit/integration | P1 |
| Postman | corrected collection JSON validates | valid JSON | static | P0 |
| Postman | b2-native env includes collection variables | all variables represented | static | P0 |
| Postman | S3-compatible collection JSON validates | valid JSON | static | P0 |
| Postman | s3-example env includes collection variables (applicationKeyId, applicationKey, region, keyMd5) | all variables represented | static | P0 |
| S3 API | tenant provider key works as AWS SigV4 credential against `s3.{region}.backblazeb2.com` | authenticated request succeeds | integration/mock | P0 |
| S3 API | SigV2 request rejected | 4xx error returned | integration/mock | P1 |
| S3 API | master application key never used as S3 credential by any tenant code path | grep over CI/configs/test fixtures returns empty | static/security | P0 |
| S3 API | tenant uses S3 directly to upload object | object appears in `usage_import_rows` after next CSV ingest | integration/mock | P0 |
| S3 API | tenant uses S3 directly to upload object | object does NOT appear in `usage_events` until optional list-reconciliation runs | integration/mock | P1 |
| S3 API | reconciliation job reports a non-zero delta for S3-direct workloads | delta is reported, not zero, not error | integration | P1 |
| S3 API | provisioning captures `s3_endpoint` on `storage_accounts` row | endpoint host stored, region label distinguishable from Partner API region code | integration/mock | P0 |
| S3 API | S3 multipart upload succeeds against tenant bucket | object created with same physical bytes as B2 Native equivalent | integration/mock | P1 |
| S3 API | SSE-KMS request rejected with a clear error | unsupported feature surfaced to caller | integration/mock | P1 |
| S3 API | object-level ACL set request returns 403 | platform documents this as unsupported | integration/mock | P1 |
| S3 API | object tagging operations return empty / unsupported | platform documents this as unsupported | integration/mock | P1 |
| Portal | file browser uses metadata | no direct B2 listing as primary source | integration/ui | P1 |
| Quality gates | customer overlay does not override invariants | conflict flagged | unit/doc | P1 |
