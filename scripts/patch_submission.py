from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class PatchSummary:
    rows: int
    changed: int
    eval_ids: list[str]


def patch_submission(
    *,
    target_path: Path,
    output_path: Path,
    source_path: Path,
    eval_ids: Iterable[str],
) -> PatchSummary:
    target_rows = _load_rows(target_path)
    source_by_id = {str(row["eval_id"]): row for row in _load_rows(source_path)}
    selected_ids = [str(eval_id) for eval_id in eval_ids]
    selected = set(selected_ids)

    patched_rows: list[dict[str, Any]] = []
    changed = 0
    for row in target_rows:
        eval_id = str(row["eval_id"])
        if eval_id in selected:
            if eval_id not in source_by_id:
                raise ValueError(f"Source missing eval_id {eval_id}")
            patched_rows.append(source_by_id[eval_id])
            if row.get("topk") != source_by_id[eval_id].get("topk"):
                changed += 1
            continue
        patched_rows.append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in patched_rows),
        encoding="utf-8",
    )
    return PatchSummary(rows=len(patched_rows), changed=changed, eval_ids=selected_ids)


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch selected eval rows in a JSONL submission.")
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--eval-id", action="append", required=True)
    args = parser.parse_args()

    summary = patch_submission(
        target_path=args.target,
        source_path=args.source,
        output_path=args.output,
        eval_ids=args.eval_id,
    )
    print(
        f"rows={summary.rows} changed={summary.changed} "
        f"eval_ids={','.join(summary.eval_ids)} output={args.output}"
    )
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


if __name__ == "__main__":
    raise SystemExit(main())
