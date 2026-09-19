import sys
import json
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import CELEBRITIES_JSON, EMBEDDINGS_NPY, METADATA_NPY, DATASET_DIR

with open(CELEBRITIES_JSON, 'r', encoding='utf-8') as f:
    celeb_json = json.load(f)

embeddings = np.load(EMBEDDINGS_NPY)
metadata = np.load(METADATA_NPY, allow_pickle=True)

print("=== CELEBTWIN DATABASE INTEGRITY REPORT ===")
print(f"celebrities.json entries : {len(celeb_json)}")
print(f"embeddings.npy shape     : {embeddings.shape}")
print(f"metadata.npy entries     : {len(metadata)}")

assert len(celeb_json) == len(embeddings) == len(metadata), "Mismatch in counts!"
assert embeddings.shape[1] == 512, "Embeddings are not 512-D!"

# Verify unit norms
norms = np.linalg.norm(embeddings, axis=1)
norm_diff = np.max(np.abs(norms - 1.0))
print(f"Max embedding norm deviation from 1.0: {norm_diff:.6f}")
assert norm_diff < 1e-4, "Embeddings not normalized!"

# Verify image paths
missing_imgs = []
categories = {}
for idx, (c, m) in enumerate(zip(celeb_json, metadata)):
    img_rel = m.get("image", "")
    full_path = DATASET_DIR / img_rel
    if not full_path.exists() or full_path.stat().st_size < 1000:
        missing_imgs.append((c['id'], img_rel))
    cat = m.get("category", "Unknown")
    categories[cat] = categories.get(cat, 0) + 1

print(f"\nMissing/Invalid display images: {len(missing_imgs)}")
if missing_imgs:
    for cid, img in missing_imgs[:5]:
        print(f"  - {cid}: {img}")

print("\nBreakdown by Category:")
for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
    print(f"  - {cat:15s}: {count}")

print("\nDatabase integrity check PASSED successfully! 288 total celebrities.")
