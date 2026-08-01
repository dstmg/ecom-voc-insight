# Publishing Checklist

Recommended release label: `v1.0.0`.

## Already Done

- `SKILL.md` exists and has trigger description.
- Runtime scripts are bundled in `scripts/`.
- Input, output, and report quality contracts are in `references/`.
- `README.md` exists for GitHub readers.
- `DISCLAIMER.md` exists.
- `LICENSE` exists.
- `.gitignore` excludes test output.
- Minimal synthetic regression test exists: `tests/run_min_regression.py`.
- Minimal regression passed locally.
- Internal real-sample smoke tests passed on sample02 and sample03.

## Must Pass Before GitHub Release

- Run:

```powershell
python tests/run_min_regression.py
```

- Confirm generated formal files are exactly:

```text
评价洞察到经营动作报告.html
评价洞察到经营动作报告.md
```

- Confirm no real raw exports are committed.
- Confirm `tests/_tmp/` is not committed.
- Confirm public screenshots do not expose buyer nicknames, product links, or shop names.
- Confirm README says `v1.0.0`.

## Formal Release Boundary

This release can be called `v1.0.0` because:

- real internal sample02 and sample03 smoke tests passed
- synthetic minimal regression passed
- public example data is synthetic or sanitized
- report output boundaries are documented
- heuristic limitations are stated in README and quality scorecard

Keep the following as post-release improvement items:

- fresh install test outside the original author environment
- broader category regression
- better category-aware theme clustering
- clearer evidence deduplication across merged themes

