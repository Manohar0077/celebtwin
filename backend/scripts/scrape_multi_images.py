"""
scrape_multi_images.py

Scrapes MULTIPLE portrait photos (3 to 5 images per celebrity) for 100+ top Indian celebrities:
- Cricket (Men & Women)
- Bollywood (Actors & Actresses)
- South Indian Cinema (Tamil, Telugu, Malayalam, Kannada)

For each celebrity:
1. Searches Wikimedia Commons for portrait photos (File: namespace)
2. Also fetches Wikipedia primary infobox portrait
3. Downloads up to 4-5 high-resolution images per celebrity (1.jpg, 2.jpg, 3.jpg, 4.jpg)
4. Uses InsightFace to detect faces in each photo
5. Averages all valid face embeddings and L2-normalizes (multi-angle robust representation)
6. Updates celebrities.json, embeddings.npy, and metadata.npy
"""
import sys
import json
import time
import logging
import urllib.request
import urllib.parse
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import (
    CELEBRITIES_JSON, EMBEDDINGS_NPY, METADATA_NPY, DATASET_DIR
)
from app.face_engine import face_engine

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

USER_AGENT = "CelebTwinApp/3.0 (academic/research; contact@celebtwin.local) Python-urllib"

# 105+ Top Celebrities across India
CELEBRITIES = [
    # ── 🏏 CRICKET (MEN) ──────────────────────────────────────────
    {"id": "virat_kohli",       "name": "Virat Kohli",        "category": "Cricketer", "search": "Virat Kohli"},
    {"id": "ms_dhoni",          "name": "MS Dhoni",           "category": "Cricketer", "search": "MS Dhoni"},
    {"id": "rohit_sharma",      "name": "Rohit Sharma",       "category": "Cricketer", "search": "Rohit Sharma cricketer"},
    {"id": "sachin_tendulkar",  "name": "Sachin Tendulkar",   "category": "Cricketer", "search": "Sachin Tendulkar"},
    {"id": "hardik_pandya",     "name": "Hardik Pandya",      "category": "Cricketer", "search": "Hardik Pandya"},
    {"id": "shubman_gill",      "name": "Shubman Gill",       "category": "Cricketer", "search": "Shubman Gill"},
    {"id": "jasprit_bumrah",    "name": "Jasprit Bumrah",     "category": "Cricketer", "search": "Jasprit Bumrah"},
    {"id": "ravindra_jadeja",   "name": "Ravindra Jadeja",    "category": "Cricketer", "search": "Ravindra Jadeja"},
    {"id": "rishabh_pant",      "name": "Rishabh Pant",       "category": "Cricketer", "search": "Rishabh Pant"},
    {"id": "shikhar_dhawan",    "name": "Shikhar Dhawan",     "category": "Cricketer", "search": "Shikhar Dhawan"},
    {"id": "yuvraj_singh",      "name": "Yuvraj Singh",       "category": "Cricketer", "search": "Yuvraj Singh"},
    {"id": "mohammed_shami",    "name": "Mohammed Shami",     "category": "Cricketer", "search": "Mohammed Shami"},
    {"id": "r_ashwin",          "name": "Ravichandran Ashwin","category": "Cricketer", "search": "Ravichandran Ashwin"},
    {"id": "sanju_samson",      "name": "Sanju Samson",       "category": "Cricketer", "search": "Sanju Samson"},
    {"id": "suryakumar_yadav",  "name": "Suryakumar Yadav",   "category": "Cricketer", "search": "Suryakumar Yadav"},
    {"id": "ishan_kishan",      "name": "Ishan Kishan",       "category": "Cricketer", "search": "Ishan Kishan"},
    {"id": "mohammed_siraj",    "name": "Mohammed Siraj",     "category": "Cricketer", "search": "Mohammed Siraj cricketer"},
    {"id": "sourav_ganguly",    "name": "Sourav Ganguly",     "category": "Cricketer", "search": "Sourav Ganguly"},
    {"id": "anil_kumble",       "name": "Anil Kumble",        "category": "Cricketer", "search": "Anil Kumble"},
    {"id": "virender_sehwag",   "name": "Virender Sehwag",    "category": "Cricketer", "search": "Virender Sehwag"},

    # ── 🏏 CRICKET (WOMEN) ────────────────────────────────────────
    {"id": "smriti_mandhana",   "name": "Smriti Mandhana",    "category": "Cricketer", "search": "Smriti Mandhana"},
    {"id": "harmanpreet_kaur",  "name": "Harmanpreet Kaur",   "category": "Cricketer", "search": "Harmanpreet Kaur"},
    {"id": "mithali_raj",       "name": "Mithali Raj",        "category": "Cricketer", "search": "Mithali Raj"},
    {"id": "jemimah_rodrigues", "name": "Jemimah Rodrigues",  "category": "Cricketer", "search": "Jemimah Rodrigues"},
    {"id": "shafali_verma",     "name": "Shafali Verma",      "category": "Cricketer", "search": "Shafali Verma"},
    {"id": "deepti_sharma",     "name": "Deepti Sharma",      "category": "Cricketer", "search": "Deepti Sharma cricketer"},
    {"id": "renuka_singh",      "name": "Renuka Singh Thakur","category": "Cricketer", "search": "Renuka Singh cricketer"},
    {"id": "richa_ghosh",       "name": "Richa Ghosh",        "category": "Cricketer", "search": "Richa Ghosh"},
    {"id": "pooja_vastrakar",   "name": "Pooja Vastrakar",    "category": "Cricketer", "search": "Pooja Vastrakar"},
    {"id": "harleen_deol",      "name": "Harleen Deol",       "category": "Cricketer", "search": "Harleen Deol"},

    # ── 🎬 BOLLYWOOD (ACTORS) ─────────────────────────────────────
    {"id": "shah_rukh_khan",    "name": "Shah Rukh Khan",     "category": "Actor",     "search": "Shah Rukh Khan"},
    {"id": "salman_khan",       "name": "Salman Khan",        "category": "Actor",     "search": "Salman Khan actor"},
    {"id": "aamir_khan",        "name": "Aamir Khan",         "category": "Actor",     "search": "Aamir Khan"},
    {"id": "hrithik_roshan",    "name": "Hrithik Roshan",     "category": "Actor",     "search": "Hrithik Roshan"},
    {"id": "ranbir_kapoor",     "name": "Ranbir Kapoor",      "category": "Actor",     "search": "Ranbir Kapoor"},
    {"id": "ranveer_singh",     "name": "Ranveer Singh",      "category": "Actor",     "search": "Ranveer Singh"},
    {"id": "akshay_kumar",      "name": "Akshay Kumar",       "category": "Actor",     "search": "Akshay Kumar"},
    {"id": "ajay_devgn",        "name": "Ajay Devgn",         "category": "Actor",     "search": "Ajay Devgn"},
    {"id": "amitabh_bachchan",  "name": "Amitabh Bachchan",   "category": "Actor",     "search": "Amitabh Bachchan"},
    {"id": "shahid_kapoor",     "name": "Shahid Kapoor",      "category": "Actor",     "search": "Shahid Kapoor"},
    {"id": "kartik_aaryan",     "name": "Kartik Aaryan",      "category": "Actor",     "search": "Kartik Aaryan"},
    {"id": "vicky_kaushal",     "name": "Vicky Kaushal",      "category": "Actor",     "search": "Vicky Kaushal"},
    {"id": "sidharth_malhotra", "name": "Sidharth Malhotra",  "category": "Actor",     "search": "Sidharth Malhotra"},
    {"id": "ayushmann_khurrana","name": "Ayushmann Khurrana", "category": "Actor",     "search": "Ayushmann Khurrana"},
    {"id": "john_abraham",      "name": "John Abraham",       "category": "Actor",     "search": "John Abraham actor"},
    {"id": "saif_ali_khan",     "name": "Saif Ali Khan",      "category": "Actor",     "search": "Saif Ali Khan"},
    {"id": "tiger_shroff",      "name": "Tiger Shroff",       "category": "Actor",     "search": "Tiger Shroff"},
    {"id": "anil_kapoor",       "name": "Anil Kapoor",        "category": "Actor",     "search": "Anil Kapoor"},
    {"id": "sanjay_dutt",       "name": "Sanjay Dutt",        "category": "Actor",     "search": "Sanjay Dutt"},
    {"id": "nawazuddin_siddiqui","name":"Nawazuddin Siddiqui","category":"Actor",     "search": "Nawazuddin Siddiqui"},
    {"id": "pankaj_tripathi",   "name": "Pankaj Tripathi",    "category": "Actor",     "search": "Pankaj Tripathi"},
    {"id": "boman_irani",       "name": "Boman Irani",        "category": "Actor",     "search": "Boman Irani"},
    {"id": "rajkummar_rao",     "name": "Rajkummar Rao",      "category": "Actor",     "search": "Rajkummar Rao"},

    # ── 🎬 BOLLYWOOD (ACTRESSES) ───────────────────────────────────
    {"id": "deepika_padukone",  "name": "Deepika Padukone",   "category": "Actress",   "search": "Deepika Padukone"},
    {"id": "alia_bhatt",        "name": "Alia Bhatt",         "category": "Actress",   "search": "Alia Bhatt"},
    {"id": "katrina_kaif",      "name": "Katrina Kaif",       "category": "Actress",   "search": "Katrina Kaif"},
    {"id": "priyanka_chopra",   "name": "Priyanka Chopra",    "category": "Actress",   "search": "Priyanka Chopra"},
    {"id": "kareena_kapoor",    "name": "Kareena Kapoor",     "category": "Actress",   "search": "Kareena Kapoor"},
    {"id": "anushka_sharma",    "name": "Anushka Sharma",     "category": "Actress",   "search": "Anushka Sharma"},
    {"id": "shraddha_kapoor",   "name": "Shraddha Kapoor",    "category": "Actress",   "search": "Shraddha Kapoor"},
    {"id": "kiara_advani",      "name": "Kiara Advani",       "category": "Actress",   "search": "Kiara Advani"},
    {"id": "kriti_sanon",       "name": "Kriti Sanon",        "category": "Actress",   "search": "Kriti Sanon"},
    {"id": "sara_ali_khan",     "name": "Sara Ali Khan",      "category": "Actress",   "search": "Sara Ali Khan"},
    {"id": "janhvi_kapoor",     "name": "Janhvi Kapoor",      "category": "Actress",   "search": "Janhvi Kapoor"},
    {"id": "ananya_panday",     "name": "Ananya Panday",      "category": "Actress",   "search": "Ananya Panday"},
    {"id": "aishwarya_rai",     "name": "Aishwarya Rai",      "category": "Actress",   "search": "Aishwarya Rai"},
    {"id": "madhuri_dixit",     "name": "Madhuri Dixit",      "category": "Actress",   "search": "Madhuri Dixit"},
    {"id": "kajol",             "name": "Kajol",              "category": "Actress",   "search": "Kajol"},
    {"id": "vidya_balan",       "name": "Vidya Balan",        "category": "Actress",   "search": "Vidya Balan"},
    {"id": "disha_patani",      "name": "Disha Patani",       "category": "Actress",   "search": "Disha Patani"},
    {"id": "jacqueline_fernandez","name":"Jacqueline Fernandez","category":"Actress",  "search": "Jacqueline Fernandez"},
    {"id": "taapsee_pannu",     "name": "Taapsee Pannu",      "category": "Actress",   "search": "Taapsee Pannu"},
    {"id": "bhumi_pednekar",    "name": "Bhumi Pednekar",     "category": "Actress",   "search": "Bhumi Pednekar"},
    {"id": "triptii_dimri",     "name": "Triptii Dimri",      "category": "Actress",   "search": "Triptii Dimri"},
    {"id": "tabu",              "name": "Tabu",               "category": "Actress",   "search": "Tabu actress"},

    # ── 🌟 SOUTH INDIAN (ACTORS) ──────────────────────────────────
    {"id": "allu_arjun",        "name": "Allu Arjun",         "category": "Actor",     "search": "Allu Arjun"},
    {"id": "jr_ntr",            "name": "N. T. Rama Rao Jr.", "category": "Actor",     "search": "NTR Jr"},
    {"id": "yash",              "name": "Yash",               "category": "Actor",     "search": "Yash actor KGF"},
    {"id": "kamal_haasan",      "name": "Kamal Haasan",       "category": "Actor",     "search": "Kamal Haasan"},
    {"id": "vikram",            "name": "Chiyaan Vikram",     "category": "Actor",     "search": "Vikram actor"},
    {"id": "vijay_sethupathi",  "name": "Vijay Sethupathi",   "category": "Actor",     "search": "Vijay Sethupathi"},
    {"id": "silambarasan",      "name": "Silambarasan",       "category": "Actor",     "search": "Silambarasan"},
    {"id": "mohanlal",          "name": "Mohanlal",           "category": "Actor",     "search": "Mohanlal"},
    {"id": "mammootty",         "name": "Mammootty",          "category": "Actor",     "search": "Mammootty"},
    {"id": "dulquer_salmaan",   "name": "Dulquer Salmaan",    "category": "Actor",     "search": "Dulquer Salmaan"},
    {"id": "fahadh_faasil",     "name": "Fahadh Faasil",      "category": "Actor",     "search": "Fahadh Faasil"},
    {"id": "tovino_thomas",     "name": "Tovino Thomas",      "category": "Actor",     "search": "Tovino Thomas"},
    {"id": "prithviraj_sukumaran","name":"Prithviraj Sukumaran","category":"Actor",    "search": "Prithviraj Sukumaran"},
    {"id": "rishab_shetty",     "name": "Rishab Shetty",      "category": "Actor",     "search": "Rishab Shetty"},
    {"id": "rakshit_shetty",    "name": "Rakshit Shetty",     "category": "Actor",     "search": "Rakshit Shetty"},
    {"id": "shiva_rajkumar",    "name": "Shiva Rajkumar",     "category": "Actor",     "search": "Shiva Rajkumar"},
    {"id": "puneeth_rajkumar",  "name": "Puneeth Rajkumar",   "category": "Actor",     "search": "Puneeth Rajkumar"},
    {"id": "vijay_deverakonda", "name": "Vijay Deverakonda",  "category": "Actor",     "search": "Vijay Deverakonda"},
    {"id": "nani",              "name": "Nani",               "category": "Actor",     "search": "Nani actor"},
    {"id": "naga_chaitanya",    "name": "Naga Chaitanya",     "category": "Actor",     "search": "Naga Chaitanya"},
    {"id": "chiranjeevi",       "name": "Chiranjeevi",        "category": "Actor",     "search": "Chiranjeevi"},
    {"id": "nagarjuna",         "name": "Akkineni Nagarjuna", "category": "Actor",     "search": "Nagarjuna actor"},
    {"id": "arya",              "name": "Arya",               "category": "Actor",     "search": "Arya actor"},
    {"id": "jayam_ravi",        "name": "Jayam Ravi",         "category": "Actor",     "search": "Jayam Ravi"},
    {"id": "siddharth",         "name": "Siddharth",          "category": "Actor",     "search": "Siddharth actor"},

    # ── 🌟 SOUTH INDIAN (ACTRESSES) ────────────────────────────────
    {"id": "rashmika_mandanna", "name": "Rashmika Mandanna",  "category": "Actress",   "search": "Rashmika Mandanna"},
    {"id": "pooja_hegde",       "name": "Pooja Hegde",        "category": "Actress",   "search": "Pooja Hegde"},
    {"id": "kajal_aggarwal",    "name": "Kajal Aggarwal",     "category": "Actress",   "search": "Kajal Aggarwal"},
    {"id": "tamannaah_bhatia",  "name": "Tamannaah Bhatia",   "category": "Actress",   "search": "Tamannaah Bhatia"},
    {"id": "raashii_khanna",    "name": "Raashii Khanna",     "category": "Actress",   "search": "Raashii Khanna"},
    {"id": "krithi_shetty",     "name": "Krithi Shetty",      "category": "Actress",   "search": "Krithi Shetty"},
    {"id": "mrunal_thakur",     "name": "Mrunal Thakur",      "category": "Actress",   "search": "Mrunal Thakur"},
    {"id": "kalyani_priyadarshan","name":"Kalyani Priyadarshan","category":"Actress", "search": "Kalyani Priyadarshan"},
    {"id": "parvathy_thiruvothu","name":"Parvathy Thiruvothu","category":"Actress",   "search": "Parvathy Thiruvothu"},
    {"id": "manju_warrier",     "name": "Manju Warrier",      "category": "Actress",   "search": "Manju Warrier"},
    {"id": "srinidhi_shetty",   "name": "Srinidhi Shetty",    "category": "Actress",   "search": "Srinidhi Shetty"},
    {"id": "rukmini_vasanth",   "name": "Rukmini Vasanth",    "category": "Actress",   "search": "Rukmini Vasanth"},
    {"id": "shriya_saran",      "name": "Shriya Saran",       "category": "Actress",   "search": "Shriya Saran"},
    {"id": "hansika_motwani",   "name": "Hansika Motwani",    "category": "Actress",   "search": "Hansika Motwani"},
    {"id": "priya_bhavani_shankar","name":"Priya Bhavani Shankar","category":"Actress","search":"Priya Bhavani Shankar"},
    {"id": "aishwarya_rajesh",  "name": "Aishwarya Rajesh",   "category": "Actress",   "search": "Aishwarya Rajesh"},
]


