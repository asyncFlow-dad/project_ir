from unittest import TestCase

from ir_search.chunking import chunk_document


class ChunkingTests(TestCase):
    def test_chunk_document_splits_long_text(self) -> None:
        text = "Paragraph one.\n\n" + ("word " * 400)
        chunks = chunk_document(text, max_chars=200, overlap=20)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk.text for chunk in chunks))

    def test_chunk_document_overlaps_long_paragraph_chunks(self) -> None:
        text = "".join(f"{index:03d}|" for index in range(60))

        chunks = chunk_document(text, max_chars=50, overlap=10)

        self.assertEqual(chunks[0].text[-10:], chunks[1].text[:10])
