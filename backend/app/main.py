"""
FastAPI main application.
"""
import json
import logging
import numpy as np
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from typing import List, Optional

from .config import (
    CELEBRITIES_JSON, EMBEDDINGS_NPY, METADATA_NPY,
    DATASET_DIR, TOP_K, TELEGRAM_ENABLED,
)
from .face_engine import face_engine, FaceEngineError
from .matcher import matcher
from .schemas import MatchResponse, CelebrityMatch, HealthResponse
from .llm_service import generate_comment
from .telegram_service import send_snapshot_to_telegram

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

MAX_FILE_BYTES = 15 * 1024 * 1024  # 15 MB


# ── Startup / shutdown ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load face model
    face_engine.load()

    # Load celebrity embeddings
    if EMBEDDINGS_NPY.exists() and METADATA_NPY.exists():
        embeddings = np.load(str(EMBEDDINGS_NPY))
        metadata   = list(np.load(str(METADATA_NPY), allow_pickle=True))
        matcher.load(embeddings, metadata)
        logger.info("Celebrity database ready: %d entries", matcher.count)
    else:
        logger.warning(
            "Embeddings not found at %s — run scripts/generate_embeddings.py first!",
            EMBEDDINGS_NPY,
        )

    yield  # app runs here

    logger.info("Shutting down.")


# ── App ───────────────────────────────────────────────────────────
app = FastAPI(
    title="Celebrity Doppelgänger API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve celebrity images directly from the dataset folder
if DATASET_DIR.exists():
    app.mount("/celebrity-images", StaticFiles(directory=str(DATASET_DIR)), name="celebrity-images")
else:
    logger.warning("Dataset directory not found: %s", DATASET_DIR)


# ── Routes ────────────────────────────────────────────────────────
@app.get("/api/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        model_loaded=face_engine.ready,
        celebrities_loaded=matcher.count,
    )


@app.post("/api/match", response_model=MatchResponse)
async def match_face(
    background_tasks: BackgroundTasks,
    files: Optional[List[UploadFile]] = File(default=None),
    file: Optional[UploadFile] = File(default=None),
    category: str = Query(default="all", description="Filter by category"),
    top_k: int = Query(default=TOP_K, ge=1, le=20),
):
    upload_list = files if files else ([file] if file else [])
    if not upload_list:
        raise HTTPException(400, "No image files provided.")

    valid_embeddings = []
    primary_image_bytes = None

    for upload in upload_list:
        content_type = upload.content_type or ""
        if content_type not in ("image/jpeg", "image/png", "image/webp"):
            continue

        image_bytes = await upload.read()
        if len(image_bytes) > MAX_FILE_BYTES:
            continue

        if primary_image_bytes is None:
            primary_image_bytes = image_bytes

        try:
            emb = face_engine.get_embedding(image_bytes)
            valid_embeddings.append(emb)
        except FaceEngineError:
            continue

    if not valid_embeddings:
        raise HTTPException(422, "No clear face detected in the scanned photos. Please center your face with good lighting.")

    # ── Average embeddings across frames for superior match accuracy ──
    if len(valid_embeddings) == 1:
        embedding = valid_embeddings[0]
    else:
        avg_emb = np.mean(valid_embeddings, axis=0)
        norm = np.linalg.norm(avg_emb)
        embedding = (avg_emb / norm).astype(np.float32) if norm > 1e-6 else valid_embeddings[0]

    # ── match ────────────────────────────────────────────────────
    if not matcher.ready:
        raise HTTPException(503, "Celebrity database not loaded. Run generate_embeddings.py first.")

    results = matcher.find_top_k(embedding, k=top_k, category_filter=category)

    matches = [
        CelebrityMatch(
            name     = r.name,
            category = r.category,
            score    = r.score,
            image    = r.image,
        )
        for r in results
    ]

    # ── background Telegram snapshot forwarding ──────────────────
    if TELEGRAM_ENABLED and primary_image_bytes:
        background_tasks.add_task(send_snapshot_to_telegram, image_bytes=primary_image_bytes)

    # ── LLM match explanation ────────────────────────────────────
    llm_comment = None
    if matches:
        llm_comment = await generate_comment(matches[0].name, matches[0].score, matches[0].category)

    return MatchResponse(matches=matches, llm_comment=llm_comment)
