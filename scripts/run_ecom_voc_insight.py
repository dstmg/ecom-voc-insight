from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_step(args: list[str]) -> None:
    result = subprocess.run(args, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    result.check_returncode()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ecommerce VOC insight report workflow.")
    parser.add_argument("--raw-dir", required=True, help="Folder containing raw review and Q&A exports.")
    parser.add_argument("--work-dir", required=True, help="Folder where cleaned data and reports will be written.")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    raw_dir = Path(args.raw_dir).resolve()
    work_dir = Path(args.work_dir).resolve()
    pending_dir = work_dir / "01-待清洗"
    cleaned_dir = work_dir / "02-已清洗"
    standard_csv = cleaned_dir / "评价洞察标准数据.csv"
    theme_json = work_dir / "评价洞察主题计数.json"
    formal_dir = work_dir / "评价洞察Skill-正式输出"

    work_dir.mkdir(parents=True, exist_ok=True)

    run_step(
        [
            sys.executable,
            str(script_dir / "prepare_review_insight_sample.py"),
            str(raw_dir),
            str(pending_dir),
            str(cleaned_dir),
        ]
    )
    run_step(
        [
            sys.executable,
            str(script_dir / "analyze_review_insight_sample.py"),
            str(standard_csv),
            str(work_dir),
        ]
    )
    run_step(
        [
            sys.executable,
            str(script_dir / "package_review_insight_deliverables.py"),
            "--standard-csv",
            str(standard_csv),
            "--theme-json",
            str(theme_json),
            "--output-dir",
            str(formal_dir),
        ]
    )

    files = sorted(path.name for path in formal_dir.glob("*") if path.is_file())
    print(
        json.dumps(
            {
                "raw_dir": str(raw_dir),
                "work_dir": str(work_dir),
                "formal_dir": str(formal_dir),
                "formal_files": files,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

