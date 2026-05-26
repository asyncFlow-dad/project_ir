from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class ConsensusChange:
    eval_id: str
    baseline_top1: str
    candidate_top1: str
    support: int
    sources: list[str]


@dataclass(frozen=True)
class Rank2Promotion:
    eval_id: str
    baseline_top1: str
    candidate_top1: str
    candidate_rank_in_baseline: int
    source: str
    candidate_topk: list[str]


@dataclass(frozen=True)
class PublicResult:
    eval_id: str
    outcome: str
    public_map: float | None = None
    public_mrr: float | None = None


def find_consensus_changes(
    *,
    baseline_path: Path,
    source_paths: Iterable[Path],
    min_support: int = 2,
) -> list[ConsensusChange]:
    baseline_by_id = {str(row["eval_id"]): row for row in _load_rows(baseline_path)}
    votes: dict[str, Counter[str]] = defaultdict(Counter)
    sources_by_vote: dict[tuple[str, str], list[str]] = defaultdict(list)

    for source_path in source_paths:
        for row in _load_rows(source_path):
            eval_id = str(row["eval_id"])
            baseline = baseline_by_id.get(eval_id)
            if baseline is None:
                continue
            baseline_top1 = _top1(baseline["topk"])
            candidate_top1 = _top1(row["topk"])
            if not candidate_top1 or candidate_top1 == baseline_top1:
                continue
            votes[eval_id][candidate_top1] += 1
            sources_by_vote[(eval_id, candidate_top1)].append(str(source_path))

    changes: list[ConsensusChange] = []
    for eval_id in sorted(votes, key=_sort_eval_id):
        candidate_top1, support = votes[eval_id].most_common(1)[0]
        if support < min_support:
            continue
        changes.append(
            ConsensusChange(
                eval_id=eval_id,
                baseline_top1=_top1(baseline_by_id[eval_id]["topk"]),
                candidate_top1=candidate_top1,
                support=support,
                sources=sources_by_vote[(eval_id, candidate_top1)],
            )
        )
    return changes


def find_rank2_promotions(
    *,
    baseline_path: Path,
    source_paths: Iterable[Path],
    excluded_eval_ids: set[str],
) -> list[Rank2Promotion]:
    baseline_by_id = {str(row["eval_id"]): row for row in _load_rows(baseline_path)}
    promotions_by_key: dict[tuple[str, str], Rank2Promotion] = {}

    for source_path in source_paths:
        for row in _load_rows(source_path):
            eval_id = str(row["eval_id"])
            if eval_id in excluded_eval_ids:
                continue
            baseline = baseline_by_id.get(eval_id)
            if baseline is None:
                continue
            baseline_topk = [str(docid) for docid in baseline["topk"]]
            candidate_topk = [str(docid) for docid in row["topk"]]
            baseline_top1 = _top1(baseline_topk)
            candidate_top1 = _top1(candidate_topk)
            if not candidate_top1 or candidate_top1 == baseline_top1:
                continue
            if len(baseline_topk) < 2 or candidate_top1 != baseline_topk[1]:
                continue
            key = (eval_id, candidate_top1)
            promotions_by_key.setdefault(
                key,
                Rank2Promotion(
                    eval_id=eval_id,
                    baseline_top1=baseline_top1,
                    candidate_top1=candidate_top1,
                    candidate_rank_in_baseline=2,
                    source=str(source_path),
                    candidate_topk=candidate_topk,
                ),
            )

    return sorted(promotions_by_key.values(), key=lambda row: _sort_eval_id(row.eval_id))


def write_single_row_promotions(
    *,
    baseline_path: Path,
    promotions: Iterable[Rank2Promotion],
    output_dir: Path,
    name_prefix: str,
) -> list[Path]:
    baseline_rows = _load_rows(baseline_path)
    baseline_by_id = {str(row["eval_id"]): row for row in baseline_rows}
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for promotion in promotions:
        rows = [dict(row) for row in baseline_rows]
        baseline_row = baseline_by_id[promotion.eval_id]
        for row in rows:
            if str(row["eval_id"]) == promotion.eval_id:
                row["topk"] = _promoted_topk(baseline_row["topk"], promotion.candidate_topk)
                break
        target = output_dir / f"{name_prefix}_eval{promotion.eval_id}.jsonl"
        _write_rows(target, rows)
        written.append(target)
    return written


