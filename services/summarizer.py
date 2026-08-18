"""
Turns a raw timestamped transcript into the three things the dashboard
shows: an AI Summary, a Key Highlights list, and Smart Chapters.
"""
from config import SUMMARY_MODES, DEFAULT_SUMMARY_MODE
from services.llm_client import chat_completion, safe_json_parse


def _format_transcript_with_timestamps(segments: list) -> str:
    lines = []
    for seg in segments:
        m, s = divmod(int(seg["start"]), 60)
        lines.append(f"[{m:02d}:{s:02d}] {seg['text']}")
    return "\n".join(lines)


def generate_summary(transcript_text: str, video_title: str, mode: str = DEFAULT_SUMMARY_MODE, backend: str = None) -> str:
    words = SUMMARY_MODES.get(mode, SUMMARY_MODES[DEFAULT_SUMMARY_MODE])["words"]
    system = (
        "You are an expert video summarizer. Write clear, information-dense "
        "summaries with no filler and no meta-commentary like 'this video is about'. "
        "The transcript may be in any language — always write your summary in "
        "English regardless of the transcript's language."
    )
    user = (
        f"Video title: {video_title}\n\n"
        f"Transcript:\n{transcript_text[:12000]}\n\n"
        f"Write a summary in approximately {words} words covering the main "
        f"points, key concepts explained, and any conclusions or takeaways."
    )
    return chat_completion(system, user, backend=backend).strip()


def _coerce_list(parsed, key: str) -> list:
    """
    The prompt asks the LLM for {"<key>": [...]} but models sometimes
    return a bare JSON array instead (especially with dense/technical
    transcripts). Handle both shapes so we never call .get() on a list,
    and drop any non-dict items that slip through.
    """
    if isinstance(parsed, list):
        items = parsed
    elif isinstance(parsed, dict):
        value = parsed.get(key, [])
        items = value if isinstance(value, list) else []
    else:
        items = []
    return [item for item in items if isinstance(item, dict)]


def generate_key_highlights(segments: list, max_highlights: int = 8, backend: str = None) -> list:
    """Returns [{"timestamp": "00:02:15", "seconds": 135, "text": "..."}]"""
    transcript_str = _format_transcript_with_timestamps(segments)
    system = (
        "You extract the most important moments from a timestamped video "
        "transcript. The transcript may be in any language — always write "
        "the 'text' labels in English regardless of the transcript's "
        "language. Respond ONLY with valid JSON, no other text."
    )
    user = (
        f"Timestamped transcript:\n{transcript_str[:12000]}\n\n"
        f"Pick the {max_highlights} most important moments. Return a JSON "
        'object: {"highlights": [{"timestamp": "MM:SS", "text": "short label describing the moment"}]}'
    )
    raw = chat_completion(system, user, json_mode=True, backend=backend)
    parsed = safe_json_parse(raw, {"highlights": []})
    highlights = _coerce_list(parsed, "highlights")[:max_highlights]

    for h in highlights:
        h["seconds"] = _timestamp_to_seconds(h.get("timestamp", "00:00"))
    return highlights


def generate_smart_chapters(segments: list, max_chapters: int = 8, backend: str = None) -> list:
    """Returns [{"timestamp": "00:00", "title": "Introduction"}]"""
    transcript_str = _format_transcript_with_timestamps(segments)
    system = (
        "You split a timestamped video transcript into logical chapters, "
        "like a YouTube 'Key moments' list. The transcript may be in any "
        "language — always write chapter titles in English regardless of "
        "the transcript's language. Respond ONLY with valid JSON."
    )
    user = (
        f"Timestamped transcript:\n{transcript_str[:12000]}\n\n"
        f"Create up to {max_chapters} chapters that divide this video into "
        'its natural sections. Return JSON: {"chapters": [{"timestamp": "MM:SS", "title": "short chapter title"}]}'
    )
    raw = chat_completion(system, user, json_mode=True, backend=backend)
    parsed = safe_json_parse(raw, {"chapters": []})
    chapters = _coerce_list(parsed, "chapters")[:max_chapters]

    for c in chapters:
        c["seconds"] = _timestamp_to_seconds(c.get("timestamp", "00:00"))
    return chapters


def _timestamp_to_seconds(ts: str) -> int:
    parts = ts.strip().split(":")
    try:
        parts = [int(p) for p in parts]
    except ValueError:
        return 0
    while len(parts) < 3:
        parts.insert(0, 0)
    h, m, s = parts[-3:]
    return h * 3600 + m * 60 + s