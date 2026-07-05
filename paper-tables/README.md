# Paper Table Artifacts

This directory contains table-specific base files and scripts for the paper
tables in `draft/i10p/candidate/main.tex`.

These paper-table artifacts provide the ISSRE workspace check path for the
submitted table rows.

## Layout

```text
paper-tables/
  scripts/
    verify_all_paper_tables.py
  table-iii-label-retriever-check/
    base/
    scripts/
  table-iv-triage-field-cumulative/
    base/
    scripts/
  table-v-triage-bench-cumulative/
    base/
    scripts/
```

## Build Commands

Run from `draft/i10p/git`:

```bash
python3 paper-tables/scripts/verify_all_paper_tables.py
python3 paper-tables/table-iii-label-retriever-check/scripts/build_table_iii_label_retriever_check.py
python3 paper-tables/table-iv-triage-field-cumulative/scripts/build_table_iv_triage_field_cumulative.py
python3 paper-tables/table-v-triage-bench-cumulative/scripts/build_table_v_triage_bench_cumulative.py
```

`verify_all_paper_tables.py` checks all tables in the candidate TeX. Tables I
and II are static example/definition tables, so the runner checks their
captions and rows in `candidate/main.tex`. Tables III--V are result tables, so
the runner calls the table-specific builders below and verifies their emitted
rows against the candidate TeX.

To check that emitted result rows appear in the candidate paper:

```bash
python3 paper-tables/table-iii-label-retriever-check/scripts/build_table_iii_label_retriever_check.py --check-tex
python3 paper-tables/table-iv-triage-field-cumulative/scripts/build_table_iv_triage_field_cumulative.py --check-tex
python3 paper-tables/table-v-triage-bench-cumulative/scripts/build_table_v_triage_bench_cumulative.py --check-tex
```

Table III also verifies its label and retriever rows against the source result
files and checks the shared representation, self-exclusion, candidate-count,
returned-case, and tie-policy assumptions:

```bash
python3 paper-tables/table-iii-label-retriever-check/scripts/build_table_iii_label_retriever_check.py --check-tex --verify-sources --verify-unified-protocol
```

The Table III retriever rows use the same released four-field record for each
dataset and one self-excluded protocol.
