# Scripts

This directory contains public verification scripts for the Metric-Pattern
Incident Memory public data package.

## Public Verification

Run from `draft/i10p/git`:

```bash
python3 scripts/verify_public_datasets.py
```

The script checks:

- Triage-Field row counts and family counts,
- Triage-Field self-excluded retrieval outcomes,
- Triage-Field paper numbers,
- Triage-Bench case count, family count, and prior-family count,
- Triage-Bench source incident-set completeness,
- Triage-Bench source manifest row counts,
- Triage-Bench per-case README presence,
- Triage-Bench uniform two-plot layout for every case,
- Triage-Bench paper leave-one-out numbers,
- simple sensitive-token guards for released Triage-Field CSV files.

Expected output:

```text
OK: public dataset checks passed
```

The script uses only Python's standard library.

## Triage-Bench Source Manifest Rebuild

Run from `draft/i10p/git`:

```bash
python3 scripts/build_triage_bench_source_release.py
```

This rebuilds the five primary public Triage-Bench source manifests, per-case
README files, and the two generated PNG plots from the included
`source/incidents` files. Regenerating PNG plots requires `matplotlib`.

Maintainers can refresh the included source incidents from a workspace source
copy:

```bash
python3 scripts/build_triage_bench_source_release.py \
  --input /path/to/triage-bench-source/incidents \
  --copy-incidents
```

## Checksum Manifest

Run from `draft/i10p/git`:

```bash
python3 scripts/make_manifest.py > MANIFEST.sha256
```

This creates a SHA-256 manifest for the released files.

## Paper Table Scripts

The paper table builders are grouped under `paper-tables/`:

```bash
python3 paper-tables/scripts/verify_all_paper_tables.py
python3 paper-tables/table-iii-label-retriever-check/scripts/build_table_iii_label_retriever_check.py --check-tex
python3 paper-tables/table-iv-triage-field-cumulative/scripts/build_table_iv_triage_field_cumulative.py --check-tex
python3 paper-tables/table-v-triage-bench-cumulative/scripts/build_table_v_triage_bench_cumulative.py --check-tex
```

The all-table verifier checks Table I--II static TeX rows and rebuilds Tables
III--V from table-specific sources. Table III additionally checks the shared
paper table evaluation path, self-excluded candidate counts, returned-case
separation, and tie-policy assumptions for the retriever rows.
These scripts provide the ISSRE workspace check trail for the candidate paper
tables.

## Rebuild Scope

Triage-Field is rebuilt internally from review inputs. This public
script directory supports verification of the released package and rebuild of
the included Triage-Bench source manifests.
