from __future__ import annotations

import argparse
from pathlib import Path

from .indexer import build_index, load_corpus, search
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

    parser.print_help()
    return 0
