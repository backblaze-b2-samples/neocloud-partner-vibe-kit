#!/usr/bin/env python3
"""Neocloud / Partner Vibe Kit — 5-minute concept demo.

This is NOT the platform. It is a tiny, runnable demonstration of the kit's core
invariants against a real Backblaze B2 bucket, so you can see the patterns work
before you build the real foundation (start with `prompts/pr1-foundation.md`).

It demonstrates four hard invariants from `docs/source-of-truth.md`:

  1. distribution_id-first B2 file names      (ADR 002 — spread writes, no hot spots)
  2. a DURABLE usage ledger (SQLite here)     (billing from records, not counters)
  3. metadata-based browsing                  (query the ledger, not B2 prefixes)
  4. presigned download                       (no proxying object bytes)

Run:
  cp .env.example .env   # then fill in a throwaway-bucket B2 key
  pip install -r quickstart/requirements.txt
  python quickstart/quickstart.py

Everything it writes lives under a unique `quickstart-demo/<run>/` key prefix and
is deleted at the end. The local ledger is a temp SQLite file, also removed.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
import tempfile
import uuid
from pathlib import Path
from urllib.parse import urlparse

try:
    import boto3
    from botocore.config import Config
except ImportError:
    raise SystemExit("Missing dependency — run: pip install -r quickstart/requirements.txt")

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = REPO_ROOT / ".env"

REQUIRED = ("B2_ENDPOINT", "B2_KEY_ID", "B2_APPLICATION_KEY", "B2_BUCKET_NAME")


def load_env() -> dict:
    """Load B2 settings from process env, falling back to the repo-root .env."""
    env = {k: os.environ[k] for k in REQUIRED if k in os.environ}
    if ENV_FILE.exists():
        for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    missing = [k for k in REQUIRED if not env.get(k)]
    if missing:
        raise SystemExit(
            "Missing B2 settings: " + ", ".join(missing) + "\n"
            "Add them to .env (a THROWAWAY bucket) — see .env.example. The key needs "
            "read+write+delete. Never use the operator master key here."
        )
    return env


def physical_b2_name(tenant_id: str, project_id: str, object_id: str, filename: str) -> str:
    """Invariant 1: distribution_id-first physical B2 file name (ADR 002).

    The first component is a hash-derived `distribution_id` (2 hex chars), so
    high-scale generated names spread across the lexicographical keyspace instead
    of clustering behind a constant prefix and creating a write hot spot.
    """
    distribution_id = hashlib.sha256(object_id.encode()).hexdigest()[:2]
    return f"{distribution_id}/tenants/{tenant_id}/projects/{project_id}/objects/{object_id}/{filename}"


def main() -> int:
    env = load_env()
    endpoint = env["B2_ENDPOINT"].rstrip("/")
    bucket = env["B2_BUCKET_NAME"]
    region = urlparse(endpoint).netloc.split(".")[1]
    run = uuid.uuid4().hex[:8]

    s3 = boto3.client(
        "s3", endpoint_url=endpoint, region_name=region,
        aws_access_key_id=env["B2_KEY_ID"], aws_secret_access_key=env["B2_APPLICATION_KEY"],
        config=Config(signature_version="s3v4"),  # invariant: SigV4 only
    )

    # Durable usage ledger (a real platform uses Postgres; SQLite keeps the demo
    # dependency-free). The point is that usage lives in DURABLE RECORDS.
    db_path = Path(tempfile.gettempdir()) / f"neocloud-quickstart-{run}.sqlite"
    db = sqlite3.connect(db_path)
    db.execute(
        "CREATE TABLE objects (key TEXT, tenant_id TEXT, project_id TEXT, "
        "filename TEXT, size_bytes INT, sha256 TEXT, created_at TEXT)"
    )
    db.execute(
        "CREATE TABLE usage_events (tenant_id TEXT, key TEXT, event TEXT, bytes INT)"
    )

    tenant, project = "tnt_demo", "prj_demo"
    print(f"\nNeocloud / Partner Vibe Kit — concept demo (run {run})")
    print(f"bucket={bucket}  region={region}\n" + "-" * 60)

    # 1. Upload three objects under distribution_id-first names.
    print("1. Upload — distribution_id-first physical names (ADR 002):")
    created_keys = []
    for i in range(3):
        object_id = f"obj_{uuid.uuid4().hex[:10]}"
        filename = f"reading-{i}.json"
        body = f'{{"sensor": {i}, "run": "{run}"}}'.encode()
        key = "quickstart-demo/" + run + "/" + physical_b2_name(tenant, project, object_id, filename)
        sha256 = hashlib.sha256(body).hexdigest()
        s3.put_object(Bucket=bucket, Key=key, Body=body, ChecksumAlgorithm="SHA256")
        created_keys.append(key)
        db.execute("INSERT INTO objects VALUES (?,?,?,?,?,?,datetime('now'))",
                   (key, tenant, project, filename, len(body), sha256))
        db.execute("INSERT INTO usage_events VALUES (?,?,?,?)", (tenant, key, "upload", len(body)))
        print(f"   • {key.split('quickstart-demo/'+run+'/')[1]}")
    db.commit()
    lead = sorted({k.split("quickstart-demo/" + run + "/")[1].split("/")[0] for k in created_keys})
    print(f"   → leading distribution_ids used: {lead}  (writes spread across the keyspace)")

    # 2. Browse via metadata, NOT B2 prefix enumeration.
    print("\n2. Browse — query the durable ledger, not B2 list-by-prefix:")
    rows = db.execute(
        "SELECT filename, size_bytes, substr(sha256,1,12) FROM objects WHERE tenant_id=? ORDER BY filename",
        (tenant,),
    ).fetchall()
    for fn, size, sh in rows:
        print(f"   • {fn:16} {size:>4} B  sha256={sh}…")
    print(f"   → {len(rows)} objects for {tenant} (logical view from metadata)")

    # 3. Presigned download — the platform never proxies object bytes.
    print("\n3. Download — presigned URL (direct tenant↔B2, no proxy):")
    target = created_keys[0]
    url = s3.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": target}, ExpiresIn=300)
    import urllib.request
    fetched = urllib.request.urlopen(url).read()
    db.execute("INSERT INTO usage_events VALUES (?,?,?,?)", (tenant, target, "download", len(fetched)))
    db.commit()
    print(f"   • presigned GET returned {len(fetched)} bytes ✓")

    # 4. Usage summary from the ledger (durable records → billing).
    print("\n4. Usage — aggregated from durable events (this is what bills):")
    for event, n, total in db.execute(
        "SELECT event, COUNT(*), SUM(bytes) FROM usage_events GROUP BY event ORDER BY event"
    ):
        print(f"   • {event:9} count={n}  bytes={total}")

    # cleanup
    print("\n" + "-" * 60)
    for k in created_keys:
        s3.delete_object(Bucket=bucket, Key=k)
    db.close()
    db_path.unlink(missing_ok=True)
    print(f"cleaned up {len(created_keys)} B2 objects + local ledger.")
    print("\nNext: build the real foundation → prompts/pr1-foundation.md (see START_HERE.md).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
