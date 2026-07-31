from __future__ import annotations

import argparse
import csv
import html
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def text_of(row: dict[str, str]) -> str:
    return f"{row.get('content', '')} {row.get('append_content', '')}".strip()


def pct(n: int, total: int) -> str:
    return f"{round(n / max(total, 1) * 100, 1)}%"


def top_theme_items(themes: dict[str, dict], limit: int = 6) -> list[dict[str, object]]:
    items = []
    for name, data in themes.items():
        items.append(
            {
                "theme": name,
                "count": int(data.get("count", 0) or 0),
                "share": data.get("share", 0),
                "examples": data.get("examples", []) or [],
            }
        )
    return sorted(items, key=lambda item: item["count"], reverse=True)[:limit]


def analysis_scope(_: dict) -> str:
    return "按输入数据动态归纳"


def theme_actions(theme: str) -> dict[str, str]:
    if any(key in theme for key in ["保存", "新鲜", "日期", "包装", "密封", "破损", "漏"]):
        return {
            "opportunity": "把保存、到手状态和包装可靠性前置，降低下单前的不确定",
            "main_image": "主图用角标或局部图证明包装、密封、到手状态，不只展示产品本体",
            "detail_page": "详情页补充保存/收纳/到手检查/包装保护说明",
            "faq": "回答“怎么保存、到手会不会坏、包装是否可靠”",
            "product": "评估包装结构、密封方式、分装规格或运输保护是否需要优化",
        }
    if any(key in theme for key in ["配料", "成分", "安全", "营养", "材质", "异味", "耐高温", "肤质", "兼容"]):
        return {
            "opportunity": "把安全信任和适用边界说清楚",
            "main_image": "主图露出关键材质/成分/安全证明/适用边界",
            "detail_page": "详情页前置材质、成分、参数、适用/不适用场景",
            "faq": "回答“安全吗、适合我吗、能不能用于某个场景”",
            "product": "检查包装、说明书和详情页是否能让用户一眼看到安全依据",
        }
    if any(key in theme for key in ["能做", "好用", "效果", "结果", "口感", "味道", "成功", "场景", "使用"]):
        return {
            "opportunity": "把用户买到的“使用结果”可视化",
            "main_image": "用真实结果图、使用前后对比或场景图证明效果",
            "detail_page": "补充使用步骤、适用场景、常见失败原因和结果证明",
            "faq": "回答“能不能解决我的具体问题，怎么用才不出错”",
            "product": "围绕用户成功率沉淀使用说明、工具搭配或新手指引",
        }
    if any(key in theme for key in ["规格", "克重", "数量", "斤", "kg", "尺寸", "大小", "型号", "容量", "性价比", "复购"]):
        return {
            "opportunity": "把规格选择和购买成本讲清楚",
            "main_image": "主图用规格对照、数量说明或使用场景帮助用户选对",
            "detail_page": "详情页补充规格选择表、适配场景和购买建议",
            "faq": "回答“买哪个规格、够不够用、适不适合我的场景”",
            "product": "评估规格组合、套装数量和价格带是否需要调整",
        }
    return {
        "opportunity": "把高频顾虑翻译成下单前能看懂的证明",
        "main_image": "主图第一屏回应该顾虑，用场景图或对比图证明",
        "detail_page": "详情页补充解释模块、规格选择和使用边界",
        "faq": "客服准备对应快捷话术，提前解除咨询阻力",
        "product": "把反复出现的问题纳入下一轮产品或包装优化",
    }


def business_cluster(theme: str) -> str:
    if any(key in theme for key in ["能做", "好用", "效果", "结果", "口感", "味道", "成功", "场景", "使用", "烘焙"]):
        return "使用结果是否稳定"
    if any(key in theme for key in ["保存", "新鲜", "日期", "包装", "破损", "漏", "密封"]):
        return "保存包装是否可靠"
    if any(key in theme for key in ["配料", "成分", "安全", "营养", "材质", "异味", "耐高温", "肤质", "兼容"]):
        return "安全信任与适用边界"
    if any(key in theme for key in ["规格", "克重", "数量", "斤", "kg", "尺寸", "大小", "型号", "容量", "性价比", "复购"]):
        return "规格选择与购买成本"
    return theme


def build_opportunities(data: dict) -> list[dict[str, object]]:
    review_total = int(data.get("review_rows", 0) or 0)
    question_total = int(data.get("question_answer_rows", 0) or 0)
    review_top = top_theme_items(data.get("review_themes", {}), 8)
    question_top = top_theme_items(data.get("question_themes", {}), 8)

    merged: dict[str, dict[str, object]] = {}
    for item in review_top:
        key = business_cluster(str(item["theme"]))
        merged.setdefault(key, {"theme": key, "source_themes": [], "review_count": 0, "question_count": 0, "examples": []})
        merged[key]["source_themes"].append(item["theme"])
        merged[key]["review_count"] = int(merged[key]["review_count"]) + int(item["count"])
        merged[key]["examples"] = (list(merged[key].get("examples", [])) + list(item["examples"]))[:4]
    for item in question_top:
        key = business_cluster(str(item["theme"]))
        merged.setdefault(key, {"theme": key, "source_themes": [], "review_count": 0, "question_count": 0, "examples": []})
        merged[key]["source_themes"].append(item["theme"])
        merged[key]["question_count"] = int(merged[key]["question_count"]) + int(item["count"])
        merged[key]["examples"] = (list(merged[key].get("examples", [])) + list(item["examples"]))[:3]

    opportunities = []
    for item in merged.values():
        review_count = min(int(item["review_count"]), review_total)
        question_count = min(int(item["question_count"]), question_total)
        review_freq = review_count / max(review_total, 1)
        question_freq = question_count / max(question_total, 1)
        frequency_score = min(5, max(1, round(max(review_freq, question_freq) * 5)))
        conversion_score = 5 if question_count else 3
        evidence_score = 5 if review_count and question_count else 4 if review_count > 100 or question_count > 10 else 3
        solve_cost = 2 if question_count else 3
        priority_score = frequency_score + conversion_score + evidence_score - solve_cost
        actions = theme_actions(str(item["theme"]))
        opportunities.append(
            {
                "rank": 0,
                "theme": item["theme"],
                "source_themes": sorted(set(map(str, item.get("source_themes", [])))),
                "review_count": review_count,
                "review_share": pct(review_count, review_total),
                "question_count": question_count,
                "question_share": pct(question_count, question_total),
                "opportunity": actions["opportunity"],
                "frequency_score": frequency_score,
                "conversion_score": conversion_score,
                "evidence_score": evidence_score,
                "solve_cost": solve_cost,
                "priority_score": priority_score,
                "main_image": actions["main_image"],
                "detail_page": actions["detail_page"],
                "faq": actions["faq"],
                "product": actions["product"],
                "examples": item.get("examples", []),
            }
        )
    opportunities = sorted(opportunities, key=lambda item: (int(item["priority_score"]), int(item["question_count"]), int(item["review_count"])), reverse=True)
    for idx, item in enumerate(opportunities, start=1):
        item["rank"] = idx
    return opportunities[:8]


