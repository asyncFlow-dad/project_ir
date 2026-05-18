from __future__ import annotations

import re
from dataclasses import dataclass

from .schema import ChunkPayload


@dataclass(frozen=True)
class TextChunk:
    chunk_id: int
    text: str
    section_path: list[str]


def chunk_document(
    text: str,
    *,
    max_chars: int = 1200,
    overlap: int = 150,
) -> list[TextChunk]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        return []

    chunks: list[TextChunk] = []
    buffer = ""
    chunk_id = 0

    for paragraph in paragraphs:
        candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
        if len(candidate) <= max_chars:
            buffer = candidate
            continue

        if buffer:
            chunks.append(TextChunk(chunk_id=chunk_id, text=buffer, section_path=[]))
            chunk_id += 1
            buffer = _tail_overlap(buffer, overlap)

        if len(paragraph) <= max_chars:
            buffer = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
            continue

        start = 0
        while start < len(paragraph):
            end = min(len(paragraph), start + max_chars)
            piece = paragraph[start:end].strip()
            if piece:
                chunks.append(TextChunk(chunk_id=chunk_id, text=piece, section_path=[]))
                chunk_id += 1
            start = max(end - overlap, end)

        buffer = ""

    if buffer:
        chunks.append(TextChunk(chunk_id=chunk_id, text=buffer, section_path=[]))

    return chunks


def make_chunk_payload(
    *,
    project_id: str,
    corpus: str,
    doc_id: str,
    source_uri: str,
    source_type: str,
    title: str,
    language: str,
    commit_sha: str,
    acl_role: str,
    created_at: str,
    updated_at: str,
    chunk: TextChunk,
) -> ChunkPayload:
    return ChunkPayload(
        project_id=project_id,
        corpus=corpus,
        doc_id=doc_id,
        chunk_id=chunk.chunk_id,
        source_uri=source_uri,
        source_type=source_type,
        title=title,
        language=language,
        tags=[],
        section_path=chunk.section_path,
        commit_sha=commit_sha,
        acl_role=acl_role,
        created_at=created_at,
        updated_at=updated_at,
        text=chunk.text,
    )


def _tail_overlap(text: str, overlap: int) -> str:
    if overlap <= 0:
        return ""
    return text[-overlap:].lstrip()
