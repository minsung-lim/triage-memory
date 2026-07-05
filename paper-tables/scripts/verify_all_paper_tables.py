#!/usr/bin/env python3
"""Verify all paper tables against the candidate TeX and table sources."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GIT_ROOT = ROOT.parent
I10P_ROOT = GIT_ROOT.parent
DEFAULT_TEX = I10P_ROOT / "candidate" / "main.tex"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def normalized(text: str) -> str:
    return " ".join(text.split())


def require_tex_contains(tex: str, needle: str) -> None:
    require(normalized(needle) in normalized(tex), f"Missing TeX fragment: {needle}")


def check_static_tables(tex_path: Path) -> None:
    tex = tex_path.read_text()

    # Table I is an abstracted example table, not a recomputed result table.
    require_tex_contains(tex, r"\caption{Service separation in abstracted Triage-Field cases.}")
    for fragment in [
        r"O03 & A latency  & A error                  & datastore B",
        r"O15 & A resource & D response-count drop    & service B",
        r"O29 & A error    & internal throughput drop & datastore D",
    ]:
        require_tex_contains(tex, fragment)

    # Table II defines extraction fields; it has no result counts to recompute.
    require_tex_contains(
        tex,
        r"\caption{The four retrieval fields, their extraction rules, and the alert-time question each preserves.}",
    )
    for fragment in [
        r"Alert message & Service-metric pair named in the alert message or alarm & Where was impact reported?",
        r"Maximum change & Pair with the largest baseline-normalized change in the 30-minute window & What changed most?",
        r"Earliest abnormal & Pair that first enters its abnormal range & What moved first?",
        r"Change order & Order in which abnormal pairs appeared & How did the signal unfold?",
    ]:
        require_tex_contains(tex, fragment)


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=GIT_ROOT, check=True)


def check_generated_tables(tex_path: Path) -> None:
    tex_arg = str(tex_path)
    run(
        [
            sys.executable,
            "paper-tables/table-iii-label-retriever-check/scripts/build_table_iii_label_retriever_check.py",
            "--check-tex",
            "--verify-sources",
            "--verify-unified-protocol",
            "--tex",
            tex_arg,
        ]
    )
    run(
        [
            sys.executable,
            "paper-tables/table-iv-triage-field-cumulative/scripts/build_table_iv_triage_field_cumulative.py",
            "--check-tex",
            "--tex",
            tex_arg,
        ]
    )
    run(
        [
            sys.executable,
            "paper-tables/table-v-triage-bench-cumulative/scripts/build_table_v_triage_bench_cumulative.py",
            "--check-tex",
            "--tex",
            tex_arg,
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tex", type=Path, default=DEFAULT_TEX, help="Path to candidate main.tex")
    args = parser.parse_args()

    try:
        check_static_tables(args.tex)
        print("OK: Table I--II static TeX checks passed", flush=True)
        check_generated_tables(args.tex)
    except Exception as exc:  # noqa: BLE001 - command-line verifier
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("OK: all paper table checks passed", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
