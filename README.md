# IR Project

This is a small Python Information Retrieval project. It provides a local command-line search engine over Markdown/text documents using tokenization, an inverted index, and BM25 ranking.

## Run

```bash
python3 -m ir_search search "retrieval augmented generation"
```

The npm scripts are kept only as convenience wrappers:

```bash
bun run ir:sample
bun run test
```

## Project Shape

- `data/corpus/` - sample documents to index
- `ir_search/tokenize.py` - text normalization and tokenization
- `ir_search/indexer.py` - corpus loading, inverted index, BM25 search
- `ir_search/cli.py` - command-line interface
- `tests/test_indexer.py` - basic tests
- `pyproject.toml` - Python project metadata
- `scripts/run_openclaw.py` - OpenClaw command wrapper for this workspace

## Next Steps

1. Replace the sample corpus with real documents.
2. Add metadata extraction for title, source, date, and author.
3. Add chunking for long documents.
4. Add vector search with embeddings.
5. Add evaluation data and track precision, recall, MRR, and nDCG.
6. Add a small web UI or OpenClaw agent workflow on top of the retriever.
