from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from openpyxl import Workbook


ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / "tests" / "_tmp" / "minimal_regression"
RAW = TMP / "raw_exports"
OUT = TMP / "out"


def write_xlsx(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    wb.save(path)


def build_fixture() -> None:
    if TMP.exists():
        shutil.rmtree(TMP)
    RAW.mkdir(parents=True, exist_ok=True)

    review_headers = ["SKU", "评价类型", "初评", "追评", "晒图/视频", "初评时间", "旺旺号", "有用"]
    question_headers = ["问题", "问答", "时间", "昵称"]

    write_xlsx(
        RAW / "表格导出-示例A.xlsx",
        review_headers,
        [
            [
                "蓝牙耳机 标准版 降噪麦克风",
                "好评",
                "音质清晰，打游戏能听到脚步，麦克风沟通也清楚。",
                "戴了两小时耳罩还是比较舒服，降噪效果稳定。",
                "[]",
                "2026-07-01 10:00:00",
                "buyer_a",
                3,
            ],
            [
                "蓝牙耳机 标准版 降噪麦克风",
                "好评",
                "外观有科技感，久戴不夹耳，听声辨位比旧耳机明显。",
                "",
                "[]",
                "2026-07-02 10:00:00",
                "buyer_b",
                1,
            ],
            [
                "蓝牙耳机 标准版 降噪麦克风",
                "中评",
                "包装到手没有破损，但说明书对连接方式写得不够清楚。",
                "",
                "[]",
                "2026-07-03 10:00:00",
                "buyer_c",
                0,
            ],
        ],
    )
    write_xlsx(
        RAW / "店透视-问大家分析-100000000001-2026-07-31.xlsx",
        question_headers,
        [
            ["打游戏脚步声清楚吗", "清楚，定位比普通耳机明显。", "2026-07-01 12:00:00", "user_a"],
            ["戴久了会不会夹耳", "耳罩比较软，两三个小时还可以。", "2026-07-02 12:00:00", "user_b"],
            ["麦克风开黑清楚吗", "队友说声音挺清楚。", "2026-07-03 12:00:00", "user_c"],
        ],
    )

    write_xlsx(
        RAW / "表格导出-示例B.xlsx",
        review_headers,
        [
            [
                "厨房锡纸盒 加厚款",
                "好评",
                "空气炸锅用着方便，不用刷锅，厚度比之前买的稳。",
                "",
                "[]",
                "2026-07-04 10:00:00",
                "buyer_d",
                2,
            ],
            [
                "厨房锡纸盒 加厚款",
                "差评",
                "尺寸买小了，页面如果能写清楚适合几升锅会更好。",
                "",
                "[]",
                "2026-07-05 10:00:00",
                "buyer_e",
                5,
            ],
        ],
    )


def run_workflow() -> None:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_ecom_voc_insight.py"),
        "--raw-dir",
        str(RAW),
        "--work-dir",
        str(OUT),
    ]
    subprocess.run(cmd, check=True)


def assert_output() -> None:
    formal = OUT / "评价洞察Skill-正式输出"
    html_path = formal / "评价洞察到经营动作报告.html"
    md_path = formal / "评价洞察到经营动作报告.md"
    files = sorted(path.name for path in formal.iterdir() if path.is_file())
    expected = ["评价洞察到经营动作报告.html", "评价洞察到经营动作报告.md"]
    assert files == expected, f"unexpected formal files: {files}"
    assert html_path.exists(), "missing HTML report"
    assert md_path.exists(), "missing Markdown report"

    html = html_path.read_text(encoding="utf-8")
    required = [
        "评价与问大家洞察到经营动作报告",
        "评价与问大家 Dashboard",
        "关键词云",
        "主图表达Brief",
        "详情页优化Brief",
        "客服FAQ预案",
        "产品改进优先级路线图",
    ]
    for text in required:
        assert text in html, f"missing required text: {text}"
    assert "适合公众号截图" not in html, "public-content planning phrase leaked into report"
    assert "buyer_a" not in html and "buyer_d" not in html, "buyer nickname leaked into report"


def main() -> int:
    build_fixture()
    run_workflow()
    assert_output()
    print(f"minimal regression passed: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

