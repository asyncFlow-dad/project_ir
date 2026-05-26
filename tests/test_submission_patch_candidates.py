import importlib.util
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase


def _load_candidates_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "submission_patch_candidates.py"
    spec = importlib.util.spec_from_file_location("submission_patch_candidates", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules["submission_patch_candidates"] = module
    spec.loader.exec_module(module)
    return module


class SubmissionPatchCandidatesTests(TestCase):
    def test_find_consensus_changes_requires_multiple_sources(self) -> None:
        candidates = _load_candidates_module()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline.jsonl"
            source_a = root / "source-a.jsonl"
            source_b = root / "source-b.jsonl"
            source_c = root / "source-c.jsonl"
            _write_jsonl(
                baseline,
                [
                    _row("1", ["old-a"]),
                    _row("2", ["old-b"]),
                    _row("3", ["old-c"]),
                ],
            )
            _write_jsonl(
                source_a,
                [
                    _row("1", ["new-a"]),
                    _row("2", ["new-b"]),
                    _row("3", ["solo-c"]),
                ],
            )
            _write_jsonl(
                source_b,
                [
                    _row("1", ["new-a"]),
                    _row("2", ["other-b"]),
                    _row("3", ["old-c"]),
                ],
            )
            _write_jsonl(
                source_c,
                [
                    _row("1", ["new-a"]),
                    _row("2", ["new-b"]),
                    _row("3", ["old-c"]),
                ],
            )

            changes = candidates.find_consensus_changes(
                baseline_path=baseline,
                source_paths=[source_a, source_b, source_c],
                min_support=2,
            )

        self.assertEqual([change.eval_id for change in changes], ["1", "2"])
        self.assertEqual(changes[0].candidate_top1, "new-a")
        self.assertEqual(changes[0].support, 3)
        self.assertEqual(changes[1].candidate_top1, "new-b")
        self.assertEqual(changes[1].support, 2)

    def test_find_rank2_promotions_only_allows_existing_second_rank_candidates(self) -> None:
        candidates = _load_candidates_module()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline.jsonl"
            source = root / "source.jsonl"
            _write_jsonl(
                baseline,
                [
                    _row("1", ["wrong-a", "right-a", "third-a"]),
                    _row("2", ["wrong-b", "third-b", "right-b"]),
                    _row("3", ["wrong-c", "right-c"]),
                    _row("4", ["wrong-d", "right-d"]),
                ],
            )
            _write_jsonl(
                source,
                [
                    _row("1", ["right-a", "wrong-a", "third-a"]),
                    _row("2", ["right-b", "wrong-b", "third-b"]),
                    _row("3", ["right-c", "wrong-c"]),
                    _row("4", ["right-d", "wrong-d"]),
                ],
            )

            promotions = candidates.find_rank2_promotions(
                baseline_path=baseline,
                source_paths=[source],
                excluded_eval_ids={"3"},
            )

        self.assertEqual([promotion.eval_id for promotion in promotions], ["1", "4"])
        self.assertEqual(promotions[0].candidate_rank_in_baseline, 2)

    def test_write_single_row_promotions_writes_one_file_per_eval_id(self) -> None:
        candidates = _load_candidates_module()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline.jsonl"
            source = root / "source.jsonl"
            output_dir = root / "out"
            _write_jsonl(
                baseline,
                [
                    _row("1", ["wrong-a", "right-a", "third-a"]),
                    _row("2", ["wrong-b", "right-b", "third-b"]),
                ],
            )
            _write_jsonl(
                source,
                [
                    _row("1", ["right-a", "wrong-a", "third-a"]),
                    _row("2", ["right-b", "wrong-b", "third-b"]),
                ],
            )
            promotions = candidates.find_rank2_promotions(
                baseline_path=baseline,
                source_paths=[source],
                excluded_eval_ids=set(),
            )

            written = candidates.write_single_row_promotions(
                baseline_path=baseline,
                promotions=promotions,
                output_dir=output_dir,
                name_prefix="rank2",
            )

            output_names = sorted(path.name for path in written)
            first_rows = _read_jsonl(output_dir / "rank2_eval1.jsonl")
            second_rows = _read_jsonl(output_dir / "rank2_eval2.jsonl")

        self.assertEqual(output_names, ["rank2_eval1.jsonl", "rank2_eval2.jsonl"])
        self.assertEqual(first_rows[0]["topk"], ["right-a", "wrong-a", "third-a"])
        self.assertEqual(first_rows[1]["topk"], ["wrong-b", "right-b", "third-b"])
        self.assertEqual(second_rows[0]["topk"], ["wrong-a", "right-a", "third-a"])
        self.assertEqual(second_rows[1]["topk"], ["right-b", "wrong-b", "third-b"])

    def test_filter_promotions_keeps_only_audited_eval_ids(self) -> None:
        candidates = _load_candidates_module()
        promotions = [
            candidates.Rank2Promotion("1", "wrong-a", "right-a", 2, "source", ["right-a"]),
            candidates.Rank2Promotion("2", "wrong-b", "right-b", 2, "source", ["right-b"]),
        ]

        filtered = candidates.filter_promotions(promotions, only_eval_ids={"2"})

        self.assertEqual([promotion.eval_id for promotion in filtered], ["2"])

    def test_filter_promotions_by_public_results_keeps_only_untried_eval_ids(self) -> None:
        candidates = _load_candidates_module()
        promotions = [
            candidates.Rank2Promotion("42", "old-a", "new-a", 2, "source", ["new-a"]),
            candidates.Rank2Promotion("81", "old-b", "new-b", 2, "source", ["new-b"]),
            candidates.Rank2Promotion("285", "old-c", "new-c", 2, "source", ["new-c"]),
            candidates.Rank2Promotion("295", "old-d", "new-d", 2, "source", ["new-d"]),
        ]
        public_results = [
            candidates.PublicResult("42", "improved", 0.9227, 0.9273),
            candidates.PublicResult("81", "regressed", 0.9136, 0.9182),
            candidates.PublicResult("285", "neutral", 0.9273, 0.9318),
        ]

        filtered = candidates.filter_promotions_by_public_results(
            promotions,
            public_results=public_results,
        )

        self.assertEqual([promotion.eval_id for promotion in filtered], ["295"])


def _row(eval_id: str, topk: list[str]) -> dict[str, object]:
    return {
        "eval_id": eval_id,
        "standalone_query": f"query {eval_id}",
        "topk": topk,
        "answer": "",
        "references": [],
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
