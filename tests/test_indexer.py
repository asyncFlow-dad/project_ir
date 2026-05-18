from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ir_search import build_index, load_corpus, search, tokenize
from ir_search.indexer import CorpusDocument


class TokenizeTests(TestCase):
    def test_tokenize_normalizes_english_and_korean_text(self) -> None:
        self.assertEqual(
            tokenize("Retrieval, RETRIEVAL! 검색 시스템은 빠르게."),
            ["retrieval", "retrieval", "검색", "시스템은", "빠르게"],
        )


class SearchTests(TestCase):
    def test_search_ranks_matching_documents_with_bm25(self) -> None:
        index = build_index(
            [
                CorpusDocument(
                    id="rag.md",
                    path=Path("rag.md"),
                    text="Retrieval augmented generation uses retrieved evidence before generation.",
                ),
                CorpusDocument(
                    id="metrics.md",
                    path=Path("metrics.md"),
                    text="Precision and recall evaluate ranking quality.",
                ),
            ]
        )

        results = search(index, "retrieval generation")

        self.assertEqual(results[0].document.id, "rag.md")
        self.assertGreater(results[0].score, 0)

    def test_load_corpus_reads_markdown_and_text_recursively(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.md").write_text("alpha", encoding="utf-8")
            (root / "nested").mkdir()
            (root / "nested" / "b.txt").write_text("beta", encoding="utf-8")
            (root / "ignored.json").write_text("{}", encoding="utf-8")

            documents = load_corpus(root)

        self.assertEqual([document.id for document in documents], ["a.md", "nested/b.txt"])
