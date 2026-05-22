# Testing Matrix

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
| Portal | file browser uses metadata | no direct B2 listing as primary source | integration/ui | P1 |
| Quality gates | customer overlay does not override invariants | conflict flagged | unit/doc | P1 |
