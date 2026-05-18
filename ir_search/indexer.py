from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from .tokenize import tokenize

DEFAULT_EXTENSIONS = {".md", ".txt"}


@dataclass(frozen=True)
class CorpusDocument:
    id: str
    path: Path
    text: str


@dataclass(frozen=True)
class DocumentStats:
    document: CorpusDocument
    term_count: int
    frequencies: Counter[str]


@dataclass(frozen=True)
class SearchIndex:
    documents: list[CorpusDocument]
    postings: dict[str, set[str]]
    doc_stats: dict[str, DocumentStats]
    average_document_length: float


@dataclass(frozen=True)
class SearchResult:
    document: CorpusDocument
    score: float
    snippet: str


def load_corpus(corpus_dir: str | Path) -> list[CorpusDocument]:
    root = Path(corpus_dir)
    files = _list_text_files(root)
    return [
        CorpusDocument(
            id=str(path.relative_to(root)),
            path=path,
            text=path.read_text(encoding="utf-8"),
        )
        for path in files
    ]


def build_index(documents: list[CorpusDocument]) -> SearchIndex:
    postings: dict[str, set[str]] = defaultdict(set)
    doc_stats: dict[str, DocumentStats] = {}
    total_terms = 0

    for document in documents:
        terms = tokenize(document.text)
        frequencies = Counter(terms)
        total_terms += len(terms)
        doc_stats[document.id] = DocumentStats(
            document=document,
            term_count=len(terms),
            frequencies=frequencies,
        )
        for term in frequencies:
            postings[term].add(document.id)

    average_document_length = total_terms / len(documents) if documents else 0.0
    return SearchIndex(
        documents=documents,
        postings=dict(postings),
        doc_stats=doc_stats,
        average_document_length=average_document_length,
    )


def search(index: SearchIndex, query: str, limit: int = 5) -> list[SearchResult]:
    query_terms = sorted(set(tokenize(query)))
    if not query_terms:
        return []

    results = [
        SearchResult(
            document=stats.document,
            score=_bm25_score(index, stats, query_terms),
            snippet=_make_snippet(stats.document.text, query_terms),
        )
        for stats in index.doc_stats.values()
    ]
    return sorted(
        (result for result in results if result.score > 0),
        key=lambda result: (-result.score, result.document.id),
    )[:limit]


def _list_text_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in DEFAULT_EXTENSIONS
    )


def _bm25_score(index: SearchIndex, stats: DocumentStats, query_terms: list[str]) -> float:
    k1 = 1.5
    b = 0.75
    document_count = len(index.documents)
    average_length = index.average_document_length or 1.0
    score = 0.0

    for term in query_terms:
        term_frequency = stats.frequencies.get(term, 0)
        if term_frequency == 0:
            continue

        document_frequency = len(index.postings.get(term, set()))
        idf = math.log(
            1 + (document_count - document_frequency + 0.5) / (document_frequency + 0.5)
        )
        length_norm = 1 - b + b * (stats.term_count / average_length)
        score += idf * (
            (term_frequency * (k1 + 1)) / (term_frequency + k1 * length_norm)
        )

    return score


def _make_snippet(text: str, query_terms: list[str]) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    lower = compact.lower()
    matches = [lower.find(term.lower()) for term in query_terms]
    first_match = min((match for match in matches if match >= 0), default=0)
    start = max(0, first_match - 80)
    snippet = compact[start : start + 220]
    prefix = "..." if start > 0 else ""
    suffix = "..." if start + 220 < len(compact) else ""
    return f"{prefix}{snippet}{suffix}"
