from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


THEMES = {
    "使用效果与结果达成": ["好用", "成功", "零失误", "拉丝", "膨胀", "发酵", "效果", "成型", "失败", "塌", "不成功", "做出来"],
    "口感味道与香味": ["口感", "味道", "香", "好吃", "不好吃", "怪味", "异味", "甜", "筋道", "松软", "难吃"],
    "配料成分与安全": ["配料", "成分", "添加", "无添加", "食品级", "安全", "健康", "营养", "过敏", "蛋白质"],
    "日期新鲜与保存": ["日期", "新鲜", "保质期", "临期", "过期", "保存", "受潮", "结块", "梅雨", "冷冻", "密封"],
    "包装破损与漏粉": ["包装", "破", "漏", "撒", "压", "袋", "封口", "快递", "物流", "损坏", "漏粉"],
    "规格克重与数量": ["规格", "克", "kg", "斤", "重量", "少", "多", "一袋", "小包装", "大包装", "分装", "数量"],
    "尺寸规格选择": ["尺寸", "规格", "几L", "几升", "5L", "4L", "6L", "升", "买大", "买小", "大小", "合适", "型号", "大了", "小了", "英寸", "cm"],
    "厚度硬挺与变形": ["厚", "薄", "软", "软趴", "硬", "硬挺", "变形", "材质", "塌", "边缘", "加厚", "结实"],
    "免洗省事与清洁": ["省事", "方便", "免洗", "不用刷", "好清理", "干净", "脏", "清洗", "刷锅", "刷盘", "懒人"],
    "耐高温安全异味": ["耐高温", "高温", "食品级", "安全", "异味", "油味", "燃烧", "着火", "有毒", "健康"],
    "数量包装与破损": ["数量", "少一个", "差一个", "个数", "一包", "包装", "破", "压", "漏发", "缺"],
    "价格性价比复购": ["价格", "性价比", "实惠", "便宜", "划算", "回购", "下次", "值得", "常备"],
    "烹饪使用场景": ["红薯", "鸡翅", "蛋挞", "烤肉", "烤鱼", "烤", "蛋糕", "空气炸锅", "食物"],
    "烘焙使用场景": ["面包", "吐司", "馒头", "包子", "饺子", "馄饨", "披萨", "蛋糕", "面条", "面包机", "烘焙"],
}

