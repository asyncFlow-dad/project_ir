import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ir_search.rag import (
    DenseIndex,
    _base_doc_id,
    _embedding_prefixes,
    _hybrid_retrieve,
    _merge_candidate_scores_rrf,
    _semantic_rerank_results,
    generate_submission,
    load_eval,
    should_retrieve,
    standalone_query,
)
from ir_search.indexer import CorpusDocument, build_index


class RagSubmissionTests(TestCase):
    def test_generate_submission_reads_jsonl_and_writes_ranked_output(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            documents = root / "documents.jsonl"
            eval_file = root / "eval.jsonl"
            output = root / "submission.jsonl"
            documents.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "docid": "rag-doc",
                                "title": "RAG",
                                "content": "Retrieval augmented generation uses evidence.",
                            }
                        ),
                        json.dumps(
                            {
                                "docid": "metrics-doc",
                                "content": "Precision and recall evaluate retrieval.",
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )
            eval_file.write_text(
                json.dumps(
                    {
                        "eval_id": "e1",
                        "msg": [{"role": "user", "content": "retrieval generation"}],
                    }
                ),
                encoding="utf-8",
            )

            responses = generate_submission(
                corpus_path=documents,
                eval_path=eval_file,
                output_path=output,
                top_k=1,
            )
            line_count = output.read_text(encoding="utf-8").count("\n")

        self.assertEqual(responses[0].topk, ["rag-doc"])
        self.assertEqual(line_count, 1)

    def test_csv_format_uses_leaderboard_jsonl_shape(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            documents = root / "documents.jsonl"
            eval_file = root / "eval.jsonl"
            output = root / "submission.csv"
            documents.write_text(
                json.dumps(
                    {
                        "docid": "rag-doc",
                        "content": "Retrieval augmented generation uses evidence.",
                    }
                ),
                encoding="utf-8",
            )
            eval_file.write_text(
                json.dumps(
                    {
                        "eval_id": "e1",
                        "msg": [{"role": "user", "content": "retrieval generation"}],
                    }
                ),
                encoding="utf-8",
            )

            generate_submission(
                corpus_path=documents,
                eval_path=eval_file,
                output_path=output,
                top_k=1,
                output_format="csv",
            )
            first_row = json.loads(output.read_text(encoding="utf-8").splitlines()[0])

        self.assertEqual(first_row["eval_id"], "e1")
        self.assertEqual(first_row["topk"], ["rag-doc"])

    def test_load_eval_accepts_query_shape(self) -> None:
        with TemporaryDirectory() as tmp:
            eval_file = Path(tmp) / "queries.jsonl"
            eval_file.write_text(
                json.dumps({"query_id": "q1", "query": "precision recall"}),
                encoding="utf-8",
            )

            examples = load_eval(eval_file)

        self.assertEqual(examples[0].eval_id, "q1")
        self.assertEqual(standalone_query(examples[0].messages), "precision recall")

    def test_load_eval_preserves_numeric_eval_id_type(self) -> None:
        with TemporaryDirectory() as tmp:
            eval_file = Path(tmp) / "eval.jsonl"
            eval_file.write_text(
                json.dumps({"eval_id": 78, "msg": [{"role": "user", "content": "질문"}]}),
                encoding="utf-8",
            )

            examples = load_eval(eval_file)

        self.assertEqual(examples[0].eval_id, 78)

    def test_standalone_query_keeps_multiturn_context_for_followup(self) -> None:
        messages = [
            {"role": "user", "content": "기억 상실증 걸리면 너무 무섭겠다."},
            {"role": "assistant", "content": "네 맞습니다."},
            {"role": "user", "content": "어떤 원인 때문에 발생하는지 궁금해."},
        ]

        self.assertIn("기억 상실증", standalone_query(messages))

    def test_should_retrieve_skips_casual_chat(self) -> None:
        messages = [{"role": "user", "content": "요새 너무 힘들다."}]

        self.assertFalse(should_retrieve(messages, standalone_query(messages)))

    def test_should_retrieve_skips_praise_without_science_question(self) -> None:
        messages = [{"role": "user", "content": "니 대답 잘해줘서 너무 신나"}]

        self.assertFalse(should_retrieve(messages, standalone_query(messages)))

    def test_should_retrieve_skips_tired_casual_variant(self) -> None:
        messages = [{"role": "user", "content": "요새 너무 힘드네"}]

        self.assertFalse(should_retrieve(messages, standalone_query(messages)))

    def test_should_retrieve_keeps_english_named_entity_question(self) -> None:
        messages = [{"role": "user", "content": "Dmitri Ivanovsky가 누구야?"}]

        self.assertTrue(should_retrieve(messages, standalone_query(messages)))

    def test_should_retrieve_keeps_energy_question_containing_neo(self) -> None:
        messages = [{"role": "user", "content": "석탄을 에너지원으로 사용할 때 장단점이 뭐야?"}]

        self.assertTrue(should_retrieve(messages, standalone_query(messages)))

    def test_dense_mode_falls_back_when_optional_dependency_missing(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            documents = root / "documents.jsonl"
            eval_file = root / "eval.jsonl"
            output = root / "submission.csv"
            documents.write_text(
                json.dumps(
                    {
                        "docid": "ivanovsky-doc",
                        "content": "Dmitri Ivanovsky discovered a virus-related phenomenon.",
                    }
                ),
                encoding="utf-8",
            )
            eval_file.write_text(
                json.dumps(
                    {
                        "eval_id": "e1",
                        "msg": [{"role": "user", "content": "Dmitri Ivanovsky가 누구야?"}],
                    }
                ),
                encoding="utf-8",
            )

            responses = generate_submission(
                corpus_path=documents,
                eval_path=eval_file,
                output_path=output,
                top_k=1,
                use_dense=True,
                embedding_model="missing-test-model",
                embedding_cache_dir=root / "dense-cache",
            )

        self.assertEqual(responses[0].topk, ["ivanovsky-doc"])

    def test_e5_embedding_model_uses_required_prefixes(self) -> None:
        self.assertEqual(
            _embedding_prefixes(
                "intfloat/multilingual-e5-large",
                query_prefix=None,
                document_prefix=None,
            ),
            ("query: ", "passage: "),
        )

    def test_embedding_prefixes_can_be_overridden(self) -> None:
        self.assertEqual(
            _embedding_prefixes(
                "intfloat/multilingual-e5-large",
                query_prefix="q: ",
                document_prefix="d: ",
            ),
            ("q: ", "d: "),
        )

    def test_hybrid_retrieve_returns_unique_base_documents(self) -> None:
        documents = [
            CorpusDocument(
                id="same-doc#chunk-0",
                path=Path("same-doc"),
                text="alpha beta gamma direct answer",
            ),
            CorpusDocument(
                id="same-doc#chunk-1",
                path=Path("same-doc"),
                text="alpha beta gamma repeated answer",
            ),
            CorpusDocument(
                id="other-doc",
                path=Path("other-doc"),
                text="alpha beta supporting answer",
            ),
        ]
        index = build_index(documents)

        results = _hybrid_retrieve(index, "alpha beta answer", limit=3)
        base_ids = [_base_doc_id(result.document.id) for result in results]

        self.assertEqual(len(base_ids), len(set(base_ids)))

    def test_rrf_fusion_can_rank_dense_and_sparse_candidates(self) -> None:
        lexical_doc = CorpusDocument(id="lex", path=Path("lex"), text="lexical")
        dense_doc = CorpusDocument(id="dense", path=Path("dense"), text="dense")

        merged = _merge_candidate_scores_rrf(
            {"lex": (10.0, lexical_doc)},
            {"dense": (0.9, dense_doc), "lex": (0.8, lexical_doc)},
            dense_weight=0.55,
        )

        self.assertEqual(merged[0][1], "lex")

    def test_semantic_rerank_can_promote_dense_match(self) -> None:
        try:
            import numpy as np
        except Exception:
            self.skipTest("numpy not installed")

        class FakeModel:
            def encode(self, texts, **_kwargs):
                return np.asarray([[1.0, 0.0]])

        off_topic = CorpusDocument(id="off", path=Path("off"), text="off topic")
        direct = CorpusDocument(id="direct", path=Path("direct"), text="alpha answer")
        dense_index = DenseIndex(
            doc_ids=["off", "direct"],
            documents={"off": off_topic, "direct": direct},
            embeddings=np.asarray([[0.0, 1.0], [1.0, 0.0]]),
            model=FakeModel(),
            query_prefix="query: ",
        )

        reranked = _semantic_rerank_results(
            "alpha",
            [
                # Original retrieval prefers off-topic result; semantic rerank should fix it.
                type("Result", (), {"document": off_topic, "score": 10.0})(),
                type("Result", (), {"document": direct, "score": 1.0})(),
            ],
            dense_index=dense_index,
            limit=1,
            semantic_weight=1.0,
        )

        self.assertEqual(reranked[0].document.id, "direct")

    def test_balanced_casual_policy_keeps_affective_content_request(self) -> None:
        messages = [{"role": "user", "content": "우울한데 신나는 얘기 좀 해줘!"}]
        query = standalone_query(messages)

        self.assertFalse(should_retrieve(messages, query))
        self.assertTrue(should_retrieve(messages, query, casual_policy="balanced"))
