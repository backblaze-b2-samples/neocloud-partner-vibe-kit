# scripts/

Maintenance tooling for the kit itself (not part of the platform you build).

## `validate_kit.py` — kit-QA validator

This kit is a content product — docs, prompts, context-packs, customer overlays,
and Postman collections. Its "tests" are the **static / doc** consistency gates
listed in `docs/testing-matrix.md`. `validate_kit.py` runs them mechanically so
the quality bar can't drift between handoffs.

```bash
pip install -r scripts/requirements.txt
python scripts/validate_kit.py        # exit 0 = all gates pass, 1 = a gate failed
```

It runs in CI on every push/PR via `.github/workflows/kit-qa.yml`.

### What it checks

| Check | Guards against |
|-------|----------------|
| Reference integrity | A doc linking to a file that was renamed/removed |
| Prompts pr1–pr12 present | A missing or misnumbered canonical prompt |
| Roadmap PR numbering (1..12) | README / CLAUDE.md / roadmap disagreeing on the sequence |
| START_HERE routing refs resolve | The routing table pointing at a non-existent prompt/context/doc |
| Postman JSON validity | A malformed collection or environment |
| Postman env var coverage | An environment missing a variable its collection uses |
| No real-looking secrets in envs | A committed credential in a Postman environment |
| Master key never sanctioned as S3 cred | Guidance loss, or an overlay disabling the rule |
| Overlays parse + isolation invariant | A broken overlay, or one switching off account-based isolation |
| Example keys documented in template | Template/example drift (examples using undocumented keys) |
| Hard-invariant content present | An invariant section silently dropped from a canonical doc |
| Feature-support consistency | A doc calling an S3 feature unsupported that `s3-compatible-api.md` lists as supported (the lifecycle-bug class) |
| Freshness headers | A system-of-record doc (`README`, `CLAUDE.md`, `START_HERE.md`, `docs/*.md`, `docs/adr/*.md`) missing its `last_verified` date |
| Context-pack routing | A context pack that doesn't point at any full source-of-truth doc (so a token-minimal builder reinvents specs that already exist) |

When you add a prompt, doc, overlay key, or Postman variable, run the validator
before opening the PR — it's the same gate CI enforces.
