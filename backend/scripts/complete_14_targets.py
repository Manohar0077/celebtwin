import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path
import cv2
import numpy as np

# Force unbuffered output
try:
    sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")
except Exception:
    pass

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.face_engine import face_engine
from app.config import CELEBRITIES_JSON, DATASET_DIR, EMBEDDINGS_NPY, METADATA_NPY

face_engine.load()

HEADERS = {
    "User-Agent": "CelebTwinBot/1.0 (https://github.com/manohar0077/celebtwin; contact@celebtwin.local) Python/3.11"
}

# Accurate wiki titles / search overrides for the remaining 14
TARGETS = [
    {"id": "radha_yadav", "name": "Radha Yadav", "category": "Cricketer", "queries": ["Radha Yadav cricketer", "Radha Yadav"]},
    {"id": "ruturaj_gaikwad", "name": "Ruturaj Gaikwad", "category": "Cricketer", "queries": ["Ruturaj Gaikwad", "Ruturaj Gaikwad CSK"]},
    {"id": "shreyas_iyer", "name": "Shreyas Iyer", "category": "Cricketer", "queries": ["Shreyas Iyer", "Shreyas Iyer cricketer"]},
    {"id": "varun_chakravarthy", "name": "Varun Chakravarthy", "category": "Cricketer", "queries": ["Varun Chakravarthy", "Varun Chakaravarthy"]},
    {"id": "ragini_prajwal", "name": "Ragini Prajwal", "category": "Actress", "queries": ["Ragini Chandran", "Ragini Prajwal"]},
    {"id": "darshana_rajendran", "name": "Darshana Rajendran", "category": "Actress", "queries": ["Darshana Rajendran"]},
    {"id": "rajisha_vijayan", "name": "Rajisha Vijayan", "category": "Actress", "queries": ["Rajisha Vijayan"]},
    {"id": "saniya_iyappan", "name": "Saniya Iyappan", "category": "Actress", "queries": ["Saniya Iyappan", "Saniya Iyyappan"]},
    {"id": "lukman_avaran", "name": "Lukman Avaran", "category": "Actor", "queries": ["Lukman Avaran", "Lukman Lukman"]},
    {"id": "pranav_mohanlal", "name": "Pranav Mohanlal", "category": "Actor", "queries": ["Pranav Mohanlal"]},
    {"id": "gautam_karthik", "name": "Gautham Karthik", "category": "Actor", "queries": ["Gautham Karthik"]},
    {"id": "kalaiyarasan", "name": "Kalaiyarasan", "category": "Actor", "queries": ["Kalaiyarasan", "Kalaiyarasan Harikrishnan"]},
    {"id": "manikandan", "name": "K. Manikandan", "category": "Actor", "queries": ["K. Manikandan", "Manikandan actor"]},
    {"id": "santosh_prathap", "name": "Santhosh Prathap", "category": "Actor", "queries": ["Santhosh Prathap", "Santhosh Prathap actor"]},
]

