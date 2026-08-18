"""
Handles pulling YouTube metadata and transcripts using stealth APIs to bypass 
Streamlit Cloud 403 Forbidden Datacenter Blocks.
"""
import re
import uuid
from pathlib import Path
import requests
from youtube_transcript_api import YouTubeTranscriptApi

from config import UPLOAD_FOLDER

class DownloadError(Exception):
    pass

class TranscriptUnavailableError(DownloadError):
    pass

def extract_video_id(url: str) -> str:
    """Extracts the 11-character YouTube video ID."""
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:\?|&|/|$)", url)
    if match:
        return match.group(1)
    raise DownloadError("Could not extract YouTube video ID from the provided URL.")

def fetch_youtube_metadata(url: str) -> dict:
    """Uses YouTube's official, public API to safely get title/thumbnail."""
    oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
    try:
        resp = requests.get(oembed_url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return {
            "title": data.get("title", "Untitled Video"),
            "channel": data.get("author_name", "Unknown Channel"),
            "thumbnail": data.get("thumbnail_url", ""),
        }
    except Exception:
        return {"title": "YouTube Video", "channel": "YouTube", "thumbnail": ""}

def fetch_youtube_transcript(url: str, progress_cb=None) -> dict:
    """
    Uses youtube-transcript-api to pull captions directly. 
    Bypasses yt-dlp entirely to avoid 403 Forbidden blocks!
    """
    if progress_cb: progress_cb(20, "Connecting to YouTube via Stealth API...")

    job_id = uuid.uuid4().hex[:10]
    video_id = extract_video_id(url)
    metadata = fetch_youtube_metadata(url)

    if progress_cb: progress_cb(50, "Extracting transcript data...")

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_transcript(['en', 'en-US', 'hi'])
        except Exception:
            transcript = next(iter(transcript_list))
            
        caption_data = transcript.fetch()
        is_generated = transcript.is_generated
        lang = transcript.language_code
        
    except Exception as e:
        raise TranscriptUnavailableError(
            "This video does not have English/Hindi captions available, or the creator disabled them."
        )

    segments = []
    full_text = []
    
    for item in caption_data:
        text = item.get("text", "").replace("\n", " ").strip()
        if not text: continue
        start = round(item.get("start", 0), 2)
        end = round(start + item.get("duration", 0), 2)
        segments.append({"start": start, "end": end, "text": text})
        full_text.append(text)

    if not segments:
        raise TranscriptUnavailableError("Transcript was found but contained no text.")

    if progress_cb: progress_cb(100, "Captions ready!")

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

def download_youtube_video(url: str, progress_cb=None) -> dict:
    raise DownloadError(
        "Audio downloading is disabled in the cloud version due to YouTube firewalls (403 Forbidden). "
        "Please paste a YouTube video that has 'CC' (Closed Captions) available!"
    )

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
