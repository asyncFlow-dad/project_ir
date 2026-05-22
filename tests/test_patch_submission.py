import importlib.util
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase


def _load_patch_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "patch_submission.py"
    spec = importlib.util.spec_from_file_location("patch_submission", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules["patch_submission"] = module
    spec.loader.exec_module(module)
    return module


class PatchSubmissionTests(TestCase):
    def test_patch_submission_replaces_requested_rows_from_source(self) -> None:
        patch_submission = _load_patch_module()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.jsonl"
            source = root / "source.jsonl"
            output = root / "output.jsonl"
            target_rows = [
                _row("a", ["a1", "a2"]),
                _row("b", ["b1", "b2"]),
            ]
            source_rows = [
                _row("a", ["source-a1", "source-a2"]),
                _row("b", ["source-b1", "source-b2"]),
            ]
            _write_jsonl(target, target_rows)
            _write_jsonl(source, source_rows)

            summary = patch_submission.patch_submission(
                target_path=target,
                output_path=output,
                source_path=source,
                eval_ids=["b"],
            )
            rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(summary.changed, 1)
        self.assertEqual(rows[0]["topk"], ["a1", "a2"])
        self.assertEqual(rows[1]["topk"], ["source-b1", "source-b2"])
        self.assertEqual(
            [reference["docid"] for reference in rows[1]["references"]],
            ["source-b1", "source-b2"],
        )


def _row(eval_id: str, topk: list[str]) -> dict[str, object]:
    return {
        "eval_id": eval_id,
        "standalone_query": f"query {eval_id}",
        "topk": topk,
        "answer": f"answer {eval_id}",
        "references": [
            {"docid": doc_id, "score": 1.0 / (index + 1), "content": f"content {doc_id}"}
            for index, doc_id in enumerate(topk)
        ],
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
