from unittest import TestCase

from ir_search.chunking import chunk_document


class ChunkingTests(TestCase):
    def test_chunk_document_splits_long_text(self) -> None:
        text = "Paragraph one.\n\n" + ("word " * 400)
        chunks = chunk_document(text, max_chars=200, overlap=20)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk.text for chunk in chunks))
