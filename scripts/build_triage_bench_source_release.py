#!/usr/bin/env python3
"""Build Triage-Bench public source manifests.

The public package includes a controlled, non-production source incident set for
Triage-Bench. This script regenerates readable CSV manifests from that source set.
Maintainers can also copy refreshed source incidents into the public package
with --input and --copy-incidents.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TRIAGE_BENCH = ROOT / "datasets/triage-bench"
DATA = TRIAGE_BENCH / "data"
SOURCE = TRIAGE_BENCH / "source"
INCIDENTS = SOURCE / "incidents"
GENERATED_PLOTS = {"snapshot_overview.png", "incident_metric_panels.png"}
PLOT_DESCRIPTIONS = {
    "snapshot_overview.png": "Case overview with target label, four-field record, and change-order timeline from pattern_case.json.",
    "incident_metric_panels.png": "Dashboard-style metric panels reconstructed from released summary fields in pattern_case.json.",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: clean_cell(row.get(name, "")) for name in fieldnames})


def clean_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return f"{value:.12g}"
    if isinstance(value, (list, tuple, set)):
        return ";".join(clean_cell(v) for v in value)
    return str(value)


def rel_offset_min(anchor_ts: Any, ts: Any) -> str:
    if not isinstance(anchor_ts, (int, float)) or not isinstance(ts, (int, float)):
        return ""
    if not math.isfinite(anchor_ts) or not math.isfinite(ts):
        return ""
    return f"{(ts - anchor_ts) / 60.0:.3f}"


def injection_text(detail: dict[str, Any] | None) -> str:
    if not detail:
        return ""
    return ";".join(f"{k}={v}" for k, v in sorted(detail.items()))


def load_case_ids() -> list[str]:
    ids = read_json(DATA / "case_ids_200.json")
    if not isinstance(ids, list):
        raise TypeError("case_ids_200.json must contain a list")
    return ids


def load_bucket_map() -> dict[str, str]:
    summary = read_json(DATA / "summary_200.json")
    bucket_map: dict[str, str] = {}
    for bucket_name, payload in summary.get("symptom_buckets", {}).items():
        for family_id in payload.get("family_ids", []):
            bucket_map[family_id] = bucket_name
    return bucket_map


def case_paths(incidents: Path, case_id: str) -> tuple[Path, Path, Path]:
    base = incidents / case_id
    return (
        base / "truth/truth.json",
        base / "pattern/pattern_case.json",
        base / "pattern/rag_pattern.json",
    )


def validate_incidents(incidents: Path, case_ids: list[str]) -> None:
    missing: list[str] = []
    for case_id in case_ids:
        for path in case_paths(incidents, case_id):
            if not path.exists():
                missing.append(str(path.relative_to(ROOT)))
    if missing:
        raise FileNotFoundError("Missing Triage-Bench source files:\n" + "\n".join(missing[:30]))


def copy_incidents(input_dir: Path, incidents: Path) -> None:
    if not input_dir.exists():
        raise FileNotFoundError(input_dir)
    if incidents.exists():
        shutil.rmtree(incidents)
    incidents.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(input_dir, incidents)


def build_case_manifest(incidents: Path, case_ids: list[str], bucket_map: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_id in case_ids:
        truth_path, pattern_path, _ = case_paths(incidents, case_id)
        truth = read_json(truth_path)
        pattern = read_json(pattern_path)
        logical = pattern.get("logical_time", {})
        execution = pattern.get("execution") or {}
        injection = execution.get("injection_detail") or {}
        dominant = pattern.get("dominant_signal", {})
        earliest = pattern.get("earliest_change", {})
        rows.append(
            {
                "case_id": case_id,
                "family_id": truth.get("family_id"),
                "run_id": case_id.rsplit("_run_", 1)[-1],
                "case_group": bucket_map.get(truth.get("family_id", ""), ""),
                "region": truth.get("region"),
                "traffic_bucket": truth.get("traffic_bucket"),
                "intensity": truth.get("intensity"),
                "duration_min": truth.get("duration_min"),
                "observation_window_min": logical.get("observation_window_min"),
                "pre_window_min": logical.get("pre_window_min"),
                "active_window_min": logical.get("active_window_min"),
                "post_window_min": logical.get("post_window_min"),
                "target_service": truth.get("root_service_truth"),
                "target_metric": truth.get("root_metric_truth"),
                "expected_earliest": truth.get("expected_earliest"),
                "expected_dominant": truth.get("expected_dominant"),
                "dominant_service": dominant.get("service"),
                "dominant_metric": dominant.get("metric_family"),
                "earliest_service": earliest.get("service"),
                "earliest_metric": earliest.get("metric_family"),
                "change_sequence_rows": len(pattern.get("change_sequence", [])),
                "metric_rows": len(pattern.get("metric_rows", [])),
                "execution_available": bool(execution),
                "runtime_profile_available": bool(execution.get("runtime_profile")),
                "recovered_from_prometheus": bool(pattern.get("recovered_from_prometheus")),
                "injection_detail": injection_text(injection),
            }
        )
    return rows


def build_family_manifest(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in case_rows:
        grouped[row["family_id"]].append(row)

    rows: list[dict[str, Any]] = []
    for family_id in sorted(grouped):
        cases = grouped[family_id]
        rows.append(
            {
                "family_id": family_id,
                "cases": len(cases),
                "case_group": unique_join(row["case_group"] for row in cases),
                "target_service": unique_join(row["target_service"] for row in cases),
                "target_metric": unique_join(row["target_metric"] for row in cases),
                "duration_min_values": unique_join(row["duration_min"] for row in cases),
                "regions": unique_join(row["region"] for row in cases),
                "injection_details": unique_join(row["injection_detail"] or "missing" for row in cases),
                "runtime_profile_missing_cases": sum(not row["runtime_profile_available"] for row in cases),
                "example_case_id": cases[0]["case_id"],
            }
        )
    return rows


def unique_join(values: Any) -> str:
    return ";".join(sorted({str(v) for v in values if v not in ("", None)}))


def build_metric_signal_rows(incidents: Path, case_ids: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_id in case_ids:
        _, pattern_path, _ = case_paths(incidents, case_id)
        pattern = read_json(pattern_path)
        family_id = pattern.get("family_id")
        anchor_ts = (pattern.get("actual_window") or {}).get("anchor_ts")
        dominant = pattern.get("dominant_signal") or {}
        earliest = pattern.get("earliest_change") or {}
        change_sequence = pattern.get("change_sequence") or []
        change_rank = {
            signal_key(row): idx + 1
            for idx, row in enumerate(change_sequence)
        }

        for idx, metric in enumerate(pattern.get("metric_rows") or [], start=1):
            key = signal_key(metric)
            rows.append(
                {
                    "case_id": case_id,
                    "family_id": family_id,
                    "metric_row_index": idx,
                    "change_order_rank": change_rank.get(key, ""),
                    "is_dominant": key == signal_key(dominant),
                    "is_earliest": key == signal_key(earliest),
                    "service": metric.get("service"),
                    "metric_family": metric.get("metric_family"),
                    "earliest_offset_min": rel_offset_min(anchor_ts, metric.get("earliest_timestamp")),
                    "peak_offset_min": rel_offset_min(anchor_ts, metric.get("peak_timestamp")),
                    "baseline_mean": metric.get("baseline_mean"),
                    "baseline_std": metric.get("baseline_std"),
                    "earliest_value": metric.get("earliest_value"),
                    "earliest_delta_pct": metric.get("earliest_delta_pct"),
                    "earliest_residual_z": metric.get("earliest_residual_z"),
                    "peak_value": metric.get("peak_value"),
                    "peak_delta": metric.get("peak_delta"),
                    "peak_delta_pct": metric.get("peak_delta_pct"),
                    "peak_residual_z": metric.get("peak_residual_z"),
                    "sustained_trigger_points": metric.get("sustained_trigger_points"),
                    "rank_score": metric.get("rank_score"),
                }
            )
    return rows


def signal_key(row: dict[str, Any]) -> tuple[Any, Any, Any]:
    return (row.get("service"), row.get("metric_family"), row.get("earliest_timestamp"))


def build_runtime_summary(incidents: Path, case_ids: list[str]) -> list[dict[str, Any]]:
    service_values: dict[str, dict[str, Counter[Any]]] = defaultdict(lambda: defaultdict(Counter))
    scaled_services: set[str] = set()
    profile_names: Counter[str] = Counter()
    available_cases = 0

    for case_id in case_ids:
        _, pattern_path, _ = case_paths(incidents, case_id)
        pattern = read_json(pattern_path)
        runtime = ((pattern.get("execution") or {}).get("runtime_profile") or {})
        if not runtime:
            continue
        available_cases += 1
        profile_names[runtime.get("profile_name", "")] += 1
        for svc, replicas in (runtime.get("service_replicas") or {}).items():
            if replicas == 3:
                scaled_services.add(svc)
        for svc, counts in (runtime.get("snapshot") or {}).items():
            for key in ["desired_replicas", "available_replicas", "ready_replicas", "updated_replicas"]:
                service_values[svc][key][counts.get(key)] += 1

    rows: list[dict[str, Any]] = []
    for service in sorted(service_values):
        values = service_values[service]
        rows.append(
            {
                "service": service,
                "runtime_profile_cases": available_cases,
                "profile_names": unique_join(profile_names),
                "scaled_to_three_replicas": service in scaled_services,
                "desired_replicas_values": unique_join(values["desired_replicas"]),
                "available_replicas_values": unique_join(values["available_replicas"]),
                "ready_replicas_values": unique_join(values["ready_replicas"]),
                "updated_replicas_values": unique_join(values["updated_replicas"]),
            }
        )
    return rows


def build_window_duration_summary(incidents: Path, case_ids: list[str]) -> list[dict[str, Any]]:
    counters: dict[str, Counter[Any]] = {
        "truth_duration_min": Counter(),
        "logical_pre_window_min": Counter(),
        "logical_observation_window_min": Counter(),
        "logical_active_window_min": Counter(),
        "logical_post_window_min": Counter(),
        "execution_available": Counter(),
        "runtime_profile_available": Counter(),
        "recovered_from_prometheus": Counter(),
    }

    for case_id in case_ids:
        truth_path, pattern_path, _ = case_paths(incidents, case_id)
        truth = read_json(truth_path)
        pattern = read_json(pattern_path)
        logical = pattern.get("logical_time", {})
        execution = pattern.get("execution") or {}
        counters["truth_duration_min"][truth.get("duration_min")] += 1
        counters["logical_pre_window_min"][logical.get("pre_window_min")] += 1
        counters["logical_observation_window_min"][logical.get("observation_window_min")] += 1
        counters["logical_active_window_min"][logical.get("active_window_min")] += 1
        counters["logical_post_window_min"][logical.get("post_window_min")] += 1
        counters["execution_available"][bool(execution)] += 1
        counters["runtime_profile_available"][bool(execution.get("runtime_profile"))] += 1
        counters["recovered_from_prometheus"][bool(pattern.get("recovered_from_prometheus"))] += 1

    rows: list[dict[str, Any]] = []
    for dimension, counter in counters.items():
        for value, cases in sorted(counter.items(), key=lambda item: str(item[0])):
            rows.append({"dimension": dimension, "value": value, "cases": cases})
    return rows


def finite_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def clipped_abs(value: Any, limit: float) -> float:
    number = finite_float(value)
    if number is None:
        return 0.0
    return min(abs(number), limit)


def clipped_signed(value: Any, limit: float) -> float:
    number = finite_float(value)
    if number is None:
        return 0.0
    return max(-limit, min(number, limit))


def offset_minutes(anchor_ts: Any, ts: Any) -> float | None:
    anchor = finite_float(anchor_ts)
    timestamp = finite_float(ts)
    if anchor is None or timestamp is None:
        return None
    return (timestamp - anchor) / 60.0


def metric_label(row: dict[str, Any]) -> str:
    service = row.get("service") or "unknown"
    metric = row.get("metric_family") or "metric"
    return f"{service}/{metric}"


def ranked_rows(pattern: dict[str, Any], limit: int = 12) -> list[dict[str, Any]]:
    rows = list(pattern.get("change_sequence") or [])
    if not rows:
        rows = sorted(
            pattern.get("metric_rows") or [],
            key=lambda row: finite_float(row.get("rank_score")) or 0.0,
            reverse=True,
        )
    return rows[:limit]


def representative_rows(pattern: dict[str, Any], limit: int = 8) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for key in ["dominant_signal", "earliest_change"]:
        row = pattern.get(key) or {}
        if row:
            candidates.append(row)
    candidates.extend(pattern.get("change_sequence") or [])
    candidates.extend(pattern.get("slot_signals") or [])
    candidates.extend(
        sorted(
            pattern.get("metric_rows") or [],
            key=lambda row: finite_float(row.get("rank_score")) or 0.0,
            reverse=True,
        )
    )

    rows: list[dict[str, Any]] = []
    seen: set[tuple[Any, Any]] = set()
    for row in candidates:
        key = (row.get("service"), row.get("metric_family"))
        if key in seen or key == (None, None):
            continue
        seen.add(key)
        rows.append(row)
        if len(rows) >= limit:
            break
    return rows


def field_pair(row: dict[str, Any]) -> str:
    if not row:
        return "n/a"
    return metric_label(row)


def fmt_offset(anchor_ts: Any, ts: Any) -> str:
    offset = offset_minutes(anchor_ts, ts)
    if offset is None:
        return "n/a"
    return f"{offset:.1f}m"


def fmt_number(value: Any, digits: int = 2) -> str:
    number = finite_float(value)
    if number is None:
        return "n/a"
    return f"{number:.{digits}f}"


def short_label(label: str, limit: int = 32) -> str:
    return label if len(label) <= limit else label[: limit - 1] + "…"


def write_snapshot_overview_plot(case_root: Path) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # noqa: BLE001 - make the missing dependency explicit
        raise RuntimeError("matplotlib is required to regenerate snapshot overview plots") from exc

    truth = read_json(case_root / "truth/truth.json")
    pattern = read_json(case_root / "pattern/pattern_case.json")
    rag = read_json(case_root / "pattern/rag_pattern.json")
    rows = ranked_rows(pattern, limit=5)
    anchor_ts = (pattern.get("actual_window") or {}).get("anchor_ts")
    logical = pattern.get("logical_time") or {}
    execution = pattern.get("execution") or {}
    dominant = pattern.get("dominant_signal") or {}
    earliest = pattern.get("earliest_change") or {}
    pre_window = finite_float(logical.get("pre_window_min")) or 30.0

    plot_root = case_root / "plots"
    plot_root.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(12, 7.2), constrained_layout=True)
    fig.suptitle(f"Case overview: {case_root.name}", fontsize=14, fontweight="bold")
    grid = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.15, 1.25])
    ax_case = fig.add_subplot(grid[0, 0])
    ax_record = fig.add_subplot(grid[0, 1])
    ax_timeline = fig.add_subplot(grid[1, :])
    ax_order = fig.add_subplot(grid[2, :])

    case_lines = [
        f"family_id: {truth.get('family_id', '')}",
        f"target: {truth.get('root_service_truth', '')}/{truth.get('root_metric_truth', '')}",
        f"region: {truth.get('region', '')}",
        f"traffic_bucket: {logical.get('traffic_bucket', '')}",
        f"duration_min: {truth.get('duration_min', '')}",
        f"pre_window_min: {logical.get('pre_window_min', '')}",
        f"metric_rows: {len(pattern.get('metric_rows') or [])}",
        f"change_rows: {len(pattern.get('change_sequence') or [])}",
        f"runtime_profile: {'yes' if execution.get('runtime_profile') else 'no'}",
    ]
    ax_case.axis("off")
    ax_case.set_title("Controlled case", loc="left")
    ax_case.text(0.0, 0.95, "\n".join(case_lines), va="top", family="monospace", fontsize=9, linespacing=1.35)

    order_pairs = [
        f"{idx}. {metric_label(row)} {fmt_offset(anchor_ts, row.get('earliest_timestamp'))}"
        for idx, row in enumerate(rows, start=1)
    ]
    record_lines = [
        f"alert-service: {rag.get('anchor_service', '')}/{rag.get('alarm_family', '')}",
        f"maximum-change: {field_pair(dominant)}",
        f"earliest-abnormal: {field_pair(earliest)}",
        "change-order:",
        *(f"  {line}" for line in order_pairs),
    ]
    ax_record.axis("off")
    ax_record.set_title("Four-field record", loc="left")
    ax_record.text(0.0, 0.95, "\n".join(record_lines), va="top", family="monospace", fontsize=9, linespacing=1.35)

    if rows:
        y = list(range(len(rows)))
        labels = [short_label(metric_label(row), 42) for row in rows]
        earliest_offsets = [
            offset_minutes(anchor_ts, row.get("earliest_timestamp")) if row.get("earliest_timestamp") is not None else None
            for row in rows
        ]
        peak_offsets = [
            offset_minutes(anchor_ts, row.get("peak_timestamp")) if row.get("peak_timestamp") is not None else None
            for row in rows
        ]
        usable_earliest = [value if value is not None else -pre_window for value in earliest_offsets]
        usable_peak = [value if value is not None else value_e for value, value_e in zip(peak_offsets, usable_earliest)]
        for idx, (start, end) in enumerate(zip(usable_earliest, usable_peak)):
            ax_timeline.plot([start, end], [idx, idx], color="#6b7280", linewidth=1.2)
        ax_timeline.scatter(usable_earliest, y, marker="o", facecolor="white", edgecolor="#111827", s=42, label="earliest")
        ax_timeline.scatter(usable_peak, y, marker="s", color="#111827", s=34, label="peak")
        ax_timeline.set_yticks(y, labels=labels, fontsize=8)
        ax_timeline.invert_yaxis()
    ax_timeline.set_title("Pre-anchor change-order timeline", loc="left")
    ax_timeline.set_xlim(-pre_window, 0.8)
    ax_timeline.set_xlabel("minutes from anchor")
    ax_timeline.axvline(0, color="#111827", linewidth=1.0)
    ax_timeline.grid(axis="x", color="#d4d4d4", linewidth=0.6)
    ax_timeline.legend(loc="lower right", fontsize=8)

    table_rows = []
    for idx, row in enumerate(rows, start=1):
        table_rows.append(
            [
                str(idx),
                metric_label(row),
                fmt_offset(anchor_ts, row.get("earliest_timestamp")),
                fmt_offset(anchor_ts, row.get("peak_timestamp")),
                fmt_number(row.get("peak_residual_z")),
                fmt_number(row.get("rank_score")),
            ]
        )
    ax_order.axis("off")
    ax_order.set_title("Released change-order rows", loc="left")
    table = ax_order.table(
        cellText=table_rows,
        colLabels=["rank", "service-metric", "earliest", "peak", "peak z", "score"],
        loc="upper left",
        colWidths=[0.06, 0.42, 0.13, 0.13, 0.12, 0.10],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.18)
    for cell in table.get_celld().values():
        cell.set_edgecolor("#d4d4d4")
        cell.set_linewidth(0.6)

    fig.savefig(plot_root / "snapshot_overview.png", dpi=160)
    plt.close(fig)


def write_incident_metric_panels_plot(case_root: Path) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # noqa: BLE001 - make the missing dependency explicit
        raise RuntimeError("matplotlib is required to regenerate incident metric panel plots") from exc

    pattern = read_json(case_root / "pattern/pattern_case.json")
    rows = representative_rows(pattern, limit=8)
    anchor_ts = (pattern.get("actual_window") or {}).get("anchor_ts")
    logical = pattern.get("logical_time") or {}
    pre_window = finite_float(logical.get("pre_window_min")) or 30.0

    plot_root = case_root / "plots"
    plot_root.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(4, 2, figsize=(12, 8), sharex=True, constrained_layout=True)
    fig.suptitle(
        f"{case_root.name}: metric panel samples\nsummary-field reconstruction",
        fontsize=13,
        fontweight="bold",
    )

    flat_axes = list(axes.flat)
    for ax, row in zip(flat_axes, rows):
        earliest_offset = offset_minutes(anchor_ts, row.get("earliest_timestamp"))
        peak_offset = offset_minutes(anchor_ts, row.get("peak_timestamp"))
        if peak_offset is None:
            peak_offset = -1.0
        if earliest_offset is None:
            earliest_offset = max(-pre_window, peak_offset - 2.0)
        pre_earliest = max(-pre_window, earliest_offset - 2.0)
        post_peak = min(0.0, peak_offset + 2.0)
        earliest_z = clipped_signed(row.get("earliest_residual_z"), 20.0)
        peak_z = clipped_signed(row.get("peak_residual_z"), 20.0)

        points = [
            (-pre_window, 0.0),
            (pre_earliest, 0.0),
            (earliest_offset, earliest_z),
            (peak_offset, peak_z),
            (post_peak, peak_z),
            (0.0, peak_z),
        ]
        ordered: dict[float, float] = {}
        for x_value, y_value in sorted(points, key=lambda item: item[0]):
            ordered[x_value] = y_value
        xs = list(ordered)
        ys = [ordered[x_value] for x_value in xs]

        ax.plot(xs, ys, color="#111827", linewidth=1.4)
        ax.scatter([earliest_offset], [earliest_z], marker="o", facecolor="white", edgecolor="#111827", s=32, zorder=3)
        ax.scatter([peak_offset], [peak_z], marker="s", color="#111827", s=28, zorder=3)
        ax.axhline(0, color="#a3a3a3", linewidth=0.8)
        ax.axvline(0, color="#404040", linewidth=0.9)
        ax.set_xlim(-pre_window, 0.8)
        ax.set_ylim(-21.5, 21.5)
        ax.grid(color="#e5e5e5", linewidth=0.5)
        ax.set_title(short_label(metric_label(row), 48), loc="left", fontsize=9)
        ax.text(
            0.02,
            0.04,
            f"score {fmt_number(row.get('rank_score'))} | peak z {fmt_number(row.get('peak_residual_z'))}",
            transform=ax.transAxes,
            fontsize=7,
            color="#404040",
        )

    for ax in flat_axes[len(rows):]:
        ax.axis("off")
    for ax in flat_axes[-2:]:
        if ax.has_data():
            ax.set_xlabel("minutes from anchor")
    for ax in flat_axes[::2]:
        if ax.has_data():
            ax.set_ylabel("residual z")

    fig.savefig(plot_root / "incident_metric_panels.png", dpi=160)
    plt.close(fig)


def write_case_plots(incidents: Path, case_ids: list[str]) -> None:
    for case_id in case_ids:
        case_root = incidents / case_id
        plot_root = case_root / "plots"
        if plot_root.exists():
            for target in plot_root.glob("*.png"):
                if target.name not in GENERATED_PLOTS:
                    target.unlink()
        write_snapshot_overview_plot(case_root)
        write_incident_metric_panels_plot(case_root)


def plot_link_rows(case_root: Path) -> list[str]:
    plot_root = case_root / "plots"
    if not plot_root.exists():
        return ["No plot files are present for this case."]
    rows = []
    for path in sorted(plot_root.glob("*.png")):
        description = PLOT_DESCRIPTIONS.get(path.name, "Per-case plot.")
        rows.append(f"- [`plots/{path.name}`](plots/{path.name}): {description}")
    return rows or ["No plot files are present for this case."]


def write_case_readmes(incidents: Path, case_rows: list[dict[str, Any]]) -> None:
    rows_by_case = {str(row["case_id"]): row for row in case_rows}
    for case_id in sorted(rows_by_case):
        row = rows_by_case[case_id]
        case_root = incidents / case_id
        readme = case_root / "README.md"
        plot_rows = "\n".join(plot_link_rows(case_root))
        text = f"""# {case_id}