def filter_promotions(
    promotions: Iterable[Rank2Promotion],
    *,
    only_eval_ids: set[str],
) -> list[Rank2Promotion]:
    rows = list(promotions)
    if not only_eval_ids:
        return rows
    return [promotion for promotion in rows if promotion.eval_id in only_eval_ids]


def filter_promotions_by_public_results(
    promotions: Iterable[Rank2Promotion],
    *,
    public_results: Iterable[PublicResult],
) -> list[Rank2Promotion]:
    blocked = {result.eval_id for result in public_results}
    return [promotion for promotion in promotions if promotion.eval_id not in blocked]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find eval rows where multiple candidate submissions agree on a new top-1."
    )
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--source", action="append", required=True, type=Path)
    parser.add_argument("--min-support", default=2, type=int)
    parser.add_argument("--rank2-only", action="store_true")
    parser.add_argument("--exclude-eval-id", action="append", default=[])
    parser.add_argument("--only-eval-id", action="append", default=[])
    parser.add_argument("--public-results", type=Path, default=None)
    parser.add_argument("--single-output-dir", type=Path, default=None)
    parser.add_argument("--name-prefix", default="rank2_promotion")
    args = parser.parse_args()

    if args.rank2_only:
        promotions = find_rank2_promotions(
            baseline_path=args.baseline,
            source_paths=args.source,
            excluded_eval_ids={str(eval_id) for eval_id in args.exclude_eval_id},
        )
        promotions = filter_promotions(
            promotions,
            only_eval_ids={str(eval_id) for eval_id in args.only_eval_id},
        )
        if args.public_results is not None:
            promotions = filter_promotions_by_public_results(
                promotions,
                public_results=load_public_results(args.public_results),
            )
        for promotion in promotions:
            print(
                f"eval_id={promotion.eval_id} baseline_top1={promotion.baseline_top1} "
                f"candidate_top1={promotion.candidate_top1} rank_in_baseline=2 "
                f"source={promotion.source}"
            )
        if args.single_output_dir is not None:
            written = write_single_row_promotions(
                baseline_path=args.baseline,
                promotions=promotions,
                output_dir=args.single_output_dir,
                name_prefix=args.name_prefix,
            )
            for path in written:
                print(f"wrote={path}")
        return 0

    changes = find_consensus_changes(
        baseline_path=args.baseline,
        source_paths=args.source,
        min_support=args.min_support,
    )
    for change in changes:
        print(
            f"eval_id={change.eval_id} baseline_top1={change.baseline_top1} "
            f"candidate_top1={change.candidate_top1} support={change.support}"
        )
    return 0


def load_public_results(path: Path) -> list[PublicResult]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("public results must be a JSON array")
    results: list[PublicResult] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"public results row {index} must be an object")
        results.append(
            PublicResult(
                eval_id=str(row["eval_id"]),
                outcome=str(row["outcome"]),
                public_map=_optional_float(row.get("map")),
                public_mrr=_optional_float(row.get("mrr")),
            )
        )
    return results


def _top1(topk: list[str]) -> str:
    return topk[0] if topk else ""


def _promoted_topk(baseline_topk: list[str], candidate_topk: list[str]) -> list[str]:
    promoted: list[str] = []
    for docid in candidate_topk + baseline_topk:
        if docid and docid not in promoted:
            promoted.append(str(docid))
        if len(promoted) == 3:
            break
    return promoted


def _sort_eval_id(eval_id: str) -> tuple[int, str]:
    return (int(eval_id), eval_id) if eval_id.isdigit() else (10**9, eval_id)


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _optional_float(value: Any) -> float | None:
    return float(value) if value is not None else None


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
