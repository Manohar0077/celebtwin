"""Application configuration loaded from environment variables."""
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# Paths
BASE_DIR       = Path(__file__).parent.parent  # backend/
CELEBRITY_DATA = BASE_DIR / "celebrity_data"
CELEBRITIES_JSON = CELEBRITY_DATA / "celebrities.json"
EMBEDDINGS_NPY   = CELEBRITY_DATA / "embeddings.npy"
METADATA_NPY     = CELEBRITY_DATA / "metadata.npy"

# Dataset root (relative to project root)
PROJECT_ROOT   = BASE_DIR.parent
DATASET_DIR    = PROJECT_ROOT / "south-indian-celebrity-dataset"

# InsightFace
INSIGHTFACE_MODEL = os.getenv("INSIGHTFACE_MODEL", "buffalo_sc")
DET_SIZE          = (640, 640)

# API
TOP_K = int(os.getenv("TOP_K", "5"))

# LLM (optional)
LLM_API_KEY  = os.getenv("LLM_API_KEY", "")
LLM_MODEL    = os.getenv("LLM_MODEL", "gemini-1.5-flash")
LLM_ENABLED  = bool(LLM_API_KEY)

# Telegram Notification (Optional)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_ENABLED   = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
