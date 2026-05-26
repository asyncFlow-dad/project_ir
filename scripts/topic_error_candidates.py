from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ir_search.indexer import CorpusDocument, build_index, search
from scripts.ollama_candidate_judge import (
    Judgement,
    judge_pairwise_candidate,
    judge_topic_error_candidate,
    promoted_topk,
)
from scripts.submission_doc_audit import relevance_score
from scripts.submission_patch_candidates import load_public_results


@dataclass(frozen=True)
class RecallPreset:
    candidate_pool: int
    per_eval_candidates: int
    max_baseline_relevance: float
    min_candidate_relevance: float
    min_delta: float
    recall_limit: int
    min_topic_confidence: float
    min_pairwise_confidence: float


@dataclass(frozen=True)
class RecallCandidate:
    eval_id: str
    query: str
    tier: str
    baseline_top1: str
    candidate_top1: str
    baseline_relevance: float
    candidate_relevance: float
    relevance_delta: float
    candidate_topk: list[str]


@dataclass(frozen=True)
class AcceptedCandidate:
    recall: RecallCandidate
    topic_confidence: float
    topic_reason: str
    pairwise_confidence: float
    pairwise_reason: str


@dataclass(frozen=True)
class RejectedCandidate:
    recall: RecallCandidate
    stage: str
    winner: str
    docid: str
    confidence: float
    reason: str


def generate_recall_candidates(
    *,
    baseline_path: Path,
    corpus_path: Path,
    locked_eval_ids: set[str],
    tier: str,
    candidate_pool: int,
    per_eval_candidates: int,
    max_baseline_relevance: float,
    min_candidate_relevance: float,
    min_delta: float,
    limit: int,
) -> list[RecallCandidate]:
    baseline_rows = _load_rows(baseline_path)
    docs_by_id = {str(row["docid"]): row for row in _load_rows(corpus_path)}
    doc_texts = {docid: _doc_text(row) for docid, row in docs_by_id.items()}
    index = build_index(
        [CorpusDocument(id=docid, path=Path(docid), text=text) for docid, text in doc_texts.items()]
    )
    candidates: list[RecallCandidate] = []
    for row in baseline_rows:
        eval_id = str(row["eval_id"])
        if eval_id in locked_eval_ids:
            continue
        query = str(row.get("standalone_query") or "").strip()
        baseline_topk = [str(docid) for docid in row.get("topk") or []]
        if not query or not baseline_topk:
            continue
        baseline_top1 = baseline_topk[0]
        baseline_relevance = relevance_score(query, doc_texts.get(baseline_top1, ""))
        if baseline_relevance > max_baseline_relevance:
            continue
        per_eval: list[RecallCandidate] = []
        for result in search(index, query, limit=max(candidate_pool, len(baseline_topk) + 1)):
            docid = result.document.id
            if docid in baseline_topk:
                continue
            candidate_relevance = relevance_score(query, result.document.text)
            relevance_delta = round(candidate_relevance - baseline_relevance, 6)
            if candidate_relevance < min_candidate_relevance or relevance_delta < min_delta:
                continue
            per_eval.append(
                RecallCandidate(
                    eval_id=eval_id,
                    query=query,
                    tier=tier,
                    baseline_top1=baseline_top1,
                    candidate_top1=docid,
                    baseline_relevance=baseline_relevance,
                    candidate_relevance=candidate_relevance,
                    relevance_delta=relevance_delta,
                    candidate_topk=promoted_topk(baseline_topk, docid),
                )
            )
            if len(per_eval) >= per_eval_candidates:
                break
        candidates.extend(per_eval)
    return sorted(
        candidates,
        key=lambda item: (
            item.baseline_relevance,
            -item.relevance_delta,
            -item.candidate_relevance,
            int(item.eval_id) if item.eval_id.isdigit() else 10**9,
        ),
    )[:limit]


