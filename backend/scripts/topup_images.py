"""
topup_images.py
Downloads additional portrait images for low-coverage celebrities
and regenerates the embedding database.
"""
import sys, json, time, logging, urllib.request, urllib.parse
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import CELEBRITIES_JSON, EMBEDDINGS_NPY, METADATA_NPY, DATASET_DIR
from app.face_engine import face_engine

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

USER_AGENT = "CelebTwinApp/3.0 (academic/research) Python-urllib"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
MIN_DIM = 65
MIN_SCORE = 0.70
TARGET_USABLE = 5  # aim for 5 usable images per celebrity

# 40 celebrities identified as needing more images
LOW_COVERAGE = {
    "virat_kohli":      "Virat Kohli portrait",
    "chiranjeevi":      "Chiranjeevi actor",
    "fahadh_faasil":    "Fahadh Faasil actor",
    "sanju_samson":     "Sanju Samson cricketer",
    "boman_irani":      "Boman Irani actor",
    "vikram":           "Vikram Chiyaan actor",
    "janhvi_kapoor":    "Janhvi Kapoor actress",
    "jayam_ravi":       "Jayam Ravi actor",
    "kalyani_priyadarshan": "Kalyani Priyadarshan actress",
    "pankaj_tripathi":  "Pankaj Tripathi actor",
    "rakshit_shetty":   "Rakshit Shetty actor",
    "r_ashwin":         "Ravichandran Ashwin cricketer",
    "shikhar_dhawan":   "Shikhar Dhawan cricketer",
    "yuvraj_singh":     "Yuvraj Singh cricketer",
    "aishwarya_rajesh": "Aishwarya Rajesh actress",
    "nagarjuna":        "Nagarjuna actor",
    "bhumi_pednekar":   "Bhumi Pednekar actress",
    "hardik_pandya":    "Hardik Pandya cricketer",
    "kamal_haasan":     "Kamal Haasan actor",
    "katrina_kaif":     "Katrina Kaif actress",
    "kiara_advani":     "Kiara Advani actress",
    "manju_warrier":    "Manju Warrier actress",
    "parvathy_thiruvothu": "Parvathy actress",
    "pooja_hegde":      "Pooja Hegde actress",
    "puneeth_rajkumar": "Puneeth Rajkumar actor",
    "raashii_khanna":   "Raashii Khanna actress",
    "rashmika_mandanna":"Rashmika Mandanna actress",
    "ravindra_jadeja":  "Ravindra Jadeja cricketer",
    "rishab_shetty":    "Rishab Shetty actor",
    "rishabh_pant":     "Rishabh Pant cricketer",
    "rohit_sharma":     "Rohit Sharma cricketer",
    "rukmini_vasanth":  "Rukmini Vasanth actress",
    "sachin_tendulkar": "Sachin Tendulkar cricketer",
    "shiva_rajkumar":   "Shiva Rajkumar actor",
    "siddharth":        "Siddharth actor",
    "silambarasan":     "Silambarasan actor",
    "taapsee_pannu":    "Taapsee Pannu actress",
    "tovino_thomas":    "Tovino Thomas actor",
    "vijay_sethupathi": "Vijay Sethupathi actor",
    "yash":             "Yash actor KGF",
}

def count_usable(folder_path):
    imgs = [f for f in folder_path.iterdir() if f.suffix.lower() in IMAGE_EXTS]
    count = 0
    for img in imgs:
        import cv2
        im = cv2.imread(str(img))
        if im is None: continue
        faces = face_engine._app.get(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
        if len(faces) == 0: continue
        if len(faces) > 1:
            scored = sorted([(f, (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1])) for f in faces], key=lambda x:x[1], reverse=True)
            if scored[0][1] < 2.5 * scored[1][1]: continue
            face = scored[0][0]
        else: face = faces[0]
        score = float(getattr(face, "det_score", 0.0))
        x1,y1,x2,y2 = face.bbox
        if score >= MIN_SCORE and int(x2-x1) >= MIN_DIM and int(y2-y1) >= MIN_DIM:
            count += 1
    return count

