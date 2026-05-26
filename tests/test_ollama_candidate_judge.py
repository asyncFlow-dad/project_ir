import importlib.util
import os
import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch


def _load_judge_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "ollama_candidate_judge.py"
    spec = importlib.util.spec_from_file_location("ollama_candidate_judge", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules["ollama_candidate_judge"] = module
    spec.loader.exec_module(module)
    return module


class OllamaCandidateJudgeTests(TestCase):
    def test_parse_judgement_accepts_candidate_winner(self) -> None:
        judge = _load_judge_module()
        parsed = judge.parse_judgement(
            '{"winner":"candidate","docid":"new-doc","confidence":0.82,"reason":"direct"}'
        )

        self.assertEqual(parsed.winner, "candidate")
        self.assertEqual(parsed.docid, "new-doc")
        self.assertEqual(parsed.confidence, 0.82)

    def test_parse_judgement_rejects_unknown_winner(self) -> None:
        judge = _load_judge_module()

        with self.assertRaises(ValueError):
            judge.parse_judgement('{"winner":"maybe","docid":"new-doc"}')

    def test_try_parse_judgement_returns_none_for_non_json(self) -> None:
        judge = _load_judge_module()

        parsed = judge.try_parse_judgement("")

        self.assertIsNone(parsed)

    def test_promoted_topk_deduplicates_candidate_and_baseline(self) -> None:
        judge = _load_judge_module()

        topk = judge.promoted_topk(["old-a", "new-a", "old-b"], "new-a")

        self.assertEqual(topk, ["new-a", "old-a", "old-b"])

    def test_upstage_api_key_prefers_secret_key(self) -> None:
        judge = _load_judge_module()

        with patch.dict(
            os.environ,
            {"UPSTAGE_API_SECRET_KEY": "secret-key", "UPSTAGE_API_KEY": "public-key"},
            clear=False,
        ):
            self.assertEqual(judge._upstage_api_key(), "secret-key")

    def test_chat_dispatches_to_upstage_provider(self) -> None:
        judge = _load_judge_module()

        with patch.object(judge, "_upstage_chat", return_value='{"winner":"tie"}') as upstage_chat:
            content = judge._chat(
                provider="upstage",
                host="https://api.upstage.ai/v1",
                model="solar-pro3",
                prompt="judge",
                api_key="secret-key",
            )

        self.assertEqual(content, '{"winner":"tie"}')
        upstage_chat.assert_called_once_with(
            base_url="https://api.upstage.ai/v1",
            model="solar-pro3",
            prompt="judge",
            api_key="secret-key",
        )

    def test_strict_reason_filter_rejects_topic_mismatch_language(self) -> None:
        judge = _load_judge_module()

        self.assertTrue(
            judge.is_rejected_reason(
                "query와 직접적인 관련이 없지만 baseline이 무관한 내용이므로 candidate 중 가장 관련성이 높은 문서를 선택"
            )
        )
        self.assertTrue(judge.is_rejected_reason("시나리오 드리프트가 명확합니다."))

    def test_judge_candidates_filters_rejected_reason(self) -> None:
        judge = _load_judge_module()
        payload = (
            '{"winner":"candidate","docid":"new-doc","confidence":0.95,'
            '"reason":"query와 직접적인 관련이 없지만 candidate 중 가장 관련성이 높은 문서"}'
        )

        with patch.object(judge, "_chat", return_value=payload):
            parsed = judge.judge_candidates(
                query="공교육 지출 현황",
                baseline_docid="old-doc",
                baseline_text="baseline",
                candidate_docids=["new-doc"],
                doc_texts={"new-doc": "우량계 강수량 데이터"},
                model="solar-pro3",
                host="https://api.upstage.ai/v1",
                provider="upstage",
                api_key="secret-key",
            )

        self.assertIsNone(parsed)

    def test_pairwise_judge_prefers_baseline_when_baseline_already_answers(self) -> None:
        judge = _load_judge_module()
        payload = '{"winner":"baseline","docid":"","confidence":0.99,"reason":"baseline exact evidence"}'

        with patch.object(judge, "_chat", return_value=payload) as chat:
            parsed = judge.judge_pairwise_candidate(
                query="전류 흐름 극대화",
                baseline_docid="old-doc",
                baseline_text="고전압 배터리와 저항기를 직렬로 연결하면 가장 큰 전류를 만들 수 있다.",
                candidate_docid="new-doc",
                candidate_text="전기 저항은 전압과 전류의 비율이다.",
                model="solar-pro3",
                host="https://api.upstage.ai/v1",
                provider="upstage",
                api_key="secret-key",
            )

        self.assertEqual(parsed.winner, "baseline")
        self.assertIn("quote exact Korean evidence", chat.call_args.kwargs["prompt"])

    def test_topic_error_judge_requires_baseline_wrong_and_candidate_evidence(self) -> None:
        judge = _load_judge_module()
        payload = (
            '{"winner":"candidate","docid":"new-doc","confidence":0.97,'
            '"reason":"baseline_failure=반복 실험; candidate_evidence=예외 처리"}'
        )

        with patch.object(judge, "_chat", return_value=payload) as chat:
            parsed = judge.judge_topic_error_candidate(
                query="예외처리 필요한 경우",
                baseline_docid="old-doc",
                baseline_text="반복 실험은 재현성을 높인다.",
                candidate_docid="new-doc",
                candidate_text="N=0 런타임 오류는 예외 처리로 다룬다.",
                model="solar-pro3",
                host="https://api.upstage.ai/v1",
                provider="upstage",
                api_key="secret-key",
            )

        self.assertEqual(parsed.winner, "candidate")
        self.assertIn("baseline must be wrong", chat.call_args.kwargs["prompt"])
        self.assertIn("candidate must directly answer", chat.call_args.kwargs["prompt"])

    def test_topic_error_judge_treats_malformed_response_as_baseline(self) -> None:
        judge = _load_judge_module()

        with patch.object(judge, "_chat", return_value='{"winner":"candidate"'):
            parsed = judge.judge_topic_error_candidate(
                query="예외처리 필요한 경우",
                baseline_docid="old-doc",
                baseline_text="반복 실험은 재현성을 높인다.",
                candidate_docid="new-doc",
                candidate_text="N=0 런타임 오류는 예외 처리로 다룬다.",
                model="solar-pro3",
                host="https://api.upstage.ai/v1",
                provider="upstage",
                api_key="secret-key",
            )

        self.assertEqual(parsed.winner, "baseline")
