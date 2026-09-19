"""
scrape_celebrities.py

Scrapes portrait images for 100+ top Indian celebrities across:
- Cricket (Men & Women)
- Bollywood (Actors & Actresses)
- South Indian Cinema (Tamil, Telugu, Malayalam, Kannada)

Uses Wikipedia / Wikimedia Commons API with batched queries, detects faces
with InsightFace, extracts 512-d L2-normalized embeddings, and merges them
into the database.
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

# Curated list of 115+ famous Indian celebrities
CELEBRITIES_TO_ADD = [
    # ── 🏏 CRICKET (MEN) ──────────────────────────────────────────
    {"id": "virat_kohli",       "name": "Virat Kohli",        "category": "Cricketer", "wiki": "Virat_Kohli"},
    {"id": "ms_dhoni",          "name": "MS Dhoni",           "category": "Cricketer", "wiki": "MS_Dhoni"},
    {"id": "rohit_sharma",      "name": "Rohit Sharma",       "category": "Cricketer", "wiki": "Rohit_Sharma"},
    {"id": "sachin_tendulkar",  "name": "Sachin Tendulkar",   "category": "Cricketer", "wiki": "Sachin_Tendulkar"},
    {"id": "hardik_pandya",     "name": "Hardik Pandya",      "category": "Cricketer", "wiki": "Hardik_Pandya"},
    {"id": "shubman_gill",      "name": "Shubman Gill",       "category": "Cricketer", "wiki": "Shubman_Gill"},
    {"id": "jasprit_bumrah",    "name": "Jasprit Bumrah",     "category": "Cricketer", "wiki": "Jasprit_Bumrah"},
    {"id": "ravindra_jadeja",   "name": "Ravindra Jadeja",    "category": "Cricketer", "wiki": "Ravindra_Jadeja"},
    {"id": "rishabh_pant",      "name": "Rishabh Pant",       "category": "Cricketer", "wiki": "Rishabh_Pant"},
    {"id": "shikhar_dhawan",    "name": "Shikhar Dhawan",     "category": "Cricketer", "wiki": "Shikhar_Dhawan"},
    {"id": "yuvraj_singh",      "name": "Yuvraj Singh",       "category": "Cricketer", "wiki": "Yuvraj_Singh"},
    {"id": "suresh_raina",      "name": "Suresh Raina",       "category": "Cricketer", "wiki": "Suresh_Raina"},
    {"id": "shreyas_iyer",      "name": "Shreyas Iyer",       "category": "Cricketer", "wiki": "Shreyas_Iyer"},
    {"id": "mohammed_shami",    "name": "Mohammed Shami",     "category": "Cricketer", "wiki": "Mohammed_Shami"},
    {"id": "r_ashwin",          "name": "Ravichandran Ashwin","category": "Cricketer", "wiki": "Ravichandran_Ashwin"},
    {"id": "sanju_samson",      "name": "Sanju Samson",       "category": "Cricketer", "wiki": "Sanju_Samson"},
    {"id": "suryakumar_yadav",  "name": "Suryakumar Yadav",   "category": "Cricketer", "wiki": "Suryakumar_Yadav"},
    {"id": "ishan_kishan",      "name": "Ishan Kishan",       "category": "Cricketer", "wiki": "Ishan_Kishan"},
    {"id": "mohammed_siraj",    "name": "Mohammed Siraj",     "category": "Cricketer", "wiki": "Mohammed_Siraj"},
    {"id": "sourav_ganguly",    "name": "Sourav Ganguly",     "category": "Cricketer", "wiki": "Sourav_Ganguly"},

    # ── 🏏 CRICKET (WOMEN) ────────────────────────────────────────
    {"id": "smriti_mandhana",   "name": "Smriti Mandhana",    "category": "Cricketer", "wiki": "Smriti_Mandhana"},
    {"id": "harmanpreet_kaur",  "name": "Harmanpreet Kaur",   "category": "Cricketer", "wiki": "Harmanpreet_Kaur"},
    {"id": "mithali_raj",       "name": "Mithali Raj",        "category": "Cricketer", "wiki": "Mithali_Raj"},
    {"id": "jemimah_rodrigues", "name": "Jemimah Rodrigues",  "category": "Cricketer", "wiki": "Jemimah_Rodrigues"},
    {"id": "shafali_verma",     "name": "Shafali Verma",      "category": "Cricketer", "wiki": "Shafali_Verma"},
    {"id": "deepti_sharma",     "name": "Deepti Sharma",      "category": "Cricketer", "wiki": "Deepti_Sharma"},
    {"id": "renuka_singh",      "name": "Renuka Singh Thakur","category": "Cricketer", "wiki": "Renuka_Singh_(cricketer)"},
    {"id": "richa_ghosh",       "name": "Richa Ghosh",        "category": "Cricketer", "wiki": "Richa_Ghosh"},
    {"id": "pooja_vastrakar",   "name": "Pooja Vastrakar",    "category": "Cricketer", "wiki": "Pooja_Vastrakar"},
    {"id": "harleen_deol",      "name": "Harleen Deol",       "category": "Cricketer", "wiki": "Harleen_Deol"},

    # ── 🎬 BOLLYWOOD (ACTORS) ─────────────────────────────────────
    {"id": "shah_rukh_khan",    "name": "Shah Rukh Khan",     "category": "Actor",     "wiki": "Shah_Rukh_Khan"},
    {"id": "salman_khan",       "name": "Salman Khan",        "category": "Actor",     "wiki": "Salman_Khan"},
    {"id": "aamir_khan",        "name": "Aamir Khan",         "category": "Actor",     "wiki": "Aamir_Khan"},
    {"id": "hrithik_roshan",    "name": "Hrithik Roshan",     "category": "Actor",     "wiki": "Hrithik_Roshan"},
    {"id": "ranbir_kapoor",     "name": "Ranbir Kapoor",      "category": "Actor",     "wiki": "Ranbir_Kapoor"},
    {"id": "ranveer_singh",     "name": "Ranveer Singh",      "category": "Actor",     "wiki": "Ranveer_Singh"},
    {"id": "akshay_kumar",      "name": "Akshay Kumar",       "category": "Actor",     "wiki": "Akshay_Kumar"},
    {"id": "ajay_devgn",        "name": "Ajay Devgn",         "category": "Actor",     "wiki": "Ajay_Devgn"},
    {"id": "amitabh_bachchan",  "name": "Amitabh Bachchan",   "category": "Actor",     "wiki": "Amitabh_Bachchan"},
    {"id": "shahid_kapoor",     "name": "Shahid Kapoor",      "category": "Actor",     "wiki": "Shahid_Kapoor"},
    {"id": "kartik_aaryan",     "name": "Kartik Aaryan",      "category": "Actor",     "wiki": "Kartik_Aaryan"},
    {"id": "vicky_kaushal",     "name": "Vicky Kaushal",      "category": "Actor",     "wiki": "Vicky_Kaushal"},
    {"id": "varun_dhawan",      "name": "Varun Dhawan",       "category": "Actor",     "wiki": "Varun_Dhawan"},
    {"id": "sidharth_malhotra", "name": "Sidharth Malhotra",  "category": "Actor",     "wiki": "Sidharth_Malhotra"},
    {"id": "ayushmann_khurrana","name": "Ayushmann Khurrana", "category": "Actor",     "wiki": "Ayushmann_Khurrana"},
    {"id": "john_abraham",      "name": "John Abraham",       "category": "Actor",     "wiki": "John_Abraham"},
    {"id": "saif_ali_khan",     "name": "Saif Ali Khan",      "category": "Actor",     "wiki": "Saif_Ali_Khan"},
    {"id": "tiger_shroff",      "name": "Tiger Shroff",       "category": "Actor",     "wiki": "Tiger_Shroff"},
    {"id": "anil_kapoor",       "name": "Anil Kapoor",        "category": "Actor",     "wiki": "Anil_Kapoor"},
    {"id": "sanjay_dutt",       "name": "Sanjay Dutt",        "category": "Actor",     "wiki": "Sanjay_Dutt"},
    {"id": "nawazuddin_siddiqui","name":"Nawazuddin Siddiqui","category":"Actor",     "wiki": "Nawazuddin_Siddiqui"},
    {"id": "pankaj_tripathi",   "name": "Pankaj Tripathi",    "category": "Actor",     "wiki": "Pankaj_Tripathi"},
    {"id": "boman_irani",       "name": "Boman Irani",        "category": "Actor",     "wiki": "Boman_Irani"},
    {"id": "rajkummar_rao",     "name": "Rajkummar Rao",      "category": "Actor",     "wiki": "Rajkummar_Rao"},

    # ── 🎬 BOLLYWOOD (ACTRESSES) ───────────────────────────────────
    {"id": "deepika_padukone",  "name": "Deepika Padukone",   "category": "Actress",   "wiki": "Deepika_Padukone"},
    {"id": "alia_bhatt",        "name": "Alia Bhatt",         "category": "Actress",   "wiki": "Alia_Bhatt"},
    {"id": "katrina_kaif",      "name": "Katrina Kaif",       "category": "Actress",   "wiki": "Katrina_Kaif"},
    {"id": "priyanka_chopra",   "name": "Priyanka Chopra",    "category": "Actress",   "wiki": "Priyanka_Chopra"},
    {"id": "kareena_kapoor",    "name": "Kareena Kapoor",     "category": "Actress",   "wiki": "Kareena_Kapoor"},
    {"id": "anushka_sharma",    "name": "Anushka Sharma",     "category": "Actress",   "wiki": "Anushka_Sharma"},
    {"id": "shraddha_kapoor",   "name": "Shraddha Kapoor",    "category": "Actress",   "wiki": "Shraddha_Kapoor"},
    {"id": "kiara_advani",      "name": "Kiara Advani",       "category": "Actress",   "wiki": "Kiara_Advani"},
    {"id": "kriti_sanon",       "name": "Kriti Sanon",        "category": "Actress",   "wiki": "Kriti_Sanon"},
    {"id": "sara_ali_khan",     "name": "Sara Ali Khan",      "category": "Actress",   "wiki": "Sara_Ali_Khan"},
    {"id": "janhvi_kapoor",     "name": "Janhvi Kapoor",      "category": "Actress",   "wiki": "Janhvi_Kapoor"},
    {"id": "ananya_panday",     "name": "Ananya Panday",      "category": "Actress",   "wiki": "Ananya_Panday"},
    {"id": "aishwarya_rai",     "name": "Aishwarya Rai",      "category": "Actress",   "wiki": "Aishwarya_Rai"},
    {"id": "madhuri_dixit",     "name": "Madhuri Dixit",      "category": "Actress",   "wiki": "Madhuri_Dixit"},
    {"id": "kajol",             "name": "Kajol",              "category": "Actress",   "wiki": "Kajol"},
    {"id": "vidya_balan",       "name": "Vidya Balan",        "category": "Actress",   "wiki": "Vidya_Balan"},
    {"id": "disha_patani",      "name": "Disha Patani",       "category": "Actress",   "wiki": "Disha_Patani"},
    {"id": "jacqueline_fernandez","name":"Jacqueline Fernandez","category":"Actress",  "wiki": "Jacqueline_Fernandez"},
    {"id": "taapsee_pannu",     "name": "Taapsee Pannu",      "category": "Actress",   "wiki": "Taapsee_Pannu"},
    {"id": "bhumi_pednekar",    "name": "Bhumi Pednekar",     "category": "Actress",   "wiki": "Bhumi_Pednekar"},
    {"id": "sonam_kapoor",      "name": "Sonam Kapoor",       "category": "Actress",   "wiki": "Sonam_Kapoor"},
    {"id": "triptii_dimri",     "name": "Triptii Dimri",      "category": "Actress",   "wiki": "Triptii_Dimri"},
    {"id": "tabu",              "name": "Tabu",               "category": "Actress",   "wiki": "Tabu_(actress)"},

    # ── 🌟 SOUTH INDIAN (ACTORS) ──────────────────────────────────
    {"id": "allu_arjun",        "name": "Allu Arjun",         "category": "Actor",     "wiki": "Allu_Arjun"},
    {"id": "jr_ntr",            "name": "N. T. Rama Rao Jr.", "category": "Actor",     "wiki": "N._T._Rama_Rao_Jr."},
    {"id": "yash",              "name": "Yash",               "category": "Actor",     "wiki": "Yash_(actor)"},
    {"id": "kamal_haasan",      "name": "Kamal Haasan",       "category": "Actor",     "wiki": "Kamal_Haasan"},
    {"id": "vikram",            "name": "Vikram",             "category": "Actor",     "wiki": "Vikram_(actor)"},
    {"id": "vijay_sethupathi",  "name": "Vijay Sethupathi",   "category": "Actor",     "wiki": "Vijay_Sethupathi"},
    {"id": "silambarasan",      "name": "Silambarasan",       "category": "Actor",     "wiki": "Silambarasan"},
    {"id": "mohanlal",          "name": "Mohanlal",           "category": "Actor",     "wiki": "Mohanlal"},
    {"id": "mammootty",         "name": "Mammootty",          "category": "Actor",     "wiki": "Mammootty"},
    {"id": "dulquer_salmaan",   "name": "Dulquer Salmaan",    "category": "Actor",     "wiki": "Dulquer_Salmaan"},
    {"id": "fahadh_faasil",     "name": "Fahadh Faasil",      "category": "Actor",     "wiki": "Fahadh_Faasil"},
    {"id": "tovino_thomas",     "name": "Tovino Thomas",      "category": "Actor",     "wiki": "Tovino_Thomas"},
    {"id": "prithviraj_sukumaran","name":"Prithviraj Sukumaran","category":"Actor",    "wiki": "Prithviraj_Sukumaran"},
    {"id": "rishab_shetty",     "name": "Rishab Shetty",      "category": "Actor",     "wiki": "Rishab_Shetty"},
    {"id": "rakshit_shetty",    "name": "Rakshit Shetty",     "category": "Actor",     "wiki": "Rakshit_Shetty"},
    {"id": "shiva_rajkumar",    "name": "Shiva Rajkumar",     "category": "Actor",     "wiki": "Shiva_Rajkumar"},
    {"id": "puneeth_rajkumar",  "name": "Puneeth Rajkumar",   "category": "Actor",     "wiki": "Puneeth_Rajkumar"},
    {"id": "vijay_deverakonda", "name": "Vijay Deverakonda",  "category": "Actor",     "wiki": "Vijay_Deverakonda"},
    {"id": "nani",              "name": "Nani",               "category": "Actor",     "wiki": "Nani_(actor)"},
    {"id": "naga_chaitanya",    "name": "Naga Chaitanya",     "category": "Actor",     "wiki": "Naga_Chaitanya"},
    {"id": "venkatesh",         "name": "Venkatesh Daggubati","category": "Actor",     "wiki": "Venkatesh_(actor)"},
    {"id": "chiranjeevi",       "name": "Chiranjeevi",        "category": "Actor",     "wiki": "Chiranjeevi"},
    {"id": "nagarjuna",         "name": "Akkineni Nagarjuna", "category": "Actor",     "wiki": "Nagarjuna_(actor)"},
    {"id": "balakrishna",       "name": "Nandamuri Balakrishna","category":"Actor",   "wiki": "Nandamuri_Balakrishna"},
    {"id": "arya",              "name": "Arya",               "category": "Actor",     "wiki": "Arya_(actor)"},
    {"id": "jayam_ravi",        "name": "Jayam Ravi",         "category": "Actor",     "wiki": "Jayam_Ravi"},
    {"id": "siddharth",         "name": "Siddharth",          "category": "Actor",     "wiki": "Siddharth_(actor)"},

    # ── 🌟 SOUTH INDIAN (ACTRESSES) ────────────────────────────────
    {"id": "rashmika_mandanna", "name": "Rashmika Mandanna",  "category": "Actress",   "wiki": "Rashmika_Mandanna"},
    {"id": "pooja_hegde",       "name": "Pooja Hegde",        "category": "Actress",   "wiki": "Pooja_Hegde"},
    {"id": "kajal_aggarwal",    "name": "Kajal Aggarwal",     "category": "Actress",   "wiki": "Kajal_Aggarwal"},
    {"id": "tamannaah_bhatia",  "name": "Tamannaah Bhatia",   "category": "Actress",   "wiki": "Tamannaah_Bhatia"},
    {"id": "raashii_khanna",    "name": "Raashii Khanna",     "category": "Actress",   "wiki": "Raashii_Khanna"},
    {"id": "krithi_shetty",     "name": "Krithi Shetty",      "category": "Actress",   "wiki": "Krithi_Shetty"},
    {"id": "mrunal_thakur",     "name": "Mrunal Thakur",      "category": "Actress",   "wiki": "Mrunal_Thakur"},
    {"id": "kalyani_priyadarshan","name":"Kalyani Priyadarshan","category":"Actress", "wiki": "Kalyani_Priyadarshan"},
    {"id": "parvathy_thiruvothu","name":"Parvathy Thiruvothu","category":"Actress",   "wiki": "Parvathy_Thiruvothu"},
    {"id": "manju_warrier",     "name": "Manju Warrier",      "category": "Actress",   "wiki": "Manju_Warrier"},
    {"id": "srinidhi_shetty",   "name": "Srinidhi Shetty",    "category": "Actress",   "wiki": "Srinidhi_Shetty"},
    {"id": "rukmini_vasanth",   "name": "Rukmini Vasanth",    "category": "Actress",   "wiki": "Rukmini_Vasanth"},
    {"id": "shriya_saran",      "name": "Shriya Saran",       "category": "Actress",   "wiki": "Shriya_Saran"},
    {"id": "hansika_motwani",   "name": "Hansika Motwani",    "category": "Actress",   "wiki": "Hansika_Motwani"},
    {"id": "asasin",            "name": "Asin Thottumkal",    "category": "Actress",   "wiki": "Asin"},
    {"id": "genelia_dsouza",    "name": "Genelia D'Souza",    "category": "Actress",   "wiki": "Genelia_D%27Souza"},
    {"id": "priya_bhavani_shankar","name":"Priya Bhavani Shankar","category":"Actress","wiki":"Priya_Bhavani_Shankar"},
    {"id": "aiishwarya_rajesh", "name": "Aishwarya Rajesh",   "category": "Actress",   "wiki": "Aishwarya_Rajesh"},
]


def batch_fetch_wiki_thumbnails(wiki_titles: list[str]) -> dict[str, str]:
    """
    Fetch thumbnail URLs for multiple Wikipedia titles in a single API call (up to 40 titles).
    Returns mapping from title -> thumbnail URL.
    """
    results = {}
    chunk_size = 35
    for i in range(0, len(wiki_titles), chunk_size):
        chunk = wiki_titles[i:i + chunk_size]
        joined_titles = "|".join(chunk)
        url = (
            f"https://en.wikipedia.org/w/api.php?action=query&titles={joined_titles}"
            "&prop=pageimages&format=json&pithumbsize=600"
        )
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "CelebrityDoppelgangerApp/2.0 (contact: info@celebapp.com) Python-urllib"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                pages = data.get("query", {}).get("pages", {})
                for _, page in pages.items():
                    title = page.get("title", "")
                    thumb = page.get("thumbnail", {}).get("source")
                    if thumb:
                        # normalize title
                        results[title] = thumb
                        results[title.replace(" ", "_")] = thumb
        except Exception as exc:
            logger.warning("Batch fetch failed for chunk [%d..%d]: %s", i, i + len(chunk), exc)
        time.sleep(1.0)  # respectful delay between batch queries
    return results


def download_image(img_url: str, dest_path: Path) -> bool:
    """Download image to disk with polite User-Agent."""
    try:
        req = urllib.request.Request(
            img_url,
            headers={
                "User-Agent": "CelebrityDoppelgangerApp/2.0 (contact: info@celebapp.com) Python-urllib"
            }
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read()
            if len(content) < 4000:
                return False
            dest_path.write_bytes(content)
            return True
    except Exception as exc:
        logger.warning("Download error for %s: %s", dest_path.name, exc)
        return False


def main():
    logger.info("=" * 65)
    logger.info("Mega Indian Celebrity Dataset Expansion (100+ Celebrities)")
    logger.info("=" * 65)

    # 1. Load existing
    with open(CELEBRITIES_JSON, "r", encoding="utf-8") as f:
        existing_celebs = json.load(f)
    existing_ids = {c["id"] for c in existing_celebs}

    existing_embeddings = []
    existing_metadata = []
    if EMBEDDINGS_NPY.exists() and METADATA_NPY.exists():
        existing_embeddings = list(np.load(str(EMBEDDINGS_NPY)))
        existing_metadata = list(np.load(str(METADATA_NPY), allow_pickle=True))
        logger.info("Current database size: %d entries", len(existing_embeddings))

    # Filter out already existing
    candidates = [c for c in CELEBRITIES_TO_ADD if c["id"] not in existing_ids]
    logger.info("Found %d candidate celebrities to fetch and process.", len(candidates))

    if not candidates:
        logger.info("All celebrities already in database.")
        return

    # 2. Batch fetch thumbnail URLs from Wikipedia
    wiki_titles = [c["wiki"] for c in candidates]
    logger.info("Batch-fetching thumbnail URLs from Wikipedia API...")
    url_map = batch_fetch_wiki_thumbnails(wiki_titles)
    logger.info("Found image URLs for %d/%d celebrities.", len(url_map), len(candidates))

    # 3. Load face engine
    logger.info("Initializing FaceEngine...")
    face_engine.load()
    logger.info("FaceEngine ready. Processing faces...")

    added_celebs = []
    new_embeddings = []
    new_metadata = []

    for idx, celeb in enumerate(candidates, 1):
        cid = celeb["id"]
        cname = celeb["name"]
        cat = celeb["category"]
        wiki = celeb["wiki"]

        # find URL
        img_url = url_map.get(wiki) or url_map.get(wiki.replace("_", " "))
        if not img_url:
            logger.warning("[%d/%d] No thumbnail for %s (%s)", idx, len(candidates), cname, wiki)
            continue

        celeb_dir = DATASET_DIR / cid
        celeb_dir.mkdir(parents=True, exist_ok=True)
        img_path = celeb_dir / "1.jpg"

        # Download image if not already cached
        if not img_path.exists() or img_path.stat().st_size < 4000:
            if not download_image(img_url, img_path):
                logger.warning("[%d/%d] Could not download image for %s", idx, len(candidates), cname)
                continue
            time.sleep(0.15)  # small courteous delay

        # Extract face embedding
        emb = face_engine.embedding_from_file(str(img_path))
        if emb is None:
            logger.warning("[%d/%d] ✗ No face or multiple faces detected for %s", idx, len(candidates), cname)
            continue

        rel_path = f"{cid}/1.jpg"
        new_embeddings.append(emb)
        new_metadata.append({
            "name": cname,
            "category": cat,
            "image": rel_path,
        })
        added_celebs.append({
            "id": cid,
            "name": cname,
            "category": cat,
            "folder": cid,
        })
        logger.info("[%d/%d] ✓ Added %s (%s)", idx, len(candidates), cname, cat)

    logger.info("\n" + "=" * 65)
    logger.info("Successfully added %d new Indian celebrities!", len(added_celebs))

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
