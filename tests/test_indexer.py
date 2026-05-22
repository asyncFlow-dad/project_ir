from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ir_search import build_index, load_corpus, search, tokenize
from ir_search.indexer import CorpusDocument
from ir_search.tokenize import normalize_query


class TokenizeTests(TestCase):
    def test_tokenize_normalizes_english_and_korean_text(self) -> None:
        self.assertEqual(
            tokenize("Retrieval, RETRIEVAL! 검색 시스템은 빠르게."),
            ["retrieval", "retrieval", "검색", "시스템은", "시스템", "빠르게"],
        )

    def test_tokenize_splits_english_name_with_korean_particle(self) -> None:
        self.assertEqual(
            tokenize("Dmitri Ivanovsky가 누구야?"),
            ["dmitri", "ivanovsky가", "ivanovsky", "누구야"],
        )

    def test_tokenize_splits_numbers_and_units(self) -> None:
        self.assertEqual(
            tokenize("10,000헥타르 km^2 제곱킬로미터"),
            ["10000", "헥타르", "hectare", "km2", "제곱킬로미터", "km2"],
        )

    def test_normalize_query_removes_filler(self) -> None:
        self.assertEqual(
            normalize_query("나무의 분류에 대해 조사해 보기 위한 방법은?"),
            "나무 분류 방법",
        )

    def test_normalize_query_rewrites_cultivation_phrase(self) -> None:
        self.assertEqual(normalize_query("복숭아 키우는 노하우좀"), "복숭아 재배 방법")

    def test_normalize_query_keeps_single_syllable_adjectives(self) -> None:
        self.assertEqual(normalize_query("작은 기체 하나의 질량"), "작은 기체 하나 질량")
        self.assertEqual(normalize_query("같은 독감 다시 걸리는 이유"), "같은 독감 다시 걸리 이유")

    def test_normalize_query_rewrites_common_eval_typos(self) -> None:
        self.assertEqual(normalize_query("DNA 결합 과정에 대히 설명해줘."), "dna 결합 과정")
        self.assertEqual(normalize_query("세균이 나쁜줄말 알았는데"), "세균 나쁜줄 알았는데")
        self.assertEqual(normalize_query("초코렛이 녹는 원리"), "초콜릿 녹 원리")
        self.assertEqual(normalize_query("디엔에이 리가아제의 기능"), "dna 리가아제 기능")

    def test_normalize_query_rewrites_science_aliases(self) -> None:
        self.assertEqual(normalize_query("아세틸 콜린의 역할"), "아세틸콜린 역할")
        self.assertEqual(
            normalize_query("슈퍼옥시드 디스무타아제 라는 효소"),
            "superoxide dismutase 라 효소",
        )
        self.assertEqual(normalize_query("퓨린과 피리미딘 비율"), "푸린 피리미딘 비율")
        self.assertEqual(normalize_query("목성 trojan의 특징"), "목성 트로이군 특징")
        self.assertEqual(normalize_query("리보오솜의 역할"), "리보솜 역할")
        self.assertEqual(normalize_query("interferon의 역할"), "인터페론 역할")


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
