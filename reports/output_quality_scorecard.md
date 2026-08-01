# Output Quality Scorecard

Status: v1.0.0 first public release.

## Smoke Evidence

| case | input | result |
|---|---|---|
| sample02 | 3 products, 950 reviews, 115 Q&A rows | pass |
| sample03 | 3 products, 891 reviews, 178 Q&A rows | pass |
| synthetic minimal fixture | 2 products, 5 reviews, 3 Q&A rows | pass |

## Required Assertions

| assertion | status |
|---|---|
| wrapper can generate cleaned data, theme JSON, HTML, and MD | pass on sample02 package regression |
| formal output directory contains only HTML and MD | pass on sample02 and sample03 |
| HTML title is `评价与问大家洞察到经营动作报告` | pass |
| first-screen Dashboard has metrics and keyword cloud | pass |
| report does not contain `适合公众号截图` | pass |
| one displayed opportunity count does not exceed total denominator | fixed and smoke checked |
| examples are sanitized before GitHub publication | pass for synthetic minimal fixture |

## Package Regression

Command tested:

```powershell
python scripts/run_ecom_voc_insight.py --raw-dir "<sample02 raw export dir>" --work-dir "<sample02 skill-package-regression-v1.0.0>"
```

Result:

- 3 products
- 950 reviews
- 115 Q&A rows
- 1065 valid texts
- formal files: `评价洞察到经营动作报告.html`, `评价洞察到经营动作报告.md`

## Synthetic Minimal Regression

Command tested:

```powershell
python tests/run_min_regression.py
```

Result:

- creates synthetic `.xlsx` review and Q&A exports
- runs the full wrapper workflow
- validates formal output file contract
- validates required HTML sections
- validates `适合公众号截图` does not leak into the report
- validates synthetic buyer nicknames do not leak into the report

## Known Risks

- Theme clustering still uses heuristic词表 and may need category-context correction.
- Evidence counts are capped for display but not fully deduplicated by `evidence_id` across merged themes.
- Fresh external install testing remains a post-release hardening item.
