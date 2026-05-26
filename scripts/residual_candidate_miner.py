from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.ollama_candidate_judge import (
    Judgement,
    _chat,
    judge_direct_answer_candidate,
    judge_pairwise_candidate,
    promoted_topk,
)
from scripts.submission_patch_candidates import PublicResult, load_public_results


@dataclass(frozen=True)
class ResidualCandidate:
    eval_id: str
    query: str
    baseline_top1: str
    candidate_top1: str
    candidate_topk: list[str]
    support: int
    sources: list[str]
    baseline_rank: int | None
    baseline_topk: list[str] | None = None


@dataclass(frozen=True)
class ResidualReview:
    candidate: ResidualCandidate
    score: int
    accepted: bool
    reason: str
    judgement: Judgement | None = None
    answer_span_judgement: "AnswerSpanJudgement | None" = None


@dataclass(frozen=True)
class AnswerSpanJudgement:
    required_answer_facts: list[str]
    baseline_missing_facts: list[str]
    candidate_covered_facts: list[str]
    winner: str
    docid: str
    confidence: float
    submit_risk: str
    reason: str
    baseline_present_quotes: list[str] | None = None
    candidate_exact_quotes: list[str] | None = None


@dataclass(frozen=True)
class FaultJudgement:
    baseline_failure_type: str
    baseline_failure_quote: str
    candidate_exact_quote: str
    candidate_is_broader: bool
    winner: str
    docid: str
    confidence: float
    submit_risk: str
    reason: str


def collect_residual_candidates(
    *,
    baseline_path: Path,
    public_results_path: Path,
    source_paths: Iterable[Path],
) -> list[ResidualCandidate]:
    baseline_rows = _load_rows(baseline_path)
    baseline_by_id = {str(row["eval_id"]): row for row in baseline_rows}
    locked = {result.eval_id for result in load_public_results(public_results_path)}
    votes: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    topks: dict[tuple[str, str], list[str]] = {}
    sources_by_key: dict[tuple[str, str], list[str]] = defaultdict(list)

    for source in _expand_sources(source_paths):
        for row in _load_rows(source):
            eval_id = str(row.get("eval_id"))
            if eval_id in locked:
                continue
            baseline = baseline_by_id.get(eval_id)
            if baseline is None:
                continue
            baseline_topk = [str(docid) for docid in baseline.get("topk") or []]
            source_topk = [str(docid) for docid in row.get("topk") or []]
            if not baseline_topk or not source_topk:
                continue
            baseline_top1 = baseline_topk[0]
            candidate_top1 = source_topk[0]
            if candidate_top1 == baseline_top1:
                continue
            key = (eval_id, candidate_top1)
            votes[key][str(source)] += 1
            sources_by_key[key].append(str(source))
            topks.setdefault(key, promoted_topk(baseline_topk, candidate_top1))

    candidates: list[ResidualCandidate] = []
    for (eval_id, candidate_top1), source_counter in votes.items():
        baseline = baseline_by_id[eval_id]
        baseline_topk = [str(docid) for docid in baseline.get("topk") or []]
        rank = _rank_in_topk(candidate_top1, baseline_topk)
        candidates.append(
            ResidualCandidate(
                eval_id=eval_id,
                query=str(baseline.get("standalone_query") or "").strip(),
                baseline_top1=baseline_topk[0],
                candidate_top1=candidate_top1,
                candidate_topk=topks[(eval_id, candidate_top1)],
                support=len(source_counter),
                sources=sorted(sources_by_key[(eval_id, candidate_top1)]),
                baseline_rank=rank if rank in {2, 3} else None,
                baseline_topk=baseline_topk,
            )
        )
    return sorted(candidates, key=lambda item: (-base_score(item), _sort_eval_id(item.eval_id), item.candidate_top1))


def base_score(candidate: ResidualCandidate) -> int:
    score = 0
    if candidate.support >= 2:
        score += 3
    if candidate.baseline_rank in {2, 3}:
        score += 2
    return score


