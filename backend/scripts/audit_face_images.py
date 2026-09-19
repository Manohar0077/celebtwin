"""
audit_face_images.py
Audits every celebrity image to check face detection quality.
"""
import sys
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import CELEBRITIES_JSON, DATASET_DIR
from app.face_engine import face_engine

logging.basicConfig(level=logging.WARNING, format="%(levelname)s | %(message)s")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
MIN_DIM    = 85
MIN_SCORE  = 0.70

def audit_image(img_path):
    r = {"path": img_path.name, "detected": 0, "det_score": 0.0, "face_w": 0, "face_h": 0, "usable": False, "reason": ""}
    img = cv2.imread(str(img_path))
    if img is None:
        r["reason"] = "Cannot load"; return r
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    faces = face_engine._app.get(img_rgb)
    r["detected"] = len(faces)
    if len(faces) == 0:
        r["reason"] = "No face detected"; return r
    if len(faces) > 1:
        scored = sorted([(f, float(getattr(f, "det_score", 0.0)), (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1])) for f in faces], key=lambda x: x[2], reverse=True)
        if scored[0][2] < 2.5 * scored[1][2]:
            r["reason"] = f"{len(faces)} faces, none dominant"; return r
        face, score = scored[0][0], scored[0][1]
    else:
        face = faces[0]; score = float(getattr(face, "det_score", 0.0))
    r["det_score"] = score
    x1,y1,x2,y2 = face.bbox
    r["face_w"] = int(x2-x1); r["face_h"] = int(y2-y1)
    if score < MIN_SCORE:
        r["reason"] = f"Low score={score:.2f}"; return r
    if r["face_w"] < MIN_DIM or r["face_h"] < MIN_DIM:
        r["reason"] = f"Too small {r['face_w']}x{r['face_h']}"; return r
    r["usable"] = True; r["reason"] = f"OK score={score:.2f} {r['face_w']}x{r['face_h']}"; return r

print("Loading InsightFace model...")
face_engine.load()
print("Model ready.\n")

with open(CELEBRITIES_JSON) as f:
    celebrities = json.load(f)

critical, partial, ok = [], [], []

for celeb in celebrities:
    folder_path = DATASET_DIR / celeb["folder"]
    name = celeb["name"]
    folder = celeb["folder"]
    if not folder_path.exists():
        critical.append((name, folder, [{"path":"(missing)", "reason":"Folder missing", "usable":False}]))
        continue
    images = sorted([f for f in folder_path.iterdir() if f.suffix.lower() in IMAGE_EXTS])
    if not images:
        critical.append((name, folder, [{"path":"(empty)", "reason":"No images", "usable":False}]))
        continue
    results = [audit_image(img) for img in images]
    usable_count = sum(1 for r in results if r["usable"])
    if usable_count == 0:
        critical.append((name, folder, results))
    elif usable_count < len(results):
        partial.append((name, folder, results))
    else:
        ok.append((name, folder, results))

print("=" * 65)
print(f"RESULTS: OK={len(ok)}  PARTIAL={len(partial)}  CRITICAL={len(critical)}")
print("=" * 65)

if critical:
    print(f"\n--- CRITICAL (no usable faces) [{len(critical)}] ---")
    for name, folder, imgs in critical:
        print(f"  {name} ({folder})")
        for i in imgs:
            print(f"    [{i['path']}] {i['reason']}")

if partial:
    print(f"\n--- PARTIAL (some images fail) [{len(partial)}] ---")
    for name, folder, imgs in partial:
        usable = sum(1 for i in imgs if i['usable'])
        print(f"  {name} ({folder})  [{usable}/{len(imgs)} usable]")
        for i in imgs:
            icon = "OK" if i['usable'] else "XX"
            print(f"    [{icon}] {i['path']} -> {i['reason']}")

print(f"\nDone. {len(ok)} OK, {len(partial)} partial, {len(critical)} critical.")
