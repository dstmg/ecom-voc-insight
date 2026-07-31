---
name: ecom-voc-insight
description: Generate ecommerce VOC insight reports from review and Q&A exports. Use when the user provides Taobao/Tmall/Pinduoduo/JD ecommerce review files, buyer-show/comment exports, negative-review tables, or 问大家/问答 exports and wants an HTML/Markdown report that turns VOC evidence into main-image actions, detail-page actions, customer-service FAQ, and product improvement priorities. Do not use for writing public WeChat articles, scraping platforms, generic sentiment summaries, or main-image generation without review/Q&A data.
---

# 电商腿毛哥 · 评价与问大家洞察 Skill

Use this skill to turn ecommerce review and 问大家 exports into one evidence-backed operating report.

## Workflow

1. Confirm the user has provided a folder containing review exports and, if available, 问大家 exports.
2. Read `references/input_contract.md` if field support, missing files, or pairing rules are unclear.
3. Run the bundled wrapper script:

```powershell
python scripts/run_ecom_voc_insight.py --raw-dir "<原始导出目录>" --work-dir "<输出工作目录>"
```

The wrapper creates:

```text
<work-dir>/
├── 01-待清洗/
├── 02-已清洗/
├── 评价洞察主题计数.json
├── 评价洞察报告-初版.md
└── 评价洞察Skill-正式输出/
    ├── 评价洞察到经营动作报告.html
    └── 评价洞察到经营动作报告.md
```

Only the two files in `评价洞察Skill-正式输出/` are formal deliverables.

## Output Rules

- Keep review and 问大家 denominators separate, then merge insights into one operating decision chain.
- Do not invent shop names, product titles, links, rankings, sales, category certainty, or industry claims.
- If 问大家 is missing for a product, report it as `0问` and avoid pretending purchase-before concerns are complete.
- If shop name, title, or URL is missing, state the data boundary rather than fabricating context.
- Keep public article writing outside this skill. This skill outputs the report evidence, not a WeChat article.
- Read `references/output_contract.md` before changing deliverable filenames or report sections.
- Read `references/report_quality.md` before visually revising the HTML report.

## Scripts

- `scripts/run_ecom_voc_insight.py`: one-command workflow.
- `scripts/prepare_review_insight_sample.py`: normalize raw exports.
- `scripts/analyze_review_insight_sample.py`: build theme counts and evidence.
- `scripts/package_review_insight_deliverables.py`: generate formal HTML and Markdown.

## Validation

Before calling the skill ready for reuse, run at least one real sample and check:

- the wrapper exits successfully
- formal output directory contains only the HTML and MD deliverables
- HTML title is `评价与问大家洞察到经营动作报告`
- first-screen Dashboard has non-empty metrics and keyword cloud
- no phrase like `适合公众号截图` appears in the HTML
- no formal conclusion claims unsupported category, shop, or ranking information