This directory is one Triage-Bench source case. It contains the
controlled fault label, the extracted pre-anchor metric pattern, the compact
retrieval record, released metric rows, and per-case plots colocated with the
source files.

## Case Summary

| Field | Value |
| --- | --- |
| family_id | {clean_cell(row.get("family_id"))} |
| run_id | {clean_cell(row.get("run_id"))} |
| target_service | {clean_cell(row.get("target_service"))} |
| target_metric | {clean_cell(row.get("target_metric"))} |
| dominant_service_metric | {clean_cell(row.get("dominant_service"))}/{clean_cell(row.get("dominant_metric"))} |
| earliest_service_metric | {clean_cell(row.get("earliest_service"))}/{clean_cell(row.get("earliest_metric"))} |
| duration_min | {clean_cell(row.get("duration_min"))} |
| pre_window_min | {clean_cell(row.get("pre_window_min"))} |
| metric_rows | {clean_cell(row.get("metric_rows"))} |
| change_sequence_rows | {clean_cell(row.get("change_sequence_rows"))} |
| runtime_profile_available | {clean_cell(row.get("runtime_profile_available"))} |
| recovered_from_prometheus | {clean_cell(row.get("recovered_from_prometheus"))} |

The target fields use the benchmark controlled fault-label vocabulary.