def build_evidence_index(data: dict) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen = set()
    for source_name, themes in [("review", data.get("review_themes", {})), ("question_answer", data.get("question_themes", {}))]:
        for theme, payload in themes.items():
            for ex in payload.get("examples", []) or []:
                evidence_id = ex.get("evidence_id") or f"{source_name}-{len(rows) + 1}"
                key = (source_name, theme, evidence_id, ex.get("text", ""))
                if key in seen:
                    continue
                seen.add(key)
                rows.append(
                    {
                        "evidence_id": evidence_id,
                        "content_type": source_name,
                        "sample_id": str(evidence_id).split(":")[0],
                        "item_id": ex.get("item_id", ""),
                        "theme": theme,
                        "rating_type": ex.get("rating_type", ""),
                        "evidence_text": ex.get("text", ""),
                        "keywords": "、".join(ex.get("keywords", []) or []),
                    }
                )
    return rows


def build_faq(opportunities: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for item in opportunities[:8]:
        examples = item.get("examples", []) or []
        question = examples[0].get("text", "") if examples else str(item["theme"])
        rows.append(
            {
                "用户问题/顾虑": question,
                "推荐回答": item["faq"],
                "触发场景": "问大家/客服咨询/详情页FAQ",
                "对应主题": item["theme"],
                "证据量": f"评价{item['review_count']}条，问大家{item['question_count']}条",
            }
        )
    return rows


def write_main_image_brief(path: Path, data: dict, opportunities: list[dict[str, object]]) -> None:
    scope = analysis_scope(data)
    lines = [
        "# 主图表达Brief",
        "",
        f"- 分析口径：{scope}",
        f"- 样本口径：评价 {data.get('review_rows', 0)} 条，问大家 {data.get('question_answer_rows', 0)} 条",
        "- 使用方式：交给主图拆解/生图 Skill，作为卖点、场景、角标和禁用表达输入。",
        "",
        "## 主图优先表达顺序",
        "",
    ]
    for item in opportunities[:5]:
        lines += [
            f"### {item['rank']}. {item['theme']}",
            "",
            f"- 机会判断：{item['opportunity']}",
            f"- 主图动作：{item['main_image']}",
            f"- 证据量：评价 {item['review_count']} 条（{item['review_share']}），问大家 {item['question_count']} 条（{item['question_share']}）",
            "- 推荐画面：产品主体放大 + 使用结果/场景证明 + 一个明确角标，不要只堆参数。",
            "- 禁用表达：不要写无法被当前样本证明的销量、全网第一、绝对功效。",
            "",
        ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_detail_brief(path: Path, data: dict, opportunities: list[dict[str, object]]) -> None:
    lines = [
        "# 详情页优化Brief",
        "",
        "详情页不是把评价总结贴上去，而是把用户下单前的疑问拆成可验证模块。",
        "",
        "## 建议模块顺序",
        "",
    ]
    module_names = ["核心结论", "适用场景", "规格/成分/材质说明", "使用方法", "风险解除FAQ", "真实评价证据"]
    for idx, name in enumerate(module_names, start=1):
        lines.append(f"{idx}. {name}")
    lines += ["", "## 具体优化项", ""]
    for item in opportunities[:6]:
        lines += [
            f"### {item['theme']}",
            "",
            f"- 详情页动作：{item['detail_page']}",
            f"- 对应顾虑：{item['opportunity']}",
            f"- 证据口径：评价 {item['review_count']} 条，问大家 {item['question_count']} 条",
            "",
        ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_md_report(path: Path, data: dict, opportunities: list[dict[str, object]], evidence_rows: list[dict[str, object]]) -> None:
    scope = analysis_scope(data)
    sample_count = len(data.get("samples", []) or [])
    lines = [
        "# 评价与问大家洞察到经营动作报告",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 0. 证据可信度",
        "",
        f"- 分析口径：{scope}",
        f"- 商品样本：{sample_count} 个",
        f"- 有效评价：{data.get('review_rows', 0)} 条",
        f"- 问大家：{data.get('question_answer_rows', 0)} 条",
        f"- 证据索引：{len(evidence_rows)} 条典型原文证据",
        "- 限制说明：如果原始导出缺少店铺名、商品标题或链接，本报告只按样本编号和商品ID判断，不冒充完整竞品调研。",
        "",
        "## 1. 结论总览",
        "",
    ]
    for item in opportunities[:3]:
        lines.append(f"- {item['theme']}：{item['opportunity']}，优先级 {item['priority_score']}。")
    lines += ["", "## 2. 样本覆盖", ""]
    lines.append("| 样本 | 商品ID | 评价数 | 问大家数 | 总记录 |")
    lines.append("|---|---|---:|---:|---:|")
    for row in data.get("samples", []) or []:
        lines.append("| " + " | ".join(map(str, row[:5])) + " |")
    lines += ["", "## 3. 评价洞察", ""]
    for item in top_theme_items(data.get("review_themes", {}), 6):
        example = item["examples"][0]["text"] if item["examples"] else ""
        lines.append(f"- {item['theme']}：{item['count']} 条，占比 {item['share']}%。典型原文：{example}")
    lines += ["", "## 4. 问大家顾虑", ""]
    for item in top_theme_items(data.get("question_themes", {}), 6):
        example = item["examples"][0]["text"] if item["examples"] else ""
        lines.append(f"- {item['theme']}：{item['count']} 条，占比 {item['share']}%。典型原文：{example}")
    lines += ["", "## 5. 经营机会评分", ""]
    lines.append("| 排名 | 机会主题 | 评价证据 | 问大家证据 | 频次 | 转化影响 | 证据强度 | 解决成本 | 优先级 |")
    lines.append("|---:|---|---:|---:|---:|---:|---:|---:|---:|")
    for item in opportunities:
        lines.append(
            f"| {item['rank']} | {item['theme']} | {item['review_count']} | {item['question_count']} | {item['frequency_score']} | {item['conversion_score']} | {item['evidence_score']} | {item['solve_cost']} | {item['priority_score']} |"
        )
    lines += ["", "## 6. 主图动作", ""]
    for item in opportunities[:5]:
        lines.append(f"- {item['theme']}：{item['main_image']}")
    lines += ["", "## 7. 详情页动作", ""]
    for item in opportunities[:5]:
        lines.append(f"- {item['theme']}：{item['detail_page']}")
    lines += ["", "## 8. 客服FAQ", ""]
    for item in opportunities[:5]:
        lines.append(f"- {item['theme']}：{item['faq']}")
    lines += ["", "## 9. 产品改进路线图", ""]
    for item in opportunities[:5]:
        lines.append(f"- {item['theme']}：{item['product']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_cards(opportunities: list[dict[str, object]]) -> str:
    cards = []
    for item in opportunities[:4]:
        cards.append(
            f"""
            <article class="op-card">
              <div class="rank">#{esc(item['rank'])}</div>
              <h3>{esc(item['theme'])}</h3>
              <p>{esc(item['opportunity'])}</p>
              <div class="score"><span>优先级</span><strong>{esc(item['priority_score'])}</strong></div>
            </article>
            """
        )
    return "\n".join(cards)


def render_table(headers: list[str], rows: list[list[object]]) -> str:
    return (
        '<div class="table-wrap"><table><thead><tr>'
        + "".join(f"<th>{esc(h)}</th>" for h in headers)
        + "</tr></thead><tbody>"
        + "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in row) + "</tr>" for row in rows)
        + "</tbody></table></div>"
    )


def fmt_int(value: object) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def clamp_percent(value: float, floor: int = 8) -> int:
    return max(floor, min(100, round(value)))


def build_keyword_cloud(rows: list[dict[str, str]], data: dict, limit: int = 18) -> list[tuple[str, int]]:
    terms = [
        "质量好",
        "物流快",
        "包装好",
        "客服好",
        "性价比高",
        "好用",
        "推荐",
        "回购",
        "价格",
        "发货快",
        "外观",
        "质感",
        "做工",
        "尺寸",
        "规格",
        "材质",
        "厚度",
        "安全",
        "味道",
        "口感",
        "香味",
        "新鲜",
        "保存",
        "破损",
        "漏",
        "柔软",
        "硬挺",
        "耐用",
        "舒服",
        "清晰",
        "音质",
        "降噪",
        "麦克风",
        "耳罩",
        "久戴",
        "游戏",
        "脚步",
        "听声辨位",
        "不漏音",
        "沉浸",
        "科技感",
        "炫酷",
        "顺丰",
    ]
    stop_terms = {"克", "多", "大", "小", "好", "买", "用", "做", "个", "款", "不", "是"}
    counter: Counter[str] = Counter()
    for row in rows:
        text = " ".join([row.get("content", ""), row.get("append_content", ""), row.get("sku", "")])
        for term in terms:
            count = text.count(term)
            if count:
                counter[term] += count

    for section in ["review_themes", "question_themes"]:
        for payload in (data.get(section) or {}).values():
            for ex in payload.get("examples", []) or []:
                for keyword in ex.get("keywords", []) or []:
                    keyword = str(keyword).strip()
                    if len(keyword) > 1 and keyword not in stop_terms:
                        counter[keyword] += 1

    if not counter:
        for item in top_theme_items(data.get("review_themes", {}), limit):
            counter[str(item["theme"])] += int(item["count"])
        for item in top_theme_items(data.get("question_themes", {}), limit):
            counter[str(item["theme"])] += int(item["count"])

    return counter.most_common(limit)


def render_keyword_cloud(keyword_cloud: list[tuple[str, int]]) -> str:
    if not keyword_cloud:
        return '<div class="word-cloud-map"><strong class="cloud-core">暂无关键词<small>0</small></strong></div>'
    core_word, core_count = keyword_cloud[0]
    words = keyword_cloud[1:15]
    return (
        f'<div class="word-cloud-map"><strong class="cloud-core">{esc(core_word)}<small>{fmt_int(core_count)}</small></strong>'
        + "".join(
            f'<span class="wc wc-{idx}">{esc(word)}<small>{fmt_int(count)}</small></span>'
            for idx, (word, count) in enumerate(words, start=1)
        )
        + "</div>"
    )


def render_keyword_top10(keyword_cloud: list[tuple[str, int]]) -> str:
    if not keyword_cloud:
        return '<div class="bar-list"><div class="bar-label"><span>暂无关键词</span><strong>0</strong></div></div>'
    max_count = max([count for _, count in keyword_cloud[:10]] or [1])
    rows = []
    for word, count in keyword_cloud[:10]:
        width = clamp_percent(count / max_count * 100)
        rows.append(
            f"""
            <div class="bar-row keyword-row">
              <div class="bar-label"><span>{esc(word)}</span><strong>{fmt_int(count)}</strong></div>
              <div class="bar-track compact"><i style="--bar-width:{width}%"></i></div>
            </div>
            """
        )
    return "\n".join(rows)


def render_dashboard_hero(data: dict, opportunities: list[dict[str, object]]) -> str:
    review_total = int(data.get("review_rows", 0) or 0)
    question_total = int(data.get("question_answer_rows", 0) or 0)
    total = max(review_total + question_total, 1)
    review_deg = round(review_total / total * 360)
    review_share = round(review_total / total * 100)
    question_share = round(question_total / total * 100)
    sample_count = len(data.get("samples", []) or [])
    keyword_cloud = data.get("keyword_cloud", []) or []
    max_evidence = max([int(item["review_count"]) + int(item["question_count"]) for item in opportunities] or [1])

    focus_cards = []
    for item in opportunities[:3]:
        focus_cards.append(
            f"""
            <article class="focus-card">
              <div><span>#{esc(item['rank'])}</span><b>{esc(item['theme'])}</b></div>
              <p>{esc(item['opportunity'])}</p>
            </article>
            """
        )

    bars = []
    evidence_sorted = sorted(opportunities, key=lambda item: int(item["review_count"]) + int(item["question_count"]), reverse=True)
    for item in evidence_sorted[:5]:
        evidence_count = int(item["review_count"]) + int(item["question_count"])
        width = clamp_percent(evidence_count / max_evidence * 100)
        bars.append(
            f"""
            <div class="bar-row">
              <div class="bar-label"><span>{esc(item['theme'])}</span><strong>{fmt_int(evidence_count)}</strong></div>
              <div class="bar-track"><i style="--bar-width:{width}%"></i></div>
            </div>
            """
        )

    sample_rows = []
    for row in (data.get("samples", []) or [])[:4]:
        sample_rows.append(
            f"""
            <div class="sample-row">
              <b>{esc(row[0])}</b>
              <span>{esc(row[1])}</span>
              <em>{esc(row[2])}评 / {esc(row[3])}问</em>
            </div>
            """
        )

    return f"""
    <section class="hero">
      <div class="hero-story">
        <div class="eyebrow">电商腿毛哥 · 评价与问大家洞察 Skill</div>
        <h1>评价与问大家 Dashboard</h1>
        <p>把购买后评价和购买前顾虑合成一份经营动作报告，先看哪里最该改，再落到主图、详情页、客服FAQ和产品路线图。</p>
        <div class="hero-tags">
          <span>VOC 证据链</span>
          <span>经营动作输出</span>
          <span>正式交付报告</span>
        </div>
        <div class="hero-focus">
          <div class="focus-head">
            <b>本次优先动作</b>
            <span>先处理最影响成交判断的 3 个问题</span>
          </div>
          {"".join(focus_cards)}
        </div>
        <div class="hero-samples">
          <div class="focus-head">
            <b>样本来源</b>
            <span>{fmt_int(sample_count)} 个商品样本</span>
          </div>
          <div class="hero-sample-list">{"".join(sample_rows)}</div>
        </div>
        <div class="hero-note">
          <b>决策链</b>
          <span>评价洞察 → 问大家顾虑 → 经营机会 → 主图动作 → 详情页动作 → 客服FAQ → 产品改进路线图</span>
        </div>
      </div>
      <div class="dashboard-board">
        <div class="dashboard-title">
          <div>
            <span>评论分析 Dashboard</span>
            <strong>{fmt_int(total)} 条有效文本</strong>
          </div>
          <em>正式交付版</em>
        </div>
        <div class="metric-grid">
          <div class="metric-card"><span>评价证据</span><strong>{fmt_int(review_total)}</strong><small>购买后的真实反馈</small></div>
          <div class="metric-card"><span>问大家</span><strong>{fmt_int(question_total)}</strong><small>下单前的不确定</small></div>
          <div class="metric-card"><span>商品样本</span><strong>{fmt_int(sample_count)}</strong><small>按导出文件归并</small></div>
          <div class="metric-card"><span>经营机会</span><strong>{fmt_int(len(opportunities))}</strong><small>已映射到动作</small></div>
        </div>
        <div class="dashboard-visuals">
          <div class="dash-panel evidence-panel">
            <div class="panel-head"><b>证据结构</b><span>评价 / 问大家</span></div>
            <div class="donut-wrap">
              <div class="donut" style="--review-deg:{review_deg}deg"><span>{fmt_int(total)}<small>总文本</small></span></div>
              <div class="legend">
                <p><i class="review-dot"></i>评价 {review_share}%</p>
                <p><i class="question-dot"></i>问大家 {question_share}%</p>
              </div>
            </div>
          </div>
          <div class="dash-panel">
            <div class="panel-head"><b>经营机会 TOP5</b><span>按证据量排序</span></div>
            <div class="bar-list">{"".join(bars)}</div>
          </div>
        </div>
        <div class="dashboard-lower">
          <div class="dash-panel cloud-panel">
            <div class="panel-head"><b>关键词云</b><span>来自评价和问大家原文</span></div>
            {render_keyword_cloud(keyword_cloud)}
          </div>
          <div class="dash-panel keyword-panel">
            <div class="panel-head"><b>高频关键词 TOP10</b><span>按出现次数</span></div>
            <div class="bar-list">{render_keyword_top10(keyword_cloud)}</div>
          </div>
        </div>
      </div>
    </section>
    """


def render_delivery_chain() -> str:
    steps = [
        ("01", "评价证据", "购买后的真实反馈"),
        ("02", "问大家顾虑", "下单前的不确定"),
        ("03", "机会评分", "先改最影响转化的点"),
        ("04", "主图 Brief", "第一屏证明什么"),
        ("05", "详情页 Brief", "页面需要补什么"),
        ("06", "FAQ/路线图", "客服和产品继续执行"),
    ]
    return "\n".join(
        f"""
        <article class="chain-step">
          <span>{esc(index)}</span>
          <b>{esc(title)}</b>
          <small>{esc(desc)}</small>
        </article>
        """
        for index, title, desc in steps
    )


def render_output_assets() -> str:
    assets = [
        ("主图表达 Brief", "设计师 / 生图 Skill", "决定第一屏证明什么、怎么构图、写什么角标"),
        ("详情页优化 Brief", "运营 / 详情页 Skill", "决定详情页应该补哪些模块和解释"),
        ("客服 FAQ", "客服 / 客服机器人", "把问大家变成可回答的话术方向"),
        ("产品改进路线图", "运营 / 产品负责人", "把反复出现的问题排成可执行优先级"),
    ]
    return "\n".join(
        f"""
        <article class="asset-card">
          <div class="asset-type">{esc(name)}</div>
          <h3>{esc(user)}</h3>
          <p>{esc(value)}</p>
        </article>
        """
        for name, user, value in assets
    )


def render_product_roadmap(opportunities: list[dict[str, object]]) -> str:
    stages = ["立即修正", "下一轮优化", "持续验证"]
    cards = []
    for idx, item in enumerate(opportunities[:6]):
        stage = stages[0] if idx < 2 else stages[1] if idx < 4 else stages[2]
        cards.append(
            f"""
            <article class="roadmap-card">
              <div class="roadmap-top">
                <span>{esc(stage)}</span>
                <strong>#{esc(item['rank'])}</strong>
              </div>
              <h3>{esc(item['theme'])}</h3>
              <p>{esc(item['product'])}</p>
              <div class="roadmap-meta">
                <span>优先级 {esc(item['priority_score'])}</span>
                <span>评价 {esc(item['review_count'])} / 问大家 {esc(item['question_count'])}</span>
              </div>
            </article>
            """
        )
    return "\n".join(cards)


def render_voc_evidence(opportunities: list[dict[str, object]]) -> str:
    rows = []
    for item in opportunities[:4]:
        examples = item.get("examples", []) or []
        evidence = examples[0].get("text", "") if examples else "暂无典型原文"
        rows.append(
            [
                evidence,
                item["theme"],
                item["main_image"],
            ]
        )
    return render_table(["用户原声", "AI归纳的问题簇", "对应经营动作"], rows)


def render_main_image_brief(opportunities: list[dict[str, object]]) -> str:
    cards = []
    for item in opportunities[:4]:
        cards.append(
            f"""
            <article class="brief-card">
              <div class="brief-label">主图任务 #{esc(item['rank'])}</div>
              <h3>{esc(item['theme'])}</h3>
              <ul>
                <li><b>核心利益：</b>{esc(item['opportunity'])}</li>
                <li><b>画面证明：</b>{esc(item['main_image'])}</li>
                <li><b>证据口径：</b>评价 {esc(item['review_count'])} 条，问大家 {esc(item['question_count'])} 条</li>
              </ul>
            </article>
            """
        )
    return "\n".join(cards)


def render_detail_page_brief(opportunities: list[dict[str, object]]) -> str:
    cards = []
    for item in opportunities[:4]:
        cards.append(
            f"""
            <article class="brief-card">
              <div class="brief-label">详情模块 #{esc(item['rank'])}</div>
              <h3>{esc(item['theme'])}</h3>
              <ul>
                <li><b>要补什么：</b>{esc(item['detail_page'])}</li>
                <li><b>用户为什么需要：</b>{esc(item['opportunity'])}</li>
                <li><b>可转 FAQ：</b>{esc(item['faq'])}</li>
              </ul>
            </article>
            """
        )
    return "\n".join(cards)


def write_html_report(path: Path, data: dict, opportunities: list[dict[str, object]], evidence_rows: list[dict[str, object]]) -> None:
    scope = analysis_scope(data)
    rows = [
        [
            item["rank"],
            item["theme"],
            f"评价 {item['review_count']} / 问大家 {item['question_count']}",
            item["opportunity"],
            item["priority_score"],
        ]
        for item in opportunities
    ]
    main_rows = [[item["theme"], item["main_image"], item["detail_page"], item["faq"], item["product"]] for item in opportunities[:6]]
    faq_rows = [[item["theme"], item["faq"], f"评价{item['review_count']}条，问大家{item['question_count']}条"] for item in opportunities[:8]]
    html_doc = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>评价与问大家洞察到经营动作报告</title>
  <style>
    :root {{
      --bg-a: hsl(220, 18%, 91%);
      --bg-b: hsl(210, 22%, 95%);
      --bg-c: hsl(44, 22%, 96%);
      --surface: hsl(0, 0%, 100%);
      --surface-soft: hsl(214, 26%, 97%);
      --surface-raised: hsl(0, 0%, 100%);
      --surface-ink: hsl(220, 22%, 14%);
      --ink: hsl(220, 22%, 14%);
      --ink-2: hsl(218, 10%, 34%);
      --muted: hsl(220, 8%, 50%);
      --accent: hsl(217, 86%, 55%);
      --accent-2: hsl(184, 58%, 34%);
      --accent-3: hsl(35, 86%, 52%);
      --accent-light: hsl(216, 78%, 94%);
      --success: hsl(145, 40%, 34%);
      --warning: hsl(39, 70%, 46%);
      --danger: hsl(5, 62%, 47%);
      --info: hsl(204, 42%, 40%);
      --border: hsla(220, 14%, 34%, .16);
      --border-strong: hsla(220, 16%, 26%, .3);
      --hero-note: hsl(211, 80%, 86%);
      --hero-body: hsl(213, 22%, 86%);
      --dashboard-surface: hsla(0, 0%, 100%, .96);
      --dashboard-soft: hsl(216, 54%, 97%);
      --dashboard-line: hsla(218, 50%, 30%, .14);
      --metric-bg: hsl(215, 80%, 98%);
      --bar-bg: hsl(216, 36%, 91%);
      --bar-fill: linear-gradient(90deg, var(--accent), var(--accent-2));
      --donut-track: hsl(216, 26%, 90%);
      --table-head: hsl(216, 36%, 94%);
      --table-row-alt: hsl(216, 28%, 98%);
      --roadmap-stage-bg: hsl(220, 18%, 18%);
      --roadmap-stage-text: hsl(42, 24%, 92%);
      --shadow-sm: 0 8px 24px hsla(220, 20%, 18%, .08);
      --shadow-md: 0 22px 60px hsla(220, 20%, 18%, .14);
      --radius-sm: 6px;
      --radius-md: 8px;
      --radius-lg: 12px;
      --space-1: 4px;
      --space-2: 8px;
      --space-3: 12px;
      --space-4: 16px;
      --space-6: 24px;
      --space-8: 32px;
      --space-12: 48px;
      --text-xs: .75rem;
      --text-sm: .875rem;
      --text-base: 1rem;
      --text-lg: 1.125rem;
      --text-xl: 1.25rem;
      --text-2xl: 1.5rem;
      --text-3xl: 1.875rem;
      --text-4xl: 2.25rem;
      --leading-tight: 1.25;
      --leading-normal: 1.55;
      --leading-relaxed: 1.78;
      --max-w-full: 1320px;
      --gradient-page: linear-gradient(135deg, var(--bg-a), var(--bg-b), var(--bg-c));
      --gradient-hero: linear-gradient(135deg, hsl(222, 42%, 11%), hsl(218, 34%, 20%) 54%, hsl(190, 42%, 20%));
      --gradient-number: linear-gradient(90deg, var(--accent), var(--accent-2));
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--gradient-page);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
      line-height: var(--leading-normal);
    }}
    .page {{ width: min(var(--max-w-full), calc(100vw - 48px)); margin: var(--space-8) auto var(--space-12); }}
    .hero {{
      display: grid;
      grid-template-columns: minmax(0, .82fr) minmax(0, 1.35fr);
      gap: var(--space-8);
      align-items: stretch;
      min-height: 620px;
      padding: var(--space-8);
      color: var(--surface-raised);
      background: var(--gradient-hero);
      border: 1px solid var(--border-strong);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-md);
      overflow: hidden;
    }}
    .hero-story {{ display: flex; flex-direction: column; justify-content: flex-start; min-width: 0; padding-top: var(--space-12); }}
    .eyebrow {{ display: inline-flex; align-items: center; width: fit-content; padding: var(--space-2) var(--space-3); color: var(--hero-note); background: hsla(0, 0%, 100%, .06); border: 1px solid hsla(214, 70%, 88%, .18); border-radius: var(--radius-sm); font-weight: 900; font-size: var(--text-base); margin-bottom: var(--space-4); }}
    h1 {{ margin: 0; max-width: 760px; font-size: var(--text-4xl); line-height: var(--leading-tight); letter-spacing: 0; }}
    .hero p {{ max-width: 760px; color: var(--hero-body); line-height: var(--leading-relaxed); margin: var(--space-4) 0 0; }}
    .hero-tags {{ display: flex; flex-wrap: wrap; gap: var(--space-2); margin-top: var(--space-6); }}
    .hero-tags span {{ padding: var(--space-2) var(--space-3); border: 1px solid hsla(214, 70%, 88%, .22); border-radius: var(--radius-sm); color: var(--hero-note); background: hsla(0, 0%, 100%, .06); font-size: var(--text-xs); font-weight: 800; }}
    .hero-focus {{ margin-top: var(--space-6); display: grid; gap: var(--space-3); }}
    .focus-head {{ display: flex; align-items: end; justify-content: space-between; gap: var(--space-3); color: var(--surface-raised); }}
    .focus-head b {{ font-size: var(--text-sm); }}
    .focus-head span {{ color: var(--hero-body); font-size: var(--text-xs); }}
    .focus-card {{ padding: var(--space-3); border: 1px solid hsla(214, 70%, 88%, .16); border-radius: var(--radius-md); background: hsla(0, 0%, 100%, .07); }}
    .focus-card div {{ display: flex; align-items: center; gap: var(--space-2); }}
    .focus-card span {{ color: var(--hero-note); font-size: var(--text-xs); font-weight: 900; }}
    .focus-card b {{ color: var(--surface-raised); font-size: var(--text-sm); }}
    .focus-card p {{ margin: var(--space-2) 0 0; color: var(--hero-body); font-size: var(--text-xs); line-height: var(--leading-relaxed); }}
    .hero-samples {{ margin-top: var(--space-5, 20px); }}
    .hero-sample-list {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-2); margin-top: var(--space-3); }}
    .hero-sample-list .sample-row {{ grid-template-columns: 1fr; gap: var(--space-1); background: hsla(0, 0%, 100%, .07); border-color: hsla(214, 70%, 88%, .16); }}
    .hero-sample-list .sample-row b {{ color: var(--hero-note); }}
    .hero-sample-list .sample-row span {{ color: var(--surface-raised); font-size: var(--text-xs); }}
    .hero-sample-list .sample-row em {{ grid-column: auto; color: var(--hero-body); }}
    .hero-note {{ margin-top: var(--space-5, 20px); padding: var(--space-4); border: 1px solid hsla(214, 70%, 88%, .18); border-radius: var(--radius-md); background: hsla(0, 0%, 100%, .08); }}
    .hero-note b {{ display: block; color: var(--surface-raised); font-size: var(--text-sm); }}
    .hero-note span {{ display: block; margin-top: var(--space-2); color: var(--hero-body); font-size: var(--text-sm); line-height: var(--leading-relaxed); }}
    .dashboard-board {{ min-width: 0; padding: var(--space-5, 20px); color: var(--ink); background: var(--dashboard-surface); border: 1px solid hsla(214, 60%, 88%, .34); border-radius: var(--radius-lg); box-shadow: 0 18px 56px hsla(220, 30%, 8%, .22); }}
    .dashboard-title {{ display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); margin-bottom: var(--space-4); }}
    .dashboard-title span {{ display: block; color: var(--accent); font-size: var(--text-xs); font-weight: 900; }}
    .dashboard-title strong {{ display: block; margin-top: var(--space-1); color: var(--ink); font-size: var(--text-2xl); line-height: var(--leading-tight); }}
    .dashboard-title em {{ flex: 0 0 auto; padding: var(--space-1) var(--space-2); border: 1px solid var(--dashboard-line); border-radius: var(--radius-sm); color: var(--muted); font-style: normal; font-size: var(--text-xs); font-weight: 800; }}
    .metric-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--space-3); }}
    .metric-card {{ min-height: 112px; padding: var(--space-4); background: var(--metric-bg); border: 1px solid var(--dashboard-line); border-radius: var(--radius-md); }}
    .metric-card span {{ display: block; color: var(--muted); font-size: var(--text-xs); font-weight: 700; }}
    .metric-card strong {{ display: block; margin-top: var(--space-1); color: var(--ink); font-size: var(--text-2xl); line-height: var(--leading-tight); }}
    .metric-card small {{ display: block; margin-top: var(--space-2); color: var(--muted); font-size: var(--text-xs); line-height: var(--leading-normal); }}
    .dashboard-visuals {{ display: grid; grid-template-columns: .85fr 1.15fr; gap: var(--space-3); margin-top: var(--space-3); }}
    .dashboard-lower {{ display: grid; grid-template-columns: 1.15fr .85fr; gap: var(--space-3); margin-top: var(--space-3); }}
    .dash-panel {{ min-width: 0; padding: var(--space-4); background: var(--surface-raised); border: 1px solid var(--dashboard-line); border-radius: var(--radius-md); }}
    .panel-head {{ display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); margin-bottom: var(--space-3); }}
    .panel-head b {{ color: var(--ink); font-size: var(--text-sm); }}
    .panel-head span {{ color: var(--muted); font-size: var(--text-xs); }}
    .donut-wrap {{ display: flex; align-items: center; gap: var(--space-4); min-height: 170px; }}
    .donut {{ width: 142px; aspect-ratio: 1; border-radius: 50%; display: grid; place-items: center; background: conic-gradient(var(--accent) 0 var(--review-deg), var(--accent-2) var(--review-deg) 360deg); box-shadow: inset 0 0 0 14px var(--dashboard-soft); }}
    .donut span {{ display: grid; place-items: center; width: 92px; aspect-ratio: 1; border-radius: 50%; color: var(--ink); background: var(--surface-raised); font-size: var(--text-xl); font-weight: 900; line-height: 1; }}
    .donut small {{ margin-top: var(--space-1); color: var(--muted); font-size: var(--text-xs); font-weight: 700; }}
    .legend p {{ display: flex; align-items: center; gap: var(--space-2); margin: var(--space-2) 0; color: var(--ink-2); font-size: var(--text-sm); }}
    .legend i {{ width: 10px; height: 10px; border-radius: 50%; }}
    .review-dot {{ background: var(--accent); }}
    .question-dot {{ background: var(--accent-2); }}
    .bar-list {{ display: grid; gap: var(--space-3); }}
    .bar-label {{ display: flex; justify-content: space-between; gap: var(--space-3); margin-bottom: var(--space-1); color: var(--ink-2); font-size: var(--text-xs); }}
    .bar-label span {{ overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .bar-label strong {{ color: var(--ink); }}
    .bar-track {{ height: 10px; overflow: hidden; border-radius: 99px; background: var(--bar-bg); }}
    .bar-track i {{ display: block; width: var(--bar-width); height: 100%; border-radius: inherit; background: var(--bar-fill); }}
    .word-cloud-map {{ position: relative; min-height: 220px; overflow: hidden; border-radius: var(--radius-sm); background: linear-gradient(180deg, hsl(216, 80%, 99%), hsl(216, 56%, 97%)); }}
    .cloud-core, .word-cloud-map .wc {{ position: absolute; display: inline-flex; align-items: baseline; gap: var(--space-1); white-space: nowrap; line-height: 1; letter-spacing: 0; }}
    .cloud-core {{ left: 50%; top: 48%; transform: translate(-50%, -50%); color: var(--accent); font-size: var(--text-3xl); font-weight: 950; }}
    .word-cloud-map small {{ color: var(--muted); font-size: var(--text-xs); font-weight: 700; }}
    .word-cloud-map .wc {{ color: hsl(214, 58%, 62%); font-size: var(--text-sm); font-weight: 800; }}
    .word-cloud-map .wc-1 {{ left: 38%; top: 22%; font-size: var(--text-lg); color: var(--accent-2); }}
    .word-cloud-map .wc-2 {{ left: 58%; top: 28%; font-size: var(--text-base); color: hsl(214, 70%, 54%); }}
    .word-cloud-map .wc-3 {{ left: 18%; top: 42%; font-size: var(--text-base); }}
    .word-cloud-map .wc-4 {{ left: 68%; top: 48%; font-size: var(--text-base); color: hsl(186, 54%, 38%); }}
    .word-cloud-map .wc-5 {{ left: 30%; top: 70%; color: hsl(214, 70%, 54%); }}
    .word-cloud-map .wc-6 {{ left: 62%; top: 72%; }}
    .word-cloud-map .wc-7 {{ left: 12%; top: 24%; color: hsl(214, 48%, 70%); }}
    .word-cloud-map .wc-8 {{ left: 72%; top: 20%; color: hsl(214, 48%, 70%); }}
    .word-cloud-map .wc-9 {{ left: 13%; top: 62%; color: hsl(214, 48%, 70%); }}
    .word-cloud-map .wc-10 {{ left: 78%; top: 66%; color: hsl(214, 48%, 70%); }}
    .word-cloud-map .wc-11 {{ left: 46%; top: 12%; color: hsl(214, 40%, 74%); }}
    .word-cloud-map .wc-12 {{ left: 46%; top: 84%; color: hsl(214, 40%, 74%); }}
    .word-cloud-map .wc-13 {{ left: 24%; top: 12%; color: hsl(214, 40%, 74%); }}
    .word-cloud-map .wc-14 {{ left: 78%; top: 84%; color: hsl(214, 40%, 74%); }}
    .bar-track.compact {{ height: 8px; }}
    .sample-list {{ display: grid; gap: var(--space-2); }}
    .sample-row {{ display: grid; grid-template-columns: 52px minmax(0, 1fr); gap: var(--space-2) var(--space-3); padding: var(--space-2); border: 1px solid var(--dashboard-line); border-radius: var(--radius-sm); background: var(--dashboard-soft); }}
    .sample-row b {{ color: var(--accent); }}
    .sample-row span {{ overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--ink); font-size: var(--text-sm); }}
    .sample-row em {{ grid-column: 2; color: var(--muted); font-style: normal; font-size: var(--text-xs); }}
    .section {{ margin-top: var(--space-6); padding: var(--space-6); background: linear-gradient(180deg, var(--surface), var(--surface-soft)); border: 1px solid var(--border); border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); }}
    .section-head {{ display: flex; justify-content: space-between; align-items: end; gap: var(--space-4); margin-bottom: var(--space-4); }}
    h2 {{ margin: 0; font-size: var(--text-xl); letter-spacing: 0; }}
    .section-head p {{ max-width: 620px; margin: 0; color: var(--muted); font-size: var(--text-sm); }}
    .trust-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--space-4); }}
    .trust, .op-card {{ padding: var(--space-4); background: var(--surface-raised); border: 1px solid var(--border); border-radius: var(--radius-md); }}
    .trust b {{ display: block; color: var(--accent); font-size: var(--text-lg); }}
    .trust span {{ display: block; margin-top: var(--space-1); color: var(--muted); font-size: var(--text-sm); }}
    .op-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--space-4); }}
    .rank {{ display: inline-flex; padding: var(--space-1) var(--space-2); border-radius: var(--radius-sm); background: var(--accent-light); color: var(--accent); font-weight: 800; font-size: var(--text-xs); }}
    h3 {{ margin: var(--space-3) 0 var(--space-2); font-size: var(--text-base); line-height: var(--leading-tight); letter-spacing: 0; }}
    .op-card p {{ margin: 0; color: var(--ink-2); font-size: var(--text-sm); line-height: var(--leading-relaxed); }}
    .score {{ display: flex; justify-content: space-between; align-items: center; margin-top: var(--space-3); padding-top: var(--space-3); border-top: 1px solid var(--border); color: var(--muted); font-size: var(--text-xs); }}
    .score strong {{ color: var(--accent); font-size: var(--text-xl); }}
    .chain {{ display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: var(--space-2); }}
    .chain-step {{ position: relative; padding: var(--space-4); background: var(--surface-raised); border: 1px solid var(--border); border-radius: var(--radius-md); }}
    .chain-step span {{ display: block; color: var(--accent); font-size: var(--text-xs); font-weight: 800; }}
    .chain-step b {{ display: block; margin-top: var(--space-2); color: var(--ink); font-size: var(--text-base); }}
    .chain-step small {{ display: block; margin-top: var(--space-1); color: var(--muted); font-size: var(--text-xs); line-height: var(--leading-normal); }}
    .asset-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--space-4); margin-bottom: var(--space-4); }}
    .asset-card {{ padding: var(--space-4); background: linear-gradient(180deg, var(--surface-raised), var(--surface-soft)); border: 1px solid var(--border); border-radius: var(--radius-md); }}
    .asset-type {{ color: var(--accent); font-size: var(--text-xs); font-weight: 800; }}
    .asset-card p {{ margin: var(--space-2) 0 0; color: var(--ink-2); font-size: var(--text-sm); line-height: var(--leading-relaxed); }}
    .brief-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-4); }}
    .brief-card {{ padding: var(--space-4); background: var(--surface-raised); border: 1px solid var(--border); border-radius: var(--radius-md); box-shadow: var(--shadow-sm); }}
    .brief-label {{ display: inline-flex; padding: var(--space-1) var(--space-2); border-radius: var(--radius-sm); color: var(--accent); background: var(--accent-light); font-size: var(--text-xs); font-weight: 800; }}
    .brief-card ul {{ margin: var(--space-3) 0 0; padding-left: var(--space-4); color: var(--ink-2); font-size: var(--text-sm); line-height: var(--leading-relaxed); }}
    .brief-card li + li {{ margin-top: var(--space-2); }}
    .brief-card b {{ color: var(--ink); }}
    .roadmap-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-4); }}
    .roadmap-card {{ min-height: 220px; padding: var(--space-4); background: var(--surface-raised); border: 1px solid var(--border); border-radius: var(--radius-md); box-shadow: var(--shadow-sm); display: flex; flex-direction: column; }}
    .roadmap-top {{ display: flex; justify-content: space-between; align-items: center; gap: var(--space-3); }}
    .roadmap-top span {{ display: inline-flex; padding: var(--space-1) var(--space-2); border-radius: var(--radius-sm); background: var(--roadmap-stage-bg); color: var(--roadmap-stage-text); font-size: var(--text-xs); font-weight: 800; }}
    .roadmap-top strong {{ color: var(--accent); font-size: var(--text-lg); }}
    .roadmap-card p {{ margin: var(--space-2) 0 0; color: var(--ink-2); font-size: var(--text-sm); line-height: var(--leading-relaxed); }}
    .roadmap-meta {{ display: flex; flex-wrap: wrap; gap: var(--space-2); margin-top: auto; padding-top: var(--space-3); color: var(--muted); font-size: var(--text-xs); }}
    .roadmap-meta span {{ padding: var(--space-1) var(--space-2); border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface-soft); }}
    .table-wrap {{ overflow-x: auto; border: 1px solid var(--border); border-radius: var(--radius-md); background: var(--surface-raised); }}
    table {{ width: 100%; border-collapse: collapse; min-width: 860px; font-size: var(--text-sm); }}
    th, td {{ padding: var(--space-3); border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }}
    th {{ background: var(--table-head); color: var(--ink); font-weight: 800; }}
    tr:nth-child(even) td {{ background: var(--table-row-alt); }}
    .footer {{ margin-top: var(--space-6); color: var(--muted); font-size: var(--text-xs); text-align: center; }}
    @media (max-width: 1100px) {{ .hero, .dashboard-visuals, .dashboard-lower, .op-grid, .trust-grid, .asset-grid {{ grid-template-columns: 1fr 1fr; }} .metric-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} .chain {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }} }}
    @media (max-width: 900px) {{ .hero, .brief-grid, .roadmap-grid, .dashboard-visuals, .dashboard-lower {{ grid-template-columns: 1fr; }} .hero-note {{ margin-top: var(--space-6); }} }}
    @media (max-width: 720px) {{ .page {{ width: 100%; margin: 0; }} .hero, .section {{ border-radius: 0; padding: var(--space-4); }} .op-grid, .trust-grid, .asset-grid, .chain, .metric-grid {{ grid-template-columns: 1fr; }} h1 {{ font-size: var(--text-2xl); }} .section-head {{ display: block; }} .section-head p {{ margin-top: var(--space-2); }} .dashboard-board {{ padding: var(--space-3); }} .donut-wrap {{ flex-direction: column; align-items: flex-start; }} }}
  </style>
