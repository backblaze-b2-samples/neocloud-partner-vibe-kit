# API Payload Examples

Examples are target neocloud application payloads, not current implemented API promises.

## Create tenant

```json
{
  "name": "Acme Corp",
  "billing_account_id": "bill_acme"
}
```

## Provision storage account

```json
{
  "region": "us-west",
  "alias": "cust_12345-us-west@storage.example-neocloud.com",
  "group_id": "grp_123",
  "display_name": "Acme US West Storage Account"
}
```

`group_id` must be an existing Backblaze Group ID that was created in the Backblaze website and linked/discovered by neocloud. `alias` is sent to Backblaze as Partner API `memberEmail`, so it must be email-shaped and must not already belong to a Backblaze account.


## Eject storage account from provider Group

```json
{
  "confirm_eject": true,
  "acknowledge_not_readdable_via_partner_api": true,
  "key_policy": "revoke_tracked_provider_keys"
}
```

Use this only for explicit deprovisioning/offboarding, not normal suspension.

## Create upload session

```json
{
  "filename": "checkpoint-00042.safetensors",
  "size_bytes": 5368709120,
  "content_type": "application/octet-stream"
}
```

## Complete upload session

```json
{
  "parts": [
    {"part_number": 1, "checksum": "example"}
  ]
}
```

## Usage import request

```json
{
  "period": "2026-05",
  "source": "b2_csv",
  "file_name": "usage-2026-05.csv"
}
```

## Billing export request

```json
{
  "period": "2026-05",
  "format": "csv",
  "tenant_id": "tnt_acme"
}
```
