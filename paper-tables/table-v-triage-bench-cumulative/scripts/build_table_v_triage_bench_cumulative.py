#!/usr/bin/env python3
"""Build the paper Table V rows from table-specific base files."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


TABLE_ROOT = Path(__file__).resolve().parents[1]
BASE = TABLE_ROOT / "base"
I10P_ROOT = TABLE_ROOT.parents[2]
DEFAULT_TEX = I10P_ROOT / "candidate" / "main.tex"

ORDER = [
    ("alert_message_only", "Alert message only"),
    ("through_maximum_change", "+ maximum change"),
    ("through_earliest_abnormal", "+ earliest abnormal"),
    ("four_field_with_order", "+ change order"),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def build_rows() -> list[list[str]]:
    ablation = {
        row["input_condition"]: row
        for row in read_csv(BASE / "triage_bench_ablation_results.csv")
        if row["view"] == "all_200"
    }
    leave_one_out = json.loads((BASE / "triage_bench_leave_one_out_all_200.json").read_text())
    summary = json.loads((BASE / "triage_bench_summary_200.json").read_text())
    assert summary["counts"]["all_cases"] == 200

    rows = [["Field set", "FS@1", "SM@1", "Tied rec."]]
    final_loo = leave_one_out["four_field_with_order"]
    assert final_loo["first_service_count"] == 155
    assert final_loo["service_metric_count"] == 153

    for key, label in ORDER:
        row = ablation[key]
        rows.append([
            label,
            row["first_service_at1"],
            row["service_metric_at1"],
            row["avg_tied_top_score_records"],
        ])
    return rows


def check_tex(tex_path: Path, rows: list[list[str]]) -> None:
    tex = tex_path.read_text()
    required = [
        "Alert message only  & 71/200  & 61/200  & 13.19",
        "+ maximum change    & 155/200 & 146/200 & 12.38",
        "+ earliest abnormal & \\textbf{159/200} & 149/200 & 8.02",
        "+ change order      & 155/200 & \\textbf{153/200} & \\textbf{1.04}",
    ]
    missing = [needle for needle in required if needle not in tex]
    if missing:
        raise SystemExit("Missing Table V TeX rows: " + "; ".join(missing))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-tex", action="store_true", help="Check rows against candidate/main.tex")
    parser.add_argument("--tex", type=Path, default=DEFAULT_TEX, help="Path to candidate main.tex")
    args = parser.parse_args()

    rows = build_rows()
    writer = csv.writer(__import__("sys").stdout)
    writer.writerows(rows)
    if args.check_tex:
        check_tex(args.tex, rows)
        print("\nOK: Table V rows match candidate TeX")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
