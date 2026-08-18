"""
Extracts a mono 16kHz WAV track from a video file — the format
faster-whisper wants — using ffmpeg under the hood.
"""
import shutil
import subprocess
from pathlib import Path

from config import FFMPEG_LOCATION


class AudioExtractionError(Exception):
    pass


def _ffmpeg_bin(name: str) -> str:
    """Resolves the ffmpeg/ffprobe binary, honoring FFMPEG_LOCATION if set."""
    if FFMPEG_LOCATION:
        candidate = Path(FFMPEG_LOCATION) / name
        return str(candidate)
    return name


def _ensure_ffmpeg_available():
    if FFMPEG_LOCATION:
        return  # trust the user-provided path
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise AudioExtractionError(
            "ffmpeg and/or ffprobe were not found on your system PATH. "
            "Install ffmpeg (it bundles ffprobe) from https://ffmpeg.org/download.html, "
            "confirm it works with `ffmpeg -version` and `ffprobe -version` in a "
            "terminal, then restart the app. If it's installed but not on your PATH, "
            "set FFMPEG_LOCATION in your .env file to the folder containing it."
        )


def extract_audio(video_path: str, job_id: str, output_dir: Path) -> str:
    _ensure_ffmpeg_available()
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_path = output_dir / f"{job_id}.wav"

    cmd = [
        _ffmpeg_bin("ffmpeg"), "-y",
        "-i", video_path,
        "-vn",                 # no video
        "-ac", "1",             # mono
        "-ar", "16000",         # 16kHz sample rate (whisper's native rate)
        "-acodec", "pcm_s16le",
        str(audio_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError as e:
        raise AudioExtractionError(
            f"Could not run ffmpeg ({e}). Check that FFMPEG_LOCATION in .env "
            "points to the correct folder, or that ffmpeg is on your PATH."
        ) from e

    if result.returncode != 0:
        raise AudioExtractionError(result.stderr[-2000:])

    return str(audio_path)


def get_duration_seconds(video_path: str) -> float:
    _ensure_ffmpeg_available()
    cmd = [
        _ffmpeg_bin("ffprobe"), "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        return 0.0
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0