</head>
<body>
  <main class="page">
    {render_dashboard_hero(data, opportunities)}
    <section class="section">
      <div class="section-head"><h2>0. 证据可信度</h2><p>先说清楚数据边界，后面的结论才不是“AI自由发挥”。</p></div>
      <div class="trust-grid">
        <div class="trust"><b>{esc(data.get("total_valid_rows", 0))}</b><span>有效文本</span></div>
        <div class="trust"><b>{esc(data.get("review_rows", 0))}</b><span>评价分母</span></div>
        <div class="trust"><b>{esc(data.get("question_answer_rows", 0))}</b><span>问大家分母</span></div>
        <div class="trust"><b>{len(evidence_rows)}</b><span>典型证据索引</span></div>
      </div>
    </section>
    <section class="section">
      <div class="section-head"><h2>报告闭环</h2><p>这份报告最终不是停在分析，而是继续交给主图、详情页、客服和产品动作。</p></div>
      <div class="chain">{render_delivery_chain()}</div>
    </section>
    <section class="section">
      <div class="section-head"><h2>1. 结论总览</h2><p>先看最值得动手的机会，而不是先陷入明细。</p></div>
      <div class="op-grid">{render_cards(opportunities)}</div>
    </section>
    <section class="section">
      <div class="section-head"><h2>2. 样本覆盖</h2><p>按商品样本拆开看，避免把缺少问大家的样本硬凑进顾虑分析。</p></div>
      {render_table(["样本", "商品ID", "评价数", "问大家数", "总记录"], data.get("samples", []) or [])}
    </section>
    <section class="section">
      <div class="section-head"><h2>3-5. 洞察与机会评分</h2><p>把评价主题和问大家顾虑合并为经营机会，并给出优先级。</p></div>
      {render_table(["排名", "机会主题", "证据量", "机会判断", "优先级"], rows)}
    </section>
    <section class="section">
      <div class="section-head"><h2>VOC 原声证据</h2><p>保留少量用户原话，让报告具备“真实数据推出来”的可信度。</p></div>
      {render_voc_evidence(opportunities)}
    </section>
    <section class="section">
      <div class="section-head"><h2>6-9. 可执行动作矩阵</h2><p>每个机会都必须能落到主图、详情页、客服FAQ和产品改进，先给经营者一张总表。</p></div>
      {render_table(["机会主题", "主图动作", "详情页动作", "客服FAQ", "产品改进"], main_rows)}
    </section>
    <section class="section">
      <div class="section-head"><h2>主图表达Brief</h2><p>这是报告内的可交付模块：把评价和问大家里的顾虑翻译成主图第一屏要证明的内容。</p></div>
      <div class="asset-grid">{render_output_assets()}</div>
      <div class="brief-grid">{render_main_image_brief(opportunities)}</div>
    </section>
    <section class="section">
      <div class="section-head"><h2>详情页优化Brief</h2><p>这是报告内的可交付模块：把用户下单前没想清楚、评价里反复验证过的问题，变成详情页应该补的模块。</p></div>
      <div class="brief-grid">{render_detail_page_brief(opportunities)}</div>
    </section>
    <section class="section">
      <div class="section-head"><h2>客服FAQ预案</h2><p>把问大家变成客服能直接使用的话术方向。</p></div>
      {render_table(["对应主题", "推荐回答方向", "证据量"], faq_rows)}
    </section>
    <section class="section">
      <div class="section-head"><h2>产品改进优先级路线图</h2><p>把反复出现的问题拆成可排期动作，避免报告只停留在“看到了问题”。</p></div>
      <div class="roadmap-grid">{render_product_roadmap(opportunities)}</div>
    </section>
    <p class="footer">本 HTML 是正式交付报告；中间数据只用于生成、复盘和后续 Skill 串联。</p>
  </main>
</body>
</html>
"""
    path.write_text(html_doc, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--standard-csv", required=True)
    parser.add_argument("--theme-json", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    standard_csv = Path(args.standard_csv)
    theme_json = Path(args.theme_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(theme_json.read_text(encoding="utf-8"))
    standard_rows = read_csv(standard_csv)
    data["keyword_cloud"] = build_keyword_cloud(standard_rows, data)
    opportunities = build_opportunities(data)
    evidence_rows = build_evidence_index(data)

    for stale_name in [
        "cleaned_reviews.csv",
        "evidence_index.csv",
        "review_insight.json",
        "主图表达Brief.md",
        "详情页优化Brief.md",
        "客服FAQ.csv",
        "产品改进优先级路线图.csv",
    ]:
        stale_path = output_dir / stale_name
        if stale_path.exists():
            stale_path.unlink()

    write_md_report(output_dir / "评价洞察到经营动作报告.md", data, opportunities, evidence_rows)
    write_html_report(output_dir / "评价洞察到经营动作报告.html", data, opportunities, evidence_rows)
    print(json.dumps({"output_dir": str(output_dir), "files": 2}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
