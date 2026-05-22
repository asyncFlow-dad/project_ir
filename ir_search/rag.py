from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from .chunking import chunk_document
from .indexer import CorpusDocument, SearchIndex, build_index, search
from .tokenize import normalize_query, tokenize


DEFAULT_TOP_K = 3
DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.1"
DEFAULT_EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
DEFAULT_CANDIDATE_LIMIT = 200
DEFAULT_DENSE_WEIGHT = 0.55
DEFAULT_FUSION_METHOD = "score"
DEFAULT_CASUAL_POLICY = "strict"
DEFAULT_RERANK_METHOD = "none"
DEFAULT_RERANK_CANDIDATES = 30
DEFAULT_SEMANTIC_RERANK_WEIGHT = 0.85

KNOWLEDGE_CUES = (
    "?",
    "가능",
    "과정",
    "궁금",
    "누구",
    "뭐",
    "무엇",
    "무슨",
    "방법",
    "방식",
    "분류",
    "설명",
    "알려",
    "어떤",
    "어떻게",
    "왜",
    "원리",
    "원인",
    "의미",
    "이유",
    "차이",
    "특징",
    "현상",
    "효과",
    "역할",
)
CASUAL_CUES = (
    "고마워",
    "괜찮아",
    "그만 얘기",
    "기분",
    "똑똑",
    "너무 힘들",
    "무섭겠다",
    "반가워",
    "사랑해",
    "신나",
    "심심",
    "안녕",
    "우울",
    "잘해",
    "잘 지내",
    "즐거웠",
    "힘드",
    "힘들다",
)
FOLLOWUP_CUES = ("그", "그럼", "그 이유", "그 원인", "어떤", "왜", "어떻게", "이유", "원인")
QUERY_STOP_TERMS = {
    "관한",
    "궁금해",
    "대해",
    "말해줘",
    "보기",
    "설명해줘",
    "알려줘",
    "위한",
    "조사해",
    "조사",
    "노하우",
    "방법중",
    "방법은",
}


@dataclass(frozen=True)
class RagExample:
    eval_id: int | str
    messages: list[dict[str, str]]


@dataclass(frozen=True)
class RagResponse:
    eval_id: int | str
    standalone_query: str
    topk: list[str]
    answer: str
    references: list[dict[str, object]]

    def to_dict(self) -> dict[str, object]:
        return {
            "eval_id": self.eval_id,
            "standalone_query": self.standalone_query,
            "topk": self.topk,
            "answer": self.answer,
            "references": self.references,
        }


@dataclass(frozen=True)
class HybridResult:
    document: CorpusDocument
    score: float


@dataclass(frozen=True)
class DenseIndex:
    doc_ids: list[str]
    documents: dict[str, CorpusDocument]
    embeddings: Any
    model: Any
    query_prefix: str = ""


def load_jsonl_documents(path: str | Path) -> list[CorpusDocument]:
    documents: list[CorpusDocument] = []
    for row_number, row in enumerate(_read_jsonl(path), start=1):
        doc_id = _first_string(row, ("docid", "doc_id", "id", "document_id"))
        text = _first_string(row, ("content", "text", "body", "contents"))
        title = _first_string(row, ("title", "name"), default="")
        if not doc_id:
            doc_id = f"doc-{row_number}"
        if not text:
            continue
        joined = f"{title}\n\n{text}".strip() if title else text
        documents.append(CorpusDocument(id=doc_id, path=Path(doc_id), text=joined))
    return documents


def load_rag_corpus(path: str | Path) -> list[CorpusDocument]:
    source = Path(path)
    if source.is_dir():
        return _chunk_documents(load_jsonl_documents(source / "documents.jsonl")) if (
            source / "documents.jsonl"
        ).exists() else _chunk_documents(_load_text_corpus(source))
    if source.suffix == ".jsonl":
        return _chunk_documents(load_jsonl_documents(source))
    return _chunk_documents(_load_text_corpus(source))


def load_eval(path: str | Path) -> list[RagExample]:
    examples: list[RagExample] = []
    for row_number, row in enumerate(_read_jsonl(path), start=1):
        eval_id = _first_value(row, ("eval_id", "query_id", "id"), default=f"eval-{row_number}")
        messages_value = row.get("msg", row.get("messages"))
        if isinstance(messages_value, list):
            messages = [
                {
                    "role": str(message.get("role", "user")),
                    "content": str(message.get("content", "")),
                }
                for message in messages_value
                if isinstance(message, dict)
            ]
        else:
            query = _first_string(row, ("query", "question", "input", "msg"), default="")
            messages = [{"role": "user", "content": query}]
        examples.append(RagExample(eval_id=eval_id, messages=messages))
    return examples


