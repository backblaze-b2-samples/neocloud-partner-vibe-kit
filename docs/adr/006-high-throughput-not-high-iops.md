<!-- last_verified: 2026-06-06 -->
# ADR 006 — High-throughput, Not High-IOPS Tiny-object Design

## Status
Accepted

## Context
Neocloud workloads may include huge numbers of small files or records.

## Decision
Treat B2 as high-throughput object storage, not a high-IOPS tiny-object database. Prefer 1 MB+ objects where practical. For tiny-record workloads, use packing, manifests, and range reads. Do not globally forbid small files.

## Consequences
Small-file-heavy workflows may need additional metadata/index design.
