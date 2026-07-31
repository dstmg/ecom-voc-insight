# Publishing Checklist

Recommended release label: `v0.2-alpha`.

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

## Must Pass Before GitHub Upload

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
- Confirm README still says `v0.2-alpha`, not stable release.

## Conditions For Calling It A Stable Formal Version

Do not call this `v1.0` or stable formal release until:

- A fresh install test passes outside the original project folder.
- At least 3-5 different categories have passed regression.
- Example data is fully synthetic or sanitized.
- The theme clustering issue has been improved or clearly documented.
- A user other than the author can follow the README and generate a report.