def generate_submission(
    *,
    corpus_path: str | Path,
    eval_path: str | Path,
    output_path: str | Path,
    top_k: int = DEFAULT_TOP_K,
    use_openai: bool = False,
    use_ollama: bool = False,
    use_ollama_answers: bool = False,
    use_ollama_rerank: bool = False,
    ollama_rerank_candidates: int = 10,
    model: str = "gpt-4o-mini",
    ollama_model: str = DEFAULT_OLLAMA_MODEL,
    ollama_host: str = DEFAULT_OLLAMA_HOST,
    use_dense: bool = False,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    embedding_cache_dir: str | Path = "data/indexes/rag_dense",
    embedding_query_prefix: str | None = None,
    embedding_document_prefix: str | None = None,
    candidate_limit: int = DEFAULT_CANDIDATE_LIMIT,
    dense_weight: float = DEFAULT_DENSE_WEIGHT,
    fusion_method: str = DEFAULT_FUSION_METHOD,
    casual_policy: str = DEFAULT_CASUAL_POLICY,
    rerank_method: str = DEFAULT_RERANK_METHOD,
    rerank_candidates: int = DEFAULT_RERANK_CANDIDATES,
    semantic_rerank_weight: float = DEFAULT_SEMANTIC_RERANK_WEIGHT,
    output_format: str = "jsonl",
) -> list[RagResponse]:
    documents = load_rag_corpus(corpus_path)
    if not documents:
        raise ValueError(f"No documents loaded from {corpus_path}")
    index = build_index(documents)
    dense_index = (
        _build_or_load_dense_index(
            documents,
            model_name=embedding_model,
            cache_dir=embedding_cache_dir,
            query_prefix=embedding_query_prefix,
            document_prefix=embedding_document_prefix,
        )
        if use_dense
        else None
    )
    examples = load_eval(eval_path)

    responses = []
    for example in examples:
        query, retrieve = _plan_retrieval(
            example.messages,
            use_ollama=use_ollama,
            ollama_model=ollama_model,
            ollama_host=ollama_host,
            casual_policy=casual_policy,
        )
        if not retrieve:
            responses.append(
                RagResponse(
                    eval_id=example.eval_id,
                    standalone_query="",
                    topk=[],
                    answer=_chat_answer(example.messages),
                    references=[],
                )
            )
            continue

        retrieve_limit = max(
            top_k,
            ollama_rerank_candidates if use_ollama_rerank else top_k,
            rerank_candidates if rerank_method != "none" else top_k,
        )
        results = _hybrid_retrieve(
            index,
            query,
            limit=retrieve_limit,
            candidate_limit=candidate_limit,
            dense_index=dense_index,
            dense_weight=dense_weight,
            fusion_method=fusion_method,
        )
        if rerank_method == "semantic" and dense_index is not None and results:
            results = _semantic_rerank_results(
                query,
                results,
                dense_index=dense_index,
                limit=top_k,
                semantic_weight=semantic_rerank_weight,
            )
        elif use_ollama_rerank and results:
            results = _ollama_rerank_results(
                query,
                results,
                model=ollama_model,
                host=ollama_host,
                limit=top_k,
            )
        else:
            results = results[:top_k]
        references = [
            {
                "score": result.score,
                "docid": _base_doc_id(result.document.id),
                "content": result.document.text,
            }
            for result in results
        ]
        contexts = [str(reference["content"]) for reference in references]
        if use_ollama and use_ollama_answers:
            answer = _ollama_answer(
                example.messages,
                contexts,
                model=ollama_model,
                host=ollama_host,
            )
        elif use_openai:
            answer = _openai_answer(example.messages, contexts, model=model)
        else:
            answer = _extractive_answer(query, contexts)
        responses.append(
            RagResponse(
                eval_id=example.eval_id,
                standalone_query=query,
                topk=[_base_doc_id(result.document.id) for result in results],
                answer=answer,
                references=references,
            )
        )

    write_submission(responses, output_path, output_format=output_format)
    return responses


