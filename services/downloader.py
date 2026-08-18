"""
Handles pulling a YouTube video (and its metadata) down to disk with yt-dlp.
"""
import json
import re
import shutil
import tempfile
import uuid
from pathlib import Path

import requests
import yt_dlp

from config import UPLOAD_FOLDER, FFMPEG_LOCATION, YOUTUBE_COOKIES_CONTENT, YOUTUBE_COOKIES_FILE


class DownloadError(Exception):
    pass


class TranscriptUnavailableError(DownloadError):
    pass


def _ensure_ffmpeg_available():
    """
    yt-dlp needs both ffmpeg AND ffprobe to merge YouTube's separate video
    and audio streams.
    """
    if FFMPEG_LOCATION:
        return  
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise DownloadError(
            "ffmpeg and/or ffprobe were not found on your system PATH. "
            "yt-dlp needs both to download and extract media. "
            "Locally: install ffmpeg from https://ffmpeg.org/download.html."
        )


def _cookiefile_path():
    """
    Resolves a cookies.txt path for yt-dlp to authenticate as a real
    signed-in session, which YouTube now requires for many videos.
    """
    if YOUTUBE_COOKIES_FILE:
        if not Path(YOUTUBE_COOKIES_FILE).exists():
            raise DownloadError(
                f"YOUTUBE_COOKIES_FILE is set to '{YOUTUBE_COOKIES_FILE}' but that "
                "file doesn't exist. Check the path in your config."
            )
        return YOUTUBE_COOKIES_FILE

    if YOUTUBE_COOKIES_CONTENT:
        path = Path(tempfile.gettempdir()) / "jarvis_yt_cookies.txt"
        path.write_text(YOUTUBE_COOKIES_CONTENT)
        return str(path)

    return None


# --- Caption-based path (no download, no ffmpeg, no Whisper) -----------------

def _parse_json3_captions(data: dict) -> list:
    segments = []
    for event in data.get("events", []):
        if "segs" not in event:
            continue
        text = "".join(seg.get("utf8", "") for seg in event["segs"])
        text = " ".join(text.replace("\n", " ").split())
        if not text:
            continue
        start = event.get("tStartMs", 0) / 1000
        dur = event.get("dDurationMs", 0) / 1000
        segments.append({"start": round(start, 2), "end": round(start + dur, 2), "text": text})
    return segments


_VTT_CUE_RE = re.compile(
    r"(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3}).*?\n(.*?)(?=\n\n|\Z)",
    re.DOTALL,
)


def _vtt_timestamp_to_seconds(ts: str) -> float:
    h, m, s = ts.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def _parse_vtt_captions(vtt_text: str) -> list:
    segments = []
    prev_text = ""
    for match in _VTT_CUE_RE.finditer(vtt_text):
        start, end, raw_text = match.groups()
        text = re.sub(r"<[^>]+>", "", raw_text)
        text = " ".join(text.split())
        if not text or text == prev_text or (prev_text and (prev_text in text or text in prev_text)):
            if len(text) > len(prev_text):
                prev_text = text
            continue
        segments.append({
            "start": round(_vtt_timestamp_to_seconds(start), 2),
            "end": round(_vtt_timestamp_to_seconds(end), 2),
            "text": text,
        })
        prev_text = text
    return segments


