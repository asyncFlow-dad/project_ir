from __future__ import annotations

import argparse
from pathlib import Path

from .indexer import build_index, load_corpus, search
from .rag import (
    DEFAULT_CANDIDATE_LIMIT,
    DEFAULT_CASUAL_POLICY,
    DEFAULT_DENSE_WEIGHT,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_FUSION_METHOD,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_RERANK_CANDIDATES,
    DEFAULT_RERANK_METHOD,
    DEFAULT_SEMANTIC_RERANK_WEIGHT,
    generate_submission,
)
from .snapshot import build_or_load_index, save_snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ir_search",
        description="Local Information Retrieval demo over Markdown and text files.",
    )
    subparsers = parser.add_subparsers(dest="command")

    index_parser = subparsers.add_parser("index", help="Build BM25 snapshot for a corpus")
    index_parser.add_argument(
        "--corpus",
        default="data/corpus",
        type=Path,
        help="Directory containing .md and .txt documents",
    )
    index_parser.add_argument(
        "--snapshot-dir",
        default="data/indexes",
        type=Path,
        help="Directory for on-disk index snapshots",
    )

    search_parser = subparsers.add_parser("search", help="Search the local corpus")
    search_parser.add_argument("query", nargs="+", help="Search query")
    search_parser.add_argument(
        "--corpus",
        default="data/corpus",
        type=Path,
        help="Directory containing .md and .txt documents",
    )
    search_parser.add_argument(
        "--snapshot-dir",
        default="data/indexes",
        type=Path,
        help="Directory for on-disk index snapshots",
    )
    search_parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Ignore cached snapshot and rebuild from corpus",
    )
    search_parser.add_argument("--limit", default=5, type=int, help="Maximum results")

    rag_parser = subparsers.add_parser(
        "rag-submit", help="Generate a RAG leaderboard submission"
    )
    rag_parser.add_argument("--corpus", default="data/documents.jsonl", type=Path)
    rag_parser.add_argument("--eval", default="data/eval.jsonl", type=Path)
    rag_parser.add_argument("--output", default="sample_submission.csv", type=Path)
    rag_parser.add_argument("--top-k", default=3, type=int)
    rag_parser.add_argument("--format", choices=("jsonl", "csv"), default="jsonl")
    rag_parser.add_argument("--openai", action="store_true")
    rag_parser.add_argument("--ollama", action="store_true")
    rag_parser.add_argument("--ollama-answers", action="store_true")
    rag_parser.add_argument("--ollama-rerank", action="store_true")
    rag_parser.add_argument("--ollama-rerank-candidates", default=10, type=int)
    rag_parser.add_argument("--model", default="gpt-4o-mini")
    rag_parser.add_argument("--ollama-model", default=DEFAULT_OLLAMA_MODEL)
    rag_parser.add_argument("--ollama-host", default=DEFAULT_OLLAMA_HOST)
    rag_parser.add_argument("--dense", action="store_true")
    rag_parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    rag_parser.add_argument("--embedding-cache-dir", default="data/indexes/rag_dense")
    rag_parser.add_argument("--embedding-query-prefix", default=None)
    rag_parser.add_argument("--embedding-document-prefix", default=None)
    rag_parser.add_argument("--candidate-limit", default=DEFAULT_CANDIDATE_LIMIT, type=int)
    rag_parser.add_argument("--dense-weight", default=DEFAULT_DENSE_WEIGHT, type=float)
    rag_parser.add_argument("--fusion-method", choices=("score", "rrf"), default=DEFAULT_FUSION_METHOD)
    rag_parser.add_argument(
        "--rerank-method",
        choices=("none", "semantic"),
        default=DEFAULT_RERANK_METHOD,
    )
    rag_parser.add_argument("--rerank-candidates", default=DEFAULT_RERANK_CANDIDATES, type=int)
    rag_parser.add_argument(
        "--semantic-rerank-weight",
        default=DEFAULT_SEMANTIC_RERANK_WEIGHT,
        type=float,
    )
    rag_parser.add_argument(
        "--casual-policy",
        choices=("strict", "balanced", "off"),
        default=DEFAULT_CASUAL_POLICY,
    )

    args = parser.parse_args(argv)
    if args.command == "index":
        documents = load_corpus(args.corpus)
        index = build_index(documents)
        target = save_snapshot(index, args.corpus, args.snapshot_dir)
        print(f"Indexed {len(documents)} documents -> {target}")
        return 0

    if args.command == "search":
        query = " ".join(args.query).strip()
        if args.rebuild:
            documents = load_corpus(args.corpus)
            index = build_index(documents)
        else:
            index = build_or_load_index(args.corpus, args.snapshot_dir)
        results = search(index, query, limit=args.limit)

        if not results:
            print(f'No results for "{query}".')
            return 0

        print(f'Results for "{query}"\n')
        for position, result in enumerate(results, start=1):
            print(f"{position}. {result.document.id}  score={result.score:.3f}")
            print(f"   {result.snippet}\n")
        return 0

    if args.command == "rag-submit":
        responses = generate_submission(
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
        print(f"Wrote {len(responses)} rows -> {args.output}")
        return 0

    parser.print_help()
    return 0