def fetch_image_urls(query_name: str, max_count: int = 5) -> list[str]:
    """Search Wikimedia Commons for multiple photos of the celebrity."""
    urls = []
    try:
        url = (
            f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
            f"&gsrnamespace=6&gsrsearch={urllib.parse.quote(query_name)}&gsrlimit={max_count + 3}"
            "&prop=imageinfo&iiprop=url&iiurlwidth=700&format=json"
        )
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for _, p in pages.items():
                title = p.get("title", "").lower()
                # filter out maps, logos, icons, audio, pdf, graphs
                if any(bad in title for bad in ["logo", "icon", "map", "signature", "graph", "diagram", "flag"]):
                    continue
                ii_list = p.get("imageinfo", [])
                if ii_list:
                    thumb = ii_list[0].get("thumburl") or ii_list[0].get("url")
                    if thumb:
                        urls.append(thumb)
                if len(urls) >= max_count:
                    break
    except Exception as exc:
        logger.warning("Error fetching images for %s: %s", query_name, exc)
    return urls


def download_file(url: str, dest: Path) -> bool:
    """Download single image file."""
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


def main():
    logger.info("=" * 65)
    logger.info("Multi-Image Indian Celebrity Dataset Scraper (100+ Celebrities)")
    logger.info("=" * 65)

    with open(CELEBRITIES_JSON, "r", encoding="utf-8") as f:
        existing_celebs = json.load(f)
    existing_ids = {c["id"] for c in existing_celebs}

    existing_embeddings = []
    existing_metadata = []
    if EMBEDDINGS_NPY.exists() and METADATA_NPY.exists():
        existing_embeddings = list(np.load(str(EMBEDDINGS_NPY)))
        existing_metadata = list(np.load(str(METADATA_NPY), allow_pickle=True))
        logger.info("Current database entries: %d", len(existing_embeddings))

    candidates = [c for c in CELEBRITIES if c["id"] not in existing_ids]
    logger.info("Found %d new candidate celebrities to process with multiple photos.", len(candidates))

    if not candidates:
        logger.info("All celebrities are already processed!")
        return

    logger.info("Loading InsightFace FaceEngine...")
    face_engine.load()
    logger.info("FaceEngine ready.\n")

    added_celebs = []
    new_embeddings = []
    new_metadata = []

    for idx, celeb in enumerate(candidates, 1):
        cid = celeb["id"]
        cname = celeb["name"]
        cat = celeb["category"]
        search_query = celeb["search"]

        celeb_dir = DATASET_DIR / cid
        celeb_dir.mkdir(parents=True, exist_ok=True)

        logger.info("[%d/%d] Scraping multi-photos for: %s (%s)...", idx, len(candidates), cname, cat)

        # 1. Fetch up to 5 image URLs
        urls = fetch_image_urls(search_query, max_count=5)
        if not urls:
            # Fallback search with just the name
            urls = fetch_image_urls(cname, max_count=5)

        time.sleep(0.3)  # courteous request pacing

        # 2. Download each image and collect valid face embeddings
        valid_embeddings = []
        best_display_img = None
        best_quality = -1.0

        for img_idx, url in enumerate(urls, 1):
            img_path = celeb_dir / f"{img_idx}.jpg"
            if not img_path.exists() or img_path.stat().st_size < 4000:
                if not download_file(url, img_path):
                    continue
                time.sleep(0.1)

            # Detect face with strict clarity, resolution & prominence checks
            emb, quality = face_engine.get_clear_face_embedding(str(img_path), min_dim=85, min_det_score=0.70)
            if emb is not None:
                valid_embeddings.append(emb)
                if quality > best_quality:
                    best_quality = quality
                    best_display_img = f"{cid}/{img_idx}.jpg"

        if not valid_embeddings:
            logger.warning("  ✗ No usable faces found for %s across %d photos", cname, len(urls))
            continue

        # 3. Average embeddings and L2-normalize
        avg_emb = np.mean(valid_embeddings, axis=0)
        norm = np.linalg.norm(avg_emb)
        if norm == 0:
            continue
        final_embedding = avg_emb / norm

        rel_display = best_display_img or f"{cid}/1.jpg"

        new_embeddings.append(final_embedding)
        new_metadata.append({
            "name": cname,
            "category": cat,
            "image": rel_display,
        })
        added_celebs.append({
            "id": cid,
            "name": cname,
            "category": cat,
            "folder": cid,
        })

        logger.info(
            "  ✓ Added %s! (%d photos averaged, display=%s)",
            cname, len(valid_embeddings), rel_display
        )

    logger.info("\n" + "=" * 65)
    logger.info("Scraped and processed %d new celebrities with multi-image embeddings!", len(added_celebs))

    if added_celebs:
        all_celebs = existing_celebs + added_celebs
        all_embeddings = existing_embeddings + new_embeddings
        all_metadata = existing_metadata + new_metadata

        emb_arr = np.array(all_embeddings, dtype=np.float32)
        meta_arr = np.array(all_metadata, dtype=object)

        np.save(str(EMBEDDINGS_NPY), emb_arr)
        np.save(str(METADATA_NPY), meta_arr)
        with open(CELEBRITIES_JSON, "w", encoding="utf-8") as f:
            json.dump(all_celebs, f, indent=2)

        logger.info("TOTAL Database Size: %d celebrities", len(all_celebs))
        logger.info("Saved to: %s & %s", EMBEDDINGS_NPY, CELEBRITIES_JSON)
    logger.info("Done ✓")


if __name__ == "__main__":
    main()
