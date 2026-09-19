# Celebrity Doppelgänger 🎬

A one-page web app that uses your webcam to find which South Indian celebrity you look most like — powered by InsightFace face embeddings and cosine similarity.

## Demo

**Left panel:** Live webcam feed — press the camera button to snap.  
**Right panel:** Your top 5 celebrity matches appear instantly.

No image upload. No stored photos. Results in seconds.

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React + Vite + Tailwind CSS + Framer Motion |
| Backend | FastAPI + Python |
| Face Detection | InsightFace (buffalo_l model, CPU) |
| Embeddings | ONNX Runtime |
| Similarity | Cosine similarity (L2-normalised dot product) |
| Optional AI | Google Gemini (fun commentary only) |

---

## Project Structure

```
celebrity_doppleganger/
├── frontend/               # React app
│   └── src/App.jsx         # Single-page split-screen UI
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI app
│   │   ├── face_engine.py  # InsightFace wrapper
│   │   ├── matcher.py      # Cosine similarity search
│   │   ├── schemas.py      # Pydantic models
│   │   ├── config.py       # Environment config
│   │   └── llm_service.py  # Optional Gemini commentary
│   ├── celebrity_data/
│   │   ├── celebrities.json
│   │   ├── embeddings.npy  # generated
│   │   └── metadata.npy    # generated
│   ├── scripts/
│   │   └── generate_embeddings.py
│   └── requirements.txt
└── south-indian-celebrity-dataset/
    ├── ajith/
    ├── nayanthara/
    └── ... (24 celebrity folders)
```

---

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux

# Install dependencies (first time is slow — downloads ONNX, InsightFace)
pip install -r requirements.txt
```

### 2. Generate Celebrity Embeddings

> **Required before starting the backend!**
> 
> First run downloads the InsightFace `buffalo_l` model (~300 MB).

```bash
# From backend/ directory, with venv active
python scripts/generate_embeddings.py
```

Expected output:
```
INFO | Loading InsightFace model ...
INFO | Processing: Ajith Kumar (ajith)
INFO |   ✓ 12/15 images used
...
INFO | Saved 24 embeddings → celebrity_data/embeddings.npy
INFO | Done ✓
```

### 3. Start Backend

```bash
# From backend/ directory, with venv active
uvicorn app.main:app --reload --port 8000
```

API available at `http://localhost:8000`  
Docs at `http://localhost:8000/docs`

### 4. Start Frontend

```bash
cd frontend
npm install   # first time only
npm run dev
```

App available at `http://localhost:5173`

---

## Environment Variables

Copy `.env.example` to `.env` in the `backend/` directory:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_KEY` | *(empty)* | Gemini API key for fun comments (optional) |
| `LLM_MODEL` | `gemini-1.5-flash` | Gemini model to use |
| `TOP_K` | `5` | Number of matches to return |
| `INSIGHTFACE_MODEL` | `buffalo_l` | InsightFace model name |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check + model status |
| `POST` | `/api/match` | Submit photo, get top matches |
| `GET` | `/celebrity-images/{path}` | Serve celebrity images |

### Match request

```bash
curl -X POST http://localhost:8000/api/match \
  -F "file=@photo.jpg" \
  -F "category=all"
```

### Match response

```json
{
  "matches": [
    {
      "name": "Ajith Kumar",
      "category": "Actor",
      "score": 0.82,
      "image": "ajith/1.jpg"
    }
  ],
  "llm_comment": "You share some great facial features with Ajith Kumar! ..."
}
```

---

## Adding Celebrities

1. Add a folder under `south-indian-celebrity-dataset/{folder_name}/` with face images
2. Add an entry to `backend/celebrity_data/celebrities.json`
3. Re-run the embedding generator: `python scripts/generate_embeddings.py`

---

## Privacy

- User photos are processed **in-memory only**
- Images are **never written to disk**
- No user data is stored or logged
- Photos are discarded immediately after embedding generation

---

## Troubleshooting

**"No face detected"** — Ensure good lighting and face the camera directly.  
**"Multiple faces detected"** — Only one person should be in frame.  
**Backend 503** — Run `generate_embeddings.py` first.  
**Slow first startup** — InsightFace downloads model on first run.  
**Camera denied** — Click the lock icon in the browser address bar and allow camera.
