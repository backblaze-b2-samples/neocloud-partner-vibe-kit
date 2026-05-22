# Postman Collection

This folder contains Postman artifacts.

## B2 Native API collection

`Backblaze_B2_Postman_Collection_CORRECTED_v3.json`

Status: candidate corrected v3 reference collection pending live-environment review.

This is a B2 Native API reference collection. It is not the target neocloud platform API contract. Use `docs/api-contracts.md` for target application APIs.

Use these environments with the B2 Native API collection:

- `b2-native-example.postman_environment.json`
- `b2-native-local.postman_environment.json`

These are placeholder templates. Never commit a populated environment with real credentials. For Partner API account creation, set `memberEmail` to the Neocloud alias value. For large-file part uploads, set `partSha1` to the precomputed SHA-1 for the current part and use the same checksum in `b2_finish_large_file`. For Object Lock examples, set `retainUntilTimestamp` to a future Unix timestamp in milliseconds.

## Neocloud platform API environments

Use these for future neocloud platform API requests, not for the B2 Native API collection:

- `neocloud-example.postman_environment.json`
- `neocloud-local.postman_environment.json`

## Security

Do not commit real API keys, application keys, customer data, account IDs, bucket IDs, production URLs, private tokens, or cookies.