def standalone_query(messages: list[dict[str, str]]) -> str:
    user_texts = [
        message.get("content", "").strip()
        for message in messages
        if message.get("role") == "user" and message.get("content", "").strip()
    ]
    if not user_texts:
        return ""
    if len(user_texts) == 1:
        return _clean_query(user_texts[-1])
    last = user_texts[-1]
    if any(cue in last for cue in FOLLOWUP_CUES) or len(tokenize(last)) <= 4:
        return _clean_query(f"{_topic_fragment(user_texts[-2])} {last}".strip())
    return _clean_query(last)


def should_retrieve(
    messages: list[dict[str, str]],
    query: str,
    *,
    casual_policy: str = DEFAULT_CASUAL_POLICY,
) -> bool:
    last_user = ""
    for message in reversed(messages):
        if message.get("role") == "user":
            last_user = message.get("content", "").strip()
            break
    if not query.strip():
        return False
    if casual_policy == "off":
        return True
    if _looks_like_named_entity_query(query):
        return True
    if casual_policy == "balanced" and _looks_like_affective_content_request(last_user):
        return True
    if any(cue in last_user for cue in CASUAL_CUES) or _looks_like_personal_chat(
        last_user, query
    ):
        return False
    if any(cue in query for cue in KNOWLEDGE_CUES):
        return True
    return len(tokenize(query)) >= 2


