import importlib.util
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase


def _load_report_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "submission_diff_report.py"
    spec = importlib.util.spec_from_file_location("submission_diff_report", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules["submission_diff_report"] = module
    spec.loader.exec_module(module)
    return module


class SubmissionDiffReportTests(TestCase):
    def test_summarize_submission_diff_reports_changed_rows_and_hash(self) -> None:
        report = _load_report_module()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline.jsonl"
            candidate = root / "candidate.jsonl"
            _write_jsonl(
                baseline,
                [
                    _row("1", ["a", "b"]),
                    _row("2", []),
                    _row("3", ["x", "y"]),
                ],
            )
            _write_jsonl(
                candidate,
                [
                    _row("1", ["a", "c"]),
                    _row("2", ["filled"]),
                    _row("3", ["z", "y"]),
                ],
            )

            summary = report.summarize_submission_diff(candidate, baseline)

        self.assertEqual(summary.rows, 3)
        self.assertEqual(summary.empty_topk, 0)
        self.assertEqual(summary.duplicate_topk, 0)
        self.assertEqual(summary.changed, 3)
        self.assertEqual(summary.top1_changed, 2)
        self.assertEqual(summary.empty_to_filled, 1)
        self.assertEqual(summary.filled_to_empty, 0)
        self.assertEqual(summary.changed_eval_ids, ["1", "2", "3"])
        self.assertEqual(summary.top1_changed_eval_ids, ["2", "3"])
        self.assertEqual(len(summary.sha256), 64)


def _row(eval_id: str, topk: list[str]) -> dict[str, object]:
    return {
        "eval_id": eval_id,
        "standalone_query": f"query {eval_id}",
        "topk": topk,
        "answer": f"answer {eval_id}",
        "references": [],
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