QUESTION_THEMES = {
    "保存与新鲜度": ["保存", "新鲜", "保质期", "临期", "日期", "过期", "冷冻", "受潮", "梅雨", "密封"],
    "配料和成分": ["配料", "成分", "添加", "无添加", "蛋白质", "营养", "安全"],
    "能做什么": ["做", "面包", "馒头", "包子", "饺子", "馄饨", "披萨", "蛋糕", "面条"],
    "好不好用": ["好用", "怎么样", "推荐", "值得", "成功", "失败"],
    "规格怎么买": ["规格", "克", "kg", "斤", "几袋", "重量", "小包装", "大包装"],
    "怎么选尺寸": ["尺寸", "规格", "几L", "几升", "5L", "4L", "6L", "升", "型号", "英寸", "cm", "用哪个"],
    "厚不厚会不会软": ["厚", "薄", "软", "软趴", "硬", "变形", "材质", "加厚"],
    "安全耐高温": ["耐高温", "高温", "食品级", "安全", "异味", "油味", "燃烧", "着火", "有毒"],
    "数量是否准确": ["数量", "少", "差一个", "几个", "多少个", "一包"],
    "是否推荐购买": ["推荐", "值得", "好用", "正品", "购买"],
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def text_of(row: dict[str, str]) -> str:
    return f"{row.get('content', '')}\n{row.get('append_content', '')}".strip()


def match_themes(rows: list[dict[str, str]], themes: dict[str, list[str]]) -> dict[str, dict[str, object]]:
    stats: dict[str, dict[str, object]] = {}
    for theme, keywords in themes.items():
        hits = []
        examples = []
        for row in rows:
            text = text_of(row)
            if not text:
                continue
            matched = [kw for kw in keywords if kw.lower() in text.lower()]
            if not matched:
                continue
            hits.append(row)
            if len(examples) < 5:
                examples.append(
                    {
                        "evidence_id": f"{row.get('sample_id')}:{row.get('source_row')}",
                        "item_id": row.get("item_id", ""),
                        "content_type": row.get("content_type", ""),
                        "rating_type": row.get("rating_type", ""),
                        "text": text.replace("\n", " ")[:180],
                        "keywords": matched[:5],
                    }
                )
        stats[theme] = {
            "count": len(hits),
            "share": round(len(hits) / max(len(rows), 1) * 100, 1),
            "examples": examples,
        }
    return dict(sorted(stats.items(), key=lambda item: item[1]["count"], reverse=True))


def top_values(rows: list[dict[str, str]], key: str, limit: int = 20) -> list[tuple[str, int]]:
    counter = Counter(row.get(key, "") or "未知" for row in rows)
    return counter.most_common(limit)


def detect_category(review_rows: list[dict[str, str]], question_rows: list[dict[str, str]]) -> dict[str, object]:
    text = " ".join(
        [row.get("sku", "") for row in review_rows[:300]]
        + [text_of(row) for row in review_rows[:300]]
        + [text_of(row) for row in question_rows[:120]]
    )
    rules = [
        ("食品/烘焙", ["面包", "面粉", "小麦粉", "烘焙", "酵母", "高筋", "吐司", "馒头", "饺子", "馄饨"]),
        ("家居百货", ["空气炸锅", "锡纸", "收纳", "置物", "厨房", "家用", "一次性", "尺寸", "材质"]),
        ("服饰", ["尺码", "版型", "显瘦", "面料", "色差", "洗后", "上身", "穿着", "衣服", "裤子"]),
        ("小家电", ["噪音", "功率", "清洁", "安装", "电机", "续航", "充电", "加热", "档位"]),
        ("美妆个护", ["肤质", "敏感", "刺激", "成分", "保湿", "控油", "香味", "头发", "洗发", "护肤"]),
        ("3C数码", ["兼容", "发热", "续航", "蓝牙", "接口", "稳定", "卡顿", "屏幕", "充电"]),
    ]
    scored = []
    for name, words in rules:
        count = sum(text.count(word) for word in words)
        if count:
            scored.append((name, count, [word for word in words if word in text][:8]))
    if not scored:
        return {
            "category": "类目不确定",
            "confidence": "low",
            "evidence_words": [],
            "fallback": "使用通用电商 VOC 结构",
        }
    scored.sort(key=lambda item: item[1], reverse=True)
    top = scored[0]
    confidence = "high" if top[1] >= 20 else "medium"
    return {
        "category": top[0],
        "confidence": confidence,
        "evidence_words": top[2],
        "fallback": "",
    }


def md_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    header = rows[0]
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    for row in rows[1:]:
        out.append("| " + " | ".join(str(v).replace("\n", " ") for v in row) + " |")
    return "\n".join(out)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: analyze_review_insight_sample.py <standard_csv> <output_dir>", file=sys.stderr)
        return 2

    input_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = [row for row in read_csv(input_path) if text_of(row)]
    review_rows = [row for row in rows if row.get("content_type") == "review"]
    question_rows = [row for row in rows if row.get("content_type") == "question_answer"]
    category = detect_category(review_rows, question_rows)
    sku_text = " ".join(row.get("sku", "") for row in review_rows[:200])
    is_baking = category["category"] == "食品/烘焙"
    theme_stats = match_themes(review_rows, THEMES)
    question_stats = match_themes(question_rows, QUESTION_THEMES)

    sample_rows = []
    for sample_id, count in top_values(rows, "sample_id", 20):
        item_ids = sorted({row.get("item_id", "") for row in rows if row.get("sample_id") == sample_id})
        reviews = sum(1 for row in review_rows if row.get("sample_id") == sample_id)
        questions = sum(1 for row in question_rows if row.get("sample_id") == sample_id)
        sample_rows.append([sample_id, ",".join(item_ids), str(reviews), str(questions), str(count)])

    rating_rows = [[label, str(count)] for label, count in top_values(review_rows, "rating_type", 10)]
    theme_rows = [[name, str(data["count"]), f"{data['share']}%"] for name, data in theme_stats.items()]
    q_theme_rows = [[name, str(data["count"]), f"{data['share']}%"] for name, data in question_stats.items()]

    result = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input_path": str(input_path),
        "total_valid_rows": len(rows),
        "review_rows": len(review_rows),
        "question_answer_rows": len(question_rows),
        "category": category,
        "samples": sample_rows,
        "ratings": rating_rows,
        "review_themes": theme_stats,
        "question_themes": question_stats,
    }
    (output_dir / "评价洞察主题计数.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    strongest = list(theme_stats.items())[:4]
    q_strongest = list(question_stats.items())[:3]

    lines = [
        "# 评价洞察报告-初版",
        "",
        f"生成时间：{result['generated_at']}",
        "",
        "## 类目判断",
        "",
        f"- 判断类目：{category['category']}",
        f"- 置信度：{category['confidence']}",
        f"- 判断依据：{', '.join(category['evidence_words']) if category['evidence_words'] else '无明确类目词，按通用电商 VOC 结构处理'}",
        "",
        "## 数据口径",
        "",
        f"- 有效文本总数：{len(rows)}",
        f"- 评价：{len(review_rows)}",
        f"- 问大家：{len(question_rows)}",
        "- 店铺名、商品标题、商品链接：原始导出未提供，本轮先按商品样本编号和问大家商品 ID 分组。",
        "- `晒图/视频` 在原始表中是合并字段，本轮只能判断是否存在媒体，不能可靠区分图片和视频。",
        "",
        "## 样本分布",
        "",
        md_table([["样本", "商品ID", "评价数", "问大家数", "总记录"]] + sample_rows),
        "",
        "## 评价类型",
        "",
        md_table([["评价类型", "数量"]] + rating_rows),
        "",
        "## 评论里最明显的主题",
        "",
        md_table([["主题", "命中记录", "占评价比例"]] + theme_rows),
        "",
        "## 问大家里的购买前顾虑",
        "",
        md_table([["顾虑", "命中记录", "占问大家比例"]] + q_theme_rows),
        "",
        "## 用户顾虑合并洞察",
        "",
        "统计口径保持分开：评价、问大家、中差评分别计算；经营判断合并到同一个用户顾虑主题下，最后统一落到主图、详情页、客服和产品动作。",
        "",
        *(
            [
                "### 主题：能不能做出稳定结果",
                "",
                "- 评价证据：烘焙使用场景、口感味道、使用效果是高频主题，说明用户买的是成品成功率，不只是原料。",
                "- 问大家证据：大量问题集中在“能做什么”，说明下单前需要明确适用边界。",
                "- 主图动作：展示真实成品、切面、拉丝、膨胀效果。",
                "- 详情页动作：补配方比例、适用工具、常见失败原因。",
                "- 客服动作：准备“能不能做馄饨/馒头/披萨/面包机”等快捷回答。",
                "",
                "### 主题：新鲜度和保存方式",
                "",
                "- 评价证据：日期新鲜、包装、保存相关内容进入高频主题。",
                "- 问大家证据：保存与新鲜度问题直接出现，尤其是梅雨季保存。",
                "- 主图动作：突出日期新鲜、密封包装。",
                "- 详情页动作：补开封后保存方法、梅雨季保存建议。",
                "- 产品动作：评估分装、小包装、封口设计是否有优化空间。",
                "",
                "### 主题：配料成分和使用边界",
                "",
                "- 评价证据：口感和使用场景反馈可以证明产品适合哪些烘焙结果。",
                "- 问大家证据：配料表、能做什么是购买前顾虑。",
                "- 详情页动作：前置配料表和适用/不适用做法。",
                "- 客服动作：遇到跨用途问题时，不要泛泛说都可以，要给明确边界。",
            ]
            if is_baking
            else [
                "### 主题：规格选择和使用稳定性",
                "",
                "- 评价证据：尺寸、厚度、变形和使用场景共同影响购买后满意度。",
                "- 问大家证据：下单前会反复确认规格、厚度、是否适用。",
                "- 主图动作：把规格选择和稳定性证明前置。",
                "- 详情页动作：补规格选择表、适用场景和 FAQ。",
                "- 客服动作：准备按容量/尺寸推荐的快捷回答。",
            ]
        ),
        "",
        "## 初步业务判断",
        "",
        *(
            [
                "1. 这类产品的购买前阻力集中在保存、新鲜度、配料成分和适用场景。详情页不能只堆“高筋/面包粉”，要回答能做什么、怎么保存、日期新不新鲜。",
                "2. 评论里的高价值信任点集中在做面包的成功率、拉丝/膨胀效果、口感香味和复购。主图和详情页要把“做出来的结果”可视化，而不是只展示包装袋。",
                "3. 对烘焙新手来说，用户买的不是一袋粉，而是“少失败、容易成功”。页面应补配方比例、适用工具、常见失败原因和保存方式。",
                "4. 问大家暴露出的风险点适合直接变成 FAQ：梅雨季怎么保存、能不能做馄饨/馒头/披萨、配料表是什么、好不好用。",
            ]
            if is_baking
            else [
                "1. 这类产品的购买前最大问题不是“要不要买”，而是“买哪个尺寸/规格才不会错”。主图和详情页需要把锅容量、盘尺寸、适用场景做成一眼能判断的规格选择模块。",
                "2. 评论里的信任关键词集中在厚度、硬挺、不变形、边缘、材质。单纯写“加厚”不够，最好用对比图或承重/捏压/装食物场景证明。",
                "3. 真正的使用利益是省事、免洗、不用刷锅、保持空气炸锅干净。这比“食品级铝箔”更接近用户的即时动机。",
                "4. 问大家暴露出的风险点包括尺寸选错、太薄、数量是否足、是否有异味、能不能耐高温。它们适合变成详情页 FAQ 和主图角标。",
            ]
        ),
        "",
        "## 可转成主图/详情页的表达",
        "",
        *(
            [
                "- 主图核心利益：新手也能做出稳定蓬松、拉丝、有香味的面包。",
                "- 信任证明：晒真实成品、面包切面、拉丝/膨胀效果、复购评价。",
                "- 规格辅助：500g/2.5kg/5kg 对应家庭尝试、稳定复购、长期烘焙囤货。",
                "- 购买顾虑回应：日期新鲜、密封保存、梅雨季保存方法、配料表清楚、适用做法边界。",
            ]
            if is_baking
            else [
                "- 主图核心利益：空气炸锅免洗，烤完直接丢，不用刷锅。",
                "- 信任证明：加厚硬挺，不易软塌；装油汤、烤红薯、鸡翅也不容易漏。",
                "- 规格辅助：2-3L、3-4L、4-5L、5L 以上分别对应几英寸/几厘米。",
                "- 购买顾虑回应：无异味、耐高温、数量足、边缘不割手、到手不压变形。",
            ]
        ),
        "",
        "## 典型证据",
        "",
    ]

    for name, data in strongest:
        lines.append(f"### {name}")
        for ex in data["examples"][:3]:
            lines.append(f"- `{ex['evidence_id']}`：{ex['text']}")
        lines.append("")

    for name, data in q_strongest:
        lines.append(f"### 问大家：{name}")
        for ex in data["examples"][:3]:
            lines.append(f"- `{ex['evidence_id']}`：{ex['text']}")
        lines.append("")

    (output_dir / "评价洞察报告-初版.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output_dir), "rows": len(rows), "reviews": len(review_rows), "questions": len(question_rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
