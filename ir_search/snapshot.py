from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from .indexer import SearchIndex, build_index, load_corpus


def default_snapshot_dir() -> Path:
    return Path("data/indexes")


def corpus_fingerprint(corpus_dir: Path) -> str:
    files = sorted(path for path in corpus_dir.rglob("*") if path.is_file())
    digest = sha256()
    for path in files:
        digest.update(str(path).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


def snapshot_path(corpus_dir: Path, base_dir: Path | None = None) -> Path:
    root = base_dir or default_snapshot_dir()
    return root / corpus_fingerprint(corpus_dir)


def save_snapshot(index: SearchIndex, corpus_dir: Path, base_dir: Path | None = None) -> Path:
    target = snapshot_path(corpus_dir, base_dir)
    target.mkdir(parents=True, exist_ok=True)

    documents = [
        {
            "id": document.id,
            "text": document.text,
        }
        for document in index.documents
    ]
    doc_stats = {
        doc_id: {
            "term_count": stats.term_count,
            "frequencies": dict(stats.frequencies),
        }
        for doc_id, stats in index.doc_stats.items()
    }
    postings = {term: sorted(doc_ids) for term, doc_ids in index.postings.items()}

    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "corpus_dir": str(corpus_dir),
        "average_document_length": index.average_document_length,
        "documents": documents,
        "doc_stats": doc_stats,
        "postings": postings,
    }
    (target / "index.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return target


def load_snapshot(corpus_dir: Path, base_dir: Path | None = None) -> SearchIndex | None:
    path = snapshot_path(corpus_dir, base_dir)
    index_file = path / "index.json"
    if not index_file.exists():
        return None

    from collections import Counter

    from .indexer import CorpusDocument, DocumentStats, SearchIndex

    payload = json.loads(index_file.read_text(encoding="utf-8"))
    documents = [
        CorpusDocument(id=item["id"], path=Path(item["id"]), text=item["text"])
        for item in payload["documents"]
    ]
    doc_stats = {
        doc_id: DocumentStats(
            document=next(doc for doc in documents if doc.id == doc_id),
            term_count=stats["term_count"],
            frequencies=Counter(stats["frequencies"]),
        )
        for doc_id, stats in payload["doc_stats"].items()
    }
    postings = {term: set(doc_ids) for term, doc_ids in payload["postings"].items()}
    return SearchIndex(
        documents=documents,
        postings=postings,
        doc_stats=doc_stats,
        average_document_length=float(payload["average_document_length"]),
    )


def build_or_load_index(corpus_dir: Path, base_dir: Path | None = None) -> SearchIndex:
    cached = load_snapshot(corpus_dir, base_dir)
    if cached is not None:
        return cached
    documents = load_corpus(corpus_dir)
    return build_index(documents)
