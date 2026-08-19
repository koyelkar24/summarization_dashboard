"""
Handles pulling YouTube media and transcripts with Cookie support to bypass 403 blocks.
"""
import re
import shutil
import tempfile
import uuid
from pathlib import Path
import yt_dlp

from config import UPLOAD_FOLDER, FFMPEG_LOCATION, YOUTUBE_COOKIES_CONTENT, YOUTUBE_COOKIES_FILE

class DownloadError(Exception): pass
class TranscriptUnavailableError(DownloadError): pass

def _cookiefile_path():
    if YOUTUBE_COOKIES_CONTENT:
        path = Path(tempfile.gettempdir()) / "jarvis_yt_cookies.txt"
        path.write_text(YOUTUBE_COOKIES_CONTENT)
        return str(path)
    return None

def fetch_youtube_transcript(url: str, progress_cb=None) -> dict:
    raise TranscriptUnavailableError("Skipping CC extraction to force Whisper download.")

def download_youtube_video(url: str, progress_cb=None) -> dict:
    job_id = uuid.uuid4().hex[:10]
    out_template = str(UPLOAD_FOLDER / f"{job_id}.%(ext)s")

    def _hook(d):
        if not progress_cb: return
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 1
            pct = int(d.get("downloaded_bytes", 0) / total * 100)
            progress_cb(pct, "Downloading audio track...")
        elif d["status"] == "finished":
            progress_cb(100, "Download complete")

    ydl_opts = {
        "format": "ba/best", 
        "outtmpl": out_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [_hook],
        "extractor_args": {"youtube": {"player_client": ["ios", "android", "mweb"]}}
    }

    if FFMPEG_LOCATION: ydl_opts["ffmpeg_location"] = FFMPEG_LOCATION
    
    cookie_path = _cookiefile_path()
    if cookie_path: ydl_opts["cookiefile"] = cookie_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_path = Path(ydl.prepare_filename(info))
    except Exception as e:
        raise DownloadError(f"Download Failed. Ensure cookies are set in Streamlit Secrets! Error: {e}") from e

    return {
        "job_id": job_id, "file_path": str(final_path), "title": info.get("title", "Untitled video"),
        "duration_seconds": info.get("duration", 0), "thumbnail": info.get("thumbnail"),
        "channel": info.get("uploader", "Unknown"), "upload_date": info.get("upload_date"),
        "source": "youtube", "source_url": url,
    }

def register_uploaded_file(saved_path: Path) -> dict:
    return {"job_id": uuid.uuid4().hex[:10], "file_path": str(saved_path), "title": saved_path.stem, "duration_seconds": None, "thumbnail": None, "channel": "Local upload", "upload_date": None, "source": "upload", "source_url": None}
