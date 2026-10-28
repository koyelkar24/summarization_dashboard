"""
J.A.R.V.I.S. — AI Video Summarizer (Streamlit edition)
"""
import os
import uuid
from pathlib import Path
import streamlit as st

# --- set_page_config MUST be the very first Streamlit command -------------
st.set_page_config(
    page_title="J.A.R.V.I.S. — AI Video Summarizer",
    page_icon="🤖",
    layout="wide",
)

# --- Bridge Streamlit secrets -> environment variables ---------------------
if Path(".streamlit/secrets.toml").exists():
    try:
        for _key, _value in st.secrets.items():
            os.environ.setdefault(_key, str(_value))
    except Exception:
        pass

from config import (
    UPLOAD_FOLDER, TRANSCRIPT_FOLDER, ALLOWED_VIDEO_EXTENSIONS,
    SUMMARY_MODES, DEFAULT_SUMMARY_MODE, AI_BACKEND, DEPLOYED_MODE,
    MAX_VIDEO_DURATION_SECONDS, MAX_CONTENT_LENGTH,
)
from services import downloader, audio_extractor, transcriber, summarizer
from services import chat_service, study_service, exporter


# =============================================================================
# Theme — J.A.R.V.I.S. professional dashboard
# =============================================================================
st.markdown("""
<style>
:root {
    --canvas: #0b1220;
    --surface: #111b2b;
    --border: #26364c;
    --text: #e8eef7;
    --muted: #98a9bf;
    --accent: #55a6ff;
    --accent-strong: #2f80ed;
}
html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.stApp { background: var(--canvas); color: var(--text); }
[data-testid="stAppViewContainer"] main .block-container { max-width: 1440px; padding: 2.25rem 3rem 4rem; }
[data-testid="stHeader"] { background: transparent; }
section[data-testid="stSidebar"] { background: #0e1725; border-right: 1px solid var(--border); }
section[data-testid="stSidebar"] > div { padding-top: 1.5rem; }
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: var(--muted); }
.sidebar-brand { display: flex; align-items: center; gap: .75rem; padding: .25rem 0 1rem; }
.brand-mark { display: grid; place-items: center; width: 2.5rem; height: 2.5rem; border-radius: .75rem; background: #173458; color: #8cc8ff; font-size: 1.25rem; font-weight: 750; }
.sidebar-brand strong { display: block; color: var(--text); font-size: 1rem; letter-spacing: .04em; }
.sidebar-brand small { display: block; color: var(--muted); font-size: .78rem; margin-top: .12rem; }
.jarvis-hero { display: flex; align-items: center; justify-content: space-between; gap: 1.5rem; margin: 0 0 1.6rem; padding: 1.6rem 1.8rem; border: 1px solid var(--border); border-radius: 1rem; background: linear-gradient(115deg, #132238 0%, #101a2a 58%, #12243a 100%); }
.hero-kicker { color: #7bbcff; font-size: .73rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; }
.jarvis-title { margin: .35rem 0 .15rem; color: #f4f7fb; font-size: 2rem; font-weight: 720; letter-spacing: .035em; }
.jarvis-sub { margin: 0; color: #afbed0; font-size: .98rem; }
.hero-tag { flex: 0 0 auto; padding: .55rem .8rem; border: 1px solid #31547a; border-radius: 999px; background: #122944; color: #a7d3ff; font-size: .82rem; font-weight: 600; }
h1, h2, h3, h4, h5, h6 { color: #f0f4fa !important; font-weight: 650 !important; letter-spacing: -.015em; }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li { color: #c4cfdd; }
[data-testid="stCaptionContainer"] p { color: var(--muted); font-size: .88rem; }
[data-testid="stMetric"] { min-height: 6.1rem; padding: 1rem 1.1rem; border: 1px solid var(--border); border-radius: .85rem; background: var(--surface); box-shadow: 0 8px 22px rgba(0, 0, 0, .12); }
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: .82rem !important; }
[data-testid="stMetricValue"] { color: #eff5fc !important; font-size: 1.55rem !important; font-weight: 650; }
[data-testid="stTabs"] [role="tablist"] { gap: .55rem; border-bottom: 1px solid var(--border); }
[data-testid="stTabs"] button[role="tab"] { color: var(--muted); border-radius: .65rem .65rem 0 0; font-weight: 600; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color: #8fc7ff; }
[data-baseweb="tab-highlight"] { background: var(--accent) !important; height: 2px !important; }
[data-testid="stTextInput"] input, [data-testid="stSelectbox"] [data-baseweb="select"] > div { min-height: 2.8rem; border-color: #34465e; border-radius: .65rem; background: #101a29; color: var(--text); }
[data-testid="stTextInput"] input:focus, [data-testid="stTextInput"] input:focus-visible { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }
[data-testid="stFileUploader"] section { border: 1px dashed #405670; border-radius: .8rem; background: #101a29; }
[data-testid="stFileUploader"] section:hover { border-color: var(--accent); }
.stButton > button { min-height: 2.55rem; border: 1px solid #34465e; border-radius: .65rem; background: #152236; color: #dce6f2; font-weight: 600; transition: background .15s ease, border-color .15s ease; }
.stButton > button:hover { border-color: #5689bd; background: #1b2d45; color: #fff; }
.stButton > button[kind="primary"] { border-color: var(--accent-strong); background: var(--accent-strong); color: #fff; }
.stButton > button[kind="primary"]:hover { border-color: #4a98ff; background: #4a98ff; }
.stButton > button:focus-visible { outline: 2px solid #91caff; outline-offset: 2px; }
[data-testid="stExpander"], [data-testid="stChatMessage"] { border: 1px solid var(--border); border-radius: .8rem; background: var(--surface); }
[data-testid="stExpander"] summary { color: var(--text); font-weight: 600; }
[data-testid="stChatMessage"] p { color: #d3dce8; }
[data-testid="stAlert"] { border-radius: .75rem; }
[data-testid="stVideo"] { overflow: hidden; border: 1px solid var(--border); border-radius: .85rem; }
hr { border-color: var(--border) !important; }
@media (max-width: 800px) {
    [data-testid="stAppViewContainer"] main .block-container { padding: 1.25rem 1rem 3rem; }
    .jarvis-hero { align-items: flex-start; flex-direction: column; padding: 1.25rem; }
    .jarvis-title { font-size: 1.7rem; }
}
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; } }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# Session state
# =============================================================================
def init_state():
    defaults = {
        "videos": {},            
        "current_job_id": None,
        "chat_history": {},      
        "study_output": {},      
        "ai_backend": AI_BACKEND,
        "stats_videos": 0,
        "stats_hours": 0.0,
        "video_start_time": 0,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)

init_state()


# =============================================================================
# Pipeline (runs synchronously, with a live st.status widget)
# =============================================================================
def run_pipeline(input_kind: str, summary_mode: str, backend: str,
                 youtube_url: str = None, uploaded_file=None):
    with st.status("Starting pipeline…", expanded=True) as status:
        try:
            # --- Step 1: get a transcript ---
            if input_kind == "url":
                status.update(label="🔎 Fetching captions from YouTube…")

                def progress_cb(pct, msg):
                    status.update(label=f"🔎 {msg} ({pct}%)")

                try:
                    # ATTEMPT 1: Try getting the fast captions from YouTube directly
                    video_meta = downloader.fetch_youtube_transcript(youtube_url, progress_cb=progress_cb)
                    job_id = video_meta["job_id"]
                    transcript = {"text": video_meta["transcript_text"], "segments": video_meta["segments"]}

                    caption_kind = "auto-generated" if video_meta.get("caption_auto_generated") else "manual"
                    status.write(
                        f"✅ Loaded: **{video_meta.get('title', 'Video')}** "
                        f"({caption_kind} captions, {video_meta.get('caption_language', 'en')})"
                    )

                except downloader.TranscriptUnavailableError as e:
                    # This exception type IS the "no usable captions" signal —
                    # always fall back to downloading + Whisper for it,
                    # regardless of the specific underlying reason (rate
                    # limit, IP block, captions genuinely disabled, etc).
                    # Using the exception TYPE instead of string-matching
                    # the message means this can never silently stop
                    # triggering just because the wording changes.
                    status.update(label=f"⚠️ {e} Falling back to Whisper…")

                    video_meta = downloader.download_youtube_video(youtube_url, progress_cb=progress_cb)
                    job_id = video_meta["job_id"]
                    status.write(f"✅ Downloaded: **{video_meta['title']}**")

                    duration = video_meta.get("duration_seconds")
                    if not duration:
                        duration = audio_extractor.get_duration_seconds(video_meta["file_path"])
                        video_meta["duration_seconds"] = duration

                    if duration and duration > MAX_VIDEO_DURATION_SECONDS:
                        limit_min = MAX_VIDEO_DURATION_SECONDS // 60
                        actual_min = int(duration // 60)
                        status.update(
                            label=f"❌ Video is {actual_min} min, over the {limit_min} min limit.",
                            state="error",
                        )
                        return None

                    status.update(label="🎧 Extracting audio…")
                    audio_path = audio_extractor.extract_audio(video_meta["file_path"], job_id, TRANSCRIPT_FOLDER)

                    status.update(label="📝 Transcribing audio locally with Whisper…")
                    transcript = transcriber.transcribe_audio(audio_path)
                    # Note: any error raised inside THIS fallback (e.g. a
                    # DownloadError from a still-403'd download) is NOT
                    # caught here — it propagates to the outer except
                    # below, which is correct: if both the transcript API
                    # AND the download fallback fail, that's worth
                    # surfacing, not silently swallowing.

            else:
                # --- FILE UPLOAD LOGIC ---
                ext = uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else ""
                if ext not in ALLOWED_VIDEO_EXTENSIONS:
                    status.update(label=f"❌ Unsupported file type: .{ext}", state="error")
                    return None
                if uploaded_file.size > MAX_CONTENT_LENGTH:
                    status.update(label="File exceeds the 500 MB upload limit.", state="error")
                    return None
                status.write("📁 Saving uploaded file…")
                job_id = uuid.uuid4().hex[:10]
                safe_name = f"{job_id}_{Path(uploaded_file.name).name}"
                saved_path = UPLOAD_FOLDER / safe_name
                with open(saved_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                video_meta = downloader.register_uploaded_file(saved_path)
                job_id = video_meta["job_id"]
                status.write(f"✅ Loaded: **{video_meta['title']}**")

                duration = audio_extractor.get_duration_seconds(video_meta["file_path"])
                video_meta["duration_seconds"] = duration
                if duration and duration > MAX_VIDEO_DURATION_SECONDS:
                    limit_min = MAX_VIDEO_DURATION_SECONDS // 60
                    actual_min = int(duration // 60)
                    status.update(
                        label=f"❌ Video is {actual_min} min, over the {limit_min} min limit.",
                        state="error",
                    )
                    return None

                status.update(label="🎧 Extracting audio…")
                audio_path = audio_extractor.extract_audio(video_meta["file_path"], job_id, TRANSCRIPT_FOLDER)

                status.update(label="📝 Transcribing audio (can take a minute)…")
                transcript = transcriber.transcribe_audio(audio_path)

            # Caption-only runs do not pass through the audio duration checks.
            if not video_meta.get("file_path"):
                duration = video_meta.get("duration_seconds") or 0
                if duration > MAX_VIDEO_DURATION_SECONDS:
                    limit_min = MAX_VIDEO_DURATION_SECONDS // 60
                    actual_min = int(duration // 60)
                    status.update(
                        label=f"Video is {actual_min} min, over the {limit_min} min limit.",
                        state="error",
                    )
                    return None

            status.update(label="🔍 Analyzing content for highlights & chapters…")
            highlights = summarizer.generate_key_highlights(transcript["segments"], backend=backend)
            chapters = summarizer.generate_smart_chapters(transcript["segments"], backend=backend)

            status.update(label="✨ Generating summary…")
            summary_text = summarizer.generate_summary(
                transcript["text"], video_meta["title"], summary_mode, backend=backend
            )

            status.update(label="✅ Pipeline complete!", state="complete")

        except Exception as e:
            status.update(label=f"❌ Failed: {e}", state="error")
            st.error(str(e))
            return None

    return {
        **video_meta,
        "transcript": transcript["text"],
        "segments": transcript["segments"],
        "summary": summary_text,
        "highlights": highlights,
        "chapters": chapters,
        "summary_mode": summary_mode,
    }


def format_duration(seconds):
    if not seconds:
        return "—"
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


# =============================================================================
# Sidebar
# =============================================================================
with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand"><span class="brand-mark">J</span>'
        '<div><strong>J.A.R.V.I.S.</strong><small>Video intelligence</small></div></div>',
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown("### Settings")
    backend_options = ["Gemini (Cloud)"] if DEPLOYED_MODE else ["Gemini (Cloud)", "Ollama (Local)"]
    default_index = 0 if st.session_state.ai_backend == "gemini" else (1 if len(backend_options) > 1 else 0)
    backend_label = st.selectbox("AI Backend", backend_options, index=default_index)
    st.session_state.ai_backend = "gemini" if backend_label.startswith("Gemini") else "ollama"

    summary_label_to_key = {v["label"]: k for k, v in SUMMARY_MODES.items()}
    summary_mode_label = st.selectbox(
        "Summary Mode", list(summary_label_to_key.keys()),
        index=list(summary_label_to_key.values()).index(DEFAULT_SUMMARY_MODE),
    )
    selected_summary_mode = summary_label_to_key[summary_mode_label]

    st.divider()
    st.markdown("### Recent videos")
    if st.session_state.videos:
        for jid, v in reversed(list(st.session_state.videos.items())):
            label = v["title"][:26] + ("…" if len(v["title"]) > 26 else "")
            if st.button(label, key=f"hist_{jid}", use_container_width=True):
                st.session_state.current_job_id = jid
                st.session_state.video_start_time = 0
                st.rerun()
    else:
        st.caption("No videos processed yet this session.")

    st.divider()
    st.caption("Your video history is saved for this session.")


# =============================================================================
# Header
# =============================================================================
model_display = "Gemini Cloud" if st.session_state.ai_backend == "gemini" else "Ollama Local"
st.markdown(
    '<div class="jarvis-hero"><div><div class="hero-kicker">Video intelligence</div>'
    '<div class="jarvis-title">J.A.R.V.I.S.</div>'
    '<p class="jarvis-sub">Turn long videos into clear summaries and useful study material.</p></div>'
    f'<div class="hero-tag">Active model&nbsp;&nbsp;·&nbsp;&nbsp;{model_display}</div></div>',
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns(3)
c1.metric("Videos processed this session", st.session_state.stats_videos)
c2.metric("Video hours analyzed", f"{st.session_state.stats_hours:.1f}")
c3.metric("Summary length", SUMMARY_MODES[selected_summary_mode]["label"].split(" (")[0])

st.divider()

# =============================================================================
# Process New Video
# =============================================================================
st.markdown("### Create a video brief")
st.caption("Paste a YouTube link or upload a video to get started.")

tab_url, tab_upload = st.tabs(["🔗 YouTube URL", "📁 Upload File"])

with tab_url:
    youtube_url = st.text_input(
        "YouTube video URL", key="yt_url_input",
        placeholder="https://www.youtube.com/watch?v=…",
    )

    st.caption("Or load a sample link")
    ex_cols = st.columns(3)
    examples = {
        "AI Agents Explained": "https://www.youtube.com/watch?v=eXdVDhOGqoE",
        "LangChain Tutorial": "https://www.youtube.com/watch?v=1bUy-1hGZpI",
        "Cybersecurity Basics": "https://www.youtube.com/watch?v=U_P23SqJaDc",
    }
    
    def set_example_url(url_to_set):
        st.session_state.yt_url_input = url_to_set

    for col, (label, url) in zip(ex_cols, examples.items()):
        col.button(
            label, 
            key=f"example_{label}", 
            use_container_width=True, 
            on_click=set_example_url, 
            args=(url,)
        )

    if st.button("Analyze video", type="primary", key="analyze_url_btn"):
        if not youtube_url or not youtube_url.strip():
            st.warning("Paste a YouTube URL first.")
        else:
            result = run_pipeline("url", selected_summary_mode, st.session_state.ai_backend, youtube_url=youtube_url.strip())
            if result:
                jid = result["job_id"]
                st.session_state.videos[jid] = result
                st.session_state.current_job_id = jid
                st.session_state.video_start_time = 0
                st.session_state.stats_videos += 1
                st.session_state.stats_hours += (result.get("duration_seconds") or 0) / 3600
                st.rerun()

with tab_upload:
    uploaded_file = st.file_uploader(
        "Choose a video file", type=["mp4", "mov", "webm", "mkv", "avi"],
    )
    st.caption("MP4, MOV, WebM, MKV, AVI — up to 500 MB")

    if st.button("Analyze video", type="primary", key="analyze_upload_btn"):
        if not uploaded_file:
            st.warning("Choose a video file first.")
        else:
            result = run_pipeline("upload", selected_summary_mode, st.session_state.ai_backend, uploaded_file=uploaded_file)
            if result:
                jid = result["job_id"]
                st.session_state.videos[jid] = result
                st.session_state.current_job_id = jid
                st.session_state.video_start_time = 0
                st.session_state.stats_videos += 1
                st.session_state.stats_hours += (result.get("duration_seconds") or 0) / 3600
                st.rerun()

st.divider()

# =============================================================================
# Results Workspace
# =============================================================================
current_id = st.session_state.current_job_id
result = st.session_state.videos.get(current_id) if current_id else None

if not result:
    st.markdown("### Your video workspace")
    st.info("Your summary, key moments, chapters, and study tools will appear here after you analyze a video.")
else:
    col_preview, col_summary = st.columns([1, 1])

    with col_preview:
        st.markdown("#### Video preview")
        if result.get("source") == "upload":
            st.video(result["file_path"], start_time=st.session_state.video_start_time)
        elif result.get("source_url"):
            st.video(result["source_url"], start_time=st.session_state.video_start_time)
        st.markdown(f"**{result['title']}**")
        st.caption(f"{result.get('channel', 'Unknown')} · {format_duration(result.get('duration_seconds'))} · {result.get('source', 'Unknown')}")

    with col_summary:
        st.markdown("#### AI summary")
        with st.container(border=True):
            st.markdown(result["summary"])

        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            pdf_path = exporter.export_pdf(current_id, result["title"], result["summary"])
            with open(pdf_path, "rb") as f:
                st.download_button("📄 Export PDF", f, file_name=f"{result['title'][:40]}_summary.pdf",
                                    mime="application/pdf", use_container_width=True, key=f"pdf_{current_id}")
        with exp_col2:
            txt_path = exporter.export_txt(current_id, result["title"], result["summary"])
            with open(txt_path, "rb") as f:
                st.download_button("📄 Export TXT", f, file_name=f"{result['title'][:40]}_summary.txt",
                                    mime="text/plain", use_container_width=True, key=f"txt_{current_id}")

    st.divider()
    col_hi, col_ch = st.columns(2)

    with col_hi:
        st.markdown("#### Key moments")
        highlights = result.get("highlights", [])
        if not highlights:
            st.caption("No highlights generated.")
        for i, h in enumerate(highlights):
            hc1, hc2, hc3 = st.columns([1.2, 4, 0.8])
            hc1.markdown(f"`{h.get('timestamp', '--:--')}`")
            hc2.write(h.get("text", ""))
            if hc3.button("▶", key=f"hi_jump_{current_id}_{i}"):
                st.session_state.video_start_time = h.get("seconds", 0)
                st.rerun()

    with col_ch:
        st.markdown("#### Smart chapters")
        chapters = result.get("chapters", [])
        if not chapters:
            st.caption("No chapters generated.")
        for i, c in enumerate(chapters):
            cc1, cc2, cc3 = st.columns([1.2, 4, 0.8])
            cc1.markdown(f"`{c.get('timestamp', '--:--')}`")
            cc2.write(c.get("title", ""))
            if cc3.button("▶", key=f"ch_jump_{current_id}_{i}"):
                st.session_state.video_start_time = c.get("seconds", 0)
                st.rerun()

    st.divider()
    col_chat, col_study = st.columns(2)

    # ---------------- Chat with video ----------------
    with col_chat:
        st.markdown("#### Ask the video")
        history = st.session_state.chat_history.setdefault(current_id, [])

        chat_box = st.container(height=280)
        with chat_box:
            if not history:
                st.caption("Ask anything about this video…")
            for turn in history:
                with st.chat_message(turn["role"]):
                    st.write(turn["content"])

        suggestion_cols = st.columns(2)
        suggestion_clicked = None
        if suggestion_cols[0].button("What is this video about?", key=f"sugg1_{current_id}", use_container_width=True):
            suggestion_clicked = "What is this video about?"
        if suggestion_cols[1].button("Summarize in 5 points.", key=f"sugg2_{current_id}", use_container_width=True):
            suggestion_clicked = "Summarize in 5 points."

        question = st.chat_input("Type your question…", key=f"chat_input_{current_id}")
        question = question or suggestion_clicked

        if question:
            history.append({"role": "user", "content": question})
            with st.spinner("Thinking…"):
                try:
                    answer = chat_service.answer_question(
                        result["transcript"], result["title"], question, history[:-1],
                        backend=st.session_state.ai_backend,
                    )
                except Exception as e:
                    answer = f"Error: {e}"
            history.append({"role": "assistant", "content": answer})
            st.rerun()

    # ---------------- Study assistant ----------------
    with col_study:
        st.markdown("#### Study tools")
        study_state = st.session_state.study_output.setdefault(current_id, {})

        sb1, sb2 = st.columns(2)
        sb3, sb4 = st.columns(2)
        study_buttons = {
            "exam-notes": (sb1, "📝 Exam Notes"),
            "viva-questions": (sb2, "❓ Viva Questions"),
            "mcq": (sb3, "📋 MCQ Generator"),
            "flashcards": (sb4, "🗂 Flashcards"),
        }

        for kind, (col, label) in study_buttons.items():
            if col.button(label, key=f"study_{kind}_{current_id}", use_container_width=True):
                with st.spinner("Generating…"):
                    try:
                        if kind == "exam-notes":
                            study_state[kind] = study_service.generate_exam_notes(
                                result["transcript"], result["title"], backend=st.session_state.ai_backend)
                        elif kind == "viva-questions":
                            study_state[kind] = study_service.generate_viva_questions(
                                result["transcript"], result["title"], backend=st.session_state.ai_backend)
                        elif kind == "mcq":
                            study_state[kind] = study_service.generate_mcqs(
                                result["transcript"], result["title"], backend=st.session_state.ai_backend)
                        elif kind == "flashcards":
                            study_state[kind] = study_service.generate_flashcards(
                                result["transcript"], result["title"], backend=st.session_state.ai_backend)
                    except Exception as e:
                        study_state[kind] = f"Error: {e}"

        if study_state.get("exam-notes"):
            with st.expander("📝 Exam Notes", expanded=True):
                st.markdown(study_state["exam-notes"])

        if study_state.get("viva-questions"):
            with st.expander("❓ Viva Questions", expanded=True):
                if isinstance(study_state["viva-questions"], list):
                    for i, q in enumerate(study_state["viva-questions"]):
                        st.markdown(f"**Q{i+1}. {q.get('question','')}**")
                        st.caption(q.get("answer", ""))
                else:
                    st.error(study_state["viva-questions"])

        if study_state.get("mcq"):
            with st.expander("📋 MCQ Generator", expanded=True):
                if isinstance(study_state["mcq"], list):
                    for i, m in enumerate(study_state["mcq"]):
                        st.markdown(f"**Q{i+1}. {m.get('question','')}**")
                        options = m.get("options", [])
                        if isinstance(options, list):
                            for j, opt in enumerate(options):
                                marker = "✅" if j == m.get("correct_index", -1) else "◻️"
                                st.write(f"{marker} {chr(65+j)}. {opt}")
                        if m.get("explanation"):
                            st.caption(m["explanation"])
                else:
                    st.error(study_state["mcq"])

        if study_state.get("flashcards"):
            with st.expander("🗂 Flashcards", expanded=True):
                if isinstance(study_state["flashcards"], list):
                    for i, f in enumerate(study_state["flashcards"]):
                        st.markdown(f"**{f.get('front','')}**")
                        st.caption(f.get("back", ""))
                        st.write("")
                else:
                    st.error(study_state["flashcards"])
