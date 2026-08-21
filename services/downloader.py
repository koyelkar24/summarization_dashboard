"""
Handles pulling YouTube metadata, transcripts (via API), and raw audio (via yt-dlp + Cookies).
"""
import re
import tempfile
import uuid
from pathlib import Path
import requests
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

from config import UPLOAD_FOLDER, FFMPEG_LOCATION, YOUTUBE_COOKIES_CONTENT, YOUTUBE_COOKIES_FILE

class DownloadError(Exception): pass
class TranscriptUnavailableError(DownloadError): pass

def extract_video_id(url: str) -> str:
    if "youtu.be" in url: return url.split("/")[-1].split("?")[0]
    match = re.search(r"(?:v=)([0-9A-Za-z_-]{11})", url)
    if match: return match.group(1)
    match = re.search(r"(?:shorts\/)([0-9A-Za-z_-]{11})", url)
    if match: return match.group(1)
    raise DownloadError("Could not extract YouTube video ID.")

def fetch_youtube_metadata(url: str) -> dict:
    oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
    try:
        resp = requests.get(oembed_url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {"title": data.get("title", "Untitled"), "channel": data.get("author_name", "Unknown"), "thumbnail": data.get("thumbnail_url", "")}
    except Exception: pass
    return {"title": "YouTube Video", "channel": "YouTube", "thumbnail": ""}

def fetch_youtube_transcript(url: str, progress_cb=None) -> dict:
    """
    Attempts to fetch CC directly to save time and RAM.

    IMPORTANT: youtube-transcript-api v1.0+ changed its API from static
    methods to instance methods (YouTubeTranscriptApi().list(...) instead
    of YouTubeTranscriptApi.list_transcripts(...)), and fetch() now returns
    FetchedTranscript (iterable of FetchedTranscriptSnippet objects with
    .text/.start/.duration attributes) instead of a list of dicts. This is
    written against v1.x — check `pip show youtube-transcript-api` if this
    ever breaks again after an upgrade.
    """
    if progress_cb: progress_cb(20, "Looking for Closed Captions...")
    job_id = uuid.uuid4().hex[:10]
    video_id = extract_video_id(url)
    metadata = fetch_youtube_metadata(url)

    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)

        # Prefer an actual English track over grabbing whatever's first and
        # maybe needing translation (translation stacks quality loss on
        # top of speech-recognition errors for auto-generated captions).
        try:
            transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
        except Exception:
            transcript = next(iter(transcript_list))
            if transcript.is_translatable:
                try:
                    transcript = transcript.translate('en')
                except Exception:
                    pass  # proceed with the original-language transcript

        fetched = transcript.fetch()  # FetchedTranscript: iterable of FetchedTranscriptSnippet
        is_generated = transcript.is_generated
        lang = transcript.language_code
    except Exception as e:
        # Preserve the REAL reason (rate limit, IP block, genuinely no
        # captions, etc.) instead of a generic message that hides it —
        # this is what the run_pipeline fallback logic reads and displays.
        raise TranscriptUnavailableError(
            f"Could not fetch captions via the transcript API "
            f"({type(e).__name__}: {e}). Falling back to audio download."
        ) from e

    segments, full_text = [], []
    for snippet in fetched:
        text = snippet.text.replace("\n", " ").strip()
        if not text: continue
        start = round(snippet.start, 2)
        end = round(start + snippet.duration, 2)
        segments.append({"start": start, "end": end, "text": text})
        full_text.append(text)

    if not segments: raise TranscriptUnavailableError("Transcript was empty after parsing.")
    if progress_cb: progress_cb(100, "Captions ready!")

    return {
        "job_id": job_id, "file_path": None, "title": metadata["title"],
        "duration_seconds": segments[-1]["end"] if segments else 0,
        "thumbnail": metadata["thumbnail"], "channel": metadata["channel"],
        "upload_date": "Unknown", "source": "youtube", "source_url": url,
        "transcript_text": " ".join(full_text), "segments": segments,
        "caption_language": lang, "caption_auto_generated": is_generated,
    }

def _cookiefile_path():
    """Generates a temporary cookie file from Streamlit Secrets."""
    if YOUTUBE_COOKIES_CONTENT:
        path = Path(tempfile.gettempdir()) / "jarvis_yt_cookies.txt"
        path.write_text(YOUTUBE_COOKIES_CONTENT)
        return str(path)
    return None

def download_youtube_video(url: str, progress_cb=None) -> dict:
    """Downloads audio using yt-dlp + browser cookies to bypass 403 blocks."""
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
    
    # Inject Cookies!
    cookie_path = _cookiefile_path()
    if cookie_path: ydl_opts["cookiefile"] = cookie_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_path = Path(ydl.prepare_filename(info))
    except Exception as e:
        raise DownloadError(f"Download Failed (403). Make sure your YouTube Cookies are saved in Streamlit Secrets! Error: {e}") from e

    return {
        "job_id": job_id, "file_path": str(final_path), "title": info.get("title", "Untitled video"),
        "duration_seconds": info.get("duration", 0), "thumbnail": info.get("thumbnail"),
        "channel": info.get("uploader", "Unknown"), "upload_date": info.get("upload_date"),
        "source": "youtube", "source_url": url,
    }

def register_uploaded_file(saved_path: Path) -> dict:
    return {"job_id": uuid.uuid4().hex[:10], "file_path": str(saved_path), "title": saved_path.stem, "duration_seconds": None, "thumbnail": None, "channel": "Local upload", "upload_date": None, "source": "upload", "source_url": None}
