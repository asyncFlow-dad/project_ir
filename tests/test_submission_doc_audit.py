import importlib.util
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase


def _load_audit_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "submission_doc_audit.py"
    spec = importlib.util.spec_from_file_location("submission_doc_audit", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules["submission_doc_audit"] = module
    spec.loader.exec_module(module)
    return module


class SubmissionDocAuditTests(TestCase):
    def test_build_audit_rows_includes_query_and_top1_document_text(self) -> None:
        audit = _load_audit_module()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline.jsonl"
            candidate = root / "candidate.jsonl"
            corpus = root / "documents.jsonl"
            _write_jsonl(baseline, [_submission_row("7", "seed question", ["old-doc"])])
            _write_jsonl(candidate, [_submission_row("7", "seed question", ["new-doc"])])
            _write_jsonl(
                corpus,
                [
                    {"docid": "old-doc", "title": "Old", "content": "Old seed text."},
                    {"docid": "new-doc", "title": "New", "content": "New seed text."},
                ],
            )

            rows = audit.build_audit_rows(
                candidate_path=candidate,
                baseline_path=baseline,
                corpus_path=corpus,
                eval_ids=["7"],
            )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].eval_id, "7")
        self.assertEqual(rows[0].query, "seed question")
        self.assertEqual(rows[0].baseline_top1, "old-doc")
        self.assertEqual(rows[0].candidate_top1, "new-doc")
        self.assertIn("Old seed text", rows[0].baseline_text)
        self.assertIn("New seed text", rows[0].candidate_text)


def _submission_row(eval_id: str, query: str, topk: list[str]) -> dict[str, object]:
    return {
        "eval_id": eval_id,
        "standalone_query": query,
        "topk": topk,
        "answer": "",
        "references": [],
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
