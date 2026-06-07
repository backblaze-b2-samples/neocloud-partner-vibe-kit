---
status: context-pack
token_note: Short compressed context. Open full docs only when needed.
source_of_truth:
  - docs/small-file-and-throughput-guidance.md
  - docs/configuration-reference.md
  - docs/upload-data-plane.md
---

# Small Files Context

B2 is high-throughput object storage. It is best suited for moving and storing larger object streams, not for treating every tiny record as its own high-RPS object operation.

Do not globally reject small files; some workflows legitimately require them. Prefer 1 MB+ objects where practical, but treat that as a recommendation, not a hard requirement.

When a workload can concatenate, pack, batch, or aggregate small files into larger objects, prefer that pattern. Store a manifest or index that maps each logical file or record to a physical B2 file name, byte offset, length, checksum, and metadata. Use range reads to retrieve only the needed portion of the larger object.

This pattern can improve performance and scalability by lowering request rate, reducing per-object overhead, and increasing potential throughput.

Use a database for tiny metadata, manifests, indexes, and lookup-heavy access patterns when object storage is not the right primary access layer.
