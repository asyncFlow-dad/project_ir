from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ir_search.indexer import CorpusDocument, build_index, search
from scripts.submission_patch_candidates import load_public_results


@dataclass(frozen=True)
class Judgement:
    winner: str
    docid: str
    confidence: float
    reason: str
    baseline_is_wrong: bool | None = None
    candidate_direct_answer: bool | None = None
    candidate_offtopic: bool | None = None
    submit_risk: str = ""


@dataclass(frozen=True)
class CandidateDecision:
    eval_id: str
    query: str
    baseline_top1: str
    candidate_top1: str
    confidence: float
    reason: str
    candidate_topk: list[str]


def parse_judgement(content: str) -> Judgement:
    match = re.search(r"\{.*\}", content, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object in judgement")
    payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise ValueError("Judgement must be a JSON object")
    winner = str(payload.get("winner", ""))
    if winner not in {"baseline", "candidate", "tie"}:
        raise ValueError(f"Unknown winner: {winner}")
    return Judgement(
        winner=winner,
        docid=str(payload.get("docid") or ""),
        confidence=float(payload.get("confidence") or 0.0),
        reason=str(payload.get("reason") or ""),
        baseline_is_wrong=_optional_bool(payload.get("baseline_is_wrong")),
        candidate_direct_answer=_optional_bool(payload.get("candidate_direct_answer")),
        candidate_offtopic=_optional_bool(payload.get("candidate_offtopic")),
        submit_risk=str(payload.get("submit_risk") or ""),
    )


def try_parse_judgement(content: str) -> Judgement | None:
    try:
        return parse_judgement(content)
    except (ValueError, json.JSONDecodeError):
        return None


def is_rejected_reason(reason: str) -> bool:
    rejected_patterns = [
        "관련이 없",
        "무관",
        "드리프트",
        "가장 관련성이 높은",
        "부적절",
        "query와 직접적인 관련",
        "쿼리 주제와 직접적인 관련",
    ]
    return any(pattern in reason for pattern in rejected_patterns)


def promoted_topk(baseline_topk: list[str], candidate_top1: str) -> list[str]:
    topk: list[str] = []
    for docid in [candidate_top1, *baseline_topk]:
        if docid and docid not in topk:
            topk.append(docid)
        if len(topk) == 3:
            break
    return topk


def generate_decisions(
    *,
    baseline_path: Path,
    corpus_path: Path,
    locked_eval_ids: set[str],
    provider: str,
    model: str,
    host: str,
    api_key: str | None,
    pool_size: int,
    limit: int,
    min_confidence: float,
    max_eval_id: int | None = None,
    min_eval_id: int | None = None,
) -> list[CandidateDecision]:
    baseline_rows = _load_rows(baseline_path)
    docs_by_id = {str(row["docid"]): row for row in _load_rows(corpus_path)}
    doc_texts = {docid: _doc_text(row) for docid, row in docs_by_id.items()}
    index = build_index(
        [CorpusDocument(id=docid, path=Path(docid), text=text) for docid, text in doc_texts.items()]
    )
    decisions: list[CandidateDecision] = []

    for row in baseline_rows:
        eval_id = str(row["eval_id"])
        if eval_id in locked_eval_ids:
            continue
        if min_eval_id is not None and eval_id.isdigit() and int(eval_id) < min_eval_id:
            continue
        if max_eval_id is not None and eval_id.isdigit() and int(eval_id) > max_eval_id:
            continue
        query = str(row.get("standalone_query") or "").strip()
        baseline_topk = [str(docid) for docid in row.get("topk") or []]
        if not query or not baseline_topk:
            continue
        candidates = [
            result.document.id
            for result in search(index, query, limit=max(pool_size + len(baseline_topk), 10))
            if result.document.id not in baseline_topk
        ][:pool_size]
        if not candidates:
            continue
        judgement = judge_candidates(
            query=query,
            baseline_docid=baseline_topk[0],
            baseline_text=doc_texts.get(baseline_topk[0], ""),
            candidate_docids=candidates,
            doc_texts=doc_texts,
            model=model,
            host=host,
            provider=provider,
            api_key=api_key,
        )
        if judgement is None:
            continue
        if (
            judgement.winner != "candidate"
            or judgement.docid not in candidates
            or judgement.confidence < min_confidence
        ):
            continue
        decisions.append(
            CandidateDecision(
                eval_id=eval_id,
                query=query,
                baseline_top1=baseline_topk[0],
                candidate_top1=judgement.docid,
                confidence=judgement.confidence,
                reason=judgement.reason,
                candidate_topk=promoted_topk(baseline_topk, judgement.docid),
            )
        )
        if len(decisions) >= limit:
            break
    return decisions


def judge_candidates(
    *,
    query: str,
    baseline_docid: str,
    baseline_text: str,
    candidate_docids: list[str],
    doc_texts: dict[str, str],
    model: str,
    host: str,
    provider: str = "ollama",
    api_key: str | None = None,
) -> Judgement | None:
    candidates = [
        {"docid": docid, "content": doc_texts.get(docid, "")[:700]}
        for docid in candidate_docids
    ]
    prompt = (
        "Korean IR retrieval judge. Decide whether baseline document or one candidate "
        "more directly answers query. Prefer exact query topic, not keyword overlap. "
        "If baseline already answers well, choose baseline. If candidates are scenario drift, choose baseline. "
        "Never choose a candidate that is merely the least-bad option. "
        "Choose candidate only when it directly answers the query's entity and requested relation, cause, role, or definition. "
        "Output JSON only: "
        '{"winner":"baseline|candidate|tie","docid":"candidate-docid-or-empty","confidence":0.0,"reason":"short Korean"}\n\n'
        f"query={query}\n"
        f"baseline={{\"docid\":{json.dumps(baseline_docid, ensure_ascii=False)},"
        f"\"content\":{json.dumps(baseline_text[:900], ensure_ascii=False)}}}\n"
        f"candidates={json.dumps(candidates, ensure_ascii=False)}"
    )
    content = _chat(provider=provider, host=host, model=model, prompt=prompt, api_key=api_key)
    judgement = try_parse_judgement(content)
    if judgement is not None and is_rejected_reason(judgement.reason):
        return None
    return judgement


def judge_pairwise_candidate(
    *,
    query: str,
    baseline_docid: str,
    baseline_text: str,
    candidate_docid: str,
    candidate_text: str,
    model: str,
    host: str,
    provider: str = "ollama",
    api_key: str | None = None,
) -> Judgement:
    prompt = (
        "Strict Korean IR pairwise judge. Choose candidate only if it clearly beats baseline. "
        "If baseline already directly answers query, choose baseline. "
        "If candidate changes topic, is generic, or only shares keywords, choose baseline. "
        "You must quote exact Korean evidence from the chosen document in reason. "
        "Output JSON only: "
        '{"winner":"baseline|candidate|tie","docid":"candidate-docid-or-empty","confidence":0.0,"reason":"quote exact Korean evidence"}\n\n'
        f"query={query}\n"
        f"baseline={{\"docid\":{json.dumps(baseline_docid, ensure_ascii=False)},"
        f"\"content\":{json.dumps(baseline_text[:1200], ensure_ascii=False)}}}\n"
        f"candidate={{\"docid\":{json.dumps(candidate_docid, ensure_ascii=False)},"
        f"\"content\":{json.dumps(candidate_text[:1200], ensure_ascii=False)}}}"
    )
    content = _chat(provider=provider, host=host, model=model, prompt=prompt, api_key=api_key)
    judgement = try_parse_judgement(content)
    if judgement is None:
        return Judgement(winner="baseline", docid="", confidence=0.0, reason="malformed response")
    if is_rejected_reason(judgement.reason):
        return Judgement(winner="baseline", docid="", confidence=judgement.confidence, reason=judgement.reason)
    return judgement


def judge_topic_error_candidate(
    *,
    query: str,
    baseline_docid: str,
    baseline_text: str,
    candidate_docid: str,
    candidate_text: str,
    model: str,
    host: str,
    provider: str = "ollama",
    api_key: str | None = None,
) -> Judgement:
    prompt = (
        "Strict Korean IR topic-error judge. Submit budget is scarce. "
        "Choose candidate only when BOTH conditions hold: "
        "1) baseline must be wrong, unrelated, or answer a different topic; "
        "2) candidate must directly answer the query with exact evidence. "
        "If baseline is partially or fully correct, choose baseline. "
        "If candidate is only broader, narrower, adjacent, or keyword-matched, choose baseline. "
        "Reason must include baseline_failure=<short exact issue> and candidate_evidence=<exact Korean quote>. "
        "Output JSON only: "
        '{"winner":"baseline|candidate|tie","docid":"candidate-docid-or-empty","confidence":0.0,"reason":"baseline_failure=...; candidate_evidence=..."}\n\n'
        f"query={query}\n"
        f"baseline={{\"docid\":{json.dumps(baseline_docid, ensure_ascii=False)},"
        f"\"content\":{json.dumps(baseline_text[:1300], ensure_ascii=False)}}}\n"
        f"candidate={{\"docid\":{json.dumps(candidate_docid, ensure_ascii=False)},"
        f"\"content\":{json.dumps(candidate_text[:1300], ensure_ascii=False)}}}"
    )
    content = _chat(provider=provider, host=host, model=model, prompt=prompt, api_key=api_key)
    judgement = try_parse_judgement(content)
    if judgement is None:
        return Judgement(winner="baseline", docid="", confidence=0.0, reason="malformed response")
    if is_rejected_reason(judgement.reason):
        return Judgement(winner="baseline", docid="", confidence=judgement.confidence, reason=judgement.reason)
    return judgement


def judge_direct_answer_candidate(
    *,
    query: str,
    baseline_docid: str,
    baseline_text: str,
    candidate_docid: str,
    candidate_text: str,
    model: str,
    host: str,
    provider: str = "ollama",
    api_key: str | None = None,
) -> Judgement:
    prompt = (
        "Korean IR direct-answer judge. Submit budget is scarce, but baseline may be partially relevant. "
        "Choose candidate only when it directly answers the query's requested entity/relation better than baseline. "
        "Reject candidates that are off-topic, generic, adjacent, narrower, broader, or only keyword-matched. "
        "Set candidate_direct_answer=true only when candidate contains exact evidence for the query. "
        "Set candidate_offtopic=true for scenario drift or keyword-only matches. "
        "Set baseline_is_wrong=true only when baseline answers a different topic; false is allowed for partial baseline. "
        "Use submit_risk as low, medium, or high. Never choose candidate when submit_risk is high. "
        "Output JSON only: "
        '{"winner":"baseline|candidate|tie","docid":"candidate-docid-or-empty","confidence":0.0,'
        '"baseline_is_wrong":true,"candidate_direct_answer":true,"candidate_offtopic":false,'
        '"submit_risk":"low|medium|high","reason":"short Korean evidence"}\n\n'
        f"query={query}\n"
        f"baseline={{\"docid\":{json.dumps(baseline_docid, ensure_ascii=False)},"
        f"\"content\":{json.dumps(baseline_text[:1300], ensure_ascii=False)}}}\n"
        f"candidate={{\"docid\":{json.dumps(candidate_docid, ensure_ascii=False)},"
        f"\"content\":{json.dumps(candidate_text[:1300], ensure_ascii=False)}}}"
    )
    content = _chat(provider=provider, host=host, model=model, prompt=prompt, api_key=api_key)
    judgement = try_parse_judgement(content)
    if judgement is None:
        return Judgement(winner="baseline", docid="", confidence=0.0, reason="malformed response")
    if judgement.candidate_offtopic or not judgement.candidate_direct_answer or judgement.submit_risk == "high":
        return Judgement(
            winner="baseline",
            docid="",
            confidence=judgement.confidence,
            reason=judgement.reason,
            baseline_is_wrong=judgement.baseline_is_wrong,
            candidate_direct_answer=judgement.candidate_direct_answer,
            candidate_offtopic=judgement.candidate_offtopic,
            submit_risk=judgement.submit_risk,
        )
    return judgement


def write_single_row_decisions(
    *,
    baseline_path: Path,
    corpus_path: Path,
    decisions: list[CandidateDecision],
    output_dir: Path,
    name_prefix: str,
) -> list[Path]:
    baseline_rows = _load_rows(baseline_path)
    docs_by_id = {str(row["docid"]): row for row in _load_rows(corpus_path)}
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for decision in decisions:
        rows = [dict(row) for row in baseline_rows]
        for row in rows:
            if str(row["eval_id"]) != decision.eval_id:
                continue
            row["topk"] = decision.candidate_topk
            row["references"] = [
                {"score": decision.confidence if index == 0 else 0.0, "docid": docid, "content": _doc_text(docs_by_id[docid])}
                for index, docid in enumerate(decision.candidate_topk)
                if docid in docs_by_id
            ]
            break
        target = output_dir / f"{name_prefix}_eval{decision.eval_id}.jsonl"
        _write_rows(target, rows)
        written.append(target)
    return written


def write_audit(path: Path, decisions: list[CandidateDecision]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [decision.__dict__ for decision in decisions]
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Use Ollama or Upstage to judge fresh corpus candidates.")
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--public-results", type=Path, default=None)
    parser.add_argument("--provider", choices=("ollama", "upstage"), default="ollama")
    parser.add_argument("--model", default=None)
    parser.add_argument("--host", default=None)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--pool-size", type=int, default=8)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--min-confidence", type=float, default=0.8)
    parser.add_argument("--max-eval-id", type=int, default=None)
    parser.add_argument("--min-eval-id", type=int, default=None)
    parser.add_argument("--audit-output", type=Path, default=None)
    parser.add_argument("--single-output-dir", type=Path, default=None)
    parser.add_argument("--name-prefix", default="ollama_judge")
    args = parser.parse_args()

    locked = (
        {result.eval_id for result in load_public_results(args.public_results)}
        if args.public_results is not None
        else set()
    )
    model = args.model or ("solar-pro3" if args.provider == "upstage" else "granite4.1:8b")
    host = args.host or (
        os.environ.get("UPSTAGE_BASE_URL", "https://api.upstage.ai/v1")
        if args.provider == "upstage"
        else "http://localhost:11434"
    )
    api_key = args.api_key or _upstage_api_key() if args.provider == "upstage" else args.api_key
    decisions = generate_decisions(
        baseline_path=args.baseline,
        corpus_path=args.corpus,
        locked_eval_ids=locked,
        provider=args.provider,
        model=model,
        host=host,
        api_key=api_key,
        pool_size=args.pool_size,
        limit=args.limit,
        min_confidence=args.min_confidence,
        max_eval_id=args.max_eval_id,
        min_eval_id=args.min_eval_id,
    )
    for decision in decisions:
        print(
            f"eval_id={decision.eval_id} baseline_top1={decision.baseline_top1} "
            f"candidate_top1={decision.candidate_top1} confidence={decision.confidence:.3f} "
            f"reason={decision.reason}"
        )
    if args.audit_output is not None:
        write_audit(args.audit_output, decisions)
        print(f"audit={args.audit_output}")
    if args.single_output_dir is not None:
        written = write_single_row_decisions(
            baseline_path=args.baseline,
            corpus_path=args.corpus,
            decisions=decisions,
            output_dir=args.single_output_dir,
            name_prefix=args.name_prefix,
        )
        for path in written:
            print(f"wrote={path}")
    return 0


def _chat(*, provider: str, host: str, model: str, prompt: str, api_key: str | None = None) -> str:
    if provider == "ollama":
        return _ollama_chat(host=host, model=model, prompt=prompt)
    if provider == "upstage":
        return _upstage_chat(base_url=host, model=model, prompt=prompt, api_key=api_key)
    raise ValueError(f"Unsupported provider: {provider}")


def _ollama_chat(*, host: str, model: str, prompt: str) -> str:
    endpoint = host.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0, "num_predict": 300},
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8"))
    message = data.get("message", {}) if isinstance(data, dict) else {}
    return str(message.get("content", "")) if isinstance(message, dict) else ""


def _upstage_chat(*, base_url: str, model: str, prompt: str, api_key: str | None = None) -> str:
    key = api_key or _upstage_api_key()
    if not key:
        raise RuntimeError("UPSTAGE_API_SECRET_KEY or UPSTAGE_API_KEY is required for --provider upstage")
    endpoint = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 300,
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8"))
    choices = data.get("choices", []) if isinstance(data, dict) else []
    if not choices:
        return ""
    message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
    return str(message.get("content", "")) if isinstance(message, dict) else ""


def _upstage_api_key() -> str | None:
    return os.environ.get("UPSTAGE_API_SECRET_KEY") or os.environ.get("UPSTAGE_API_KEY")


def _optional_bool(value: object) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return None


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