def fetch_youtube_transcript(url: str, progress_cb=None) -> dict:
    """
    Extracts captions cleanly using yt-dlp's subtitle downloader with skip_download=True.
    No video or audio files are ever downloaded to disk.
    """
    job_id = uuid.uuid4().hex[:10]
    output_dir = UPLOAD_FOLDER / job_id
    output_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en", "en-US", "hi"], # Supports English and Hindi auto-captions
        "subtitlesformat": "json3/vtt/best",
        "outtmpl": str(output_dir / "sub"),
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        }
    }

    cookiefile = _cookiefile_path()
    if cookiefile:
        ydl_opts["cookiefile"] = cookiefile

    if progress_cb:
        progress_cb(20, "Extracting caption data from YouTube…")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as e:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise DownloadError(f"Could not fetch YouTube captions: {str(e)}")

    # Look for the downloaded subtitle file on disk
    sub_files = list(output_dir.glob("sub.*"))
    if not sub_files:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise TranscriptUnavailableError(
            "This video does not have readable captions. "
            "Try using a different video URL."
        )

    # Parse the subtitle file found
    sub_file = sub_files[0]
    segments = []
    used_auto = "auto" in sub_file.name

    if sub_file.suffix == ".json3" or "json3" in sub_file.name:
        try:
            data = json.loads(sub_file.read_text(encoding="utf-8"))
            segments = _parse_json3_captions(data)
        except Exception:
            pass
    
    if not segments:
        # Fallback to parsing VTT format
        vtt_text = sub_file.read_text(encoding="utf-8", errors="ignore")
        segments = _parse_vtt_captions(vtt_text)

    # Clean up temp caption folder
    shutil.rmtree(output_dir, ignore_errors=True)

    if not segments:
        raise TranscriptUnavailableError("Found caption file but couldn't parse text segments.")

    if progress_cb:
        progress_cb(100, "Captions ready")

    return {
        "job_id": job_id,
        "file_path": None,  
        "title": info.get("title", "Untitled video"),
        "duration_seconds": info.get("duration", 0),
        "thumbnail": info.get("thumbnail"),
        "channel": info.get("uploader", "Unknown"),
        "upload_date": info.get("upload_date"),
        "source": "youtube",
        "source_url": url,
        "transcript_text": " ".join(s["text"] for s in segments),
        "segments": segments,
        "caption_language": info.get("subtitles_langs", ["en"])[0] if info.get("subtitles_langs") else "auto",
        "caption_auto_generated": used_auto,
    }


def download_youtube_video(url: str, progress_cb=None) -> dict:
    _ensure_ffmpeg_available()

    job_id = uuid.uuid4().hex[:10]
    out_template = str(UPLOAD_FOLDER / f"{job_id}.%(ext)s")

    def _hook(d):
        if not progress_cb:
            return
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 1
            done = d.get("downloaded_bytes", 0)
            pct = int(done / total * 100)
            progress_cb(pct, "Downloading audio track…")
        elif d["status"] == "finished":
            progress_cb(100, "Download complete")

    ydl_opts = {
        "format": "ba/best", # Best audio only
        "outtmpl": out_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [_hook],
        "retries": 10,
        "fragment_retries": 10,
        "source_address": "0.0.0.0",
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "web"] 
            }
        }
    }
    
    if FFMPEG_LOCATION:
        ydl_opts["ffmpeg_location"] = FFMPEG_LOCATION

    cookiefile = _cookiefile_path()
    if cookiefile:
        ydl_opts["cookiefile"] = cookiefile

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_path = Path(ydl.prepare_filename(info))
            
    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        if "403" in msg or "Forbidden" in msg:
            msg += (
                "\n\nA 403 here usually means yt-dlp's YouTube signature logic is out of date. "
                "Update yt-dlp: `pip install -U yt-dlp`. If using cookies, try re-exporting them."
            )
        raise DownloadError(msg) from e
    except AttributeError as e:
        raise DownloadError(f"Internal yt-dlp/ffmpeg error: {e}") from e

    return {
        "job_id": job_id,
        "file_path": str(final_path),
        "title": info.get("title", "Untitled video"),
        "duration_seconds": info.get("duration", 0),
        "thumbnail": info.get("thumbnail"),
        "channel": info.get("uploader", "Unknown"),
        "upload_date": info.get("upload_date"),
        "source": "youtube",
        "source_url": url,
    }


def register_uploaded_file(saved_path: Path) -> dict:
    job_id = uuid.uuid4().hex[:10]
    return {
        "job_id": job_id,
        "file_path": str(saved_path),
        "title": saved_path.stem,
        "duration_seconds": None,
        "thumbnail": None,
        "channel": "Local upload",
        "upload_date": None,
        "source": "upload",
        "source_url": None,
    }