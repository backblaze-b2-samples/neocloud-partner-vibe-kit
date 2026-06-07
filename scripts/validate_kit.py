#!/usr/bin/env python3
"""Kit-QA validator for the Neocloud/Partner Vibe Kit.

This kit is a content product (docs, prompts, context-packs, overlays, Postman
collections), so "tests" are static/doc consistency checks. This script
mechanically enforces the P0/P1 static + doc gates that `docs/testing-matrix.md`
already declares, so the quality bar can't silently drift between handoffs.

Run:   python scripts/validate_kit.py
Deps:  PyYAML  (pip install -r scripts/requirements.txt)
Exit:  0 if every check passes, 1 otherwise.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("FATAL: PyYAML is required — run `pip install -r scripts/requirements.txt`")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent

# Postman collection -> environment files expected to cover its variables.
POSTMAN_PAIRS = [
    (
        "Backblaze_B2_Postman_Collection_CORRECTED_v3.json",
        ["b2-native-example.postman_environment.json", "b2-native-local.postman_environment.json"],
    ),
    (
        "Backblaze B2 Cloud Storage S3 Compatible API.postman_collection.json",
        ["s3-example.postman_environment.json", "s3-local.postman_environment.json"],
    ),
]
POSTMAN_BUILTINS = {"$randomUUID", "$timestamp", "$guid", "$isoTimestamp", "$randomInt"}
# Tokens that look like a credential key but are obvious placeholders/mocks.
PLACEHOLDER_RE = re.compile(
    r"(your|example|placeholder|xxx|<|changeme|replace|mock|sample|local|do[-_ ]?not[-_ ]?use|\.\.\.)",
    re.I,
)
SECRET_KEY_TERMS = ("applicationkey", "authorizationtoken", "password", "secret", "token", "keymd5")


class Results:
    def __init__(self):
        self.checks: list[tuple[str, bool, str]] = []

    def add(self, name: str, ok: bool, detail: str = ""):
        self.checks.append((name, ok, detail))

    def failed(self) -> int:
        return sum(1 for _, ok, _ in self.checks if not ok)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


# --- checks -----------------------------------------------------------------


def check_reference_integrity(r: Results):
    pat = re.compile(
        r"(?<![\w/])((?:docs|prompts|context-packs|customer-overlays|examples|postman)"
        r"/[A-Za-z0-9._/-]+\.(?:md|ya?ml|json|csv))"
    )
    missing = {}
    for mf in ROOT.rglob("*.md"):
        if "internal/" in mf.as_posix():
            continue
        for ref in set(pat.findall(read(mf))):
            if not (ROOT / ref).exists():
                missing.setdefault(ref, mf.name)
    r.add(
        "Reference integrity (file paths in all .md resolve)",
        not missing,
        "" if not missing else f"broken: {sorted(missing)}",
    )


def check_pr_sequence(r: Results):
    prompts = sorted(int(m.group(1)) for p in ROOT.glob("prompts/pr*.md")
                     if (m := re.match(r"pr(\d+)", p.name)))
    ok_prompts = prompts == list(range(1, 13))
    r.add("Prompts present pr1–pr12", ok_prompts, "" if ok_prompts else f"found {prompts}")

    # Every doc that enumerates the roadmap must cover the full 1..12 set.
    # Accept both prose ("PR 12") and markdown table rows with a bare leading
    # PR-number cell ("| 12 | ... |"), since the roadmap uses a table.
    drift = []
    for f in ["CLAUDE.md", "docs/implementation-roadmap.md"]:
        t = read(ROOT / f)
        nums = {int(n) for n in re.findall(r"PR[ \-]?(\d{1,2})\b", t)}
        nums |= {int(n) for n in re.findall(r"^\|\s*(\d{1,2})\s*\|", t, re.M)}
        missing = sorted(set(range(1, 13)) - nums)
        if missing:
            drift.append(f"{f}: missing {missing}")
    r.add("Roadmap PR numbering complete (1..12)", not drift, "; ".join(drift))


def check_routing(r: Results):
    sh = read(ROOT / "START_HERE.md")
    missing = []
    for line in sh.splitlines():
        if "prompts/" in line or "context-packs/" in line:
            for tok in re.findall(r"`([^`]+)`", line):
                tok = tok.strip()
                if tok.startswith(("prompts/", "context-packs/", "docs/", "examples/")) \
                        and not (ROOT / tok).exists():
                    missing.append(tok)
    r.add("START_HERE routing refs resolve", not missing, f"missing: {missing}" if missing else "")


def _collect_vars(obj, acc: set):
    if isinstance(obj, dict):
        for v in obj.values():
            _collect_vars(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            _collect_vars(v, acc)
    elif isinstance(obj, str):
        acc.update(re.findall(r"\{\{([^}]+)\}\}", obj))


def check_postman(r: Results):
    pdir = ROOT / "postman"
    # JSON validity for every postman/*.json
    bad = []
    for f in sorted(pdir.glob("*.json")):
        try:
            json.loads(read(f))
        except Exception as e:
            bad.append(f"{f.name}: {e}")
    r.add("Postman JSON validity", not bad, "; ".join(bad))

    # Variable coverage: collection-used vars ⊆ env vars ∪ collection-defined vars.
    for coll_name, envs in POSTMAN_PAIRS:
        coll_path = pdir / coll_name
        if not coll_path.exists():
            r.add(f"Postman coverage: {coll_name}", False, "collection file missing")
            continue
        cobj = json.loads(read(coll_path))
        # Exclude the human-readable changelog so prose like "{{variables}}"
        # in info.description isn't mistaken for a real reference.
        cobj.get("info", {}).pop("description", None)
        used = set()
        _collect_vars(cobj, used)
        used -= POSTMAN_BUILTINS
        coll_defined = {v.get("key") for v in cobj.get("variable", [])}
        for env in envs:
            ep = pdir / env
            if not ep.exists():
                r.add(f"Postman coverage: {env}", False, "env file missing")
                continue
            defined = {v.get("key") for v in json.loads(read(ep)).get("values", [])} | coll_defined
            gap = sorted(used - defined)
            r.add(f"Postman env covers collection vars: {env}", not gap,
                  f"missing: {gap}" if gap else "")


def check_no_secrets(r: Results):
    leaks = []
    for env in (ROOT / "postman").glob("*postman_environment.json"):
        for v in json.loads(read(env)).get("values", []):
            key, val = v.get("key", ""), (v.get("value") or "").strip()
            if val and any(t in key.lower() for t in SECRET_KEY_TERMS):
                if not PLACEHOLDER_RE.search(val) and len(val) >= 8:
                    leaks.append(f"{env.name}:{key}={val[:24]!r}")
    r.add("No real-looking secrets in Postman envs", not leaks, "; ".join(leaks))


def check_master_key_guidance(r: Results):
    issues = []
    # Positive: the warning must exist where operators read golden rules.
    for f in ["CLAUDE.md", "docs/security-review-checklist.md"]:
        if "master" not in read(ROOT / f).lower():
            issues.append(f"{f} lacks master-key guidance")
    # Negative: any overlay declaring the flag must not disable it.
    for ov in (ROOT / "customer-overlays").glob("*.yaml"):
        d = yaml.safe_load(read(ov)) or {}
        s3 = d.get("s3_compatible_api", {}) if isinstance(d, dict) else {}
        if isinstance(s3, dict) and s3.get("master_key_must_not_be_used_as_s3_credential") is False:
            issues.append(f"{ov.name} sets master_key_must_not_be_used_as_s3_credential: false")
    r.add("Master key never sanctioned as S3 credential", not issues, "; ".join(issues))


def check_overlays(r: Results):
    odir = ROOT / "customer-overlays"
    tmpl_path = odir / "customer-profile.template.yaml"
    parse_errs, iso_errs, drift = [], [], []
    overlays = {}
    for ov in sorted(odir.glob("*.yaml")):
        try:
            overlays[ov.name] = yaml.safe_load(read(ov)) or {}
        except Exception as e:
            parse_errs.append(f"{ov.name}: {e}")
    r.add("Overlays parse as YAML", not parse_errs, "; ".join(parse_errs))

    # Isolation invariant must hold in every overlay that sets it.
    for name, d in overlays.items():
        iso = (d.get("storage_model") or {}).get("tenant_isolation")
        if iso is not None and iso != "b2_customer_account_per_tenant":
            iso_errs.append(f"{name}:{iso}")
    r.add("Overlays keep account-based tenant isolation", not iso_errs, "; ".join(iso_errs))

    # Example overlays must not use keys absent from the template (F1 guard).
    tmpl_keys = set(overlays.get(tmpl_path.name, {}).keys())
    for name, d in overlays.items():
        if "example-" not in name:
            continue
        extra = sorted(set(d.keys()) - tmpl_keys)
        if extra:
            drift.append(f"{name}: {extra}")
    r.add("Example overlay keys all documented in template", not drift, "; ".join(drift))


def check_invariant_presence(r: Results):
    missing = []
    needles = ["account/sub-account", "metadata", "self-enable"]
    for f in ["START_HERE.md", "README.md", "docs/source-of-truth.md"]:
        t = read(ROOT / f).lower()
        if not any(n in t for n in needles):
            missing.append(f)
    r.add("Hard-invariant content present in canonical docs", not missing, "; ".join(missing))


# S3 feature keywords used to detect a doc claiming a feature is unsupported when
# the canonical surface doc (s3-compatible-api.md) treats it as supported — the
# class of cross-doc contradiction that the lifecycle bug was (it shipped past
# every structural check).
_FEATURE_KEYWORDS = ["kms", "tagging", "iam", "acl", "website", "logging",
                     "sigv2", "browser", "lifecycle", "transition"]


def check_feature_support_consistency(r: Results):
    """The migration guide's "does not support" list must be a subset of the
    canonical NOT-supported list in s3-compatible-api.md. Catches a doc calling a
    feature unsupported that the surface doc lists as supported (and vice versa)."""
    s3 = read(ROOT / "docs/s3-compatible-api.md")
    guide = read(ROOT / "docs/migrating-from-aws-s3.md")

    not_sec = re.search(r"## Explicitly NOT Supported(.*?)\n---", s3, re.S)
    canonical = {k for k in _FEATURE_KEYWORDS
                 if not_sec and k in not_sec.group(1).lower()}

    # Only the explicit "does **not** support: …" enumeration (up to its period),
    # so prose elsewhere ("Lifecycle rules ARE supported") isn't misread.
    enum = re.search(r"does \*\*not\*\* support:(.*?)\.\s", guide, re.S)
    region = enum.group(1).lower() if enum else ""
    claimed = {k for k in _FEATURE_KEYWORDS if k in region}
    if "sigv2 is unsupported" in guide.lower():
        claimed.add("sigv2")

    extra = sorted(claimed - canonical)
    r.add(
        "Migration guide's unsupported features ⊆ s3-compatible-api.md NOT-supported",
        not extra,
        f"guide calls these unsupported but s3-compatible-api.md doesn't: {extra}"
        if extra else "",
    )


# System-of-record docs that must carry a freshness date. Addresses
# known-gaps.md §14 (documentation-implementation drift). We assert the header
# EXISTS and is a valid date — not that it's recent — so CI never time-bombs.
_FRESHNESS_RE = re.compile(r"last_verified:?\s*(\d{4}-\d{2}-\d{2})")


def check_freshness_headers(r: Results):
    targets = ["README.md", "CLAUDE.md", "START_HERE.md"]
    targets += [f"docs/{p.name}" for p in sorted((ROOT / "docs").glob("*.md"))]
    targets += [f"docs/adr/{p.name}" for p in sorted((ROOT / "docs/adr").glob("*.md"))]
    missing = []
    for f in targets:
        head = "\n".join(read(ROOT / f).splitlines()[:8])
        if not _FRESHNESS_RE.search(head):
            missing.append(f)
    r.add(
        "System-of-record docs carry a last_verified date",
        not missing,
        f"missing/invalid: {missing}" if missing else "",
    )


_DOCS_REF_RE = re.compile(r"docs/[A-Za-z0-9/_-]+\.md")


def check_context_pack_routing(r: Results):
    """Every context pack must point at a full source-of-truth doc. Without this,
    a token-minimal builder (which the kit encourages) stops at the compressed
    pack and reinvents specs that already exist in the full docs."""
    missing = [
        p.name for p in sorted((ROOT / "context-packs").glob("*.context.md"))
        if not _DOCS_REF_RE.search(read(p))
    ]
    r.add(
        "Context packs route to a source-of-truth doc",
        not missing,
        f"no docs/ reference: {missing}" if missing else "",
    )


# --- main -------------------------------------------------------------------


def main() -> int:
    r = Results()
    for fn in [
        check_reference_integrity,
        check_pr_sequence,
        check_routing,
        check_postman,
        check_no_secrets,
        check_master_key_guidance,
        check_overlays,
        check_invariant_presence,
        check_feature_support_consistency,
        check_context_pack_routing,
        check_freshness_headers,
    ]:
        fn(r)

    print("Neocloud/Partner Vibe Kit — validation\n")
    for name, ok, detail in r.checks:
        line = f"  {'PASS' if ok else 'FAIL'}  {name}"
        if not ok and detail:
            line += f"\n          {detail}"
        print(line)

    failed = r.failed()
    print("")
    if failed == 0:
        print(f"✓ all {len(r.checks)} checks passed")
        return 0
    print(f"✗ {failed}/{len(r.checks)} checks failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
