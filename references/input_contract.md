# Input Contract

This skill expects file-backed ecommerce VOC data.

## Supported Inputs

- `.xlsx` or `.csv` review exports containing review text, follow-up text, SKU, rating type, publish time, media flags, buyer name, and useful count when available.
- `.xlsx` or `.csv` 问大家 / Q&A exports containing questions and answers.
- Optional product title, product URL, shop name, and item ID.

Current scripts are calibrated on 店透视 exports. Other formats are allowed only when fields can be mapped into the standard schema.

## Standard Schema

Cleaned rows should become:

| field | meaning |
|---|---|
| sample_id | product sample id |
| product_label | local sample label |
| item_id | product/item id if available |
| shop_name | optional shop name |
| product_title | optional product title |
| product_url | optional product link |
| sku | SKU/spec text |
| content_type | `review` or `question_answer` |
| rating_type | 好评/中评/差评 when available |
| content | initial review or question |
| append_content | follow-up review or answer |
| has_image | media flag |
| has_video | media flag |
| publish_time | publication time |
| source_file | source filename |
| source_row | source row number |
| buyer_name | buyer nickname if present; remove before public samples |
| helpful_count | useful/helpful count if present |

## Missing Data Rules

- Missing 问大家: keep the product in sample coverage and show `0问`; do not infer purchase-before concerns from nothing.
- Missing shop name/title/link: state the data boundary; do not invent context.
- Missing item ID: pair by export timing and sample order, then label the uncertainty.
- Duplicated generic reviews: preserve enough evidence for traceability but avoid treating low-information text as high-quality insight.

## Pairing Rule

When multiple review and Q&A files are present, pair by item ID when available. If item ID is missing, pair by export timing and document the limitation.

