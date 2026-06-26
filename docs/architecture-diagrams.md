<!-- last_verified: 2026-06-26 -->
# Architecture Diagrams

Visual companion to the kit. Every diagram here reflects the golden rules in
`CLAUDE.md` and the hard invariants in `docs/source-of-truth.md` — account/sub-account
tenant isolation, website-created Groups, `distribution_id`-first B2 file names,
provider-account-first usage attribution, and durable (append-only) usage records.

These diagrams are reference, not source of truth. When a diagram and a doc disagree,
the doc wins — fix the diagram. The canonical text lives in
`docs/neocloud-architecture.md`, `docs/provisioning-and-partner-api.md`,
`docs/upload-data-plane.md`, `docs/usage-reporting-and-billing.md`, and
`docs/data-model.md`.

## System layers

```mermaid
flowchart TB
    subgraph Clients
        Admin["Operator admin portal"]
        Tenant["Tenant self-service portal / API clients"]
    end

    subgraph Platform["Neocloud platform"]
        CP["Control-plane API<br/>(tenants, accounts, keys, config)"]
        DP["Data-plane API<br/>(upload, download, presign, delete)"]
        DB[("Metadata DB<br/>tenants · projects · objects")]
        UE[("Usage event ledger<br/>usage_events · append-only")]
        REP["Reporting & reconciliation jobs<br/>usage_imports → usage_import_rows → billing_ledger"]
        SP["Storage provider abstraction<br/>NeocloudStorageProvider + BackblazePartnerApiClient"]
        AUD["Audit & observability<br/>audit_events · logs · /admin/metrics · health"]
    end

    B2["Backblaze B2<br/>customer accounts · buckets · keys · objects"]

    Admin --> CP
    Tenant --> CP
    Tenant --> DP
    CP --> DB
    DP --> DB
    DP --> UE
    DP --> SP
    CP --> SP
    REP --> UE
    REP --> DB
    SP --> B2
    AUD -. cross-cutting .-> CP
    AUD -. cross-cutting .-> DP
```

## Tenant isolation (account/sub-account, not bucket)

Isolation is driven by provisioned B2 customer accounts, organized by Backblaze
Groups. Buckets are child resources inside an account — **not** the tenant boundary.
A tenant spanning multiple regions maps to multiple customer accounts.

```mermaid
flowchart TD
    G["Backblaze Group<br/>(created in the Backblaze website,<br/>up to 5,000 accounts)"]
    T1["Tenant A"]
    T2["Tenant B"]
    A1["customer account<br/>(us-west-004)"]
    A2["customer account<br/>(eu-central-003)"]
    A3["customer account<br/>(us-west-004)"]
    B1["bucket"]
    B2["bucket"]
    B3["bucket"]
    O1["objects<br/>(distribution_id-first names)"]

    G --> A1
    G --> A2
    G --> A3
    T1 --> A1
    T1 --> A2
    T2 --> A3
    A1 --> B1
    A2 --> B2
    A3 --> B3
    B1 --> O1
```

## Tenant provisioning (Partner API)

Groups are created once in the Backblaze website; the platform only links to them.
Provisioning a tenant creates a customer account in the Group via the Partner API.

```mermaid
sequenceDiagram
    participant Op as Operator
    participant NC as Neocloud control plane
    participant PA as Partner API (BackblazePartnerApiClient)
    participant B2 as Backblaze B2

    Note over Op,B2: Prereq: Partner API + Groups enabled by Backblaze;<br/>Group created in the Backblaze website (not via API)
    Op->>NC: Provision tenant (region)
    NC->>NC: Generate alias<br/>customerId-region@storageDomain
    NC->>PA: createGroupMember({ adminAccountId, groupId, memberEmail, region })
    PA->>B2: b2_create_group_member
    B2-->>PA: customer accountId, credentials
    PA-->>NC: account + initial key
    NC->>B2: create bucket(s) + scoped application keys in the account
    NC->>NC: store storage_accounts mapping (accountId, region, s3_endpoint)
    NC->>NC: emit audit_events (group link, account, bucket, key)
    Note over NC,B2: Eject = ejectGroupMember: removes account from Group,<br/>does NOT delete it, keys keep working until revoked,<br/>cannot be re-added via Partner API. Deprovision, not suspend.
```

## Upload data plane

Single-object upload below 100 MB; multipart at or above 100 MB. All physical names
are `distribution_id`-first; usage and audit events are emitted on completion.

```mermaid
flowchart TD
    Start["Client requests upload session<br/>POST /tenant/projects/:id/upload-sessions"] --> Build["Build physical B2 file name<br/>distribution_id-first, then tenant / project / object"]
    Build --> Size{"File size ≥ 100 MB?"}

    Size -->|"No — under 100 MB"| Single["Single-object upload"]
    Single --> Emit

    Size -->|"Yes — 100 MB and up"| MStart["b2_start_large_file → fileId"]
    MStart --> MUrl["b2_get_upload_part_url (per part)"]
    MUrl --> MPart["b2_upload_part<br/>part concurrency 4 · parts 100 MB · 5 MB min / 5 GB max"]
    MPart --> MDone{"All parts ok?"}
    MDone -->|Yes| MFinish["b2_finish_large_file"]
    MDone -->|"Final failure / cancel"| Abort["Abort incomplete multipart"]
    MFinish --> Emit
    Abort --> Emit

    Emit["Emit usage_events + audit_events"]

    classDef warn fill:#fff3cd,stroke:#d39e00;
    class Abort warn;
```

Retry transient failures (408, 425, 429, 500, 502, 503, 504, network) up to 3× with
exponential backoff + jitter. Never retry 400, 401, 403, 404, 413.

## Usage → billing pipeline

Billing derives from the provider's authoritative B2 usage CSV, attributed
provider-account-first, and reconciled against the platform's own durable events.

```mermaid
flowchart LR
    CSV["B2 usage CSV"] --> Imp[("usage_imports<br/>raw + checksum")]
    Imp --> Norm["Normalize rows"]
    Norm --> Attr["Attribute:<br/>1. provider account → storage_account<br/>2. bucket id/name<br/>3. internal metadata"]
    Attr --> Rows[("usage_import_rows<br/>+ unattributed rows")]
    Rows --> Recon["Reconcile vs usage_events"]
    UE[("usage_events<br/>append-only")] --> Recon
    Recon --> Ledger[("billing_ledger<br/>billing_periods")]
    Ledger --> Exports[("report_exports")]
```

## Data model (core entities)

```mermaid
erDiagram
    groups ||--o{ storage_accounts : organizes
    tenants ||--o{ storage_accounts : "has (per region)"
    storage_accounts ||--o{ buckets : contains
    storage_accounts ||--o{ provider_keys : scopes
    tenants ||--o{ projects : owns
    projects ||--o{ objects : groups
    buckets ||--o{ objects : stores
    objects ||--o{ upload_sessions : "via"
    upload_sessions ||--o{ upload_parts : "splits into"
    service_accounts ||--o{ api_keys : issues
    tenants ||--o{ usage_events : generates
    usage_imports ||--o{ usage_import_rows : normalizes
    billing_periods ||--o{ billing_ledger : projects
    tenants ||--o{ audit_events : records

    tenants {
        id id PK
        string status
        string provider_customer_account_id
        string provider_group_id
    }
    storage_accounts {
        id id PK
        id tenant_id FK
        string provider_customer_account_id
        string region
        string alias
        string s3_endpoint
    }
    objects {
        id id PK
        string physical_b2_file_name
        string logical_path
        int size_bytes
    }
    usage_events {
        id id PK
        string event_type
        int bytes
        datetime occurred_at
    }
```
