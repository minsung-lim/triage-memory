# Triage-Bench Source

This directory contains the public source release for Triage-Bench. The
data is from a controlled OpenTelemetry microservice benchmark.

## Files

| File | Purpose |
| --- | --- |
| `incidents/<case_id>/README.md` | Per-case guide with summary fields and plot links. |
| `incidents/<case_id>/truth/truth.json` | Controlled fault label and scenario traits for a case. |
| `incidents/<case_id>/pattern/pattern_case.json` | Extracted pre-anchor metric pattern, runtime profile, load profile, and injection detail when available. |
| `incidents/<case_id>/pattern/rag_pattern.json` | Compact serialized pattern used by retrieval experiments. |
| `incidents/<case_id>/raw/metrics_long.csv` | Released timestamp/value rows for the case. |
| `incidents/<case_id>/plots/snapshot_overview.png` | Case overview with target label, four-field record, and change-order timeline from the released `pattern_case.json`. |
| `incidents/<case_id>/plots/incident_metric_panels.png` | Dashboard-style metric panels reconstructed from released summary fields in `pattern_case.json`. |
| `case_manifest_200.csv` | One row per case, extracted from the source incidents. |
| `fault_family_manifest.csv` | One row per fault family with controlled fault label and actuator summary. |
| `metric_signal_rows.csv` | Service-metric rows extracted from every `pattern_case.json`. |
| `runtime_profile_summary.csv` | Runtime profile summary for the 25 instrumented services. |
| `window_duration_summary.csv` | Window, duration, execution, and provenance counts. |
| `four_field_records.csv` | Auxiliary source four-field rows. |
| `raw_metric_manifest.csv` | Auxiliary row-count manifest for released benchmark raw metric CSVs. |

## Per-Case Layout

Each case is self-contained:

```text
incidents/<case_id>/
  README.md
  truth/truth.json
  pattern/pattern_case.json
  pattern/rag_pattern.json
  raw/metrics_long.csv
  plots/
    snapshot_overview.png
    incident_metric_panels.png
```

Both PNG files are generated from the released `pattern_case.json`, so every
case has the same two-image layout. The metric-panel plot is a summary-field
reconstruction for inspection.

The source files use benchmark-format field names for controlled fault labels.

## Rebuild

From the package root:

```bash
python3 scripts/build_triage_bench_source_release.py
```

Maintainers can refresh the included incidents from a workspace source copy:

```bash
python3 scripts/build_triage_bench_source_release.py \
  --input /path/to/triage-bench-source/incidents \
  --copy-incidents
```

The source incidents keep the pre-anchor metric patterns used for the paper's
alert-time incident triage task. The live benchmark campaign can contain
additional post-anchor collection and recovery context. Retrieval uses the
`anchor-30m` to `anchor` view.

The rebuild writes the five primary source manifests, per-case `README.md`
files, and both per-case PNG plots. Regenerating PNG plots requires
`matplotlib`.
