"""
update_long_shot_displays.py
Updates the display image for each celebrity in metadata.npy
to prefer a long shot (showing hairstyle, upper body / torso)
instead of an extreme close-up cropped face.
"""

import sys
import logging
from pathlib import Path
import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import DATASET_DIR, CELEBRITY_DATA, METADATA_NPY
from app.face_engine import face_engine

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

def find_best_long_shot(folder: Path) -> tuple[str | None, dict]:
    images = [f for f in sorted(folder.iterdir()) if f.suffix.lower() in IMAGE_EXTS]
    if not images:
        return None, {}

    candidates = []
    for img_p in images:
        img = cv2.imread(str(img_p))
        if img is None:
            continue
        h, w = img.shape[:2]
        faces = face_engine._app.get(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if not faces:
            continue

        # Sort by face area
        faces_sorted = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)
        primary = faces_sorted[0]
        score = float(getattr(primary, 'det_score', 0))
        if score < 0.70:
            continue

        # If multiple faces, ensure primary face is dominant (not a group shot)
        if len(faces_sorted) > 1:
            a1 = (faces_sorted[0].bbox[2]-faces_sorted[0].bbox[0]) * (faces_sorted[0].bbox[3]-faces_sorted[0].bbox[1])
            a2 = (faces_sorted[1].bbox[2]-faces_sorted[1].bbox[0]) * (faces_sorted[1].bbox[3]-faces_sorted[1].bbox[1])
            if a1 < 2.0 * a2:
                continue

        b = primary.bbox
        fw = b[2] - b[0]
        fh = b[3] - b[1]
        if fw < 50 or fh < 50:
            continue

        face_ratio = (fw * fh) / (w * h)
        aspect = h / w

        # Long-shot score:
        # Ideal face ratio is ~0.08 - 0.14 (8% to 14% of the photo area)
        # This provides a classic medium/long portrait shot showing head, shoulders, chest
        target_ratio = 0.10
        ratio_dist = abs(face_ratio - target_ratio)

        # Portrait bonus (prefer vertical or near-square images over wide horizontal crops)
        aspect_bonus = min(aspect, 1.6) * 0.4

        # Harsh penalty for extreme close-up faces (where face takes > 25% of image)
        close_penalty = 0.0
        if face_ratio > 0.25:
            close_penalty = (face_ratio - 0.25) * 20.0
        elif face_ratio < 0.03:
            close_penalty = (0.03 - face_ratio) * 20.0

        total_score = -(ratio_dist * 4.0) + aspect_bonus + (score * 0.3) - close_penalty

        candidates.append({
            "name": img_p.name,
            "face_ratio": face_ratio,
            "aspect": aspect,
            "det_score": score,
            "total_score": total_score,
            "res": f"{w}x{h}"
        })

    if not candidates:
        # Fallback to first image
        return images[0].name, {"fallback": True}

    candidates.sort(key=lambda x: x["total_score"], reverse=True)
    best = candidates[0]
    return best["name"], best

def main():
    metadata_path = METADATA_NPY
    if not metadata_path.exists():
        logger.error("metadata.npy not found: %s", metadata_path)
        sys.exit(1)

    logger.info("Loading metadata from %s", metadata_path)
    metadata = list(np.load(metadata_path, allow_pickle=True))
    logger.info("Loaded %d celebrity metadata entries", len(metadata))

    logger.info("Loading InsightFace model...")
    face_engine.load()
    logger.info("InsightFace model loaded.")

    updated_count = 0
    for idx, item in enumerate(metadata):
        cname = item["name"]
        old_img = item.get("image", "")
        # Folder is either first segment of old_img or derived
        folder_name = old_img.split("/")[0] if "/" in old_img else ""
        folder = DATASET_DIR / folder_name
        if not folder.exists() or not folder.is_dir():
            logger.warning("Folder not found for %s (%s)", cname, folder_name)
            continue

        best_img, info = find_best_long_shot(folder)
        if best_img:
            new_rel = f"{folder.name}/{best_img}"
            if new_rel != old_img:
                updated_count += 1
                face_pct = info.get('face_ratio', 0) * 100
                logger.info(
                    "[%d/%d] %s: %s -> %s (face coverage: %.1f%%, res: %s)",
                    idx + 1, len(metadata), cname, old_img, new_rel, face_pct, info.get('res', '')
                )
            metadata[idx]["image"] = new_rel

    logger.info("Updated %d/%d celebrity display images to long shots.", updated_count, len(metadata))

    # Save updated metadata
    np.save(metadata_path, np.array(metadata, dtype=object))
    logger.info("Successfully saved updated metadata.npy ✓")

if __name__ == "__main__":
    main()
