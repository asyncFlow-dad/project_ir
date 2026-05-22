from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DiffSummary:
    rows: int
    empty_topk: int
    duplicate_topk: int
    changed: int
    top1_changed: int
    empty_to_filled: int
    filled_to_empty: int
    changed_eval_ids: list[str]
    top1_changed_eval_ids: list[str]
    sha256: str


def summarize_submission_diff(candidate_path: Path, baseline_path: Path) -> DiffSummary:
    candidate_rows = _load_rows(candidate_path)
    baseline_by_id = {str(row["eval_id"]): row for row in _load_rows(baseline_path)}
    changed_eval_ids: list[str] = []
    top1_changed_eval_ids: list[str] = []
    empty_to_filled = 0
    filled_to_empty = 0

    for row in candidate_rows:
        eval_id = str(row["eval_id"])
        baseline = baseline_by_id.get(eval_id)
        topk = row["topk"]
        baseline_topk = baseline["topk"] if baseline is not None else []
        if baseline is None or topk != baseline_topk:
            changed_eval_ids.append(eval_id)
        if _top1(topk) != _top1(baseline_topk):
            top1_changed_eval_ids.append(eval_id)
        if baseline_topk and not topk:
            filled_to_empty += 1
        if not baseline_topk and topk:
            empty_to_filled += 1

    return DiffSummary(
        rows=len(candidate_rows),
        empty_topk=sum(1 for row in candidate_rows if not row["topk"]),
        duplicate_topk=sum(1 for row in candidate_rows if len(row["topk"]) != len(set(row["topk"]))),
        changed=len(changed_eval_ids),
        top1_changed=len(top1_changed_eval_ids),
        empty_to_filled=empty_to_filled,
        filled_to_empty=filled_to_empty,
        changed_eval_ids=changed_eval_ids,
        top1_changed_eval_ids=top1_changed_eval_ids,
        sha256=hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Report row-level differences between submissions.")
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    args = parser.parse_args()

    summary = summarize_submission_diff(args.candidate, args.baseline)
    print(f"rows={summary.rows} empty_topk={summary.empty_topk} duplicate_topk={summary.duplicate_topk}")
    print(
        "diff="
        f"changed={summary.changed} top1_changed={summary.top1_changed} "
        f"empty_to_filled={summary.empty_to_filled} filled_to_empty={summary.filled_to_empty}"
    )
    print(f"changed_eval_ids={','.join(summary.changed_eval_ids)}")
    print(f"top1_changed_eval_ids={','.join(summary.top1_changed_eval_ids)}")
    print(f"sha256={summary.sha256}")
    return 0


def _top1(topk: list[str]) -> str:
    return topk[0] if topk else ""


def _load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                raise ValueError(f"Blank line at {line_number}")
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"Line {line_number} is not a JSON object")
            rows.append(row)
    return rows


if __name__ == "__main__":
    raise SystemExit(main())