## Files

- [`truth/truth.json`](truth/truth.json): controlled fault label and scenario traits.
- [`pattern/pattern_case.json`](pattern/pattern_case.json): extracted metric pattern and provenance fields.
- [`pattern/rag_pattern.json`](pattern/rag_pattern.json): compact serialized record used by retrieval.
- [`raw/metrics_long.csv`](raw/metrics_long.csv): released timestamp/value rows for this case.

## Plots

{plot_rows}

Both plot files are generated directly from the released `pattern_case.json`
so every case has the same two-image layout.
"""
        readme.write_text(text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="Source incidents directory to copy")
    parser.add_argument("--copy-incidents", action="store_true", help="Copy --input incidents into the public package")
    parser.add_argument(
        "--skip-plots",
        action="store_true",
        help="Do not regenerate per-case PNG plot files",
    )
    args = parser.parse_args()

    if args.copy_incidents:
        if args.input is None:
            raise SystemExit("--copy-incidents requires --input")
        copy_incidents(args.input, INCIDENTS)

    case_ids = load_case_ids()
    validate_incidents(INCIDENTS, case_ids)
    bucket_map = load_bucket_map()

    case_rows = build_case_manifest(INCIDENTS, case_ids, bucket_map)
    family_rows = build_family_manifest(case_rows)
    metric_rows = build_metric_signal_rows(INCIDENTS, case_ids)
    runtime_rows = build_runtime_summary(INCIDENTS, case_ids)
    window_rows = build_window_duration_summary(INCIDENTS, case_ids)

    write_csv(
        SOURCE / "case_manifest_200.csv",
        [
            "case_id",
            "family_id",
            "run_id",
            "case_group",
            "region",
            "traffic_bucket",
            "intensity",
            "duration_min",
            "observation_window_min",
            "pre_window_min",
            "active_window_min",
            "post_window_min",
            "target_service",
            "target_metric",
            "expected_earliest",
            "expected_dominant",
            "dominant_service",
            "dominant_metric",
            "earliest_service",
            "earliest_metric",
            "change_sequence_rows",
            "metric_rows",
            "execution_available",
            "runtime_profile_available",
            "recovered_from_prometheus",
            "injection_detail",
        ],
        case_rows,
    )
    write_csv(
        SOURCE / "fault_family_manifest.csv",
        [
            "family_id",
            "cases",
            "case_group",
            "target_service",
            "target_metric",
            "duration_min_values",
            "regions",
            "injection_details",
            "runtime_profile_missing_cases",
            "example_case_id",
        ],
        family_rows,
    )
    write_csv(
        SOURCE / "metric_signal_rows.csv",
        [
            "case_id",
            "family_id",
            "metric_row_index",
            "change_order_rank",
            "is_dominant",
            "is_earliest",
            "service",
            "metric_family",
            "earliest_offset_min",
            "peak_offset_min",
            "baseline_mean",
            "baseline_std",
            "earliest_value",
            "earliest_delta_pct",
            "earliest_residual_z",
            "peak_value",
            "peak_delta",
            "peak_delta_pct",
            "peak_residual_z",
            "sustained_trigger_points",
            "rank_score",
        ],
        metric_rows,
    )
    write_csv(
        SOURCE / "runtime_profile_summary.csv",
        [
            "service",
            "runtime_profile_cases",
            "profile_names",
            "scaled_to_three_replicas",
            "desired_replicas_values",
            "available_replicas_values",
            "ready_replicas_values",
            "updated_replicas_values",
        ],
        runtime_rows,
    )
    write_csv(
        SOURCE / "window_duration_summary.csv",
        ["dimension", "value", "cases"],
        window_rows,
    )

    if not args.skip_plots:
        write_case_plots(INCIDENTS, case_ids)
    write_case_readmes(INCIDENTS, case_rows)

    print(
        "OK: wrote Triage-Bench source manifests "
        f"({len(case_rows)} cases, {len(family_rows)} families, {len(metric_rows)} metric rows)"
    )
    if not args.skip_plots:
        print(f"OK: wrote per-case PNG plots for {len(case_ids)} cases")
    print(f"OK: wrote per-case README.md files for {len(case_ids)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
