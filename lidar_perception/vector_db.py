"""Redis-backed vector database service."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
from redis import Redis


class VectorDBService:
    """Small vector DB wrapper with Redis JSON payload storage."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0", index_name: str = "agrolidar") -> None:
        self._redis = Redis.from_url(redis_url)
        self._index_name = index_name

    def add_embedding(self, id: str, vector: np.ndarray, metadata: dict[str, Any]) -> None:
        payload = {
            "id": id,
            "vector": np.asarray(vector, dtype=np.float32).tolist(),
            "metadata": metadata,
        }
        self._redis.hset(f"{self._index_name}:vectors", id, json.dumps(payload))

    def query(self, vector: np.ndarray, k: int) -> list[str]:
        query_vec = np.asarray(vector, dtype=np.float32)
        ids: list[str] = []
        scores: list[tuple[float, str]] = []
        all_items = self._redis.hgetall(f"{self._index_name}:vectors")
        for key, value in all_items.items():
            data = json.loads(value)
            candidate = np.asarray(data["vector"], dtype=np.float32)
            denom = float(np.linalg.norm(query_vec) * np.linalg.norm(candidate))
            score = float(np.dot(query_vec, candidate) / denom) if denom else -1.0
            item_id = key.decode() if isinstance(key, bytes) else str(key)
            scores.append((score, item_id))
        for _, item_id in sorted(scores, reverse=True)[:k]:
            ids.append(item_id)
        return ids
