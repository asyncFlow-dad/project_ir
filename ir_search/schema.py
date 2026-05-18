from __future__ import annotations

from dataclasses import dataclass

COLLECTION_NAME = "aiir_chunks_v1"

DENSE_VECTOR_NAME = "text_dense"
SPARSE_VECTOR_NAME = "text_sparse"

PAYLOAD_INDEX_FIELDS = (
    "project_id",
    "corpus",
    "doc_id",
    "source_uri",
    "source_type",
    "language",
    "acl_role",
    "commit_sha",
)


@dataclass(frozen=True)
class ChunkPayload:
    project_id: str
    corpus: str
    doc_id: str
    chunk_id: int
    source_uri: str
    source_type: str
    title: str
    language: str
    tags: list[str]
    section_path: list[str]
    commit_sha: str
    acl_role: str
    created_at: str
    updated_at: str
    text: str

    def to_dict(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "corpus": self.corpus,
            "doc_id": self.doc_id,
            "chunk_id": self.chunk_id,
            "source_uri": self.source_uri,
            "source_type": self.source_type,
            "title": self.title,
            "language": self.language,
            "tags": self.tags,
            "section_path": self.section_path,
            "commit_sha": self.commit_sha,
            "acl_role": self.acl_role,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "text": self.text,
        }


def collection_config(*, dense_size: int = 1024) -> dict[str, object]:
    """Qdrant collection shape from deep-research-report § Qdrant 스키마."""
    return {
        "collection": COLLECTION_NAME,
        "vectors": {
            DENSE_VECTOR_NAME: {
                "size": dense_size,
                "distance": "Cosine",
            }
        },
        "sparse_vectors": {
            SPARSE_VECTOR_NAME: {},
        },
        "payload_fields": {
            "project_id": "keyword",
            "corpus": "keyword",
            "doc_id": "keyword",
            "chunk_id": "integer",
            "source_uri": "keyword",
            "source_type": "keyword",
            "title": "text",
            "language": "keyword",
            "tags": "keyword[]",
            "section_path": "keyword[]",
            "commit_sha": "keyword",
            "acl_role": "keyword",
            "created_at": "datetime",
            "updated_at": "datetime",
        },
    }
