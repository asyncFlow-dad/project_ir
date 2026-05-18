#!/usr/bin/env python3
"""Bootstrap Qdrant collection and Redis Streams for local AI IR core."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"

sys.path.insert(0, str(ROOT))
from ir_search.schema import COLLECTION_NAME, collection_config  # noqa: E402
from ir_search.streams import STREAM_CONSUMERS  # noqa: E402


def load_env_file(path: Path) -> None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key, value = key.strip(), value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


def http_json(method: str, url: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        body = response.read().decode("utf-8")
        return json.loads(body) if body else {}


def ensure_qdrant_collection(base_url: str, dense_size: int) -> None:
    exists_url = f"{base_url.rstrip('/')}/collections/{COLLECTION_NAME}"
    try:
        http_json("GET", exists_url)
        print(f"Qdrant collection exists: {COLLECTION_NAME}")
        return
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise

    create_url = f"{base_url.rstrip('/')}/collections/{COLLECTION_NAME}"
    body = {
        "vectors": {
            "text_dense": {
                "size": dense_size,
                "distance": "Cosine",
            }
        },
        "sparse_vectors": {
            "text_sparse": {},
        },
    }
    http_json("PUT", create_url, body)
    print(f"Created Qdrant collection: {COLLECTION_NAME}")


def ensure_redis_streams(redis_url: str) -> None:
    try:
        import redis
    except ImportError as error:
        raise SystemExit(
            "redis package required for stream bootstrap: pip install redis"
        ) from error

    client = redis.from_url(redis_url)
    for stream, groups in STREAM_CONSUMERS.items():
        client.xadd(stream, {"bootstrap": "1"}, maxlen=1, approximate=True)
        for group in groups:
            try:
                client.xgroup_create(stream, group, id="0", mkstream=True)
                print(f"Created Redis group {group} on {stream}")
            except redis.ResponseError as error:
                if "BUSYGROUP" in str(error):
                    print(f"Redis group exists: {group} on {stream}")
                else:
                    raise


def main() -> int:
    load_env_file(ENV_PATH)
    qdrant_url = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
    redis_url = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
    dense_size = int(os.environ.get("AIIR_DENSE_SIZE", "1024"))

    print(json.dumps(collection_config(dense_size=dense_size), indent=2))
    ensure_qdrant_collection(qdrant_url, dense_size)
    ensure_redis_streams(redis_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
