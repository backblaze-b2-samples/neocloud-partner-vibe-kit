# ADR 004 — Multipart Upload Defaults

## Status
Accepted

## Decision
Use single upload below 100 MB and multipart at or above 100 MB. Use 100 MB default parts, 5 MB minimum except final, 5 GB maximum, 10,000 parts, retry/backoff, and abort cleanup.
