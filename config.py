"""
Central configuration for J.A.R.V.I.S. Video Summarizer.
Reads environment variables (see .env.example) with sane local defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# --- Folders -----------------------------------------------------------
UPLOAD_FOLDER = BASE_DIR / "uploads"
OUTPUT_FOLDER = BASE_DIR / "outputs"
TRANSCRIPT_FOLDER = BASE_DIR / "transcripts"

for folder in (UPLOAD_FOLDER, OUTPUT_FOLDER, TRANSCRIPT_FOLDER):
    folder.mkdir(parents=True, exist_ok=True)

# --- AI backend switch ---------------------------------------------------
# "ollama" -> free/local, needs `ollama serve` running
# "openai" -> needs OPENAI_API_KEY
AI_BACKEND = os.getenv("AI_BACKEND", "ollama")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")


# --- MISSING GEMINI CONFIG ADDED HERE ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# --- ffmpeg / ffprobe location -------------------------------------------
# Leave blank if ffmpeg/ffprobe are already on your system PATH. Otherwise
# point this at the folder containing ffmpeg(.exe)/ffprobe(.exe) — common on
# Windows if you downloaded a zip build instead of using an installer.
FFMPEG_LOCATION = os.getenv("FFMPEG_LOCATION", "").strip()

# --- Whisper transcription ------------------------------------------------
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "tiny")  # tiny/base/small/medium
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

# --- Upload limits ---------------------------------------------------------
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "webm", "mkv", "avi"}

# --- Summary modes ----------------------------------------------------------
SUMMARY_MODES = {
    "short": {"label": "Short (80 words)", "words": 80},
    "medium": {"label": "Medium (200 words)", "words": 200},
    "long": {"label": "Long (400 words)", "words": 400},
}

DEFAULT_SUMMARY_MODE = "medium"
DEPLOYED_MODE = False  # set to True when deploying to Streamlit Community Cloud
MAX_VIDEO_DURATION_SECONDS = 25000  # Increased limit to allow 5+ hour videosYOUTUBE_COOKIES_CONTENT = None  # paste exported cookies.txt content here as a string if YouTube blocks you (429s)
YOUTUBE_COOKIES_FILE = None     # or point this to a cookies.txt file path instead
YOUTUBE_COOKIES_CONTENT = None  
YOUTUBE_COOKIES_FILE = None