def score_with_judgement(
    candidate: ResidualCandidate,
    judgement: Judgement | None,
    *,
    accept_threshold: int = 7,
    topk_guard_pass: bool = True,
    topk_guard_reason: str = "",
) -> ResidualReview:
    score = base_score(candidate)
    reason_parts: list[str] = []
    if candidate.support >= 2:
        reason_parts.append(f"support={candidate.support}")
    if candidate.baseline_rank in {2, 3}:
        reason_parts.append(f"baseline_rank={candidate.baseline_rank}")

    if judgement is not None:
        if judgement.winner == "baseline":
            score -= 4
            reason_parts.append("baseline_winner")
        if judgement.winner == "candidate" and judgement.docid == candidate.candidate_top1:
            reason_parts.append("candidate_winner")
        if judgement.baseline_is_wrong is True:
            score += 2
            reason_parts.append("baseline_is_wrong")
        if judgement.candidate_direct_answer is True:
            score += 2
            reason_parts.append("candidate_direct_answer")
        if judgement.candidate_offtopic is True:
            score -= 5
            reason_parts.append("candidate_offtopic")
        if judgement.submit_risk == "high":
            score -= 5
            reason_parts.append("high_risk")
        if judgement.reason:
            reason_parts.append(judgement.reason)
    if not topk_guard_pass:
        reason_parts.append(f"topk_guard_failed={topk_guard_reason}")

    accepted = score >= accept_threshold
    if judgement is not None:
        if judgement.winner != "candidate" or judgement.docid != candidate.candidate_top1:
            accepted = False
        if judgement.baseline_is_wrong is not True:
            accepted = False
        if judgement.candidate_offtopic is True or judgement.submit_risk == "high":
            accepted = False
    if not topk_guard_pass:
        accepted = False
    return ResidualReview(
        candidate=candidate,
        score=score,
        accepted=accepted,
        reason="; ".join(reason_parts),
        judgement=judgement,
    )


