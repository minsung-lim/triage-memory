#!/usr/bin/env python3
"""Build the paper Table III rows from table-specific base files."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


TABLE_ROOT = Path(__file__).resolve().parents[1]
BASE = TABLE_ROOT / "base"
I10P_ROOT = TABLE_ROOT.parents[2]
GIT_ROOT = TABLE_ROOT.parents[1]
DEFAULT_TEX = I10P_ROOT / "candidate" / "main.tex"
RETRIEVER_SUMMARY = BASE / "retriever_summary.csv"
RETRIEVER_PER_CASE = BASE / "retriever_per_case.csv"

RETRIEVER_ROWS = [
    ("TF-IDF", "TF-IDF"),
    ("BM25", "BM25"),
    ("Dense MiniLM", "Dense MiniLM"),
    ("ColBERT", "ColBERT"),
]
FIELD_REPRESENTATION = "four_field_with_order"
BENCH_REPRESENTATION = "four_field_with_order"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def find_one(rows: list[dict[str, str]], **criteria: str) -> dict[str, str]:
    matches = [row for row in rows if all(row[key] == value for key, value in criteria.items())]
    if len(matches) != 1:
        crit = ", ".join(f"{key}={value}" for key, value in criteria.items())
        raise AssertionError(f"Expected one row for {crit}, found {len(matches)}")
    return matches[0]


def pct(agree: int, total: int) -> str:
    return f"{(agree / total) * 100:.1f}%"


def format_agreement(row: dict[str, str]) -> tuple[str, str, str]:
    total = int(row["n_cases"])
    agree = int(row["agree_count"])
    return f"{agree}/{total} ({pct(agree, total)})", f"{float(row['cohen_kappa']):.3f}", row["metric"]


def retriever_results_from_sources() -> dict[str, tuple[str, str]]:
    summary = read_csv(RETRIEVER_SUMMARY)
    results = {}
    for paper_name, source_name in RETRIEVER_ROWS:
        field_row = find_one(
            summary,
            dataset="Triage-Field",
            retriever=source_name,
            representation=FIELD_REPRESENTATION,
        )
        bench_row = find_one(
            summary,
            dataset="Triage-Bench",
            retriever=source_name,
            representation=BENCH_REPRESENTATION,
        )
        results[paper_name] = (field_row["first_service_at1"], bench_row["service_metric_at1"])
    return results


def build_sections() -> tuple[list[list[str]], list[list[str]]]:
    agreement_rows = read_csv(BASE / "label_agreement_summary.csv")
    by_metric = {row["metric"]: row for row in agreement_rows}

    fs_agreement, fs_kappa, _ = format_agreement(by_metric["first_service_label"])
    family_agreement, family_kappa, _ = format_agreement(by_metric["family_component"])
    agreement_table = [
        ["Scoring label", "Agreement", "Cohen's kappa"],
        ["First-service target", fs_agreement, fs_kappa],
        ["Incident family", family_agreement, family_kappa],
    ]

    source_values = retriever_results_from_sources()
    retriever_table = [["Retriever", "Field FS@1", "Bench SM@1"]]
    for name, _ in RETRIEVER_ROWS:
        field_fs_at1, bench_sm_at1 = source_values[name]
        retriever_table.append([name, field_fs_at1, bench_sm_at1])

    return agreement_table, retriever_table


def print_section(rows: list[list[str]]) -> None:
    writer = csv.writer(__import__("sys").stdout)
    writer.writerows(rows)


def check_tex(tex_path: Path, sections: tuple[list[list[str]], list[list[str]]]) -> None:
    tex = tex_path.read_text()
    normalized_tex = " ".join(tex.split())
    required = [
        "Label agreement and self-excluded four-field retriever check with fixed tie break.",
        "First-service target & 25/30 (83.3\\%) & 0.782",
        "Incident family & 30/30 (100.0\\%) & 1.000",
        "TF-IDF & 24/30 & 153/200",
        "BM25 & 22/30 & 157/200",
        "Dense MiniLM & 21/30 & 156/200",
        "ColBERT & 18/30 & 151/200",
    ]
    missing = [needle for needle in required if " ".join(needle.split()) not in normalized_tex]
    if missing:
        raise SystemExit("Missing Table III TeX rows: " + "; ".join(missing))


def verify_sources() -> None:
    agreement_rows = read_csv(BASE / "label_agreement_summary.csv")
    fs_label = find_one(agreement_rows, metric="first_service_label")
    family_label = find_one(agreement_rows, metric="family_component")
    require(fs_label["n_cases"] == "30", "Label agreement first-service n mismatch")
    require(fs_label["agree_count"] == "25", "Label agreement first-service count mismatch")
    require(f"{float(fs_label['cohen_kappa']):.3f}" == "0.782", "Label agreement first-service kappa mismatch")
    require(family_label["n_cases"] == "30", "Label agreement family n mismatch")
    require(family_label["agree_count"] == "30", "Label agreement family count mismatch")
    require(f"{float(family_label['cohen_kappa']):.3f}" == "1.000", "Label agreement family kappa mismatch")

    source_rows = {row["row"]: row for row in read_csv(BASE / "retriever_table_sources.csv")}
    require(set(source_rows) == {"TF-IDF", "BM25", "Dense MiniLM", "ColBERT"}, "Unexpected retriever rows")

    expected = retriever_results_from_sources()
    expected_counts = {
        "TF-IDF": ("24/30", "153/200"),
        "BM25": ("22/30", "157/200"),
        "Dense MiniLM": ("21/30", "156/200"),
        "ColBERT": ("18/30", "151/200"),
    }
    for name, values in expected_counts.items():
        require(expected[name] == values, f"{name} source mismatch: got {expected[name]}, expected {values}")
        row = source_rows[name]
        require(row["condition"] == "same four-field record", f"{name} condition mismatch")
        require(row["field_fs_at1"] == values[0], f"{name} base Field FS@1 mismatch")
        require(row["bench_sm_at1"] == values[1], f"{name} base Bench SM@1 mismatch")


def verify_table_iii_protocol() -> None:
    field_retrieval = read_csv(GIT_ROOT / "datasets/triage-field/data/retrieval_results.csv")
    require(len(field_retrieval) == 30, "TF-IDF Field retrieval row count mismatch")
    for row in field_retrieval:
        require(row["condition"] == "four_field_with_order", "TF-IDF Field condition mismatch")
        require(row["self_excluded"] == "true", "TF-IDF Field self-exclusion mismatch")
        require(row["tie_policy"] == "fixed_tie_break", "TF-IDF Field tie policy mismatch")
        require(row["case_public_id"] != row["returned_case_public_id"], "TF-IDF Field returned self case")

    bench_loo = json.loads((GIT_ROOT / "datasets/triage-bench/data/leave_one_out_all_200.json").read_text())
    tfidf_bench = bench_loo["four_field_with_order"]
    require(tfidf_bench["n"] == 200, "TF-IDF Bench n mismatch")
    require(tfidf_bench["tie_policy"] == "fixed tie break after equal-score records", "TF-IDF Bench tie policy mismatch")
    require(len(tfidf_bench["rows"]) == 200, "TF-IDF Bench row count mismatch")
    for row in tfidf_bench["rows"]:
        require(row["picked_incident_id"] != row["incident_id"], "TF-IDF Bench returned self case")
        require(row["incident_id"] not in row["top_tie_incident_ids"], "TF-IDF Bench top tie includes self")

    summary = read_csv(RETRIEVER_SUMMARY)
    per_case = read_csv(RETRIEVER_PER_CASE)
    summary_by_key = {
        (row["dataset"], row["retriever"], row["representation"]): row
        for row in summary
    }
    for _, source_name in RETRIEVER_ROWS:
        field_summary = summary_by_key[("Triage-Field", source_name, FIELD_REPRESENTATION)]
        bench_summary = summary_by_key[("Triage-Bench", source_name, BENCH_REPRESENTATION)]
        require(field_summary["n"] == "30", f"{source_name} Field n mismatch")
        require(bench_summary["n"] == "200", f"{source_name} Bench n mismatch")
        require(
            field_summary["tie_policy"] == "deterministic tie-break after equal-score candidates",
            f"{source_name} Field tie policy mismatch",
        )
        require(
            bench_summary["tie_policy"] == "fixed tie break after equal-score records",
            f"{source_name} Bench tie policy mismatch",
        )

        for dataset, representation, n, candidates in [
            ("Triage-Field", FIELD_REPRESENTATION, 30, "29"),
            ("Triage-Bench", BENCH_REPRESENTATION, 200, "199"),
        ]:
            rows = [
                row
                for row in per_case
                if row["dataset"] == dataset
                and row["retriever"] == source_name
                and row["representation"] == representation
            ]
            require(len(rows) == n, f"{source_name} {dataset} per-case count mismatch")
            for row in rows:
                require(row["candidate_count"] == candidates, f"{source_name} {dataset} candidate-count mismatch")
                require(row["case_id"] != row["picked_case_id"], f"{source_name} {dataset} returned self case")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-tex", action="store_true", help="Check rows against candidate/main.tex")
    parser.add_argument("--verify-sources", action="store_true", help="Verify Table III values against source result files")
    parser.add_argument("--verify-unified-protocol", action="store_true", help="Verify Table III retriever rows share the declared protocol")
    parser.add_argument("--tex", type=Path, default=DEFAULT_TEX, help="Path to candidate main.tex")
    args = parser.parse_args()

    sections = build_sections()
    print_section(sections[0])
    print()
    print_section(sections[1])
    if args.check_tex:
        check_tex(args.tex, sections)
        print("\nOK: Table III rows match candidate TeX")
    if args.verify_sources:
        verify_sources()
        print("\nOK: Table III source values verified")
    if args.verify_unified_protocol:
        verify_table_iii_protocol()
        print("\nOK: Table III unified protocol verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
