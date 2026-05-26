import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch


def _load_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "topic_error_candidates.py"
    spec = importlib.util.spec_from_file_location("topic_error_candidates", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules["topic_error_candidates"] = module
    spec.loader.exec_module(module)
    return module


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


class TopicErrorCandidateTests(TestCase):
    def test_recall_candidates_exclude_locked_eval_ids(self) -> None:
        topic = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline.jsonl"
            corpus = root / "corpus.jsonl"
            _write_jsonl(
                baseline,
                [
                    {"eval_id": "1", "standalone_query": "예외처리 런타임 오류", "topk": ["old-a"]},
                    {"eval_id": "2", "standalone_query": "헬륨 반응 낮은 이유", "topk": ["old-b"]},
                ],
            )
            _write_jsonl(
                corpus,
                [
                    {"docid": "old-a", "content": "반복 실험 재현성"},
                    {"docid": "new-a", "content": "예외처리 런타임 오류 입력 오류 처리 예외처리"},
                    {"docid": "old-b", "content": "헬륨 반응 낮은 이유"},
                    {"docid": "new-b", "content": "헬륨 비활성 기체 반응 낮은 이유"},
                ],
            )

            candidates = topic.generate_recall_candidates(
                baseline_path=baseline,
                corpus_path=corpus,
                locked_eval_ids={"2"},
                tier="test",
                candidate_pool=10,
                per_eval_candidates=2,
                max_baseline_relevance=0.4,
                min_candidate_relevance=0.4,
                min_delta=0.1,
                limit=10,
            )

        self.assertEqual([candidate.eval_id for candidate in candidates], ["1"])
        self.assertEqual(candidates[0].candidate_top1, "new-a")
        self.assertEqual(candidates[0].tier, "test")

    def test_balanced_preset_merges_tier_a_and_tier_b_candidates(self) -> None:
        topic = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline.jsonl"
            corpus = root / "corpus.jsonl"
            _write_jsonl(
                baseline,
                [
                    {"eval_id": "1", "standalone_query": "예외처리 런타임 오류 처리", "topk": ["old-a"]},
                    {"eval_id": "2", "standalone_query": "헬륨 비활성 기체 반응 낮은 이유", "topk": ["old-b"]},
                ],
            )
            _write_jsonl(
                corpus,
                [
                    {"docid": "old-a", "content": "반복 실험 재현성"},
                    {"docid": "new-a", "content": "예외처리 런타임 오류 입력 오류 처리"},
                    {"docid": "old-b", "content": "헬륨"},
                    {"docid": "new-b", "content": "헬륨 비활성 기체 반응 낮은 이유 최외각 전자껍질"},
                ],
            )

            candidates = topic.generate_preset_recall_candidates(
                baseline_path=baseline,
                corpus_path=corpus,
                locked_eval_ids=set(),
                preset="balanced",
                candidate_pool=10,
                per_eval_candidates=2,
                max_baseline_relevance=0.1,
                min_candidate_relevance=0.1,
                min_delta=0.1,
                recall_limit=10,
            )

        self.assertTrue({candidate.tier for candidate in candidates} <= {"tier_a", "tier_b"})
        self.assertIn("1", {candidate.eval_id for candidate in candidates})

    def test_recall_from_submission_dir_keeps_single_unlocked_top1_change(self) -> None:
        topic = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline.jsonl"
            corpus = root / "corpus.jsonl"
            candidate_dir = root / "candidates"
            candidate_dir.mkdir()
            _write_jsonl(
                baseline,
                [
                    {"eval_id": "1", "standalone_query": "예외처리 런타임 오류", "topk": ["old-a", "old-b"]},
                    {"eval_id": "2", "standalone_query": "잠긴 row", "topk": ["old-c"]},
                ],
            )
            _write_jsonl(
                corpus,
                [
                    {"docid": "old-a", "content": "반복 실험"},
                    {"docid": "old-b", "content": "기존 두번째"},
                    {"docid": "new-a", "content": "예외처리 런타임 오류 처리"},
                    {"docid": "old-c", "content": "잠긴 row"},
                    {"docid": "new-c", "content": "잠긴 row 후보"},
                ],
            )
            _write_jsonl(
                candidate_dir / "one.jsonl",
                [
                    {"eval_id": "1", "standalone_query": "예외처리 런타임 오류", "topk": ["new-a", "old-a"]},
                    {"eval_id": "2", "standalone_query": "잠긴 row", "topk": ["old-c"]},
                ],
            )
            _write_jsonl(
                candidate_dir / "locked.jsonl",
                [
                    {"eval_id": "1", "standalone_query": "예외처리 런타임 오류", "topk": ["old-a", "old-b"]},
                    {"eval_id": "2", "standalone_query": "잠긴 row", "topk": ["new-c", "old-c"]},
                ],
            )

            candidates = topic.recall_from_submission_dir(
                baseline_path=baseline,
                corpus_path=corpus,
                candidate_dir=candidate_dir,
                locked_eval_ids={"2"},
                tier="existing",
            )

        self.assertEqual([candidate.eval_id for candidate in candidates], ["1"])
        self.assertEqual(candidates[0].candidate_top1, "new-a")
        self.assertEqual(candidates[0].tier, "existing")

    def test_review_candidates_requires_topic_and_pairwise_candidate_wins(self) -> None:
        topic = _load_module()
        candidate = topic.RecallCandidate(
            eval_id="1",
            query="예외처리 런타임 오류",
            tier="test",
            baseline_top1="old-a",
            candidate_top1="new-a",
            baseline_relevance=0.1,
            candidate_relevance=0.8,
            relevance_delta=0.7,
            candidate_topk=["new-a", "old-a"],
        )

        with patch.object(topic, "judge_topic_error_candidate") as topic_judge, patch.object(
            topic, "judge_pairwise_candidate"
        ) as pairwise_judge:
            topic_judge.return_value = topic.Judgement(
                winner="candidate",
                docid="new-a",
                confidence=0.96,
                reason="baseline_failure=반복 실험; candidate_evidence=예외처리",
            )
            pairwise_judge.return_value = topic.Judgement(
                winner="baseline",
                docid="",
                confidence=0.98,
                reason="baseline evidence",
            )

            rejected = []
            accepted = topic.review_recall_candidates(
                candidates=[candidate],
                doc_texts={"old-a": "반복 실험", "new-a": "예외처리 런타임 오류"},
                provider="upstage",
                model="solar-pro3",
                host="https://api.upstage.ai/v1",
                api_key="secret-key",
                min_topic_confidence=0.93,
                min_pairwise_confidence=0.93,
                limit=1,
                rejected=rejected,
            )

        self.assertEqual(accepted, [])
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0].stage, "pairwise")
