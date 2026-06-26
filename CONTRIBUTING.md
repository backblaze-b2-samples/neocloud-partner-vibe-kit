# Contributing to the Neocloud/Partner Vibe Kit

Thanks for helping improve the kit. This is a **content product** — documentation,
prompts, context packs, and customer overlays that help Claude and engineers build a
B2-backed multi-tenant storage platform correctly. There is no application to compile;
the "build" is the consistency of the guidance.

## Ground rules

The kit's value is its **internal consistency**. Before proposing a change, read:

1. [`START_HERE.md`](START_HERE.md) — how the kit routes a reader/Claude to the right context.
2. [`CLAUDE.md`](CLAUDE.md) — the golden rules. These are non-negotiable invariants.
3. [`docs/source-of-truth.md`](docs/source-of-truth.md) — precedence order and the hard invariants that overlays may never override.

A change that contradicts a golden rule or hard invariant will not be accepted unless
it also updates the rule deliberately, with rationale (often a new or amended ADR in
[`docs/adr/`](docs/adr/)).

## The one quality gate: `validate_kit.py`

Every change must keep the kit-QA validator green. It enforces the static/doc
consistency gates declared in [`docs/testing-matrix.md`](docs/testing-matrix.md) —
reference integrity, roadmap PR numbering, routing, master-key guidance, overlay
isolation, freshness headers, and more.

```bash
pip install -r scripts/requirements.txt
python scripts/validate_kit.py        # exit 0 = all gates pass
```

This is the same check CI runs on every push and PR via
[`.github/workflows/kit-qa.yml`](.github/workflows/kit-qa.yml). See
[`scripts/README.md`](scripts/README.md) for what each gate guards against.

## Conventions

- **One concern per PR.** Keep changes reviewable; don't bundle unrelated edits.
- **Respect the roadmap.** Implementation guidance follows the canonical 12-PR
  sequence in [`docs/implementation-roadmap.md`](docs/implementation-roadmap.md);
  prompt files in [`prompts/`](prompts/) must match those PR numbers.
- **Update freshness headers.** When you meaningfully edit a system-of-record doc
  (`README.md`, `CLAUDE.md`, `START_HERE.md`, `docs/*.md`, `docs/adr/*.md`), update its
  `<!-- last_verified: YYYY-MM-DD -->` header to the date you verified it.
- **No secrets, ever.** Never commit real credentials, account IDs, customer data,
  bucket IDs, or tokens. Use placeholders (see [`.env.example`](.env.example)).
- **Keep diagrams accurate.** Mermaid diagrams must reflect the golden rules
  (account/sub-account isolation, website-created Groups, `distribution_id`-first
  naming, durable usage records).

## Submitting a change

1. Branch from `main`.
2. Make your change; run `python scripts/validate_kit.py` until it passes.
3. Open a PR using the template; explain what changed and why, and confirm the
   validator passes.

## Reporting problems

- Inaccurate or unsafe guidance, or a bug in the validator → open an issue using the
  templates in [`.github/ISSUE_TEMPLATE`](.github/ISSUE_TEMPLATE).
- A security flaw in recommended patterns, or a committed secret → **do not open a
  public issue**; follow [`SECURITY.md`](SECURITY.md).