def generate_preset_recall_candidates(
    *,
    baseline_path: Path,
    corpus_path: Path,
    locked_eval_ids: set[str],
    preset: str,
    candidate_pool: int,
    per_eval_candidates: int,
    max_baseline_relevance: float,
    min_candidate_relevance: float,
    min_delta: float,
    recall_limit: int,
) -> list[RecallCandidate]:
    if preset != "balanced":
        return generate_recall_candidates(
            baseline_path=baseline_path,
            corpus_path=corpus_path,
            locked_eval_ids=locked_eval_ids,
            tier=preset,
            candidate_pool=candidate_pool,
            per_eval_candidates=per_eval_candidates,
            max_baseline_relevance=max_baseline_relevance,
            min_candidate_relevance=min_candidate_relevance,
            min_delta=min_delta,
            limit=recall_limit,
        )

    tier_a = generate_recall_candidates(
        baseline_path=baseline_path,
        corpus_path=corpus_path,
        locked_eval_ids=locked_eval_ids,
        tier="tier_a",
        candidate_pool=candidate_pool,
        per_eval_candidates=per_eval_candidates,
        max_baseline_relevance=0.22,
        min_candidate_relevance=0.45,
        min_delta=0.20,
        limit=recall_limit,
    )
    tier_b = generate_recall_candidates(
        baseline_path=baseline_path,
        corpus_path=corpus_path,
        locked_eval_ids=locked_eval_ids,
        tier="tier_b",
        candidate_pool=max(candidate_pool, 220),
        per_eval_candidates=per_eval_candidates,
        max_baseline_relevance=0.30,
        min_candidate_relevance=0.50,
        min_delta=0.18,
        limit=recall_limit,
    )
    return _dedupe_recall_candidates([*tier_a, *tier_b])[:recall_limit]


def recall_from_submission_dir(
    *,
    baseline_path: Path,
    corpus_path: Path,
    candidate_dir: Path,
    locked_eval_ids: set[str],
    tier: str,
) -> list[RecallCandidate]:
    baseline_rows = _load_rows(baseline_path)
    baseline_by_id = {str(row["eval_id"]): row for row in baseline_rows}
    docs_by_id = {str(row["docid"]): row for row in _load_rows(corpus_path)}
    doc_texts = {docid: _doc_text(row) for docid, row in docs_by_id.items()}
    candidates: list[RecallCandidate] = []

    for path in sorted(candidate_dir.glob("*.jsonl")):
        rows = _load_rows(path)
        if len(rows) != len(baseline_rows):
            continue
        changed: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for row in rows:
            eval_id = str(row["eval_id"])
            baseline = baseline_by_id.get(eval_id)
            if baseline is None:
                continue
            if [str(docid) for docid in row.get("topk") or []] != [
                str(docid) for docid in baseline.get("topk") or []
            ]:
                changed.append((baseline, row))
        if len(changed) != 1:
            continue
        baseline, row = changed[0]
        eval_id = str(row["eval_id"])
        if eval_id in locked_eval_ids:
            continue
        query = str(row.get("standalone_query") or baseline.get("standalone_query") or "").strip()
        baseline_topk = [str(docid) for docid in baseline.get("topk") or []]
        candidate_topk = [str(docid) for docid in row.get("topk") or []]
        if not query or not baseline_topk or not candidate_topk:
            continue
        baseline_top1 = baseline_topk[0]
        candidate_top1 = candidate_topk[0]
        if candidate_top1 == baseline_top1:
            continue
        baseline_relevance = relevance_score(query, doc_texts.get(baseline_top1, ""))
        candidate_relevance = relevance_score(query, doc_texts.get(candidate_top1, ""))
        candidates.append(
            RecallCandidate(
                eval_id=eval_id,
                query=query,
                tier=tier,
                baseline_top1=baseline_top1,
                candidate_top1=candidate_top1,
                baseline_relevance=baseline_relevance,
                candidate_relevance=candidate_relevance,
                relevance_delta=round(candidate_relevance - baseline_relevance, 6),
                candidate_topk=promoted_topk(baseline_topk, candidate_top1),
            )
        )
    return _dedupe_recall_candidates(candidates)


def review_recall_candidates(
    *,
    candidates: Iterable[RecallCandidate],
    doc_texts: dict[str, str],
    provider: str,
    model: str,
    host: str,
    api_key: str | None,
    min_topic_confidence: float,
    min_pairwise_confidence: float,
    limit: int,
    rejected: list[RejectedCandidate] | None = None,
) -> list[AcceptedCandidate]:
    accepted: list[AcceptedCandidate] = []
    for candidate in candidates:
        topic = judge_topic_error_candidate(
            query=candidate.query,
            baseline_docid=candidate.baseline_top1,
            baseline_text=doc_texts.get(candidate.baseline_top1, ""),
            candidate_docid=candidate.candidate_top1,
            candidate_text=doc_texts.get(candidate.candidate_top1, ""),
            model=model,
            host=host,
            provider=provider,
            api_key=api_key,
        )
        if not _candidate_wins(topic, candidate.candidate_top1, min_topic_confidence):
            if rejected is not None:
                rejected.append(
                    RejectedCandidate(
                        recall=candidate,
                        stage="topic",
                        winner=topic.winner,
                        docid=topic.docid,
                        confidence=topic.confidence,
                        reason=topic.reason,
                    )
                )
            continue
        pairwise = judge_pairwise_candidate(
            query=candidate.query,
            baseline_docid=candidate.baseline_top1,
            baseline_text=doc_texts.get(candidate.baseline_top1, ""),
            candidate_docid=candidate.candidate_top1,
            candidate_text=doc_texts.get(candidate.candidate_top1, ""),
            model=model,
            host=host,
            provider=provider,
            api_key=api_key,
        )
        if not _candidate_wins(pairwise, candidate.candidate_top1, min_pairwise_confidence):
            if rejected is not None:
                rejected.append(
                    RejectedCandidate(
                        recall=candidate,
                        stage="pairwise",
                        winner=pairwise.winner,
                        docid=pairwise.docid,
                        confidence=pairwise.confidence,
                        reason=pairwise.reason,
                    )
                )
            continue
        accepted.append(
            AcceptedCandidate(
                recall=candidate,
                topic_confidence=topic.confidence,
                topic_reason=topic.reason,
                pairwise_confidence=pairwise.confidence,
                pairwise_reason=pairwise.reason,
            )
        )
        if len(accepted) >= limit:
            break
    return accepted


