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
    Process all images in a celebrity folder using quality-filtered face detection.
    - Skips group photos (multiple faces with no dominant one)
    - Skips very small faces (< 65px)
    - Skips low-confidence detections (< 0.70)
    - Picks a natural long-shot / medium portrait as display image (shows head, shoulders & upper body)
    Returns (averaged_embedding, display_image_path) or (None, None).
    """
    images = [f for f in sorted(folder.iterdir()) if f.suffix.lower() in IMAGE_EXTS]
    if not images:
        logger.warning("No images found in %s", folder)
        return None, None

    embeddings = []
    display_candidates = []

    for img_path in images:
        img_bgr = cv2.imread(str(img_path))
        if img_bgr is None:
            continue
        h, w = img_bgr.shape[:2]
        emb, quality = face_engine.get_clear_face_embedding(str(img_path), min_dim=65, min_det_score=0.70)
        if emb is not None:
            embeddings.append(emb)

            # Check face bbox for long-shot score
            faces = face_engine._app.get(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
            if faces:
                primary = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)[0]
                b = primary.bbox
                fw = b[2] - b[0]
                fh = b[3] - b[1]
                face_ratio = (fw * fh) / (w * h)
                aspect = h / w

                # Ideal face ratio is ~8% to 14% (classic medium/long portrait shot)
                ratio_dist = abs(face_ratio - 0.10)
                aspect_bonus = min(aspect, 1.6) * 0.4
                close_penalty = (face_ratio - 0.25) * 20.0 if face_ratio > 0.25 else (0.03 - face_ratio) * 20.0 if face_ratio < 0.03 else 0.0
                long_score = -(ratio_dist * 4.0) + aspect_bonus + (float(getattr(primary, 'det_score', 0)) * 0.3) - close_penalty

                display_candidates.append((long_score, f"{folder.name}/{img_path.name}"))
        else:
            logger.debug("  Skipped %s (no clear single face)", img_path.name)

    if not embeddings:
        logger.warning("  No usable faces found in %s", folder.name)
        return None, None

    # Average and re-normalise
    avg = np.mean(embeddings, axis=0)
    norm = np.linalg.norm(avg)
    if norm == 0:
        return None, None
    averaged = avg / norm

    # Pick highest scoring long-shot image
    if display_candidates:
        display_candidates.sort(key=lambda x: x[0], reverse=True)
        best_display = display_candidates[0][1]
    else:
        best_display = f"{folder.name}/{images[0].name}"

    logger.info("  ✓ %d/%d images used, display=%s (long shot)", len(embeddings), len(images), best_display)
    return averaged, best_display


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
