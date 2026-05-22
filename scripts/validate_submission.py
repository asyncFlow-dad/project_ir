from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_KEYS = {"eval_id", "standalone_query", "topk", "answer", "references"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate leaderboard JSONL submission.")
    parser.add_argument("submission", type=Path)
    parser.add_argument("--expected-rows", type=int, default=220)
    parser.add_argument("--experiment-name", default="")
    parser.add_argument("--map", type=float, default=None)
    parser.add_argument("--mrr", type=float, default=None)
    parser.add_argument("--record-dir", type=Path, default=Path("submissions/experiments"))
    parser.add_argument("--compare-to", type=Path, default=None)
    args = parser.parse_args()

    rows = _load_rows(args.submission)
    _validate_rows(rows, expected_rows=args.expected_rows)
    empty_topk = sum(1 for row in rows if not row["topk"])
    duplicate_topk = sum(1 for row in rows if len(row["topk"]) != len(set(row["topk"])))
    print(
        f"rows={len(rows)} empty_topk={empty_topk} duplicate_topk={duplicate_topk} "
        f"first_char={args.submission.read_text(encoding='utf-8')[:1]}"
    )
    if args.compare_to is not None:
        baseline_rows = _load_rows(args.compare_to)
        _print_diff_summary(rows, baseline_rows)

    if args.experiment_name:
        args.record_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "name": args.experiment_name,
            "submission": str(args.submission),
            "rows": len(rows),
            "empty_topk": empty_topk,
            "duplicate_topk": duplicate_topk,
            "map": args.map,
            "mrr": args.mrr,
            "first_eval_id": rows[0]["eval_id"] if rows else None,
            "last_eval_id": rows[-1]["eval_id"] if rows else None,
        }
        target = args.record_dir / f"{args.experiment_name}.json"
        target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"record={target}")
    return 0


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


def _validate_rows(rows: list[dict[str, Any]], *, expected_rows: int) -> None:
    if len(rows) != expected_rows:
        raise ValueError(f"Expected {expected_rows} rows, got {len(rows)}")
    for index, row in enumerate(rows, start=1):
        missing = REQUIRED_KEYS - set(row)
        if missing:
            raise ValueError(f"Line {index} missing keys: {sorted(missing)}")
        if not isinstance(row["topk"], list):
            raise ValueError(f"Line {index} topk must be list")
        if len(row["topk"]) > 3:
            raise ValueError(f"Line {index} topk length > 3")
        if len(row["topk"]) != len(set(row["topk"])):
            raise ValueError(f"Line {index} topk contains duplicates")
        if not isinstance(row["references"], list):
            raise ValueError(f"Line {index} references must be list")


def _print_diff_summary(rows: list[dict[str, Any]], baseline_rows: list[dict[str, Any]]) -> None:
    baseline_by_id = {row["eval_id"]: row for row in baseline_rows}
    changed = 0
    top1_changed = 0
    empty_to_filled = 0
    filled_to_empty = 0
    for row in rows:
        baseline = baseline_by_id.get(row["eval_id"])
        if baseline is None:
            changed += 1
            continue
        topk = row["topk"]
        baseline_topk = baseline["topk"]
        if topk != baseline_topk:
            changed += 1
        if (topk[:1] or [""])[0] != (baseline_topk[:1] or [""])[0]:
            top1_changed += 1
        if baseline_topk and not topk:
            filled_to_empty += 1
        if not baseline_topk and topk:
            empty_to_filled += 1
    print(
        "diff_against_baseline="
        f"changed={changed} top1_changed={top1_changed} "
        f"empty_to_filled={empty_to_filled} filled_to_empty={filled_to_empty}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