def next_img_num(folder_path):
    existing = [f for f in folder_path.iterdir() if f.suffix.lower() in IMAGE_EXTS]
    nums = []
    for f in existing:
        try: nums.append(int(f.stem))
        except: pass
    return max(nums) + 1 if nums else 1

def fetch_urls(query, max_count=8):
    urls = []
    try:
        url = (
            f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
            f"&gsrnamespace=6&gsrsearch={urllib.parse.quote(query)}&gsrlimit={max_count+5}"
            "&prop=imageinfo&iiprop=url&iiurlwidth=800&format=json"
        )
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for _, p in pages.items():
                title = p.get("title", "").lower()
                if any(bad in title for bad in ["logo", "icon", "map", "signature", "graph", "diagram", "flag", "award", "trophy", "stadium"]): continue
                ii = p.get("imageinfo", [])
                if ii:
                    thumb = ii[0].get("thumburl") or ii[0].get("url")
                    if thumb: urls.append(thumb)
                if len(urls) >= max_count: break
    except Exception as e:
        logger.warning("Fetch error: %s", e)
    # Also try Wikipedia infobox
    try:
        name = query.split(" portrait")[0].split(" actress")[0].split(" actor")[0].split(" cricketer")[0]
        url2 = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(name)}&prop=pageimages&pithumbsize=700&format=json"
        req2 = urllib.request.Request(url2, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req2, timeout=10) as resp2:
            data2 = json.loads(resp2.read().decode("utf-8"))
            pages2 = data2.get("query", {}).get("pages", {})
            for _, p in pages2.items():
                thumb = p.get("thumbnail", {}).get("source")
                if thumb and thumb not in urls:
                    urls.insert(0, thumb)  # Wikipedia infobox first - usually best
    except: pass
    return urls

def download(url, dest):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            if len(content) < 5000: return False
            dest.write_bytes(content)
            return True
    except: return False

print("=" * 60)
print("CelebTwin — Targeted Image Top-Up for Low-Coverage Celebrities")
print("=" * 60)
face_engine.load()
print("Model loaded.\n")

improved = 0
for folder_id, search_query in LOW_COVERAGE.items():
    folder_path = DATASET_DIR / folder_id
    folder_path.mkdir(parents=True, exist_ok=True)
    
    current_usable = count_usable(folder_path)
    if current_usable >= TARGET_USABLE:
        print(f"  SKIP {folder_id}: already {current_usable} usable")
        continue
    
    needed = TARGET_USABLE - current_usable
    print(f"\n[{folder_id}] currently {current_usable} usable, need {needed} more...")
    
    urls = fetch_urls(search_query, max_count=10)
    time.sleep(0.4)
    
    added = 0
    for url in urls:
        if current_usable + added >= TARGET_USABLE:
            break
        img_num = next_img_num(folder_path)
        img_path = folder_path / f"{img_num}.jpg"
        if not download(url, img_path):
            continue
        time.sleep(0.15)
        # Check if this new image has a usable face
        import cv2
        im = cv2.imread(str(img_path))
        if im is None: img_path.unlink(missing_ok=True); continue
        emb, quality = face_engine.get_clear_face_embedding(str(img_path), min_dim=MIN_DIM, min_det_score=MIN_SCORE)
        if emb is not None:
            added += 1
            print(f"  + Downloaded {img_path.name} (quality={quality:.1f})")
        else:
            img_path.unlink(missing_ok=True)
    
    final_usable = count_usable(folder_path)
    print(f"  -> {folder_id}: {current_usable} -> {final_usable} usable images")
    if final_usable > current_usable:
        improved += 1

print(f"\nImproved {improved} celebrities. Now regenerating embeddings...")
