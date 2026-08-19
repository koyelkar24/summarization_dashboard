"""
Handles pulling YouTube metadata and transcripts.

Strategy:
- Captions: youtube_transcript_api (lighter, avoids most yt-dlp bot-detection
  / 403 issues since it never downloads media, just reads the caption track).
- Video download (Whisper fallback only, when a video has no captions):
  yt-dlp, which still needs ffmpeg/ffprobe on PATH (or FFMPEG_LOCATION set).
"""
import re
import shutil
import socket
import tempfile
import uuid
from pathlib import Path

import requests
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

from config import UPLOAD_FOLDER, FFMPEG_LOCATION, YOUTUBE_COOKIES_CONTENT, YOUTUBE_COOKIES_FILE


class DownloadError(Exception):
    pass


class TranscriptUnavailableError(DownloadError):
    pass


PREFERRED_CAPTION_LANGS = ["en", "en-US", "en-GB", "hi", "en-orig"]


def extract_video_id(url: str) -> str:
    """Extracts the video ID, even from shortened or Shorts URLs."""
    if "youtu.be" in url:
        return url.split("/")[-1].split("?")[0]
    match = re.search(r"(?:v=)([0-9A-Za-z_-]{11})", url)
    if match:
        return match.group(1)
    match = re.search(r"(?:shorts\/)([0-9A-Za-z_-]{11})", url)
    if match:
        return match.group(1)
    raise DownloadError("Could not extract YouTube video ID. Please check the URL.")


def fetch_youtube_metadata(url: str) -> dict:
    """Lightweight title/channel/thumbnail lookup via YouTube's oEmbed endpoint."""
    oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
    try:
        resp = requests.get(oembed_url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "title": data.get("title", "Untitled Video"),
                "channel": data.get("author_name", "Unknown Channel"),
                "thumbnail": data.get("thumbnail_url", ""),
            }
    except Exception:
        pass
    return {"title": "YouTube Video", "channel": "YouTube", "thumbnail": ""}


def _get_field(item, key, default=None):
    """
    youtube_transcript_api >=0.6.2 returns FetchedTranscriptSnippet objects
    (attribute access), older versions return plain dicts. Support both so
    a library upgrade doesn't silently break caption parsing.
    """
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


# --- Caption fetching (no download, no ffmpeg, no Whisper) -----------------

def fetch_youtube_transcript(url: str, progress_cb=None) -> dict:
    if progress_cb:
        progress_cb(20, "Connecting to YouTube via captions API…")

    job_id = uuid.uuid4().hex[:10]
    video_id = extract_video_id(url)
    metadata = fetch_youtube_metadata(url)

    if progress_cb:
        progress_cb(50, "Extracting transcript data…")

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Prefer a manually-created (human-written) transcript in our
        # preferred languages, then fall back to auto-generated, then to
        # whatever's available at all.
        transcript = None
        for lang in PREFERRED_CAPTION_LANGS:
            try:
                transcript = transcript_list.find_manually_created_transcript([lang])
                break
            except Exception:
                continue
        if transcript is None:
            for lang in PREFERRED_CAPTION_LANGS:
                try:
                    transcript = transcript_list.find_generated_transcript([lang])
                    break
                except Exception:
                    continue
        if transcript is None:
            transcript = next(iter(transcript_list))

        # Translate to English if the chosen track isn't already English.
        if transcript.language_code not in ("en", "en-US", "en-GB"):
            try:
                transcript = transcript.translate("en")
            except Exception:
                pass  # No translation available — keep original language.

        caption_data = transcript.fetch()
        is_generated = transcript.is_generated
        lang = transcript.language_code

    except Exception as e:
        raise TranscriptUnavailableError(f"YouTube API Error: {type(e).__name__} - {str(e)}")

    segments = []
    full_text = []
    for item in caption_data:
        text = (_get_field(item, "text", "") or "").replace("\n", " ").strip()
        if not text:
            continue
        start = round(_get_field(item, "start", 0) or 0, 2)
        duration = _get_field(item, "duration", 0) or 0
        end = round(start + duration, 2)
        segments.append({"start": start, "end": end, "text": text})
        full_text.append(text)

    if not segments:
        raise TranscriptUnavailableError("Transcript found but it was completely empty.")

    if progress_cb:
        progress_cb(100, "Captions ready!")

    return {
        "job_id": job_id,
        "file_path": None,
        "title": metadata["title"],
        "duration_seconds": segments[-1]["end"] if segments else 0,
        "thumbnail": metadata["thumbnail"],
        "channel": metadata["channel"],
        "upload_date": "Unknown",
        "source": "youtube",
        "source_url": url,
        "transcript_text": " ".join(full_text),
        "segments": segments,
        "caption_language": lang,
        "caption_auto_generated": is_generated,
    }


# --- Video download (Whisper fallback only) ---------------------------------

def _ensure_ffmpeg_available():
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


def download_youtube_video(url: str, progress_cb=None) -> dict:
    """
    Used only when a video has no usable captions — downloads audio so
    Whisper can transcribe it locally. Requires ffmpeg/ffprobe.
    """
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
        "format": "ba/best",  # Best audio only
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
                "player_client": ["ios", "android", "mweb"]  # mitigates 403s
            }
        },
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
    except (socket.timeout, TimeoutError) as e:
        raise DownloadError("Timed out reaching YouTube. Try again.") from e

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
