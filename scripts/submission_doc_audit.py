from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class AuditRow:
    eval_id: str
    query: str
    baseline_top1: str
    candidate_top1: str
    baseline_text: str
    candidate_text: str


def build_audit_rows(
    *,
    candidate_path: Path,
    baseline_path: Path,
    corpus_path: Path,
    eval_ids: Iterable[str],
) -> list[AuditRow]:
    candidate_by_id = {str(row["eval_id"]): row for row in _load_rows(candidate_path)}
    baseline_by_id = {str(row["eval_id"]): row for row in _load_rows(baseline_path)}
    docs_by_id = {str(row["docid"]): row for row in _load_rows(corpus_path)}

    rows: list[AuditRow] = []
    for eval_id in [str(value) for value in eval_ids]:
        candidate = candidate_by_id[eval_id]
        baseline = baseline_by_id[eval_id]
        baseline_top1 = _top1(baseline["topk"])
        candidate_top1 = _top1(candidate["topk"])
        rows.append(
            AuditRow(
                eval_id=eval_id,
                query=str(candidate.get("standalone_query") or baseline.get("standalone_query") or ""),
                baseline_top1=baseline_top1,
                candidate_top1=candidate_top1,
                baseline_text=_doc_text(docs_by_id.get(baseline_top1)),
                candidate_text=_doc_text(docs_by_id.get(candidate_top1)),
            )
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Print query and top-1 document text for submission diffs.")
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--eval-id", action="append", required=True)
    parser.add_argument("--max-chars", type=int, default=500)
    args = parser.parse_args()

    rows = build_audit_rows(
        candidate_path=args.candidate,
        baseline_path=args.baseline,
        corpus_path=args.corpus,
        eval_ids=args.eval_id,
    )
    for row in rows:
        print(f"eval_id={row.eval_id}")
        print(f"query={row.query}")
        print(f"baseline_top1={row.baseline_top1}")
        print(_truncate(row.baseline_text, args.max_chars))
        print(f"candidate_top1={row.candidate_top1}")
        print(_truncate(row.candidate_text, args.max_chars))
        print()
    return 0


def _top1(topk: list[str]) -> str:
    return topk[0] if topk else ""


def _doc_text(row: dict[str, Any] | None) -> str:
    if row is None:
        return ""
    title = str(row.get("title") or "").strip()
    content = str(row.get("content") or "").strip()
    return "\n".join(part for part in [title, content] if part)


def _truncate(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 3].rstrip() + "..."


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
