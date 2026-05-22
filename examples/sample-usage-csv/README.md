# Sample B2 Usage CSV

This directory contains sample data only. It does not include real customer data.

Usage attribution should start with provider account/storage account, then bucket ID/name, then internal metadata. Bucket name alone is not a reliable tenant identifier.

The sample uses separate fake account IDs for separate tenants:

| Account ID | Tenant | Bucket |
|---|---|---|
| `acct-acme-001` | Acme | `nc-acme-primary` |
| `acct-beta-001` | Beta | `nc-beta-primary` |
| `acct-operator-001` | Operator/control | `nc-control-reports` |

Unknown account/bucket combinations should be imported as unattributed rows for review.
