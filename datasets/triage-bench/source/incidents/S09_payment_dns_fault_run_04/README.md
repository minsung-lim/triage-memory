# S09_payment_dns_fault_run_04

This directory is one Triage-Bench source case. It contains the
controlled fault label, the extracted pre-anchor metric pattern, the compact
retrieval record, released metric rows, and per-case plots colocated with the
source files.

## Case Summary

| Field | Value |
| --- | --- |
| family_id | S09_payment_dns_fault |
| run_id | 04 |
| target_service | payment |
| target_metric | cpu_usage |
| dominant_service_metric | payment/cpu_usage |
| earliest_service_metric | payment/cpu_usage |
| duration_min | 10 |
| pre_window_min | 30 |
| metric_rows | 67 |
| change_sequence_rows | 5 |
| runtime_profile_available | true |
| recovered_from_prometheus | false |

The target fields use the benchmark controlled fault-label vocabulary.

## Files

- [`truth/truth.json`](truth/truth.json): controlled fault label and scenario traits.
- [`pattern/pattern_case.json`](pattern/pattern_case.json): extracted metric pattern and provenance fields.
- [`pattern/rag_pattern.json`](pattern/rag_pattern.json): compact serialized record used by retrieval.
- [`raw/metrics_long.csv`](raw/metrics_long.csv): released timestamp/value rows for this case.

## Plots

- [`plots/incident_metric_panels.png`](plots/incident_metric_panels.png): Dashboard-style metric panels reconstructed from released summary fields in pattern_case.json.
- [`plots/snapshot_overview.png`](plots/snapshot_overview.png): Case overview with target label, four-field record, and change-order timeline from pattern_case.json.

Both plot files are generated directly from the released `pattern_case.json`
so every case has the same two-image layout.
