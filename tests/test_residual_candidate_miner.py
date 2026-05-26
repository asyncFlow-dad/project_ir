from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch


def _load_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "residual_candidate_miner.py"
    spec = importlib.util.spec_from_file_location("residual_candidate_miner", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules["residual_candidate_miner"] = module
    spec.loader.exec_module(module)
    return module


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


class ResidualCandidateMinerTests(TestCase):
    def test_collect_candidates_excludes_public_results_and_scores_support_and_rank_bonus(self) -> None:
        miner = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline.jsonl"
            public_results = root / "public.json"
            source_dir = root / "source"
            source_dir.mkdir()
            _write_jsonl(
                baseline,
                [
                    {"eval_id": "1", "standalone_query": "재생 가능 재료", "topk": ["old-a", "new-a", "old-c"]},
                    {"eval_id": "2", "standalone_query": "잠긴 row", "topk": ["old-b", "new-b"]},
                ],
            )
            public_results.write_text(
                json.dumps([{"eval_id": "2", "outcome": "regressed"}], ensure_ascii=False),
                encoding="utf-8",
            )
            _write_jsonl(
                source_dir / "one.jsonl",
                [
                    {"eval_id": "1", "standalone_query": "재생 가능 재료", "topk": ["new-a", "old-a"]},
                    {"eval_id": "2", "standalone_query": "잠긴 row", "topk": ["new-b", "old-b"]},
                ],
            )
            _write_jsonl(
                source_dir / "two.jsonl",
                [
                    {"eval_id": "1", "standalone_query": "재생 가능 재료", "topk": ["new-a", "old-c"]},
                    {"eval_id": "2", "standalone_query": "잠긴 row", "topk": ["new-b", "old-b"]},
                ],
            )

            candidates = miner.collect_residual_candidates(
                baseline_path=baseline,
                public_results_path=public_results,
                source_paths=[source_dir],
            )

        self.assertEqual([candidate.eval_id for candidate in candidates], ["1"])
        self.assertEqual(candidates[0].candidate_top1, "new-a")
        self.assertEqual(candidates[0].support, 2)
        self.assertEqual(candidates[0].baseline_rank, 2)
        self.assertEqual(miner.base_score(candidates[0]), 5)

    def test_apply_judgement_penalizes_baseline_winner_and_rewards_direct_candidate(self) -> None:
        miner = _load_module()
        candidate = miner.ResidualCandidate(
            eval_id="1",
            query="재생 가능 재료",
            baseline_top1="old-a",
            candidate_top1="new-a",
            candidate_topk=["new-a", "old-a"],
            support=2,
            sources=["one.jsonl", "two.jsonl"],
            baseline_rank=2,
        )

        baseline_review = miner.score_with_judgement(
            candidate,
            miner.Judgement(
                winner="baseline",
                docid="old-a",
                confidence=0.95,
                reason="baseline direct",
                baseline_is_wrong=False,
                candidate_direct_answer=False,
                candidate_offtopic=False,
                submit_risk="low",
            ),
        )
        candidate_review = miner.score_with_judgement(
            candidate,
            miner.Judgement(
                winner="candidate",
                docid="new-a",
                confidence=0.9,
                reason="candidate direct",
                baseline_is_wrong=True,
                candidate_direct_answer=True,
                candidate_offtopic=False,
                submit_risk="medium",
            ),
        )

        self.assertEqual(baseline_review.score, 1)
        self.assertFalse(baseline_review.accepted)
        self.assertEqual(candidate_review.score, 9)
        self.assertTrue(candidate_review.accepted)

    def test_apply_judgement_requires_clear_baseline_weakness_for_acceptance(self) -> None:
        miner = _load_module()
        candidate = miner.ResidualCandidate(
            eval_id="7",
            query="자성 띄지 않 유전체 내부 빛 속도 어떻게 되나",
            baseline_top1="old-a",
            candidate_top1="new-a",
            candidate_topk=["new-a", "old-a"],
            support=30,
            sources=["one.jsonl", "two.jsonl"],
            baseline_rank=2,
        )

        review = miner.score_with_judgement(
            candidate,
            miner.Judgement(
                winner="candidate",
                docid="new-a",
                confidence=0.95,
                reason="candidate slightly more detailed",
                baseline_is_wrong=False,
                candidate_direct_answer=True,
                candidate_offtopic=False,
                submit_risk="low",
            ),
        )

        self.assertEqual(review.score, 7)
        self.assertFalse(review.accepted)

    def test_write_single_row_candidate_updates_only_selected_eval(self) -> None:
        miner = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline.jsonl"
            output_dir = root / "out"
            _write_jsonl(
                baseline,
                [
                    {"eval_id": "1", "standalone_query": "재생 가능 재료", "topk": ["old-a", "new-a", "old-c"]},
                    {"eval_id": "2", "standalone_query": "유지", "topk": ["old-b"]},
                ],
            )
            review = miner.ResidualReview(
                candidate=miner.ResidualCandidate(
                    eval_id="1",
                    query="재생 가능 재료",
                    baseline_top1="old-a",
                    candidate_top1="new-a",
                    candidate_topk=["new-a", "old-a", "old-c"],
                    support=2,
                    sources=["one.jsonl", "two.jsonl"],
                    baseline_rank=2,
                ),
                score=9,
                accepted=True,
                reason="candidate direct",
            )

            written = miner.write_single_row_outputs(
                baseline_path=baseline,
                reviews=[review],
                output_dir=output_dir,
                name_prefix="residual_eval246_base",
                limit=1,
            )

            rows = [json.loads(line) for line in written[0].read_text(encoding="utf-8").splitlines()]

        self.assertEqual(written[0].name, "residual_eval246_base_eval1.jsonl")
        self.assertEqual(rows[0]["topk"], ["new-a", "old-a", "old-c"])
        self.assertEqual(rows[1]["topk"], ["old-b"])

    def test_review_candidates_rejects_candidate_that_loses_to_current_rank2(self) -> None:
        miner = _load_module()
        candidate = miner.ResidualCandidate(
            eval_id="252",
            query="해구 생겨나 원리",
            baseline_top1="old-a",
            candidate_top1="new-a",
            candidate_topk=["new-a", "old-a", "rank2-a"],
            support=30,
            sources=["one.jsonl", "two.jsonl"],
            baseline_rank=3,
            baseline_topk=["old-a", "rank2-a", "new-a"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "corpus.jsonl"
            _write_jsonl(
                corpus,
                [
                    {"docid": "old-a", "content": "해저 생태계"},
                    {"docid": "rank2-a", "content": "해구는 섭입대에서 형성됩니다"},
                    {"docid": "new-a", "content": "해구는 발산이 아닙니다"},
                ],
            )
            with patch.object(miner, "judge_direct_answer_candidate") as direct_judge, patch.object(
                miner, "judge_pairwise_candidate"
            ) as pairwise_judge:
                direct_judge.return_value = miner.Judgement(
                    winner="candidate",
                    docid="new-a",
                    confidence=0.9,
                    reason="candidate beats top1",
                    baseline_is_wrong=True,
                    candidate_direct_answer=True,
                    candidate_offtopic=False,
                    submit_risk="low",
                )
                pairwise_judge.return_value = miner.Judgement(
                    winner="baseline",
                    docid="rank2-a",
                    confidence=0.95,
                    reason="rank2 better explains formation",
                )

                reviews = miner.review_candidates(
                    candidates=[candidate],
                    corpus_path=corpus,
                    provider="upstage",
                    model="solar-pro3",
                    host="https://api.upstage.ai/v1",
                    api_key="secret-key",
                    accept_threshold=7,
                    limit=1,
                    require_topk_guard=True,
                )

        self.assertEqual(len(reviews), 1)
        self.assertFalse(reviews[0].accepted)
        self.assertIn("topk_guard_failed", reviews[0].reason)

    def test_highrisk_candidates_keep_supported_rank2_and_rank3_promotions(self) -> None:
        miner = _load_module()
        candidates = [
            miner.ResidualCandidate("1", "정량 계산", "old-a", "rank2-a", ["rank2-a", "old-a"], 12, [], 2),
            miner.ResidualCandidate("2", "절차", "old-b", "rank3-b", ["rank3-b", "old-b"], 11, [], 3),
            miner.ResidualCandidate("3", "낮은 지지", "old-c", "rank2-c", ["rank2-c", "old-c"], 9, [], 2),
            miner.ResidualCandidate("4", "topk 밖", "old-d", "new-d", ["new-d", "old-d"], 20, [], None),
        ]

        selected = miner.select_highrisk_rank_promotions(candidates, min_support=10, limit=10)

        self.assertEqual([candidate.eval_id for candidate in selected], ["1", "2"])

    def test_highrisk_review_allows_candidate_direct_answer_without_baseline_wrong(self) -> None:
        miner = _load_module()
        candidate = miner.ResidualCandidate(
            "309",
            "특정 농도 황산 sample 만드 방법",
            "old-a",
            "new-a",
            ["new-a", "old-a"],
            30,
            [],
            3,
        )

        review = miner.score_highrisk_judgement(
            candidate,
            miner.Judgement(
                winner="candidate",
                docid="new-a",
                confidence=0.95,
                reason="candidate gives exact concentration procedure",
                baseline_is_wrong=False,
                candidate_direct_answer=True,
                candidate_offtopic=False,
                submit_risk="low",
            ),
        )

        self.assertTrue(review.accepted)
        self.assertGreaterEqual(review.score, 7)

    def test_answer_span_review_rejects_when_baseline_has_required_facts(self) -> None:
        miner = _load_module()
        candidate = miner.ResidualCandidate(
            "207",
            "곤충 눈 구조",
            "old-a",
            "new-a",
            ["new-a", "old-a"],
            19,
            [],
            2,
            baseline_topk=["old-a", "new-a", "rank3-a"],
        )

        review = miner.score_answer_span_judgement(
            candidate,
            miner.AnswerSpanJudgement(
                required_answer_facts=["compound eyes", "many small visual units"],
                baseline_missing_facts=[],
                candidate_covered_facts=["compound eyes", "many small visual units"],
                winner="candidate",
                docid="new-a",
                confidence=0.91,
                submit_risk="low",
                reason="baseline already contains compound-eye facts",
            ),
            topk_guard_pass=True,
            topk_guard_reason="candidate_beats_current_topk",
        )

        self.assertFalse(review.accepted)
        self.assertIn("baseline_has_key_span", review.reason)

    def test_answer_span_review_accepts_missing_baseline_and_candidate_beats_topk(self) -> None:
        miner = _load_module()
        candidate = miner.ResidualCandidate(
            "310",
            "특정 농도 황산 sample 만드 방법",
            "old-a",
            "new-a",
            ["new-a", "old-a", "rank2-a"],
            24,
            [],
            3,
            baseline_topk=["old-a", "rank2-a", "new-a"],
        )

        review = miner.score_answer_span_judgement(
            candidate,
            miner.AnswerSpanJudgement(
                required_answer_facts=["dilution calculation", "add acid to water"],
                baseline_missing_facts=["dilution calculation"],
                candidate_covered_facts=["dilution calculation", "add acid to water"],
                winner="candidate",
                docid="new-a",
                confidence=0.94,
                submit_risk="low",
                reason="candidate gives concentration procedure",
            ),
            topk_guard_pass=True,
            topk_guard_reason="candidate_beats_current_topk",
        )

        self.assertTrue(review.accepted)
        self.assertIn("baseline_missing_facts=1", review.reason)
        self.assertIn("candidate_covered_facts=2", review.reason)

    def test_answer_span_review_rejects_when_candidate_loses_topk_guard(self) -> None:
        miner = _load_module()
        candidate = miner.ResidualCandidate(
            "311",
            "해구 생겨나 원리",
            "old-a",
            "new-a",
            ["new-a", "old-a", "rank2-a"],
            30,
            [],
            3,
            baseline_topk=["old-a", "rank2-a", "new-a"],
        )

        review = miner.score_answer_span_judgement(
            candidate,
            miner.AnswerSpanJudgement(
                required_answer_facts=["subduction"],
                baseline_missing_facts=["subduction"],
                candidate_covered_facts=["subduction"],
                winner="candidate",
                docid="new-a",
                confidence=0.9,
                submit_risk="low",
                reason="candidate mentions subduction",
            ),
            topk_guard_pass=False,
            topk_guard_reason="lost_to=rank2-a",
        )

        self.assertFalse(review.accepted)
        self.assertIn("topk_guard_failed=lost_to=rank2-a", review.reason)