def search_wikimedia_images(query: str, limit: int = 15) -> list[str]:
    urls = []
    # 1. Wikipedia opensearch to find exact article title
    try:
        url_search = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(query)}&limit=3&namespace=0&format=json"
        req = urllib.request.Request(url_search, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data and len(data) > 1 and data[1]:
                exact_title = data[1][0]
                # Fetch page image
                url_img = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(exact_title)}&prop=pageimages|images&pithumbsize=1000&format=json"
                req_img = urllib.request.Request(url_img, headers=HEADERS)
                with urllib.request.urlopen(req_img, timeout=10) as r:
                    d = json.loads(r.read().decode())
                    for _, p in d.get("query", {}).get("pages", {}).items():
                        t = p.get("thumbnail", {}).get("source")
                        if t and t not in urls:
                            urls.append(t)
                        for im_info in p.get("images", []):
                            ititle = im_info.get("title", "")
                            if any(bad in ititle.lower() for bad in ["logo", "icon", "flag", "svg", "sign", "map"]):
                                continue
                            url_info = f"https://commons.wikimedia.org/w/api.php?action=query&titles={urllib.parse.quote(ititle)}&prop=imageinfo&iiprop=url&iiurlwidth=800&format=json"
                            req_info = urllib.request.Request(url_info, headers=HEADERS)
                            try:
                                with urllib.request.urlopen(req_info, timeout=8) as r_info:
                                    d_info = json.loads(r_info.read().decode())
                                    for _, pi in d_info.get("query", {}).get("pages", {}).items():
                                        ii = pi.get("imageinfo", [])
                                        if ii:
                                            tu = ii[0].get("thumburl") or ii[0].get("url")
                                            if tu and tu not in urls:
                                                urls.append(tu)
                            except Exception:
                                pass
    except Exception as e:
        pass

    # 2. Wikimedia commons direct search
    try:
        url_comm = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrsearch={urllib.parse.quote(query)}&gsrlimit={limit}&prop=imageinfo&iiprop=url&iiurlwidth=800&format=json"
        req_comm = urllib.request.Request(url_comm, headers=HEADERS)
        with urllib.request.urlopen(req_comm, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            for _, p in data.get("query", {}).get("pages", {}).items():
                title = p.get("title", "").lower()
                if any(bad in title for bad in ["logo", "icon", "signature", "flag", "sound", "audio", "graph", "stub", "svg", "poster", "stadium"]):
                    continue
                ii = p.get("imageinfo", [])
                if ii:
                    t = ii[0].get("thumburl") or ii[0].get("url")
                    if t and t not in urls:
                        urls.append(t)
    except Exception:
        pass

    return urls

# Load DB
with open(CELEBRITIES_JSON, 'r', encoding='utf-8') as f:
    celeb_json = json.load(f)
emb_list = list(np.load(EMBEDDINGS_NPY))
meta_list = list(np.load(METADATA_NPY, allow_pickle=True))

existing_ids = {c["id"] for c in celeb_json}
added = 0
for t in TARGETS:
    cid = t["id"]
    cname = t["name"]
    if cid in existing_ids:
        continue
    folder = DATASET_DIR / cid
    folder.mkdir(parents=True, exist_ok=True)
    
    all_urls = []
    for q in t["queries"]:
        all_urls.extend(search_wikimedia_images(q))
        if len(all_urls) >= 10:
            break

    print(f"Target: {cname} -> found {len(all_urls)} URLs")
    valid_photos = []
    embeddings = []
    display_candidates = []

    for idx, u in enumerate(all_urls):
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
            faces = face_engine._app.get(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
            if len(faces) != 1:
                continue
            f = faces[0]
            b = f.bbox
            fw, fh = b[2] - b[0], b[3] - b[1]
            if f.det_score < 0.65 or fw < 45 or fh < 45:
                continue
            emb = f.embedding
            if emb is None:
                continue
            norm = np.linalg.norm(emb)
            if norm == 0:
                continue
            save_path = folder / f"img_{len(valid_photos) + 1}.jpg"
            save_path.write_bytes(content)
            valid_photos.append(save_path)
            embeddings.append(emb / norm)
            
            # Long shot score
            face_ratio = (fw * fh) / (w * h)
            aspect = h / w
            ratio_dist = abs(face_ratio - 0.10)
            aspect_bonus = min(aspect, 1.6) * 0.4
            score = -(ratio_dist * 4.0) + aspect_bonus + (f.det_score * 0.3)
            display_candidates.append((score, f"{cid}/{save_path.name}"))
            if len(valid_photos) >= 4:
                break
        except Exception:
            continue

    if valid_photos:
        avg = np.mean(embeddings, axis=0)
        composite_emb = avg / np.linalg.norm(avg)
        display_candidates.sort(key=lambda x: x[0], reverse=True)
        best_display = display_candidates[0][1]

        emb_list.append(composite_emb)
        meta_list.append({"name": cname, "category": t["category"], "image": best_display})
        celeb_json.append({"id": cid, "name": cname, "category": t["category"], "folder": cid})
        added += 1
        with open(CELEBRITIES_JSON, 'w', encoding='utf-8') as f:
            json.dump(celeb_json, f, indent=2)
        np.save(EMBEDDINGS_NPY, np.array(emb_list, dtype=np.float32))
        np.save(METADATA_NPY, np.array(meta_list, dtype=object))
        print(f"  [OK] Added {cname} ({len(valid_photos)} photos, display={best_display}) [Total in DB: {len(celeb_json)}]")
    else:
        print(f"  [X] Could not get single face photo for {cname}")

if added > 0:
    with open(CELEBRITIES_JSON, 'w', encoding='utf-8') as f:
        json.dump(celeb_json, f, indent=2)
    np.save(EMBEDDINGS_NPY, np.array(emb_list, dtype=np.float32))
    np.save(METADATA_NPY, np.array(meta_list, dtype=object))
    print(f"\nSUCCESS: Added {added} more celebrities! Total in DB: {len(celeb_json)}")
