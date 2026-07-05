# Table V: Triage-Bench Cumulative Field Addition

Builds Table V in `draft/i10p/candidate/main.tex`.

## Base Files

- `base/triage_bench_ablation_results.csv`: table rows printed in the paper.
- `base/triage_bench_leave_one_out_all_200.json`: leave-one-out check source
  for the final four-field row and tie-policy metadata.
- `base/triage_bench_summary_200.json`: benchmark scope metadata.

## Command

Run from this table directory:

```bash
python3 scripts/build_table_v_triage_bench_cumulative.py
python3 scripts/build_table_v_triage_bench_cumulative.py --check-tex
```
