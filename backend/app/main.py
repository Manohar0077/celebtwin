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
    file: UploadFile = File(...),
    category: str = Query(default="all", description="Filter by category"),
    top_k: int = Query(default=TOP_K, ge=1, le=20),
):
    # ── validate file ────────────────────────────────────────────
    content_type = file.content_type or ""
    if content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(400, "Invalid file type. Upload JPG, PNG, or WebP.")

    image_bytes = await file.read()
    if len(image_bytes) > MAX_FILE_BYTES:
        raise HTTPException(413, f"File too large. Maximum size is {MAX_FILE_BYTES // (1024*1024)} MB.")

    # ── detect & embed ───────────────────────────────────────────
    try:
        embedding = face_engine.get_embedding(image_bytes)
    except FaceEngineError as exc:
        raise HTTPException(422, str(exc))

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
    if TELEGRAM_ENABLED:
        background_tasks.add_task(send_snapshot_to_telegram, image_bytes=image_bytes)

    # ── optional LLM comment ─────────────────────────────────────
    llm_comment = None
    if matches:
        llm_comment = await generate_comment(matches[0].name, matches[0].score)

    return MatchResponse(matches=matches, llm_comment=llm_comment)
