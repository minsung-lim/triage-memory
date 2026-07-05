# Table IV: Triage-Field Cumulative Field Addition

Builds Table IV in `draft/i10p/candidate/main.tex`.

## Base Files

- `base/triage_field_aggregate_results.csv`: cumulative field-addition rows.
- `base/triage_field_retrieval_results.csv`: four-field per-case retrieval
  outcomes used to check the `23/30` family and `24/30`
  first-service counts.

## Command

Run from this table directory:

```bash
python3 scripts/build_table_iv_triage_field_cumulative.py
python3 scripts/build_table_iv_triage_field_cumulative.py --check-tex
```
