# IR Project

This project is a retrieval-focused RAG leaderboard pipeline. The competition is not centered on training a new machine learning model. It evaluates how well the system retrieves useful references with search, embeddings, reranking, and LLMs, then generates an answer grounded in those references.

The current pipeline combines lexical retrieval, dense embedding retrieval, semantic reranking, optional Ollama/OpenAI answer generation, and submission validation. The main output is JSONL rows containing `eval_id`, `standalone_query`, `topk`, `answer`, and `references`.

## Run

Local search over the sample corpus:

```bash
python3 -m ir_search search "retrieval augmented generation"
```

Generate a leaderboard-style JSONL submission:

```bash
python3 -m ir_search rag-submit \
  --corpus data/documents.jsonl \
  --eval data/eval.jsonl \
  --output submissions/submission.jsonl \
  --dense \
  --rerank-method semantic
```

Use Ollama as an LLM reranker when a local model server is available:

```bash
python3 -m ir_search rag-submit \
  --corpus data/documents.jsonl \
  --eval data/eval.jsonl \
  --output submissions/ollama_rerank.jsonl \
  --dense \
  --ollama \
  --ollama-rerank \
  --ollama-model granite4.1:8b
```

The npm scripts are kept only as convenience wrappers:

```bash
bun run ir:sample
bun run test
```

## Project Shape

- `data/documents.jsonl` - competition corpus documents
- `data/eval.jsonl` - evaluation conversations/questions
- `data/corpus/` - small sample documents for local search demos
- `ir_search/tokenize.py` - text normalization and tokenization
- `ir_search/indexer.py` - corpus loading, inverted index, BM25 retrieval
- `ir_search/rag.py` - RAG submission generation, dense retrieval, reranking, and answer generation
- `ir_search/cli.py` - command-line interface for search and submission generation
- `scripts/validate_submission.py` - JSONL submission shape and diff validation
- `scripts/submission_diff_report.py` - changed-row and top-1 change reporting
- `scripts/submission_doc_audit.py` - query/top-1 document audit with relevance scoring
- `scripts/submission_patch_candidates.py` - consensus top-1 changes across multiple rerank submissions
- `submissions/` - generated candidates, experiment records, and leaderboard notes
- `tests/` - regression tests for retrieval, submission tooling, and schema behavior
- `pyproject.toml` - Python project metadata

## Competition Strategy

1. Build candidate references with BM25, dense embeddings, or hybrid retrieval.
2. Rerank candidates with semantic similarity or an LLM such as Granite through Ollama.
3. Generate concise answers grounded only in retrieved references.
4. Validate JSONL format, empty `topk`, duplicate `topk`, and diff size before upload.
5. Compare multiple rerank outputs for consensus top-1 changes before patching.
6. Audit changed top-1 rows against source documents and relevance scores before spending leaderboard submissions.
