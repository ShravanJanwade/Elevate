"""
Elevate v3 – Embedding Cache
===============================
File-based embedding cache — no Redis or external services needed.
Caches computed embeddings to disk for fast reuse.
"""

import hashlib
import os
from typing import Callable

import numpy as np


class EmbeddingCache:
    """File-based embedding cache with LRU memory layer."""

    def __init__(self, cache_dir: str = "cache/embeddings", max_memory: int = 1000):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self._memory = {}
        self._access_order = []
        self._max_memory = max_memory

    def get_or_compute(self, text: str, encoder_fn: Callable) -> np.ndarray:
        """Get cached embedding or compute and cache it."""
        key = self._key(text)

        # Memory cache
        if key in self._memory:
            return self._memory[key]

        # Disk cache
        path = os.path.join(self.cache_dir, f"{key}.npy")
        if os.path.exists(path):
            emb = np.load(path)
            self._memory_set(key, emb)
            return emb

        # Compute
        emb = encoder_fn(text)
        if isinstance(emb, np.ndarray):
            np.save(path, emb)
            self._memory_set(key, emb)
        return emb

    def clear(self):
        """Clear all caches."""
        self._memory.clear()
        self._access_order.clear()
        import shutil
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)

    def stats(self) -> dict:
        """Get cache statistics."""
        disk_count = len([f for f in os.listdir(self.cache_dir) if f.endswith(".npy")])
        return {
            "memory_entries": len(self._memory),
            "disk_entries": disk_count,
        }

    def _key(self, text: str) -> str:
        return hashlib.md5(text[:500].encode("utf-8", errors="ignore")).hexdigest()

    def _memory_set(self, key: str, value: np.ndarray):
        self._memory[key] = value
        self._access_order.append(key)
        # Evict oldest
        while len(self._memory) > self._max_memory:
            oldest = self._access_order.pop(0)
            self._memory.pop(oldest, None)


# Singleton
_cache_instance = None


def get_embedding_cache() -> EmbeddingCache:
    """Get the global embedding cache."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = EmbeddingCache()
    return _cache_instance
# clear cache logic
