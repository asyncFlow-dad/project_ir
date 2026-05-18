from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ir_search.indexer import CorpusDocument, build_index
from ir_search.snapshot import build_or_load_index, save_snapshot, snapshot_path


class SnapshotTests(TestCase):
    def test_save_and_load_snapshot(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "a.md").write_text(
                "Retrieval augmented generation improves grounded answers.",
                encoding="utf-8",
            )

            documents = [
                CorpusDocument(
                    id="a.md",
                    path=corpus / "a.md",
                    text=(corpus / "a.md").read_text(encoding="utf-8"),
                )
            ]
            index = build_index(documents)
            save_snapshot(index, corpus, root / "indexes")

            loaded = build_or_load_index(corpus, root / "indexes")
            self.assertEqual(len(loaded.documents), 1)
            self.assertTrue(snapshot_path(corpus, root / "indexes").exists())
