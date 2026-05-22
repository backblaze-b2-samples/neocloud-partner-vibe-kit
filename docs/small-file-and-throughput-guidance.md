---
status: reference
load_when:
  - designing small-file-heavy workflows
  - implementing upload data plane
source_of_truth_for:
  - high-throughput vs high-IOPS guidance
  - small-file packing patterns
  - range-read patterns
---

# Small Files and High-Throughput Workload Guidance

## Core principle

Backblaze B2 should be treated as high-throughput object storage, not a high-IOPS tiny-object database.

This does not mean small files are forbidden. It means high-scale designs should avoid unnecessary tiny-object amplification when practical.

## Preferred object sizing

- Prefer objects of at least 1 MB when practical.
- This is a recommendation, not a hard requirement.
- Workloads may legitimately need smaller objects.
- Do not reject small files solely because they are below 1 MB unless a customer policy explicitly requires it.

## Why tiny objects can be a problem

Individually addressing many tiny objects can increase request overhead, complicate listing and indexing, increase per-object metadata overhead, and make the application request-bound instead of throughput-bound. Avoid unsupported performance guarantees; explain the tradeoff and offer patterns.

## Recommended patterns

- Batch small records into larger segment objects.
- Concatenate small files into larger container objects.
- Maintain manifests or indexes mapping logical records/files to byte ranges.
- Use range reads to retrieve sub-objects.
- Use a durable metadata DB for logical browsing and lookup.
- Use larger segment sizes for backup/archive and dataset ingest.
- Choose workload-specific formats where appropriate, such as Parquet, Arrow, JSONL batches, tar-like bundles, Zarr-like layouts, chunked archives, or customer-defined manifests.

Example manifest entry:

```json
{
  "logical_name": "records/2026/05/21/000001.json",
  "physical_b2_file_name": "7f/tenants/tnt_123/projects/prj_456/objects/obj_abc/segment-000001.bin",
  "offset": 1048576,
  "length": 32768,
  "checksum": "example"
}
```

## Range reads

Range reads let applications retrieve a portion of a larger object. They support packed or concatenated small-file workflows when the metadata or manifest service knows offsets and lengths. Range-read requests must validate tenant/project/object ownership before signing or serving a byte range.

## When individual small objects are acceptable

Individual small objects are reasonable for low-volume workflows, human-uploaded documents, control files, metadata files, web assets, compliance workflows that require object-level addressability, and customer requirements that prioritize per-object semantics.

If a customer uploads tiny records as individual objects and the workload becomes request-bound, prefer packing records into larger objects with a manifest and range reads, or store very small metadata in a database when object storage is not the right access pattern.

## B2 file-name distribution reminder

Packed objects and normal objects should still use B2 file-name distribution across the lexicographical keyspace for high-scale generated names.

## Tests

- Manifest maps logical objects to physical B2 file name + offset + length.
- Range read requests validate tenant/project/object ownership before issuing a URL or serving bytes.
- Small records can be retrieved from packed objects.
- Corrupted or missing manifest entries fail safely.
- Usage events can attribute packed object storage and access.
- Customer policy can warn on sub-1 MB objects without globally rejecting them.
