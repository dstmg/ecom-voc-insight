# ecom-voc-insight

电商评价与问大家洞察 Skill：把电商评论、追评、问大家导出表转换成一份可交付的经营动作报告。

它不是普通词频统计工具，而是把 VOC 证据继续落到：

- 主图第一屏应该证明什么
- 详情页应该补哪些解释
- 客服 FAQ 应该提前回答什么
- 产品或包装下一轮应该优先改什么

当前版本：`v0.2-alpha`

## Status

This is an alpha package.

It has passed local smoke tests on real internal samples and one synthetic minimal regression case, but it is not yet a stable public release.

## What It Generates

Formal output is fixed to two files:

```text
评价洞察Skill-正式输出/
├── 评价洞察到经营动作报告.html
└── 评价洞察到经营动作报告.md
```

The HTML report includes:

1. Dashboard overview
2. Evidence credibility
3. Decision chain
4. Summary conclusions
5. Sample coverage
6. VOC themes and opportunity scoring
7. Original VOC evidence
8. Action matrix
9. Main-image brief
10. Detail-page brief
11. Customer-service FAQ
12. Product improvement roadmap

## Inputs

Supported first:

- 店透视-style `.xlsx` review exports
- 店透视-style `.xlsx` 问大家 exports

Review export fields used when available:

- `SKU`
- `评价类型`
- `初评`
- `追评`
- `晒图/视频`
- `初评时间`
- `旺旺号`
- `有用`

Q&A export fields used when available:

- `问题`
- `问答`
- `时间`
- `昵称`

Missing shop names, product titles, product URLs, and Q&A files are allowed. The report will state the data boundary instead of inventing missing context.

## Usage

Run the wrapper script:

```powershell
python scripts/run_ecom_voc_insight.py --raw-dir "<raw-export-folder>" --work-dir "<work-output-folder>"
```

Example:

```powershell
python scripts/run_ecom_voc_insight.py --raw-dir ".\examples\raw_exports" --work-dir ".\out\sample"
```

## Minimal Regression Test

The test creates synthetic review and Q&A `.xlsx` files, runs the full workflow, and checks the output contract.

```powershell
python tests/run_min_regression.py
```

Expected result:

- wrapper exits successfully
- formal output directory contains exactly the HTML and Markdown report
- HTML title is correct
- Dashboard and keyword cloud exist
- no public-content planning phrase such as `适合公众号截图` appears

## Data Compliance

Do not publish raw exports from real shops or buyers.

Before sharing examples publicly:

- remove buyer nicknames
- replace product IDs with fake IDs
- remove shop names and product links
- avoid copying real long review text
- use synthetic or heavily rewritten sample text

See [DISCLAIMER.md](DISCLAIMER.md).

## License

MIT. See [LICENSE](LICENSE).