def write_outputs(
    *,
    baseline_path: Path,
    corpus_path: Path,
    accepted: Iterable[AcceptedCandidate],
    output_dir: Path,
    name_prefix: str,
) -> list[Path]:
    baseline_rows = _load_rows(baseline_path)
    docs_by_id = {str(row["docid"]): row for row in _load_rows(corpus_path)}
    doc_texts = {docid: _doc_text(row) for docid, row in docs_by_id.items()}
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for item in accepted:
        rows = [dict(row) for row in baseline_rows]
        recall = item.recall
        for row in rows:
            if str(row["eval_id"]) != recall.eval_id:
                continue
            row["topk"] = recall.candidate_topk
            row["references"] = [
                {
                    "score": item.topic_confidence if index == 0 else 0.0,
                    "docid": docid,
                    "content": doc_texts[docid],
                }
                for index, docid in enumerate(recall.candidate_topk)
                if docid in doc_texts
            ]
            break
        target = output_dir / f"{name_prefix}_eval{recall.eval_id}.jsonl"
        _write_rows(target, rows)
        written.append(target)
    return written


def write_audit(
    *,
    path: Path,
    recall_candidates: Iterable[RecallCandidate],
    accepted: Iterable[AcceptedCandidate],
    rejected: Iterable[RejectedCandidate] = (),
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "recall_candidates": [candidate.__dict__ for candidate in recall_candidates],
        "accepted": [
            {
                **item.recall.__dict__,
                "topic_confidence": item.topic_confidence,
                "topic_reason": item.topic_reason,
                "pairwise_confidence": item.pairwise_confidence,
                "pairwise_reason": item.pairwise_reason,
            }
            for item in accepted
        ],
        "rejected": [
            {
                **item.recall.__dict__,
                "reject_stage": item.stage,
                "judge_winner": item.winner,
                "judge_docid": item.docid,
                "judge_confidence": item.confidence,
                "judge_reason": item.reason,
            }
            for item in rejected
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Find eval205-like topic-error candidates.")
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--public-results", required=True, type=Path)
    parser.add_argument("--preset", choices=("strict", "balanced", "wide"), default="strict")
    parser.add_argument("--candidate-submission-dir", action="append", type=Path, default=[])
    parser.add_argument("--provider", choices=("ollama", "upstage"), default="upstage")
    parser.add_argument("--model", default="solar-pro3")
    parser.add_argument("--host", default=os.environ.get("UPSTAGE_BASE_URL", "https://api.upstage.ai/v1"))
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--candidate-pool", type=int, default=None)
    parser.add_argument("--per-eval-candidates", type=int, default=None)
    parser.add_argument("--max-baseline-relevance", type=float, default=None)
    parser.add_argument("--min-candidate-relevance", type=float, default=None)
    parser.add_argument("--min-delta", type=float, default=None)
    parser.add_argument("--recall-limit", type=int, default=None)
    parser.add_argument("--accepted-limit", type=int, default=3)
    parser.add_argument("--min-topic-confidence", type=float, default=None)
    parser.add_argument("--min-pairwise-confidence", type=float, default=None)
    parser.add_argument("--audit-output", type=Path, default=None)
    parser.add_argument("--single-output-dir", type=Path, default=None)
    parser.add_argument("--name-prefix", default="topic_error_candidate")
    args = parser.parse_args()

    preset = _preset_defaults(args.preset)
    locked = {result.eval_id for result in load_public_results(args.public_results)}
    recall_candidates = generate_preset_recall_candidates(
        baseline_path=args.baseline,
        corpus_path=args.corpus,
        locked_eval_ids=locked,
        preset=args.preset,
        candidate_pool=args.candidate_pool or preset.candidate_pool,
        per_eval_candidates=args.per_eval_candidates or preset.per_eval_candidates,
        max_baseline_relevance=args.max_baseline_relevance or preset.max_baseline_relevance,
        min_candidate_relevance=args.min_candidate_relevance or preset.min_candidate_relevance,
        min_delta=args.min_delta or preset.min_delta,
        recall_limit=args.recall_limit or preset.recall_limit,
    )
    for index, candidate_dir in enumerate(args.candidate_submission_dir, start=1):
        recall_candidates.extend(
            recall_from_submission_dir(
                baseline_path=args.baseline,
                corpus_path=args.corpus,
                candidate_dir=candidate_dir,
                locked_eval_ids=locked,
                tier=f"existing_{index}",
            )
        )
    recall_candidates = _dedupe_recall_candidates(recall_candidates)
    docs_by_id = {str(row["docid"]): row for row in _load_rows(args.corpus)}
    doc_texts = {docid: _doc_text(row) for docid, row in docs_by_id.items()}
    rejected: list[RejectedCandidate] = []
    accepted = review_recall_candidates(
        candidates=recall_candidates,
        doc_texts=doc_texts,
        provider=args.provider,
        model=args.model,
        host=args.host,
        api_key=args.api_key or _upstage_api_key(),
        min_topic_confidence=args.min_topic_confidence or preset.min_topic_confidence,
        min_pairwise_confidence=args.min_pairwise_confidence or preset.min_pairwise_confidence,
        limit=args.accepted_limit,
        rejected=rejected,
    )
    for item in accepted:
        recall = item.recall
        print(
            f"eval_id={recall.eval_id} tier={recall.tier} baseline_top1={recall.baseline_top1} "
            f"candidate_top1={recall.candidate_top1} topic_confidence={item.topic_confidence:.3f} "
            f"pairwise_confidence={item.pairwise_confidence:.3f}"
        )
    if args.audit_output is not None:
        write_audit(
            path=args.audit_output,
            recall_candidates=recall_candidates,
            accepted=accepted,
            rejected=rejected,
        )
        print(f"audit={args.audit_output}")
    if args.single_output_dir is not None:
        written = write_outputs(
            baseline_path=args.baseline,
            corpus_path=args.corpus,
            accepted=accepted,
            output_dir=args.single_output_dir,
            name_prefix=args.name_prefix,
        )
        for path in written:
            print(f"wrote={path}")
    if not accepted:
        print("accepted=0")
    return 0


def _preset_defaults(name: str) -> RecallPreset:
    presets = {
        "strict": RecallPreset(
            candidate_pool=180,
            per_eval_candidates=4,
            max_baseline_relevance=0.35,
            min_candidate_relevance=0.35,
            min_delta=0.10,
            recall_limit=50,
            min_topic_confidence=0.93,
            min_pairwise_confidence=0.93,
        ),
        "balanced": RecallPreset(
            candidate_pool=220,
            per_eval_candidates=4,
            max_baseline_relevance=0.30,
            min_candidate_relevance=0.45,
            min_delta=0.18,
            recall_limit=80,
            min_topic_confidence=0.80,
            min_pairwise_confidence=0.80,
        ),
        "wide": RecallPreset(
            candidate_pool=260,
            per_eval_candidates=5,
            max_baseline_relevance=0.38,
            min_candidate_relevance=0.35,
            min_delta=0.08,
            recall_limit=120,
            min_topic_confidence=0.78,
            min_pairwise_confidence=0.78,
        ),
    }
    return presets[name]


def _candidate_wins(judgement: Judgement, expected_docid: str, min_confidence: float) -> bool:
    return (
        judgement.winner == "candidate"
        and judgement.docid == expected_docid
        and judgement.confidence >= min_confidence
    )


def _dedupe_recall_candidates(candidates: Iterable[RecallCandidate]) -> list[RecallCandidate]:
    best_by_key: dict[tuple[str, str], RecallCandidate] = {}
    for candidate in candidates:
        key = (candidate.eval_id, candidate.candidate_top1)
        current = best_by_key.get(key)
        if current is None or _recall_sort_key(candidate) < _recall_sort_key(current):
            best_by_key[key] = candidate
    return sorted(best_by_key.values(), key=_recall_sort_key)


def _recall_sort_key(item: RecallCandidate) -> tuple[float, float, float, int]:
    return (
        item.baseline_relevance,
        -item.relevance_delta,
        -item.candidate_relevance,
        int(item.eval_id) if item.eval_id.isdigit() else 10**9,
    )


def _upstage_api_key() -> str | None:
    return os.environ.get("UPSTAGE_API_SECRET_KEY") or os.environ.get("UPSTAGE_API_KEY")


def _doc_text(row: dict[str, Any]) -> str:
    title = str(row.get("title") or "").strip()
    content = str(row.get("content") or "").strip()
    return "\n".join(part for part in [title, content] if part)


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


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