def write_submission(
    responses: Iterable[RagResponse],
    output_path: str | Path,
    *,
    output_format: str = "jsonl",
) -> None:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = [response.to_dict() for response in responses]
    with target.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate RAG leaderboard submission.")
    parser.add_argument("--corpus", default="data/documents.jsonl")
    parser.add_argument("--eval", default="data/eval.jsonl")
    parser.add_argument("--output", default="sample_submission.csv")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--format", choices=("jsonl", "csv"), default="jsonl")
    parser.add_argument("--openai", action="store_true", help="Use OpenAI when available")
    parser.add_argument("--ollama", action="store_true", help="Use local Ollama for retrieval planning")
    parser.add_argument("--ollama-answers", action="store_true", help="Also use Ollama for answer generation")
    parser.add_argument("--ollama-rerank", action="store_true", help="Use Ollama to rerank top retrieval candidates")
    parser.add_argument("--ollama-rerank-candidates", type=int, default=10)
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"))
    parser.add_argument("--ollama-model", default=os.environ.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL))
    parser.add_argument("--ollama-host", default=os.environ.get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST))
    parser.add_argument("--dense", action="store_true", help="Use sentence-transformer dense reranking")
    parser.add_argument("--embedding-model", default=os.environ.get("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL))
    parser.add_argument("--embedding-cache-dir", default=os.environ.get("EMBEDDING_CACHE_DIR", "data/indexes/rag_dense"))
    parser.add_argument("--embedding-query-prefix", default=os.environ.get("EMBEDDING_QUERY_PREFIX"))
    parser.add_argument("--embedding-document-prefix", default=os.environ.get("EMBEDDING_DOCUMENT_PREFIX"))
    parser.add_argument("--candidate-limit", type=int, default=DEFAULT_CANDIDATE_LIMIT)
    parser.add_argument("--dense-weight", type=float, default=DEFAULT_DENSE_WEIGHT)
    parser.add_argument("--fusion-method", choices=("score", "rrf"), default=DEFAULT_FUSION_METHOD)
    parser.add_argument(
        "--casual-policy",
        choices=("strict", "balanced", "off"),
        default=DEFAULT_CASUAL_POLICY,
    )
    parser.add_argument(
        "--rerank-method",
        choices=("none", "semantic"),
        default=DEFAULT_RERANK_METHOD,
    )
    parser.add_argument("--rerank-candidates", type=int, default=DEFAULT_RERANK_CANDIDATES)
    parser.add_argument(
        "--semantic-rerank-weight",
        type=float,
        default=DEFAULT_SEMANTIC_RERANK_WEIGHT,
    )
    args = parser.parse_args(argv)

    generate_submission(
        corpus_path=args.corpus,
        eval_path=args.eval,
        output_path=args.output,
        top_k=args.top_k,
        use_openai=args.openai,
        use_ollama=args.ollama,
        use_ollama_answers=args.ollama_answers,
        use_ollama_rerank=args.ollama_rerank,
        ollama_rerank_candidates=args.ollama_rerank_candidates,
        model=args.model,
        ollama_model=args.ollama_model,
        ollama_host=args.ollama_host,
        use_dense=args.dense,
        embedding_model=args.embedding_model,
        embedding_cache_dir=args.embedding_cache_dir,
        embedding_query_prefix=args.embedding_query_prefix,
        embedding_document_prefix=args.embedding_document_prefix,
        candidate_limit=args.candidate_limit,
        dense_weight=args.dense_weight,
        fusion_method=args.fusion_method,
        casual_policy=args.casual_policy,
        rerank_method=args.rerank_method,
        rerank_candidates=args.rerank_candidates,
        semantic_rerank_weight=args.semantic_rerank_weight,
        output_format=args.format,
    )
    return 0


def _chunk_documents(documents: list[CorpusDocument]) -> list[CorpusDocument]:
    chunks: list[CorpusDocument] = []
    for document in documents:
        doc_chunks = chunk_document(document.text, max_chars=1200, overlap=150)
        if not doc_chunks:
            chunks.append(document)
            continue
        for chunk in doc_chunks:
            chunk_id = f"{document.id}#chunk-{chunk.chunk_id}"
            chunks.append(CorpusDocument(id=chunk_id, path=document.path, text=chunk.text))
    return chunks


def _load_text_corpus(path: Path) -> list[CorpusDocument]:
    if path.is_file():
        return [CorpusDocument(id=path.name, path=path, text=path.read_text(encoding="utf-8"))]
    documents = []
    for file_path in sorted(path.rglob("*")):
        if file_path.is_file() and file_path.suffix.lower() in {".md", ".txt"}:
            documents.append(
                CorpusDocument(
                    id=str(file_path.relative_to(path)),
                    path=file_path,
                    text=file_path.read_text(encoding="utf-8"),
                )
            )
    return documents


def _extractive_answer(query: str, contexts: list[str]) -> str:
    if not contexts:
        return "검색 결과에서 답을 찾을 수 없습니다."
    terms = set(tokenize(query))
    sentences = []
    for context in contexts:
        sentences.extend(_split_sentences(context))
    if not sentences:
        return contexts[0][:350].strip()
    ranked = sorted(
        sentences,
        key=lambda sentence: (
            -sum(1 for term in tokenize(sentence) if term in terms),
            len(sentence),
        ),
    )
    selected = [sentence.strip() for sentence in ranked[:2] if sentence.strip()]
    return " ".join(selected)[:700] if selected else contexts[0][:350].strip()


def _plan_retrieval(
    messages: list[dict[str, str]],
    *,
    use_ollama: bool,
    ollama_model: str,
    ollama_host: str,
    casual_policy: str = DEFAULT_CASUAL_POLICY,
) -> tuple[str, bool]:
    fallback_query = standalone_query(messages)
    fallback_retrieve = should_retrieve(messages, fallback_query, casual_policy=casual_policy)
    if not use_ollama:
        return fallback_query, fallback_retrieve

    planned = _ollama_retrieval_plan(messages, model=ollama_model, host=ollama_host)
    if planned is None:
        return fallback_query, fallback_retrieve

    query = _clean_query(str(planned.get("query", "")).strip()) or fallback_query
    retrieve = bool(planned.get("retrieve", fallback_retrieve))
    if not should_retrieve(messages, query, casual_policy=casual_policy) and not retrieve:
        return "", False
    return query, retrieve


def _ollama_retrieval_plan(
    messages: list[dict[str, str]],
    *,
    model: str,
    host: str,
) -> dict[str, object] | None:
    prompt = (
        "다음 대화의 마지막 사용자 메시지가 과학/상식/지식 질문이면 retrieve=true로 분류하고, "
        "검색에 적합한 짧은 한국어 standalone query를 작성하세요. "
        "일상 대화, 감정 표현, 인사, 검색이 필요 없는 말이면 retrieve=false와 빈 query를 반환하세요. "
        '반드시 JSON만 출력하세요: {"retrieve": true, "query": "..."}\n\n'
        f"messages={json.dumps(messages, ensure_ascii=False)}"
    )
    content = _ollama_chat(
        [{"role": "user", "content": prompt}],
        model=model,
        host=host,
        temperature=0,
        num_predict=96,
        format_json=True,
    )
    if not content:
        return None
    match = re.search(r"\{.*\}", content, flags=re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _ollama_answer(
    messages: list[dict[str, str]],
    contexts: list[str],
    *,
    model: str,
    host: str,
) -> str:
    prompt = (
        "주어진 Reference만 근거로 한국어로 간결하게 답하세요. "
        "Reference로 답할 수 없으면 정보가 부족하다고 답하세요.\n\n"
        f"Reference:\n{json.dumps(contexts, ensure_ascii=False)}"
    )
    content = _ollama_chat(
        [{"role": "system", "content": prompt}, *messages],
        model=model,
        host=host,
        temperature=0,
        num_predict=512,
    )
    return content or _extractive_answer(standalone_query(messages), contexts)


def _ollama_rerank_results(
    query: str,
    results: list[HybridResult],
    *,
    model: str,
    host: str,
    limit: int,
) -> list[HybridResult]:
    candidates = [
        {
            "docid": _base_doc_id(result.document.id),
            "content": result.document.text[:900],
        }
        for result in results
    ]
    prompt = (
        "검색 질의와 후보 문서가 주어집니다. 질의에 가장 직접적으로 답하는 문서 docid "
        f"{limit}개를 순서대로 고르세요. 반드시 JSON만 출력하세요: "
        '{"topk":["docid1","docid2","docid3"]}\n\n'
        f"query={query}\n"
        f"candidates={json.dumps(candidates, ensure_ascii=False)}"
    )
    content = _ollama_chat(
        [{"role": "user", "content": prompt}],
        model=model,
        host=host,
        temperature=0,
        num_predict=128,
        format_json=True,
    )
    if not content:
        return results[:limit]
    match = re.search(r"\{.*\}", content, flags=re.DOTALL)
    if not match:
        return results[:limit]
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return results[:limit]
    requested = parsed.get("topk")
    if not isinstance(requested, list):
        return results[:limit]

    by_base_id = {_base_doc_id(result.document.id): result for result in results}
    reranked: list[HybridResult] = []
    seen: set[str] = set()
    for doc_id in requested:
        base_id = str(doc_id)
        if base_id in by_base_id and base_id not in seen:
            reranked.append(by_base_id[base_id])
            seen.add(base_id)
        if len(reranked) >= limit:
            break
    for result in results:
        base_id = _base_doc_id(result.document.id)
        if base_id not in seen:
            reranked.append(result)
            seen.add(base_id)
        if len(reranked) >= limit:
            break
    return reranked[:limit]


def _semantic_rerank_results(
    query: str,
    results: list[HybridResult],
    *,
    dense_index: DenseIndex,
    limit: int,
    semantic_weight: float = DEFAULT_SEMANTIC_RERANK_WEIGHT,
) -> list[HybridResult]:
    try:
        import numpy as np
    except Exception:
        return results[:limit]
    if not results:
        return []

    query_embedding = dense_index.model.encode(
        [f"{dense_index.query_prefix}{query}"],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )[0]
    doc_positions = {doc_id: index for index, doc_id in enumerate(dense_index.doc_ids)}
    original_scores = {result.document.id: result.score for result in results}
    semantic_scores: dict[str, float] = {}
    for result in results:
        position = doc_positions.get(result.document.id)
        if position is None:
            continue
        semantic_scores[result.document.id] = float(
            np.asarray(dense_index.embeddings[position]) @ query_embedding
        )
    if not semantic_scores:
        return results[:limit]

    original_norm = _normalize_scores(original_scores)
    semantic_norm = _normalize_scores(semantic_scores)
    semantic_weight = min(max(semantic_weight, 0.0), 1.0)
    original_weight = 1.0 - semantic_weight
    scored = []
    for result in results:
        doc_id = result.document.id
        score = (semantic_weight * semantic_norm.get(doc_id, 0.0)) + (
            original_weight * original_norm.get(doc_id, 0.0)
        )
        scored.append(HybridResult(document=result.document, score=score))
    return sorted(scored, key=lambda result: (-result.score, result.document.id))[:limit]


def _ollama_chat(
    messages: list[dict[str, str]],
    *,
    model: str,
    host: str,
    temperature: float,
    num_predict: int = 256,
    format_json: bool = False,
) -> str:
    endpoint = host.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": num_predict},
    }
    if format_json:
        payload["format"] = "json"
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return ""
    message = data.get("message", {}) if isinstance(data, dict) else {}
    content = message.get("content", "") if isinstance(message, dict) else ""
    return str(content).strip()


def _chat_answer(messages: list[dict[str, str]]) -> str:
    last_user = ""
    for message in reversed(messages):
        if message.get("role") == "user":
            last_user = message.get("content", "").strip()
            break
    if any(cue in last_user for cue in ("힘들", "무섭", "걱정")):
        return "그렇게 느낄 수 있습니다. 필요하면 어떤 점이 걱정되는지 더 말해 주세요."
    return "네, 알겠습니다."


def _hybrid_retrieve(
    index: SearchIndex,
    query: str,
    *,
    limit: int,
    candidate_limit: int = DEFAULT_CANDIDATE_LIMIT,
    dense_index: DenseIndex | None = None,
    dense_weight: float = DEFAULT_DENSE_WEIGHT,
    fusion_method: str = DEFAULT_FUSION_METHOD,
) -> list[HybridResult]:
    sparse_results = search(index, query, limit=max(candidate_limit, limit * 12, 60))
    query_grams = _char_ngrams(query)
    lexical_scores: dict[str, tuple[float, CorpusDocument]] = {}
    if sparse_results:
        query_terms = _coverage_terms(query)
        lexical_scores = {
            result.document.id: (
                _lexical_score(
                    query=query,
                    query_terms=query_terms,
                    query_grams=query_grams,
                    bm25_score=result.score,
                    document=result.document,
                ),
                result.document,
            )
            for result in sparse_results
        }

    dense_scores: dict[str, tuple[float, CorpusDocument]] = {}
    if dense_index is not None:
        dense_scores = _dense_retrieve(dense_index, query, limit=max(candidate_limit, limit))

    if lexical_scores or dense_scores:
        if fusion_method == "rrf":
            merged = _merge_candidate_scores_rrf(
                lexical_scores,
                dense_scores,
                dense_weight=dense_weight,
            )
        else:
            merged = _merge_candidate_scores(
                lexical_scores,
                dense_scores,
                dense_weight=dense_weight,
            )
        return [
            HybridResult(document=document, score=score)
            for score, _doc_id, document in _unique_base_candidates(merged, limit)
        ]

    scored = []
    for stats in index.doc_stats.values():
        char_score = _char_overlap(query_grams, stats.document.text)
        if char_score < 0.04:
            continue
        scored.append((char_score, stats.document.id, stats.document))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [
        HybridResult(document=document, score=score)
        for score, _doc_id, document in _unique_base_candidates(scored, limit)
        if score >= 0.18
    ]


def _unique_base_candidates(
    scored: Iterable[tuple[float, str, CorpusDocument]],
    limit: int,
) -> list[tuple[float, str, CorpusDocument]]:
    selected: list[tuple[float, str, CorpusDocument]] = []
    seen: set[str] = set()
    for score, doc_id, document in scored:
        base_id = _base_doc_id(doc_id)
        if base_id in seen:
            continue
        selected.append((score, doc_id, document))
        seen.add(base_id)
        if len(selected) >= limit:
            break
    return selected


def _topic_fragment(text: str) -> str:
    fragment = re.split(r"(걸리면|무섭|궁금|같더|맞습니다|그렇)", text, maxsplit=1)[0]
    return fragment.strip() or text.strip()


def _clean_query(query: str) -> str:
    return normalize_query(query)


def _looks_like_named_entity_query(query: str) -> bool:
    return bool(re.search(r"\b[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)+\b", query))


def _looks_like_personal_chat(last_user: str, query: str) -> bool:
    combined = f"{last_user} {query}"
    pronoun_pattern = r"(^|[^0-9A-Za-z가-힣])(너|너는|너도|너가|니|니가|네가|넌)(?=$|[^0-9A-Za-z가-힣])"
    if not re.search(pronoun_pattern, combined):
        return False
    return any(
        cue in combined
        for cue in ("누구", "뭐야", "뭘", "모르", "잘하", "잘해", "똑똑", "대답")
    )


def _looks_like_affective_content_request(last_user: str) -> bool:
    return any(cue in last_user for cue in ("우울", "힘들", "무섭", "걱정")) and any(
        cue in last_user for cue in ("얘기", "이야기", "알려", "말해", "해줘", "해줄래")
    )


def _char_ngrams(text: str, n: int = 2) -> set[str]:
    compact = re.sub(r"[^0-9A-Za-z가-힣]+", "", text.lower())
    if len(compact) <= n:
        return {compact} if compact else set()
    return {compact[index : index + n] for index in range(len(compact) - n + 1)}


def _char_overlap(query_grams: set[str], text: str) -> float:
    if not query_grams:
        return 0.0
    text_grams = _char_ngrams(text)
    if not text_grams:
        return 0.0
    return len(query_grams & text_grams) / len(query_grams)


def _coverage_terms(query: str) -> set[str]:
    return {term for term in tokenize(query) if term not in QUERY_STOP_TERMS and len(term) > 1}


def _term_coverage(query_terms: set[str], text: str) -> float:
    if not query_terms:
        return 0.0
    text_terms = set(tokenize(text))
    return len(query_terms & text_terms) / len(query_terms)


def _lexical_score(
    *,
    query: str,
    query_terms: set[str],
    query_grams: set[str],
    bm25_score: float,
    document: CorpusDocument,
) -> float:
    text = document.text
    coverage = _term_coverage(query_terms, text)
    char_overlap = _char_overlap(query_grams, text)
    phrase_boost = 1.0 if query and query in text else 0.0
    compact_query = re.sub(r"\s+", "", query)
    compact_text = re.sub(r"\s+", "", text)
    compact_boost = 0.5 if compact_query and compact_query in compact_text else 0.0
    return (bm25_score * (0.75 + coverage)) + (0.45 * char_overlap) + phrase_boost + compact_boost


def _merge_candidate_scores(
    lexical_scores: dict[str, tuple[float, CorpusDocument]],
    dense_scores: dict[str, tuple[float, CorpusDocument]],
    *,
    dense_weight: float,
) -> list[tuple[float, str, CorpusDocument]]:
    lexical_norm = _normalize_scores({doc_id: score for doc_id, (score, _) in lexical_scores.items()})
    dense_norm = _normalize_scores({doc_id: score for doc_id, (score, _) in dense_scores.items()})
    doc_ids = set(lexical_scores) | set(dense_scores)
    scored: list[tuple[float, str, CorpusDocument]] = []
    bounded_dense_weight = min(max(dense_weight, 0.0), 1.0)
    lexical_weight = 1.0 - bounded_dense_weight
    for doc_id in doc_ids:
        document = (
            lexical_scores.get(doc_id, dense_scores.get(doc_id))  # type: ignore[arg-type]
        )[1]
        if dense_scores:
            score = (lexical_weight * lexical_norm.get(doc_id, 0.0)) + (
                bounded_dense_weight * dense_norm.get(doc_id, 0.0)
            )
        else:
            score = lexical_norm.get(doc_id, 0.0)
        scored.append((score, doc_id, document))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored


def _merge_candidate_scores_rrf(
    lexical_scores: dict[str, tuple[float, CorpusDocument]],
    dense_scores: dict[str, tuple[float, CorpusDocument]],
    *,
    dense_weight: float,
    k: int = 60,
) -> list[tuple[float, str, CorpusDocument]]:
    lexical_rank = _rank_scores(lexical_scores)
    dense_rank = _rank_scores(dense_scores)
    doc_ids = set(lexical_scores) | set(dense_scores)
    bounded_dense_weight = min(max(dense_weight, 0.0), 1.0)
    lexical_weight = 1.0 - bounded_dense_weight
    scored: list[tuple[float, str, CorpusDocument]] = []
    for doc_id in doc_ids:
        document = (
            lexical_scores.get(doc_id, dense_scores.get(doc_id))  # type: ignore[arg-type]
        )[1]
        score = 0.0
        if doc_id in lexical_rank:
            score += lexical_weight / (k + lexical_rank[doc_id])
        if doc_id in dense_rank:
            score += bounded_dense_weight / (k + dense_rank[doc_id])
        scored.append((score, doc_id, document))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored


def _rank_scores(scores: dict[str, tuple[float, CorpusDocument]]) -> dict[str, int]:
    ranked = sorted(scores.items(), key=lambda item: (-item[1][0], item[0]))
    return {doc_id: rank for rank, (doc_id, _) in enumerate(ranked, start=1)}


def _normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    values = list(scores.values())
    low = min(values)
    high = max(values)
    if high <= low:
        return {doc_id: 1.0 for doc_id in scores}
    return {doc_id: (score - low) / (high - low) for doc_id, score in scores.items()}


def _build_or_load_dense_index(
    documents: Sequence[CorpusDocument],
    *,
    model_name: str,
    cache_dir: str | Path,
    query_prefix: str | None,
    document_prefix: str | None,
) -> DenseIndex | None:
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except Exception:
        return None

    cache_root = Path(cache_dir)
    cache_root.mkdir(parents=True, exist_ok=True)
    embeddings_path = cache_root / "embeddings.npy"
    meta_path = cache_root / "meta.json"
    doc_ids = [document.id for document in documents]
    documents_by_id = {document.id: document for document in documents}
    resolved_query_prefix, resolved_document_prefix = _embedding_prefixes(
        model_name,
        query_prefix=query_prefix,
        document_prefix=document_prefix,
    )
    try:
        model = SentenceTransformer(model_name)
    except Exception:
        return None

    if embeddings_path.exists() and meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if (
                meta.get("model") == model_name
                and meta.get("doc_ids") == doc_ids
                and meta.get("query_prefix") == resolved_query_prefix
                and meta.get("document_prefix") == resolved_document_prefix
            ):
                embeddings = np.load(embeddings_path)
                return DenseIndex(
                    doc_ids=doc_ids,
                    documents=documents_by_id,
                    embeddings=embeddings,
                    model=model,
                    query_prefix=resolved_query_prefix,
                )
        except Exception:
            pass

    texts = [f"{resolved_document_prefix}{document.text}" for document in documents]
    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    np.save(embeddings_path, embeddings)
    meta_path.write_text(
        json.dumps(
            {
                "model": model_name,
                "query_prefix": resolved_query_prefix,
                "document_prefix": resolved_document_prefix,
                "doc_ids": doc_ids,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return DenseIndex(
        doc_ids=doc_ids,
        documents=documents_by_id,
        embeddings=embeddings,
        model=model,
        query_prefix=resolved_query_prefix,
    )


def _dense_retrieve(
    dense_index: DenseIndex,
    query: str,
    *,
    limit: int,
) -> dict[str, tuple[float, CorpusDocument]]:
    try:
        import numpy as np
    except Exception:
        return {}
    query_embedding = dense_index.model.encode(
        [f"{dense_index.query_prefix}{query}"],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )[0]
    scores = dense_index.embeddings @ query_embedding
    candidate_count = min(limit, len(dense_index.doc_ids))
    if candidate_count <= 0:
        return {}
    top_indexes = np.argpartition(scores, -candidate_count)[-candidate_count:]
    ranked = sorted(((float(scores[index]), int(index)) for index in top_indexes), reverse=True)
    return {
        dense_index.doc_ids[index]: (score, dense_index.documents[dense_index.doc_ids[index]])
        for score, index in ranked
    }


def _embedding_prefixes(
    model_name: str,
    *,
    query_prefix: str | None,
    document_prefix: str | None,
) -> tuple[str, str]:
    if query_prefix is not None or document_prefix is not None:
        return query_prefix or "", document_prefix or ""
    lowered = model_name.lower()
    if "e5" in lowered:
        return "query: ", "passage: "
    return "", ""


def _openai_answer(messages: list[dict[str, str]], contexts: list[str], *, model: str) -> str:
    try:
        from openai import OpenAI
    except ImportError:
        return _extractive_answer(standalone_query(messages), contexts)
    if not os.environ.get("OPENAI_API_KEY"):
        return _extractive_answer(standalone_query(messages), contexts)

    prompt = (
        "주어진 Reference만 사용해 한국어로 간결하게 답하세요. "
        "Reference로 답할 수 없으면 정보가 부족하다고 답하세요.\n\n"
        f"Reference:\n{json.dumps(contexts, ensure_ascii=False)}"
    )
    client = OpenAI()
    result = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": prompt}, *messages],
        temperature=0,
        timeout=30,
    )
    return result.choices[0].message.content or ""


def _read_jsonl(path: str | Path) -> Iterable[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def _first_string(row: dict[str, Any], keys: Iterable[str], default: str = "") -> str:
    for key in keys:
        value = row.get(key)
        if value is not None:
            return str(value)
    return default


def _first_value(row: dict[str, Any], keys: Iterable[str], default: object = "") -> object:
    for key in keys:
        value = row.get(key)
        if value is not None:
            return value
    return default


def _base_doc_id(doc_id: str) -> str:
    return doc_id.split("#chunk-", 1)[0]


def _split_sentences(text: str) -> list[str]:
    compact = re.sub(r"\s+", " ", text).strip()
    return [part.strip() for part in re.split(r"(?<=[.!?。！？다요])\s+", compact) if part.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
