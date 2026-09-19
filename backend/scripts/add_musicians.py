"""
add_musicians.py
Downloads images, computes high-quality face embeddings, and adds:
- Sai Abhyankar
- Anirudh Ravichander
- A. R. Rahman
- Sid Sriram
- Yuvan Shankar Raja
- Arijit Singh
- Harris Jayaraj
- Santhosh Narayanan
- Shreya Ghoshal
to the celebrity database (celebrities.json, metadata.npy, embeddings.npy).
"""

import sys
import json
import logging
import urllib.request
import urllib.parse
from pathlib import Path
import cv2
import numpy as np

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import DATASET_DIR, CELEBRITIES_JSON, EMBEDDINGS_NPY, METADATA_NPY
from app.face_engine import face_engine

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

MUSICIANS = [
    {
        "id": "sai_abhyankkar",
        "name": "Sai Abhyankar",
        "category": "Musician",
        "folder": "sai_abhyankkar",
        "direct_urls": [
            "https://resizing.flixster.com/Z01VjTMcOecYfJ2bSml8J-vXJkQ=/ems.cHJkLWVtcy1hc3NldHMvbW92aWVzL2FhNjcwYzQzLTViYzgtNGQyYS1hZDJhLTYzYTVkNDgzZTc3Yi5qcGc=",
            "https://img.youtube.com/vi/Av3pw4fScuI/maxresdefault.jpg",
            "https://img.youtube.com/vi/jj9zCQq3U1s/maxresdefault.jpg",
            "https://img.youtube.com/vi/zD1dN1wAJqU/maxresdefault.jpg",
            "https://img.youtube.com/vi/QbfXX7b4FEg/maxresdefault.jpg",
        ],
        "commons_query": None,
    },
    {
        "id": "anirudh",
        "name": "Anirudh Ravichander",
        "category": "Musician",
        "folder": "anirudh",
        "commons_query": "Anirudh Ravichander",
    },
    {
        "id": "ar_rahman",
        "name": "A. R. Rahman",
        "category": "Musician",
        "folder": "ar_rahman",
        "commons_query": "A. R. Rahman",
    },
    {
        "id": "sid_sriram",
        "name": "Sid Sriram",
        "category": "Musician",
        "folder": "sid_sriram",
        "commons_query": "Sid Sriram",
    },
    {
        "id": "yuvan_shankar_raja",
        "name": "Yuvan Shankar Raja",
        "category": "Musician",
        "folder": "yuvan_shankar_raja",
        "commons_query": "Yuvan Shankar Raja",
    },
    {
        "id": "arijit_singh",
        "name": "Arijit Singh",
        "category": "Musician",
        "folder": "arijit_singh",
        "commons_query": "Arijit Singh",
    },
    {
        "id": "harris_jayaraj",
        "name": "Harris Jayaraj",
        "category": "Musician",
        "folder": "harris_jayaraj",
        "commons_query": "Harris Jayaraj",
    },
    {
        "id": "santhosh_narayanan",
        "name": "Santhosh Narayanan",
        "category": "Musician",
        "folder": "santhosh_narayanan",
        "commons_query": "Santhosh Narayanan",
    },
    {
        "id": "shreya_ghoshal",
        "name": "Shreya Ghoshal",
        "category": "Musician",
        "folder": "shreya_ghoshal",
        "commons_query": "Shreya Ghoshal",
    },
]

def fetch_commons_urls(query: str, max_count: int = 8) -> list[str]:
    urls = []
    try:
        url = (
            f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
            f"&gsrnamespace=6&gsrsearch={urllib.parse.quote(query)}&gsrlimit={max_count + 4}"
            "&prop=imageinfo&iiprop=url&iiurlwidth=800&format=json"
        )
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for _, p in pages.items():
                title = p.get("title", "").lower()
                if any(bad in title for bad in ["logo", "icon", "map", "signature", "graph", "diagram", "flag", "pdf"]):
                    continue
                ii = p.get("imageinfo", [])
                if ii:
                    thumb = ii[0].get("thumburl") or ii[0].get("url")
                    if thumb:
                        urls.append(thumb)
                if len(urls) >= max_count:
                    break
    except Exception as e:
        logger.warning("Commons fetch error for %s: %s", query, e)

    # Also Wikipedia infobox
    try:
        url2 = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(query)}&prop=pageimages&pithumbsize=800&format=json"
        req2 = urllib.request.Request(url2, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req2, timeout=10) as resp2:
            data2 = json.loads(resp2.read().decode("utf-8"))
            pages2 = data2.get("query", {}).get("pages", {})
            for _, p in pages2.items():
                thumb = p.get("thumbnail", {}).get("source")
                if thumb and thumb not in urls:
                    urls.insert(0, thumb)
    except Exception:
        pass
    return urls

