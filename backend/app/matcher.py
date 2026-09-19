"""
Matcher — cosine similarity search over celebrity embeddings.
Keeps all data in memory for fast lookup.
"""
import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    name: str
    category: str
    score: float
    image: Optional[str]


class Matcher:
    def __init__(self) -> None:
        self._embeddings: Optional[np.ndarray] = None   # (N, 512)
        self._metadata: Optional[list[dict]]  = None    # length N
        self._loaded = False

    def load(self, embeddings: np.ndarray, metadata: list[dict]) -> None:
        """
        Load pre-computed celebrity embeddings + metadata into memory.
        embeddings: (N, 512) float32, L2-normalised
        metadata:   list of dicts with keys: name, category, image
        """
        assert embeddings.shape[0] == len(metadata), "Embeddings / metadata length mismatch"
        self._embeddings = embeddings.astype(np.float32)
        self._metadata   = metadata
        self._loaded     = True
        logger.info("Matcher loaded %d celebrity embeddings ✓", len(metadata))

    @property
    def ready(self) -> bool:
        return self._loaded

    @property
    def count(self) -> int:
        return len(self._metadata) if self._metadata else 0

    def find_top_k(
        self,
        query: np.ndarray,
        k: int = 5,
        category_filter: Optional[str] = None,
    ) -> list[MatchResult]:
        """
        Return top-k celebrity matches by cosine similarity.
        query: (512,) float32, L2-normalised
        """
        if not self.ready:
            raise RuntimeError("Matcher not loaded. Run generate_embeddings.py first.")

        embeddings = self._embeddings
        metadata   = self._metadata

        # optional category filter
        if category_filter and category_filter.lower() != "all":
            indices = [i for i, m in enumerate(metadata) if m.get("category", "").lower() == category_filter.lower()]
            if not indices:
                logger.warning("No celebrities found for category '%s'. Using all.", category_filter)
                indices = list(range(len(metadata)))
            embeddings = embeddings[indices]
            metadata   = [metadata[i] for i in indices]

        # cosine similarity (since embeddings are L2-normalised, dot product == cosine sim)
        scores = embeddings @ query.astype(np.float32)   # (N,)

        # top-k
        top_indices = np.argsort(scores)[::-1][:k]

        results = []
        for idx in top_indices:
            m = metadata[idx]
            results.append(MatchResult(
                name     = m["name"],
                category = m["category"],
                score    = float(np.clip(scores[idx], 0.0, 1.0)),
                image    = m.get("image"),
            ))

        return results


# Singleton
matcher = Matcher()
