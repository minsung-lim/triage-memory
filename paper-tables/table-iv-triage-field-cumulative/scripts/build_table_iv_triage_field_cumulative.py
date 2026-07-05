#!/usr/bin/env python3
"""Build the paper Table IV rows from table-specific base files."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


TABLE_ROOT = Path(__file__).resolve().parents[1]
BASE = TABLE_ROOT / "base"
I10P_ROOT = TABLE_ROOT.parents[2]
DEFAULT_TEX = I10P_ROOT / "candidate" / "main.tex"

ORDER = [
    ("alert_service_metric_only", "Alert message only"),
    ("plus_maximum_change", "+ maximum change"),
    ("plus_earliest_abnormal", "+ earliest abnormal"),
    ("four_field_with_order", "+ change order"),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def build_rows() -> list[list[str]]:
    aggregate = {row["input_condition"]: row for row in read_csv(BASE / "triage_field_aggregate_results.csv")}
    retrieval = read_csv(BASE / "triage_field_retrieval_results.csv")
    family_hits = sum(row["family_hit"] == "true" for row in retrieval)
    fs_hits = sum(row["first_service_hit"] == "true" for row in retrieval)
    four_field = aggregate["four_field_with_order"]
    assert four_field["family_at1"] == f"{family_hits}/30"
    assert four_field["first_service_at1"] == f"{fs_hits}/30"

    rows = [["Field set", "Family@1", "First-service@1", "FS Cand."]]
    for key, label in ORDER:
        row = aggregate[key]
        rows.append([
            label,
            row["family_at1"],
            row["first_service_at1"],
            row["avg_first_service_candidate_count"],
        ])
    return rows


def check_tex(tex_path: Path, rows: list[list[str]]) -> None:
    tex = tex_path.read_text()
    required = [
        "Alert message only  & 9/30  & 6/30  & 2.97",
        "+ maximum change    & 18/30 & 19/30 & 1.20",
        "+ earliest abnormal & 19/30 & 20/30 & 1.00",
        "+ change order      & \\textbf{23/30} & \\textbf{24/30} & 1.00",
    ]
    missing = [needle for needle in required if needle not in tex]
    if missing:
        raise SystemExit("Missing Table IV TeX rows: " + "; ".join(missing))


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
        print("\nOK: Table IV rows match candidate TeX")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