def review_candidates(
    *,
    candidates: Iterable[ResidualCandidate],
    corpus_path: Path,
    provider: str,
    model: str,
    host: str,
    api_key: str | None,
    accept_threshold: int,
    limit: int,
    require_topk_guard: bool = True,
) -> list[ResidualReview]:
    doc_texts = _load_doc_texts(corpus_path)
    reviews: list[ResidualReview] = []
    for candidate in candidates:
        judgement = judge_direct_answer_candidate(
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
        topk_guard_pass = True
        topk_guard_reason = ""
        if require_topk_guard and _candidate_can_pass_primary(candidate, judgement, accept_threshold):
            topk_guard_pass, topk_guard_reason = _passes_topk_guard(
                candidate=candidate,
                doc_texts=doc_texts,
                provider=provider,
                model=model,
                host=host,
                api_key=api_key,
                allow_empty_candidate_docid=True,
            )
        reviews.append(
            score_with_judgement(
                candidate,
                judgement,
                accept_threshold=accept_threshold,
                topk_guard_pass=topk_guard_pass,
                topk_guard_reason=topk_guard_reason,
            )
        )
        if sum(1 for review in reviews if review.accepted) >= limit:
            break
    return sorted(reviews, key=lambda item: (-item.score, _sort_eval_id(item.candidate.eval_id)))


def select_highrisk_rank_promotions(
    candidates: Iterable[ResidualCandidate],
    *,
    min_support: int,
    limit: int,
) -> list[ResidualCandidate]:
    selected = [
        candidate
        for candidate in candidates
        if candidate.support >= min_support and candidate.baseline_rank in {2, 3}
    ]
    return sorted(selected, key=_highrisk_candidate_sort_key)[:limit]


def score_highrisk_judgement(
    candidate: ResidualCandidate,
    judgement: Judgement,
    *,
    accept_threshold: int = 7,
) -> ResidualReview:
    score = base_score(candidate)
    score += min(candidate.support // 10, 3)
    if judgement.winner == "candidate" and judgement.docid == candidate.candidate_top1:
        score += 1
    if judgement.candidate_direct_answer is True:
        score += 2
    if judgement.candidate_offtopic is True:
        score -= 5
    if judgement.submit_risk == "high":
        score -= 5
    accepted = (
        score >= accept_threshold
        and judgement.winner == "candidate"
        and judgement.docid == candidate.candidate_top1
        and judgement.candidate_direct_answer is True
        and judgement.candidate_offtopic is not True
        and judgement.submit_risk != "high"
    )
    reason = (
        f"support={candidate.support}; baseline_rank={candidate.baseline_rank}; "
        f"winner={judgement.winner}; candidate_direct_answer={judgement.candidate_direct_answer}; "
        f"risk={judgement.submit_risk}; {judgement.reason}"
    )
    return ResidualReview(
        candidate=candidate,
        score=score,
        accepted=accepted,
        reason=reason,
        judgement=judgement,
    )


def score_answer_span_judgement(
    candidate: ResidualCandidate,
    judgement: AnswerSpanJudgement,
    *,
    topk_guard_pass: bool,
    topk_guard_reason: str,
    accept_threshold: int = 7,
) -> ResidualReview:
    score = base_score(candidate)
    score += min(candidate.support // 10, 3)
    if judgement.winner == "candidate" and judgement.docid == candidate.candidate_top1:
        score += 2
    if judgement.baseline_missing_facts:
        score += min(len(judgement.baseline_missing_facts), 3)
    if judgement.candidate_covered_facts:
        score += min(len(judgement.candidate_covered_facts), 3)
    if not judgement.baseline_missing_facts:
        score -= 6
    if judgement.submit_risk == "high":
        score -= 5
    if not topk_guard_pass:
        score -= 5
    if judgement.baseline_present_quotes:
        score -= 6
    if not judgement.candidate_exact_quotes:
        score -= 4

    reason_parts = [
        f"support={candidate.support}",
        f"baseline_rank={candidate.baseline_rank}",
        f"required_answer_facts={len(judgement.required_answer_facts)}",
        f"baseline_missing_facts={len(judgement.baseline_missing_facts)}",
        f"candidate_covered_facts={len(judgement.candidate_covered_facts)}",
        f"candidate_exact_quotes={len(judgement.candidate_exact_quotes or [])}",
        f"winner={judgement.winner}",
        f"risk={judgement.submit_risk}",
    ]
    if not judgement.baseline_missing_facts:
        reason_parts.append("baseline_has_key_span")
    if judgement.baseline_present_quotes:
        reason_parts.append("baseline_present_quote")
    if not judgement.candidate_exact_quotes:
        reason_parts.append("candidate_missing_exact_quote")
    if not topk_guard_pass:
        reason_parts.append(f"topk_guard_failed={topk_guard_reason}")
    if judgement.reason:
        reason_parts.append(judgement.reason)

    accepted = (
        score >= accept_threshold
        and judgement.winner == "candidate"
        and judgement.docid == candidate.candidate_top1
        and bool(judgement.required_answer_facts)
        and bool(judgement.baseline_missing_facts)
        and bool(judgement.candidate_covered_facts)
        and not judgement.baseline_present_quotes
        and bool(judgement.candidate_exact_quotes)
        and judgement.submit_risk != "high"
        and topk_guard_pass
    )
    return ResidualReview(
        candidate=candidate,
        score=score,
        accepted=accepted,
        reason="; ".join(reason_parts),
        answer_span_judgement=judgement,
    )


def score_fault_judgement(
    candidate: ResidualCandidate,
    judgement: FaultJudgement,
    *,
    topk_guard_pass: bool,
    topk_guard_reason: str,
    accept_threshold: int = 7,
) -> ResidualReview:
    strong_failure_types = {"off_topic", "wrong_entity", "wrong_formula", "contradiction"}
    score = base_score(candidate)
    score += min(candidate.support // 10, 3)
    if judgement.baseline_failure_type in strong_failure_types:
        score += 4
    else:
        score -= 4
    if judgement.winner == "candidate" and judgement.docid == candidate.candidate_top1:
        score += 2
    if judgement.candidate_exact_quote:
        score += 2
    else:
        score -= 5
    if judgement.candidate_is_broader:
        score -= 5
    if judgement.submit_risk == "high":
        score -= 5
    if not topk_guard_pass:
        score -= 5

    reason_parts = [
        f"support={candidate.support}",
        f"baseline_rank={candidate.baseline_rank}",
        f"baseline_failure_type={judgement.baseline_failure_type}",
        f"winner={judgement.winner}",
        f"risk={judgement.submit_risk}",
    ]
    if judgement.baseline_failure_type not in strong_failure_types:
        reason_parts.append(f"weak_failure_type={judgement.baseline_failure_type}")
    if not judgement.candidate_exact_quote:
        reason_parts.append("candidate_missing_exact_quote")
    if judgement.candidate_is_broader:
        reason_parts.append("candidate_is_broader")
    if not topk_guard_pass:
        reason_parts.append(f"topk_guard_failed={topk_guard_reason}")
    if judgement.reason:
        reason_parts.append(judgement.reason)

    accepted = (
        score >= accept_threshold
        and judgement.baseline_failure_type in strong_failure_types
        and bool(judgement.baseline_failure_quote)
        and bool(judgement.candidate_exact_quote)
        and not judgement.candidate_is_broader
        and judgement.winner == "candidate"
        and judgement.docid == candidate.candidate_top1
        and judgement.submit_risk != "high"
        and topk_guard_pass
    )
    return ResidualReview(
        candidate=candidate,
        score=score,
        accepted=accepted,
        reason="; ".join(reason_parts),
    )


def review_highrisk_candidates(
    *,
    candidates: Iterable[ResidualCandidate],
    corpus_path: Path,
    provider: str,
    model: str,
    host: str,
    api_key: str | None,
    accept_threshold: int,
    limit: int,
) -> list[ResidualReview]:
    doc_texts = _load_doc_texts(corpus_path)
    reviews: list[ResidualReview] = []
    for candidate in candidates:
        judgement = judge_direct_answer_candidate(
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
        reviews.append(score_highrisk_judgement(candidate, judgement, accept_threshold=accept_threshold))
        if sum(1 for review in reviews if review.accepted) >= limit:
            break
    return sorted(reviews, key=lambda item: (-item.score, _sort_eval_id(item.candidate.eval_id)))


def review_answer_span_candidates(
    *,
    candidates: Iterable[ResidualCandidate],
    corpus_path: Path,
    provider: str,
    model: str,
    host: str,
    api_key: str | None,
    accept_threshold: int,
    limit: int,
) -> list[ResidualReview]:
    doc_texts = _load_doc_texts(corpus_path)
    reviews: list[ResidualReview] = []
    for candidate in candidates:
        judgement = judge_answer_span_candidate(
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
        topk_guard_pass = False
        topk_guard_reason = "answer_span_primary_failed"
        if _answer_span_can_pass_primary(candidate, judgement, accept_threshold):
            topk_guard_pass, topk_guard_reason = _passes_topk_guard(
                candidate=candidate,
                doc_texts=doc_texts,
                provider=provider,
                model=model,
                host=host,
                api_key=api_key,
            )
        reviews.append(
            score_answer_span_judgement(
                candidate,
                judgement,
                topk_guard_pass=topk_guard_pass,
                topk_guard_reason=topk_guard_reason,
                accept_threshold=accept_threshold,
            )
        )
        if sum(1 for review in reviews if review.accepted) >= limit:
            break
    return sorted(reviews, key=lambda item: (-item.score, _sort_eval_id(item.candidate.eval_id)))


def review_fault_candidates(
    *,
    candidates: Iterable[ResidualCandidate],
    corpus_path: Path,
    provider: str,
    model: str,
    host: str,
    api_key: str | None,
    accept_threshold: int,
    limit: int,
) -> list[ResidualReview]:
    doc_texts = _load_doc_texts(corpus_path)
    reviews: list[ResidualReview] = []
    for candidate in candidates:
        judgement = judge_fault_candidate(
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
        topk_guard_pass = False
        topk_guard_reason = "fault_primary_failed"
        if _fault_can_pass_primary(candidate, judgement, accept_threshold):
            topk_guard_pass, topk_guard_reason = _passes_topk_guard(
                candidate=candidate,
                doc_texts=doc_texts,
                provider=provider,
                model=model,
                host=host,
                api_key=api_key,
            )
        reviews.append(
            score_fault_judgement(
                candidate,
                judgement,
                topk_guard_pass=topk_guard_pass,
                topk_guard_reason=topk_guard_reason,
                accept_threshold=accept_threshold,
            )
        )
        if sum(1 for review in reviews if review.accepted) >= limit:
            break
    return sorted(reviews, key=lambda item: (-item.score, _sort_eval_id(item.candidate.eval_id)))


def judge_fault_candidate(
    *,
    query: str,
    baseline_docid: str,
    baseline_text: str,
    candidate_docid: str,
    candidate_text: str,
    model: str,
    host: str,
    provider: str,
    api_key: str | None,
) -> FaultJudgement:
    prompt = (
        "Strict Korean IR baseline-fault judge. Submit budget is very scarce. "
        "Choose candidate only when baseline top1 has a clear fault: off_topic, wrong_entity, wrong_formula, or contradiction. "
        "Do not choose candidate for missing_answer, broader detail, same topic, better wording, or more complete explanation. "
        "candidate_is_broader must be true when candidate is merely broader or more detailed than baseline. "
        "Return exact baseline failure quote and exact candidate quote. "
        "Output JSON only: "
        '{"baseline_failure_type":"off_topic|wrong_entity|wrong_formula|contradiction|missing_answer|none",'
        '"baseline_failure_quote":"exact baseline quote",'
        '"candidate_exact_quote":"exact candidate quote",'
        '"candidate_is_broader":false,'
        '"winner":"baseline|candidate|tie","docid":"candidate-docid-or-empty",'
        '"confidence":0.0,"submit_risk":"low|medium|high","reason":"short Korean evidence"}\n\n'
        f"query={query}\n"
        f"baseline={{\"docid\":{json.dumps(baseline_docid, ensure_ascii=False)},"
        f"\"content\":{json.dumps(baseline_text[:1500], ensure_ascii=False)}}}\n"
        f"candidate={{\"docid\":{json.dumps(candidate_docid, ensure_ascii=False)},"
        f"\"content\":{json.dumps(candidate_text[:1500], ensure_ascii=False)}}}"
    )
    content = _chat(provider=provider, host=host, model=model, prompt=prompt, api_key=api_key)
    try:
        payload = _parse_json_object(content)
    except (ValueError, json.JSONDecodeError):
        return FaultJudgement("none", "", "", True, "baseline", "", 0.0, "high", "malformed response")
    failure_type = str(payload.get("baseline_failure_type") or "none")
    if failure_type not in {"off_topic", "wrong_entity", "wrong_formula", "contradiction", "missing_answer", "none"}:
        failure_type = "none"
    winner = str(payload.get("winner") or "")
    if winner not in {"baseline", "candidate", "tie"}:
        winner = "baseline"
    return FaultJudgement(
        baseline_failure_type=failure_type,
        baseline_failure_quote=str(payload.get("baseline_failure_quote") or ""),
        candidate_exact_quote=str(payload.get("candidate_exact_quote") or ""),
        candidate_is_broader=_bool(payload.get("candidate_is_broader")),
        winner=winner,
        docid=str(payload.get("docid") or ""),
        confidence=float(payload.get("confidence") or 0.0),
        submit_risk=str(payload.get("submit_risk") or "high"),
        reason=str(payload.get("reason") or ""),
    )


def judge_answer_span_candidate(
    *,
    query: str,
    baseline_docid: str,
    baseline_text: str,
    candidate_docid: str,
    candidate_text: str,
    model: str,
    host: str,
    provider: str,
    api_key: str | None,
) -> AnswerSpanJudgement:
    prompt = (
        "Strict Korean IR answer-span judge. Submit budget is scarce. "
        "Extract 1-3 required answer facts for the query. "
        "Choose candidate only when baseline misses at least one required fact AND candidate directly covers it. "
        "Return exact candidate quote(s) proving coverage. "
        "Return baseline_present_quotes when baseline has any exact quote proving the same required fact; then choose baseline. "
        "If baseline already contains the key answer span, choose baseline even when candidate is broader or clearer. "
        "Reject adjacent topics, generic explanations, and keyword-only overlap. "
        "Output JSON only: "
        '{"required_answer_facts":["fact"],"baseline_missing_facts":["fact"],'
        '"candidate_covered_facts":["fact"],"baseline_present_quotes":["exact baseline quote"],'
        '"candidate_exact_quotes":["exact candidate quote"],"winner":"baseline|candidate|tie",'
        '"docid":"candidate-docid-or-empty","confidence":0.0,'
        '"submit_risk":"low|medium|high","reason":"short Korean evidence"}\n\n'
        f"query={query}\n"
        f"baseline={{\"docid\":{json.dumps(baseline_docid, ensure_ascii=False)},"
        f"\"content\":{json.dumps(baseline_text[:1500], ensure_ascii=False)}}}\n"
        f"candidate={{\"docid\":{json.dumps(candidate_docid, ensure_ascii=False)},"
        f"\"content\":{json.dumps(candidate_text[:1500], ensure_ascii=False)}}}"
    )
    content = _chat(provider=provider, host=host, model=model, prompt=prompt, api_key=api_key)
    try:
        payload = _parse_json_object(content)
    except (ValueError, json.JSONDecodeError):
        return AnswerSpanJudgement([], [], [], "baseline", "", 0.0, "high", "malformed response")
    winner = str(payload.get("winner") or "")
    if winner not in {"baseline", "candidate", "tie"}:
        winner = "baseline"
    return AnswerSpanJudgement(
        required_answer_facts=_string_list(payload.get("required_answer_facts")),
        baseline_missing_facts=_string_list(payload.get("baseline_missing_facts")),
        candidate_covered_facts=_string_list(payload.get("candidate_covered_facts")),
        winner=winner,
        docid=str(payload.get("docid") or ""),
        confidence=float(payload.get("confidence") or 0.0),
        submit_risk=str(payload.get("submit_risk") or "high"),
        reason=str(payload.get("reason") or ""),
        baseline_present_quotes=_string_list(payload.get("baseline_present_quotes")),
        candidate_exact_quotes=_string_list(payload.get("candidate_exact_quotes")),
    )


def write_single_row_outputs(
    *,
    baseline_path: Path,
    reviews: Iterable[ResidualReview],
    output_dir: Path,
    name_prefix: str,
    limit: int,
) -> list[Path]:
    baseline_rows = _load_rows(baseline_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for review in sorted(
        [item for item in reviews if item.accepted],
        key=lambda item: (-item.score, _sort_eval_id(item.candidate.eval_id)),
    )[:limit]:
        rows = [dict(row) for row in baseline_rows]
        for row in rows:
            if str(row["eval_id"]) == review.candidate.eval_id:
                row["topk"] = review.candidate.candidate_topk
                break
        target = output_dir / f"{name_prefix}_eval{review.candidate.eval_id}.jsonl"
        _write_rows(target, rows)
        written.append(target)
    return written


def write_audit(path: Path, candidates: Iterable[ResidualCandidate], reviews: Iterable[ResidualReview]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    review_list = list(reviews)
    payload = {
        "candidates": [_candidate_payload(candidate) for candidate in candidates],
        "reviews": [_review_payload(review) for review in review_list],
        "accepted": [_review_payload(review) for review in review_list if review.accepted],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Mine residual single-row candidates after public lockout.")
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--public-results", required=True, type=Path)
    parser.add_argument("--source", action="append", required=True, type=Path)
    parser.add_argument("--provider", choices=("ollama", "upstage"), default="upstage")
    parser.add_argument("--model", default="solar-pro3")
    parser.add_argument("--host", default=None)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--env-file", type=Path, default=None)
    parser.add_argument("--accept-threshold", type=int, default=7)
    parser.add_argument("--review-limit", type=int, default=40)
    parser.add_argument("--accepted-limit", type=int, default=1)
    parser.add_argument("--disable-topk-guard", action="store_true")
    parser.add_argument("--highrisk-rank-mode", action="store_true")
    parser.add_argument("--answer-span-mode", action="store_true")
    parser.add_argument("--fault-mode", action="store_true")
    parser.add_argument("--min-highrisk-support", type=int, default=10)
    parser.add_argument("--min-answer-span-support", type=int, default=10)
    parser.add_argument("--min-fault-support", type=int, default=2)
    parser.add_argument("--audit-output", type=Path, default=None)
    parser.add_argument("--single-output-dir", type=Path, default=None)
    parser.add_argument("--name-prefix", default="residual_eval246_base")
    args = parser.parse_args()

    if args.env_file is not None:
        _load_env_file(args.env_file)

    candidates = collect_residual_candidates(
        baseline_path=args.baseline,
        public_results_path=args.public_results,
        source_paths=args.source,
    )
    if args.fault_mode:
        review_candidates_input = select_highrisk_rank_promotions(
            candidates,
            min_support=args.min_fault_support,
            limit=args.review_limit,
        )
        reviews = review_fault_candidates(
            candidates=review_candidates_input,
            corpus_path=args.corpus,
            provider=args.provider,
            model=args.model,
            host=args.host or default_host(args.provider),
            api_key=args.api_key or _upstage_api_key(),
            accept_threshold=args.accept_threshold,
            limit=args.accepted_limit,
        )
    elif args.answer_span_mode:
        review_candidates_input = select_highrisk_rank_promotions(
            candidates,
            min_support=args.min_answer_span_support,
            limit=args.review_limit,
        )
        reviews = review_answer_span_candidates(
            candidates=review_candidates_input,
            corpus_path=args.corpus,
            provider=args.provider,
            model=args.model,
            host=args.host or default_host(args.provider),
            api_key=args.api_key or _upstage_api_key(),
            accept_threshold=args.accept_threshold,
            limit=args.accepted_limit,
        )
    elif args.highrisk_rank_mode:
        review_candidates_input = select_highrisk_rank_promotions(
            candidates,
            min_support=args.min_highrisk_support,
            limit=args.review_limit,
        )
        reviews = review_highrisk_candidates(
            candidates=review_candidates_input,
            corpus_path=args.corpus,
            provider=args.provider,
            model=args.model,
            host=args.host or default_host(args.provider),
            api_key=args.api_key or _upstage_api_key(),
            accept_threshold=args.accept_threshold,
            limit=args.accepted_limit,
        )
    else:
        review_candidates_input = candidates[: args.review_limit]
        reviews = review_candidates(
            candidates=review_candidates_input,
            corpus_path=args.corpus,
            provider=args.provider,
            model=args.model,
            host=args.host or default_host(args.provider),
            api_key=args.api_key or _upstage_api_key(),
            accept_threshold=args.accept_threshold,
            limit=args.accepted_limit,
            require_topk_guard=not args.disable_topk_guard,
        )
    if args.audit_output is not None:
        write_audit(args.audit_output, review_candidates_input, reviews)
        print(f"audit={args.audit_output}")
    for review in reviews:
        print(
            f"eval_id={review.candidate.eval_id} candidate_top1={review.candidate.candidate_top1} "
            f"score={review.score} accepted={str(review.accepted).lower()}"
        )
    if args.single_output_dir is not None:
        written = write_single_row_outputs(
            baseline_path=args.baseline,
            reviews=reviews,
            output_dir=args.single_output_dir,
            name_prefix=args.name_prefix,
            limit=args.accepted_limit,
        )
        for path in written:
            print(f"wrote={path}")
    if not any(review.accepted for review in reviews):
        print("accepted=0")
    return 0


def default_host(provider: str) -> str:
    if provider == "upstage":
        return os.environ.get("UPSTAGE_BASE_URL", "https://api.upstage.ai/v1")
    return "http://localhost:11434"


def _upstage_api_key() -> str | None:
    return os.environ.get("UPSTAGE_API_SECRET_KEY") or os.environ.get("UPSTAGE_API_KEY")


def _candidate_can_pass_primary(
    candidate: ResidualCandidate,
    judgement: Judgement,
    accept_threshold: int,
) -> bool:
    return score_with_judgement(candidate, judgement, accept_threshold=accept_threshold).accepted


def _answer_span_can_pass_primary(
    candidate: ResidualCandidate,
    judgement: AnswerSpanJudgement,
    accept_threshold: int,
) -> bool:
    return score_answer_span_judgement(
        candidate,
        judgement,
        topk_guard_pass=True,
        topk_guard_reason="candidate_beats_current_topk",
        accept_threshold=accept_threshold,
    ).accepted


def _fault_can_pass_primary(
    candidate: ResidualCandidate,
    judgement: FaultJudgement,
    accept_threshold: int,
) -> bool:
    return score_fault_judgement(
        candidate,
        judgement,
        topk_guard_pass=True,
        topk_guard_reason="candidate_beats_current_topk",
        accept_threshold=accept_threshold,
    ).accepted


def _passes_topk_guard(
    *,
    candidate: ResidualCandidate,
    doc_texts: dict[str, str],
    provider: str,
    model: str,
    host: str,
    api_key: str | None,
    allow_empty_candidate_docid: bool = False,
) -> tuple[bool, str]:
    baseline_topk = candidate.baseline_topk or [candidate.baseline_top1]
    for docid in baseline_topk[:3]:
        if docid == candidate.candidate_top1:
            continue
        judgement = judge_pairwise_candidate(
            query=candidate.query,
            baseline_docid=docid,
            baseline_text=doc_texts.get(docid, ""),
            candidate_docid=candidate.candidate_top1,
            candidate_text=doc_texts.get(candidate.candidate_top1, ""),
            model=model,
            host=host,
            provider=provider,
            api_key=api_key,
        )
        docid_matches = judgement.docid == candidate.candidate_top1 or (
            allow_empty_candidate_docid and judgement.winner == "candidate" and not judgement.docid
        )
        if judgement.winner != "candidate" or not docid_matches:
            return False, f"lost_to={docid}; winner={judgement.winner}; reason={judgement.reason}"
    return True, "candidate_beats_current_topk"


def _highrisk_candidate_sort_key(candidate: ResidualCandidate) -> tuple[int, int, int, str]:
    return (
        -candidate.support,
        candidate.baseline_rank or 99,
        _sort_eval_id(candidate.eval_id)[0],
        candidate.candidate_top1,
    )


def _load_env_file(path: Path) -> None:
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.removeprefix("export ").strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _expand_sources(paths: Iterable[Path]) -> list[Path]:
    expanded: list[Path] = []
    for path in paths:
        if path.is_dir():
            expanded.extend(sorted(path.glob("*.jsonl")))
        else:
            expanded.append(path)
    return expanded


def _load_doc_texts(corpus_path: Path) -> dict[str, str]:
    return {str(row["docid"]): _doc_text(row) for row in _load_rows(corpus_path)}


def _doc_text(row: dict[str, Any]) -> str:
    title = str(row.get("title") or "").strip()
    content = str(row.get("content") or "").strip()
    return "\n".join(part for part in [title, content] if part)


def _candidate_payload(candidate: ResidualCandidate) -> dict[str, Any]:
    return {
        **candidate.__dict__,
        "base_score": base_score(candidate),
    }


def _review_payload(review: ResidualReview) -> dict[str, Any]:
    judgement = review.judgement
    answer_span_judgement = review.answer_span_judgement
    return {
        **_candidate_payload(review.candidate),
        "score": review.score,
        "accepted": review.accepted,
        "reason": review.reason,
        "judge_winner": judgement.winner if judgement else None,
        "judge_docid": judgement.docid if judgement else None,
        "judge_confidence": judgement.confidence if judgement else None,
        "judge_reason": judgement.reason if judgement else None,
        "baseline_is_wrong": judgement.baseline_is_wrong if judgement else None,
        "candidate_direct_answer": judgement.candidate_direct_answer if judgement else None,
        "candidate_offtopic": judgement.candidate_offtopic if judgement else None,
        "submit_risk": judgement.submit_risk if judgement else None,
        "required_answer_facts": (
            answer_span_judgement.required_answer_facts if answer_span_judgement else None
        ),
        "baseline_missing_facts": (
            answer_span_judgement.baseline_missing_facts if answer_span_judgement else None
        ),
        "candidate_covered_facts": (
            answer_span_judgement.candidate_covered_facts if answer_span_judgement else None
        ),
        "answer_span_winner": answer_span_judgement.winner if answer_span_judgement else None,
        "answer_span_docid": answer_span_judgement.docid if answer_span_judgement else None,
        "answer_span_confidence": answer_span_judgement.confidence if answer_span_judgement else None,
        "answer_span_risk": answer_span_judgement.submit_risk if answer_span_judgement else None,
        "answer_span_reason": answer_span_judgement.reason if answer_span_judgement else None,
        "baseline_present_quotes": (
            answer_span_judgement.baseline_present_quotes if answer_span_judgement else None
        ),
        "candidate_exact_quotes": (
            answer_span_judgement.candidate_exact_quotes if answer_span_judgement else None
        ),
    }


def _rank_in_topk(docid: str, topk: list[str]) -> int | None:
    try:
        return topk.index(docid) + 1
    except ValueError:
        return None


def _sort_eval_id(eval_id: str) -> tuple[int, str]:
    return (int(eval_id), eval_id) if eval_id.isdigit() else (10**9, eval_id)


def _parse_json_object(content: str) -> dict[str, Any]:
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object")
    payload = json.loads(content[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("JSON payload must be an object")
    return payload


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


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
