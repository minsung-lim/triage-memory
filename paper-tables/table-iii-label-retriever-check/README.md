# Table III: Label Agreement and Retriever Check

Builds Table III in `draft/i10p/candidate/main.tex`.

## Base Files

- `base/label_agreement_summary.csv`: reviewer agreement summary.
- `base/retriever_table_sources.csv`: retriever rows and source notes.
- `base/retriever_summary.csv`: table source values for TF-IDF,
  BM25, Dense MiniLM, and ColBERT.
- `base/retriever_per_case.csv`: per-case check rows used to check
  self-exclusion, candidate counts, and returned-case separation.

The retriever rows use the same released four-field record for each dataset.
The TF-IDF row is the default retriever used by Tables IV--V; the other rows
are retriever checks under the same self-excluded candidate set.

`base/retriever_summary.csv` contains retriever check rows for protocol
consistency. Table IV is built from
`table-iv-triage-field-cumulative/base/triage_field_aggregate_results.csv`.
## Command

Run from this table directory:

```bash
python3 scripts/build_table_iii_label_retriever_check.py
python3 scripts/build_table_iii_label_retriever_check.py --check-tex
python3 scripts/build_table_iii_label_retriever_check.py --check-tex --verify-sources --verify-unified-protocol
```

`--verify-sources` checks the Table III rows against
`base/retriever_summary.csv`.

`--verify-unified-protocol` checks the shared protocol assumptions used by the
rows: Triage-Field and Triage-Bench representation names, case counts,
self-excluded candidate counts, returned-case separation, and tie-policy
families. The retriever rows use one comparable protocol with shared retrieval
settings.
