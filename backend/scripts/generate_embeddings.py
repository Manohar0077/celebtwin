"""
generate_embeddings.py

Reads all celebrity images from the dataset, detects faces,
generates L2-normalised embeddings, averages per celebrity,
and saves embeddings.npy + metadata.npy.

Usage (run from project root):
    cd backend
    python scripts/generate_embeddings.py
"""
import sys
import json
import logging
from pathlib import Path

import numpy as np

# Allow importing from backend/app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import CELEBRITIES_JSON, EMBEDDINGS_NPY, METADATA_NPY, DATASET_DIR
from app.face_engine import face_engine

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def pick_display_image(folder: Path) -> str | None:
    """Return relative path (folder/filename) of the first valid image."""
    for ext in [".jpg", ".jpeg", ".png"]:
        for f in sorted(folder.iterdir()):
            if f.suffix.lower() == ext:
                return f"{folder.name}/{f.name}"
    return None


def compute_celebrity_embedding(folder: Path) -> tuple[np.ndarray | None, str | None]:
    """
    Process all images in a celebrity folder.
    Returns (averaged_embedding, display_image_path) or (None, None).
    """
    images = [f for f in sorted(folder.iterdir()) if f.suffix.lower() in IMAGE_EXTS]
    if not images:
        logger.warning("No images found in %s", folder)
        return None, None

    embeddings = []
    display_image = None

    for img_path in images:
        emb = face_engine.embedding_from_file(str(img_path))
        if emb is not None:
            embeddings.append(emb)
            if display_image is None:
                display_image = f"{folder.name}/{img_path.name}"
        else:
            logger.debug("  Skipped %s (no single face)", img_path.name)

    if not embeddings:
        logger.warning("  No usable faces found in %s", folder.name)
        return None, None

    # Average and re-normalise
    avg = np.mean(embeddings, axis=0)
    norm = np.linalg.norm(avg)
    if norm == 0:
        return None, None
    averaged = avg / norm

    logger.info("  ✓ %d/%d images used, display=%s", len(embeddings), len(images), display_image)
    return averaged, display_image


def main():
    logger.info("=" * 60)
    logger.info("Celebrity Doppelgänger — Embedding Generator")
    logger.info("Dataset: %s", DATASET_DIR)
    logger.info("=" * 60)

    if not DATASET_DIR.exists():
        logger.error("Dataset directory not found: %s", DATASET_DIR)
        sys.exit(1)

    # Load celebrity metadata
    with open(CELEBRITIES_JSON) as f:
        celebrities = json.load(f)

    # Load model
    logger.info("Loading InsightFace model (may download on first run) …")
    face_engine.load()
    logger.info("Model ready.\n")

    all_embeddings = []
    all_metadata   = []
    failed         = []

    for celeb in celebrities:
        folder = DATASET_DIR / celeb["folder"]
        logger.info("Processing: %s (%s)", celeb["name"], celeb["folder"])

        if not folder.exists():
            logger.warning("  Folder not found: %s — skipping", folder)
            failed.append(celeb["name"])
            continue

        emb, display_img = compute_celebrity_embedding(folder)
        if emb is None:
            logger.warning("  No embedding generated for %s — skipping", celeb["name"])
            failed.append(celeb["name"])
            continue

        all_embeddings.append(emb)
        all_metadata.append({
            "name":     celeb["name"],
            "category": celeb["category"],
            "image":    display_img or f"{celeb['folder']}/1.jpg",
        })

    if not all_embeddings:
        logger.error("No embeddings generated. Check dataset and model.")
        sys.exit(1)

    # Save
    emb_arr = np.array(all_embeddings, dtype=np.float32)  # (N, 512)
    meta_arr = np.array(all_metadata, dtype=object)

    EMBEDDINGS_NPY.parent.mkdir(parents=True, exist_ok=True)
    np.save(str(EMBEDDINGS_NPY), emb_arr)
    np.save(str(METADATA_NPY), meta_arr)

    logger.info("\n" + "=" * 60)
    logger.info("Saved %d embeddings → %s", len(all_embeddings), EMBEDDINGS_NPY)
    logger.info("Saved metadata      → %s", METADATA_NPY)
    if failed:
        logger.warning("Skipped: %s", ", ".join(failed))
    logger.info("Done ✓")


if __name__ == "__main__":
    main()
