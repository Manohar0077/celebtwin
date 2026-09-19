"""
complete_remaining_celebrities.py
Completes ingestion of remaining ~82 Indian celebrities into CelebTwin database.
Strictly ensures:
1. len(faces) == 1 (absolutely no multi-person or couple photos)
2. det_score >= 0.70, face dimension >= 50px
3. Long shot / natural portrait selected for display image banner
4. Clean updates to celebrities.json, embeddings.npy, metadata.npy
"""

import sys
import time
import json
import logging
import urllib.request
import urllib.parse
from pathlib import Path
import cv2
import numpy as np

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import DATASET_DIR, CELEBRITIES_JSON, EMBEDDINGS_NPY, METADATA_NPY
from app.face_engine import face_engine
from scripts.batch_add_celebrities import CANDIDATES

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("CompleteCelebs")

HEADERS = {
    "User-Agent": "CelebTwinBot/1.0 (https://github.com/manohar0077/celebtwin; contact@celebtwin.local) Python/3.11"
}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

def get_candidate_urls(c_info: dict, max_urls: int = 16) -> list[str]:
    urls = []
    wiki_title = c_info.get("wiki") or c_info["name"]
    search_q = c_info.get("search") or c_info["name"]

    # 1. Wikipedia Infobox / Page thumbnail
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(wiki_title)}&prop=pageimages&pithumbsize=1000&format=json"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for _, p in data.get("query", {}).get("pages", {}).items():
                t = p.get("thumbnail", {}).get("source")
                if t and t not in urls:
                    urls.append(t)
        time.sleep(0.3)
    except Exception:
        pass

    # 2. Wikipedia article embedded images
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(wiki_title)}&generator=images&gimlimit=12&prop=imageinfo&iiprop=url&iiurlwidth=800&format=json"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for _, p in data.get("query", {}).get("pages", {}).items():
                title = p.get("title", "").lower()
                if any(b in title for b in ["logo", "icon", "signature", "flag", "sound", "audio", "graph", "stub", "svg", "poster", "film", "cover"]):
                    continue
                ii = p.get("imageinfo", [])
                if ii:
                    t = ii[0].get("thumburl") or ii[0].get("url")
                    if t and t not in urls:
                        urls.append(t)
        time.sleep(0.3)
    except Exception:
        pass

    # 3. Wikimedia Commons search queries
    for q in [search_q, f"{search_q} portrait", f"{c_info['name']}"]:
        if len(urls) >= max_urls:
            break
        try:
            url = (
                f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
                f"&gsrnamespace=6&gsrsearch={urllib.parse.quote(q)}&gsrlimit=10"
                f"&prop=imageinfo&iiprop=url&iiurlwidth=800&format=json"
            )
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for _, p in data.get("query", {}).get("pages", {}).items():
                    title = p.get("title", "").lower()
                    if any(b in title for b in ["logo", "icon", "signature", "flag", "sound", "audio", "graph", "stub", "svg", "poster", "stadium", "cover"]):
                        continue
                    ii = p.get("imageinfo", [])
                    if ii:
                        t = ii[0].get("thumburl") or ii[0].get("url")
                        if t and t not in urls:
                            urls.append(t)
            time.sleep(0.3)
        except Exception:
            pass

    return urls

