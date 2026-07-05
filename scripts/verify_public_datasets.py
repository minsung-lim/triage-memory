#!/usr/bin/env python3
"""Verify the public data package.

This script uses only Python's standard library. It checks row counts, paper
paper numbers, and a small set of sensitive-token guards for the Triage-Field
public package.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRIAGE_FIELD_ROOT = ROOT / "datasets/triage-field"
TRIAGE_FIELD = TRIAGE_FIELD_ROOT / "data"
TRIAGE_BENCH_ROOT = ROOT / "datasets/triage-bench"
TRIAGE_BENCH = TRIAGE_BENCH_ROOT / "data"
TRIAGE_BENCH_SOURCE = TRIAGE_BENCH_ROOT / "source"
TRIAGE_BENCH_INCIDENTS = TRIAGE_BENCH_SOURCE / "incidents"
PAPER_NUMBERS = ROOT / "datasets/paper_numbers.json"


SENSITIVE_RE = re.compile(
    r"\bincident_[A-Za-z0-9_-]+\b|"
    r"\b[a-z]{2}-[a-z]{2}\b|"
    r"\b20[0-9]{6}(?:_[0-9]{4,6})?\b|"
    r"\b(?:offset_min|delta_pct|residual_z)\b",
    re.IGNORECASE,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def check_triage_field() -> None:
    cases = read_csv(TRIAGE_FIELD / "cases.csv")
    fields = read_csv(TRIAGE_FIELD / "query_fields.csv")
    labels = read_csv(TRIAGE_FIELD / "labels.csv")
    retrieval = read_csv(TRIAGE_FIELD / "retrieval_results.csv")
    families = read_csv(TRIAGE_FIELD / "family_distribution.csv")
    aggregate = read_csv(TRIAGE_FIELD / "aggregate_results.csv")
    manifest = json.loads((TRIAGE_FIELD / "manifest.json").read_text())

    require(len(cases) == 30, "Triage-Field cases.csv must contain 30 rows")
    require(len(labels) == 30, "Triage-Field labels.csv must contain 30 rows")
    require(len(retrieval) == 30, "Triage-Field retrieval_results.csv must contain 30 rows")
    require(len(families) == 8, "Triage-Field family_distribution.csv must contain 8 families")
    require(len(fields) == 240, "Triage-Field query_fields.csv must contain 240 rows")
    require(manifest["case_count"] == 30, "Triage-Field manifest case_count mismatch")
    require(manifest["family_count"] == 8, "Triage-Field manifest family_count mismatch")

    family_hits = sum(row["family_hit"] == "true" for row in retrieval)
    first_service_hits = sum(row["first_service_hit"] == "true" for row in retrieval)
    top3_hits = sum(row["true_family_in_top3"] == "true" for row in retrieval)
    require(family_hits == 23, f"Triage-Field family hits expected 23, got {family_hits}")
    require(first_service_hits == 24, f"Triage-Field first-service hits expected 24, got {first_service_hits}")
    require(top3_hits == 26, f"Triage-Field true family top3 expected 26, got {top3_hits}")

    aggregate_by_condition = {row["input_condition"]: row for row in aggregate}
    require(aggregate_by_condition["alert_service_metric_only"]["first_service_at1"] == "6/30", "Triage-Field alert baseline mismatch")
    require(aggregate_by_condition["four_field_with_order"]["family_at1"] == "23/30", "Triage-Field four-field family mismatch")
    require(aggregate_by_condition["four_field_with_order"]["first_service_at1"] == "24/30", "Triage-Field four-field first-service mismatch")

    scanned_files = [
        TRIAGE_FIELD / "cases.csv",
        TRIAGE_FIELD / "query_fields.csv",
        TRIAGE_FIELD / "labels.csv",
        TRIAGE_FIELD / "retrieval_results.csv",
        TRIAGE_FIELD / "family_distribution.csv",
        TRIAGE_FIELD / "aggregate_results.csv",
        TRIAGE_FIELD / "service_alias_inventory.csv",
        ROOT / "paper-tables/table-iii-label-retriever-check/base/retriever_per_case.csv",
    ]
    for path in scanned_files:
        text = path.read_text()
        match = SENSITIVE_RE.search(text)
        if match is not None:
            raise AssertionError(f"Sensitive-looking token found in {path}: {match.group(0)}")


def check_triage_bench() -> None:
    paper_numbers = json.loads(PAPER_NUMBERS.read_text())
    summary = json.loads((TRIAGE_BENCH / "summary_200.json").read_text())
    leave_one_out = json.loads((TRIAGE_BENCH / "leave_one_out_all_200.json").read_text())
    prior = json.loads((TRIAGE_BENCH / "prior_same_family_200.json").read_text())
    ablation = read_csv(TRIAGE_BENCH / "ablation_results.csv")
    case_ids = json.loads((TRIAGE_BENCH / "case_ids_200.json").read_text())
    source_cases = read_csv(TRIAGE_BENCH_SOURCE / "case_manifest_200.csv")
    source_families = read_csv(TRIAGE_BENCH_SOURCE / "fault_family_manifest.csv")
    source_metrics = read_csv(TRIAGE_BENCH_SOURCE / "metric_signal_rows.csv")
    source_runtime = read_csv(TRIAGE_BENCH_SOURCE / "runtime_profile_summary.csv")
    source_windows = read_csv(TRIAGE_BENCH_SOURCE / "window_duration_summary.csv")

    require(summary["counts"]["all_cases"] == 200, "Triage-Bench all case count mismatch")
    require(summary["counts"]["families"] == 23, "Triage-Bench family count mismatch")
    require(summary["counts"]["past_incident_available_cases"] == 177, "Triage-Bench prior-family count mismatch")
    require(len(case_ids) == 200, "Triage-Bench case_ids_200.json must contain 200 IDs")
    require(len(source_cases) == 200, "Triage-Bench source case manifest must contain 200 rows")
    require(len(source_families) == 23, "Triage-Bench source family manifest must contain 23 rows")
    require(len(source_metrics) == 13284, "Triage-Bench source metric rows must contain 13,284 rows")
    require(len(source_runtime) == 25, "Triage-Bench runtime summary must contain 25 services")
    require({row["case_id"] for row in source_cases} == set(case_ids), "Triage-Bench source case IDs mismatch")
    require(not (TRIAGE_BENCH_SOURCE / "plots").exists(), "Triage-Bench plots must be colocated under source/incidents/<case_id>/plots")

    expected_plots = {"incident_metric_panels.png", "snapshot_overview.png"}
    for case_id in case_ids:
        case_root = TRIAGE_BENCH_INCIDENTS / case_id
        require((case_root / "README.md").exists(), f"Missing Triage-Bench case README: {case_id}/README.md")
        for rel in ["truth/truth.json", "pattern/pattern_case.json", "pattern/rag_pattern.json", "raw/metrics_long.csv"]:
            require((case_root / rel).exists(), f"Missing Triage-Bench source file: {case_id}/{rel}")
        require((case_root / "raw/metrics_long.csv").stat().st_size > 0, f"Empty Triage-Bench raw metric CSV: {case_id}/raw/metrics_long.csv")
        plot_dir = case_root / "plots"
        actual_plots = {path.name for path in plot_dir.glob("*.png")}
        require(actual_plots == expected_plots, f"Triage-Bench plot set mismatch for {case_id}: {sorted(actual_plots)}")
        for name in expected_plots:
            path = plot_dir / name
            require(path.stat().st_size > 0, f"Empty Triage-Bench plot: {case_id}/plots/{name}")

    source_by_case = {row["case_id"]: row for row in source_cases}
    runtime_available = sum(row["runtime_profile_available"] == "true" for row in source_by_case.values())
    recovered = sum(row["recovered_from_prometheus"] == "true" for row in source_by_case.values())
    require(runtime_available == 192, f"Triage-Bench runtime-profile count expected 192, got {runtime_available}")
    require(recovered == 8, f"Triage-Bench recovered-from-Prometheus count expected 8, got {recovered}")

    window_by_dimension = {(row["dimension"], row["value"]): row["cases"] for row in source_windows}
    require(window_by_dimension[("truth_duration_min", "10")] == "183", "Triage-Bench 10-minute duration count mismatch")
    require(window_by_dimension[("truth_duration_min", "5")] == "6", "Triage-Bench 5-minute duration count mismatch")
    require(window_by_dimension[("truth_duration_min", "20")] == "11", "Triage-Bench 20-minute duration count mismatch")

    order_all = leave_one_out["four_field_with_order"]
    require(order_all["first_service_count"] == 155, "Triage-Bench four-field first-service count mismatch")
    require(order_all["service_metric_count"] == 153, "Triage-Bench four-field service-metric count mismatch")

    order_prior = prior["four_field_with_order"]
    require(order_prior["n"] == 177, "Triage-Bench prior-family n mismatch")
    require(order_prior["first_service_count"] == 143, "Triage-Bench prior-family first-service count mismatch")
    require(order_prior["service_metric_count"] == 141, "Triage-Bench prior-family service-metric count mismatch")

    ablation_by_key = {(row["view"], row["input_condition"]): row for row in ablation}
    require(ablation_by_key[("all_200", "alert_message_only")]["service_metric_at1"] == "61/200", "Triage-Bench alert-message-only service-metric mismatch")
    require(ablation_by_key[("all_200", "four_field_with_order")]["service_metric_at1"] == "153/200", "Triage-Bench four-field service-metric mismatch")
    require(ablation_by_key[("all_200", "four_field_with_order")]["avg_tied_top_score_records"] == "1.04", "Triage-Bench tied-record count mismatch")

    paper_results = paper_numbers["triage_bench"]["paper_results"]
    require(paper_results["alert_message_only_service_metric"] == "61/200", "paper_numbers alert-message-only mismatch")
    require(paper_results["four_field_service_metric"] == "153/200", "paper_numbers four-field mismatch")


def main() -> int:
    try:
        check_triage_field()
        check_triage_bench()
    except Exception as exc:  # noqa: BLE001 - simple CLI verifier
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("OK: public dataset checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