def download_image(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            if len(content) < 4000:
                return False
            dest.write_bytes(content)
            return True
    except Exception:
        return False

def process_musician(m_info: dict) -> tuple[np.ndarray | None, str | None, int]:
    folder = DATASET_DIR / m_info["folder"]
    folder.mkdir(parents=True, exist_ok=True)

    urls = list(m_info.get("direct_urls", []))
    if m_info.get("commons_query"):
        urls.extend(fetch_commons_urls(m_info["commons_query"], max_count=8))

    logger.info("Downloading %d candidate images for %s...", len(urls), m_info["name"])
    for idx, u in enumerate(urls):
        dest = folder / f"{idx + 1}.jpg"
        if not dest.exists():
            download_image(u, dest)

    # Process all downloaded images in the folder
    images = [f for f in sorted(folder.iterdir()) if f.suffix.lower() in IMAGE_EXTS]
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

            # Score for long shot display
            faces = face_engine._app.get(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
            if faces:
                primary = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)[0]
                b = primary.bbox
                fw = b[2] - b[0]
                fh = b[3] - b[1]
                face_ratio = (fw * fh) / (w * h)
                aspect = h / w

                ratio_dist = abs(face_ratio - 0.10)
                aspect_bonus = min(aspect, 1.6) * 0.4
                close_penalty = (face_ratio - 0.25) * 20.0 if face_ratio > 0.25 else (0.03 - face_ratio) * 20.0 if face_ratio < 0.03 else 0.0
                score = -(ratio_dist * 4.0) + aspect_bonus + (float(getattr(primary, 'det_score', 0)) * 0.3) - close_penalty

                display_candidates.append((score, f"{folder.name}/{img_path.name}"))
        else:
            # Unusable image
            pass

    if not embeddings:
        logger.warning("No usable face embeddings found for %s", m_info["name"])
        return None, None, 0

    avg = np.mean(embeddings, axis=0)
    norm = np.linalg.norm(avg)
    if norm == 0:
        return None, None, 0
    averaged = avg / norm

    if display_candidates:
        display_candidates.sort(key=lambda x: x[0], reverse=True)
        best_display = display_candidates[0][1]
    else:
        best_display = f"{folder.name}/{images[0].name}"

    logger.info("✓ %s: %d/%d images used, display=%s", m_info["name"], len(embeddings), len(images), best_display)
    return averaged, best_display, len(embeddings)

def main():
    logger.info("=" * 60)
    logger.info("Adding Indian Musicians to CelebTwin Database")
    logger.info("=" * 60)

    face_engine.load()

    # Load existing celebrities.json
    with open(CELEBRITIES_JSON, "r", encoding="utf-8") as f:
        celebrities_json = json.load(f)
    existing_ids = {c["id"] for c in celebrities_json}

    # Load existing embeddings and metadata
    embeddings_list = list(np.load(EMBEDDINGS_NPY))
    metadata_list = list(np.load(METADATA_NPY, allow_pickle=True))
    existing_meta_names = {m["name"] for m in metadata_list}

    added_count = 0
    for m in MUSICIANS:
        if m["name"] in existing_meta_names:
            logger.info("Skipping %s (already in metadata)", m["name"])
            continue

        emb, display_img, num_used = process_musician(m)
        if emb is None:
            continue

        embeddings_list.append(emb)
        metadata_list.append({
            "name": m["name"],
            "category": m["category"],
            "image": display_img,
        })

        if m["id"] not in existing_ids:
            celebrities_json.append({
                "id": m["id"],
                "name": m["name"],
                "category": m["category"],
                "folder": m["folder"],
            })
            existing_ids.add(m["id"])

        added_count += 1
        logger.info("Successfully added %s to database! (%d photos averaged)", m["name"], num_used)

    # Save all updated files
    with open(CELEBRITIES_JSON, "w", encoding="utf-8") as f:
        json.dump(celebrities_json, f, indent=2)
    logger.info("Saved %d entries in %s", len(celebrities_json), CELEBRITIES_JSON)

    np.save(EMBEDDINGS_NPY, np.array(embeddings_list, dtype=np.float32))
    logger.info("Saved %d embeddings in %s", len(embeddings_list), EMBEDDINGS_NPY)

    np.save(METADATA_NPY, np.array(metadata_list, dtype=object))
    logger.info("Saved %d metadata entries in %s", len(metadata_list), METADATA_NPY)

    logger.info("Finished adding %d musicians! ✓ Total celebrities now: %d", added_count, len(metadata_list))

if __name__ == "__main__":
    main()
