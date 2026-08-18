"""
Transcribes audio to timestamped text using faster-whisper (runs fully
locally/offline — no API key needed).
"""
import streamlit as st
from faster_whisper import WhisperModel

from config import WHISPER_MODEL_SIZE, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE


@st.cache_resource(show_spinner="Loading Whisper model (first run only)…")
def _get_model() -> WhisperModel:
    # st.cache_resource keeps this loaded for the whole Streamlit session
    # instead of reloading the (fairly large) model on every rerun.
    return WhisperModel(
        WHISPER_MODEL_SIZE,
        device=WHISPER_DEVICE,
        compute_type=WHISPER_COMPUTE_TYPE,
    )


def transcribe_audio(audio_path: str, progress_cb=None) -> dict:
    """
    Returns:
        {
            "text": "full transcript ...",
            "segments": [{"start": 0.0, "end": 4.2, "text": "..."}],
            "language": "en"
        }
    """
    try:
        model = _get_model()
        segments_iter, info = model.transcribe(audio_path, beam_size=5, vad_filter=True)

        segments = []
        full_text_parts = []
        for seg in segments_iter:
            segments.append({
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
            })
            full_text_parts.append(seg.text.strip())
            if progress_cb:
                progress_cb(f"Transcribing… {seg.end:.0f}s processed")

        return {
            "text": " ".join(full_text_parts),
            "segments": segments,
            "language": info.language,
        }
    except Exception as e:
        raise Exception(f"Whisper transcription failed: {str(e)}")