def process_single_celebrity(c_info: dict) -> tuple[np.ndarray | None, str | None, int]:
    cid = c_info["id"]
    cname = c_info["name"]
    folder = DATASET_DIR / cid
    folder.mkdir(parents=True, exist_ok=True)

    urls = get_candidate_urls(c_info)
    if not urls:
        logger.warning("  No candidate URLs found for %s", cname)
        return None, None, 0

    valid_images = []
    embeddings = []
    display_candidates = []

    for idx, u in enumerate(urls):
        try:
            req = urllib.request.Request(u, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read()
            if len(content) < 4000:
                continue
            arr = np.frombuffer(content, np.uint8)
            im = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if im is None:
                continue

            h, w = im.shape[:2]
            rgb = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
            faces = face_engine._app.get(rgb)

            # STRICT SINGLE PERSON CONSTRAINT
            if len(faces) != 1:
                continue

            face = faces[0]
            score = float(getattr(face, "det_score", 0))
            b = face.bbox
            fw = b[2] - b[0]
            fh = b[3] - b[1]

            if score < 0.70 or fw < 50 or fh < 50:
                continue

            emb = face.embedding
            if emb is None:
                continue
            norm = np.linalg.norm(emb)
            if norm == 0:
                continue

            # Save the verified single-person photo
            save_path = folder / f"img_{len(valid_images) + 1}.jpg"
            save_path.write_bytes(content)
            valid_images.append(save_path)
            embeddings.append(emb / norm)

            # Long shot display score (prefer natural framing, not extreme close-up)
            face_ratio = (fw * fh) / (w * h)
            aspect = h / w
            ratio_dist = abs(face_ratio - 0.10)
            aspect_bonus = min(aspect, 1.6) * 0.4
            close_penalty = (face_ratio - 0.25) * 20.0 if face_ratio > 0.25 else (0.03 - face_ratio) * 20.0 if face_ratio < 0.03 else 0.0
            display_score = -(ratio_dist * 4.0) + aspect_bonus + (score * 0.3) - close_penalty
            display_candidates.append((display_score, f"{cid}/{save_path.name}"))

            time.sleep(0.2)
            # Once we have 3-4 excellent single-person photos, that is plenty
            if len(valid_images) >= 4:
                break

        except Exception as e:
            continue

    if not embeddings:
        return None, None, 0

    # Composite normalized embedding
    avg = np.mean(embeddings, axis=0)
    norm = np.linalg.norm(avg)
    if norm == 0:
        return None, None, 0
    composite_emb = avg / norm

    # Best display image
    display_candidates.sort(key=lambda x: x[0], reverse=True)
    best_display = display_candidates[0][1]

    return composite_emb, best_display, len(valid_images)

def main():
    logger.info("=" * 65)
    logger.info("Starting Ingestion of Remaining Celebrities")
    logger.info("=" * 65)

    face_engine.load()

    # Load existing database
    with open(CELEBRITIES_JSON, "r", encoding="utf-8") as f:
        celebrities_json = json.load(f)
    existing_ids = {c["id"] for c in celebrities_json}
    existing_names = {c["name"].lower().strip() for c in celebrities_json}

    embeddings_list = list(np.load(EMBEDDINGS_NPY))
    metadata_list = list(np.load(METADATA_NPY, allow_pickle=True))

    missing = [
        c for c in CANDIDATES 
        if c["id"] not in existing_ids and c["name"].lower().strip() not in existing_names
    ]

    total_missing = len(missing)
    logger.info("Loaded %d existing celebrities. Found %d missing candidates.", len(celebrities_json), total_missing)

    added = 0
    failed = []

    for idx, c in enumerate(missing):
        cname = c["name"]
        cid = c["id"]
        logger.info("[%d/%d] Processing: %s (%s)...", idx + 1, total_missing, cname, c["category"])

        emb, display_img, num_photos = process_single_celebrity(c)

        if emb is None or num_photos == 0:
            logger.warning("  [!] Failed to acquire verified single-face photos for %s", cname)
            failed.append(cname)
            continue

        embeddings_list.append(emb)
        metadata_list.append({
            "name": cname,
            "category": c["category"],
            "image": display_img,
        })
        celebrities_json.append({
            "id": cid,
            "name": cname,
            "category": c["category"],
            "folder": cid,
        })
        existing_ids.add(cid)
        existing_names.add(cname.lower().strip())
        added += 1

        logger.info("  ✓ Added %s (%d photos, display=%s)", cname, num_photos, display_img)

        # Save checkpoint every 10 additions to keep state resilient
        if added % 10 == 0:
            with open(CELEBRITIES_JSON, "w", encoding="utf-8") as f:
                json.dump(celebrities_json, f, indent=2)
            np.save(EMBEDDINGS_NPY, np.array(embeddings_list, dtype=np.float32))
            np.save(METADATA_NPY, np.array(metadata_list, dtype=object))
            logger.info("  [Checkpoint saved: %d total in DB]", len(celebrities_json))

    # Final save
    with open(CELEBRITIES_JSON, "w", encoding="utf-8") as f:
        json.dump(celebrities_json, f, indent=2)
    np.save(EMBEDDINGS_NPY, np.array(embeddings_list, dtype=np.float32))
    np.save(METADATA_NPY, np.array(metadata_list, dtype=object))

    logger.info("=" * 65)
    logger.info("COMPLETED: Added %d new celebrities! (Total in DB now: %d)", added, len(celebrities_json))
    if failed:
        logger.info("Failed (%d): %s", len(failed), ", ".join(failed))
    logger.info("=" * 65)

if __name__ == "__main__":
    main()
