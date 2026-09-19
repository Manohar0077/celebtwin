"""
FaceEngine — wraps InsightFace model.
Initialized once at app startup, reused for every request.
"""
import logging
from typing import Optional

import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis

from .config import INSIGHTFACE_MODEL, DET_SIZE

logger = logging.getLogger(__name__)


class FaceEngineError(Exception):
    """Raised for detectable face issues (no face, multiple faces, etc.)"""


class FaceEngine:
    def __init__(self) -> None:
        self._app: Optional[FaceAnalysis] = None

    # ── lifecycle ────────────────────────────────────────────────
    def load(self) -> None:
        """Download / load the InsightFace model. Call once at startup."""
        logger.info("Loading InsightFace model '%s' …", INSIGHTFACE_MODEL)
        self._app = FaceAnalysis(
            name=INSIGHTFACE_MODEL,
            providers=["CPUExecutionProvider"],
        )
        self._app.prepare(ctx_id=0, det_size=DET_SIZE)
        logger.info("InsightFace model loaded ✓")

    @property
    def ready(self) -> bool:
        return self._app is not None

    # ── public API ───────────────────────────────────────────────
    def get_embedding(self, image_bytes: bytes) -> np.ndarray:
        """
        Detect exactly one face in image_bytes and return its L2-normalised embedding.

        Raises FaceEngineError if:
          - image cannot be decoded
          - no face is detected
          - more than one face is detected
        """
        if not self.ready:
            raise RuntimeError("FaceEngine not initialised. Call load() first.")

        # decode
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise FaceEngineError("Could not decode image. Please use JPG or PNG.")

        # BGR → RGB (InsightFace expects RGB)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # detect
        faces = self._app.get(img_rgb)

        if len(faces) == 0:
            raise FaceEngineError(
                "No face detected. Please make sure your face is clearly visible and well-lit."
            )
        if len(faces) > 1:
            raise FaceEngineError(
                "Multiple faces detected. Please ensure only one face is visible in the frame."
            )

        embedding = faces[0].embedding  # shape (512,)
        if embedding is None:
            raise FaceEngineError("Could not generate face embedding. Please try a different photo.")

        # L2 normalise
        norm = np.linalg.norm(embedding)
        if norm == 0:
            raise FaceEngineError("Invalid embedding (zero norm).")
        return embedding / norm

    # ── utility ──────────────────────────────────────────────────
    def embedding_from_file(self, path: str) -> Optional[np.ndarray]:
        """
        Load an image file from disk and return its embedding.
        Returns None if no face is found (for robust embedding generation).
        """
        img = cv2.imread(path)
        if img is None:
            return None
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        faces = self._app.get(img_rgb)
        if len(faces) != 1:
            return None
        emb = faces[0].embedding
        if emb is None:
            return None
        norm = np.linalg.norm(emb)
        return emb / norm if norm > 0 else None

    def get_clear_face_embedding(
        self,
        path: str,
        min_dim: int = 65,
        min_det_score: float = 0.70,
    ) -> tuple[Optional[np.ndarray], float]:
        """
        Detect faces in image. Ensures the face is visible CLEARLY:
        - Bounding box must be at least min_dim x min_dim
        - Detection confidence score >= min_det_score
        - If multiple faces, accepts only if the primary foreground face is dominant (>2.5x area)
        Returns (normalized_embedding, quality_score) or (None, 0.0)
        """
        img = cv2.imread(path)
        if img is None:
            return None, 0.0
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        faces = self._app.get(img_rgb)
        if not faces:
            return None, 0.0

        valid_faces = []
        for f in faces:
            score = float(getattr(f, "det_score", 0.0))
            if score < min_det_score:
                continue
            x1, y1, x2, y2 = f.bbox
            w = x2 - x1
            h = y2 - y1
            if w >= min_dim and h >= min_dim:
                area = w * h
                valid_faces.append((f, score, area))

        if not valid_faces:
            return None, 0.0

        valid_faces.sort(key=lambda item: item[2], reverse=True)

        if len(valid_faces) > 1:
            largest_area = valid_faces[0][2]
            second_area = valid_faces[1][2]
            if largest_area < 2.5 * second_area:
                return None, 0.0

        best_face, best_score, best_area = valid_faces[0]
        emb = best_face.embedding
        if emb is None:
            return None, 0.0
        norm = np.linalg.norm(emb)
        if norm == 0:
            return None, 0.0

        quality = float(best_score * (best_area ** 0.5))
        return (emb / norm), quality


# Singleton — imported by main.py and scripts
face_engine = FaceEngine()
