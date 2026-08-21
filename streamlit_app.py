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
    MAX_VIDEO_DURATION_SECONDS,
)
from services import downloader, audio_extractor, transcriber, summarizer
from services import chat_service, study_service, exporter


# =============================================================================
# Theme — Futuristic Animated Blue
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@500;600;700&display=swap');

html, body, [class*="css"] { 
    font-family: 'Rajdhani', sans-serif; 
}

/* Scoped text color — main content area only, not widget internals */
.stMarkdown p, .stMarkdown li, .stMarkdown, .stCaption, .stText {
    color: #cbe4ff !important; 
    font-size: 1.1rem;
}
h1, h2, h3, h4, h5, h6 {
    color: #f0f9ff !important;
    font-weight: 700 !important;
}

/* --- Drifting animated background glow --- */
.stApp {
    background-color: #030712;
    background-image:
        radial-gradient(circle at 20% 20%, rgba(56,189,248,0.16), transparent 40%),
        radial-gradient(circle at 80% 80%, rgba(37,99,235,0.14), transparent 40%),
        radial-gradient(circle at 50% 50%, rgba(6,182,212,0.08), transparent 50%);
    background-size: 200% 200%;
    animation: bgDrift 18s ease-in-out infinite;
}
@keyframes bgDrift {
    0%   { background-position: 0% 0%, 100% 100%, 50% 50%; }
    50%  { background-position: 100% 50%, 0% 50%, 30% 70%; }
    100% { background-position: 0% 0%, 100% 100%, 50% 50%; }
}

section[data-testid="stSidebar"] { 
    background-color: #020617 !important; 
    border-right: 1px solid #1e3a5f !important; 
}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown p {
    color: #93b8dd !important;
}

/* --- Animated gradient title --- */
.jarvis-title {
    font-family: 'Orbitron', sans-serif;
    font-weight: 900;
    font-size: 2.5rem;
    letter-spacing: 6px;
    color: #f0f9ff;
    margin-bottom: 0px;
}
.jarvis-title span {
    background: linear-gradient(90deg, #38bdf8, #06b6d4, #2563eb, #38bdf8);
    background-size: 300% 100%;
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    animation: gradientFlow 6s linear infinite;
}
@keyframes gradientFlow {
    0%   { background-position: 0% 50%; }
    100% { background-position: 300% 50%; }
}
.jarvis-sub { 
    color: #6b8cb3 !important; 
    font-size: 0.95rem !important; 
    letter-spacing: 2px; 
    margin-top: 0; 
    margin-bottom: 1.5rem;
}

/* --- Metrics: glowing pulse border --- */
div[data-testid="stMetric"] {
    background: #0b1220;
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 15px 20px;
    animation: metricPulse 3s ease-in-out infinite;
}
@keyframes metricPulse {
    0%, 100% { border-color: #1e3a5f; box-shadow: 0 0 0 rgba(56,189,248,0); }
    50%      { border-color: #38bdf8; box-shadow: 0 0 16px rgba(56,189,248,0.35); }
}
div[data-testid="stMetricLabel"] { color: #7dabd6 !important; font-size: 1rem !important;}
div[data-testid="stMetricValue"] { 
    color: #38bdf8 !important; 
    font-family: 'Orbitron', sans-serif; 
    text-shadow: 0 0 10px rgba(56,189,248,0.5);
}

/* --- Status badges: pulsing online dot --- */
.status-badge {
    display: inline-block;
    font-family: monospace;
    font-size: 0.85rem;
    color: #93b8dd;
    background: #0b1220;
    border: 1px solid #1e3a5f;
    padding: 6px 14px;
    border-radius: 20px;
    margin-right: 10px;
    margin-bottom: 20px;
}
.status-badge b { color: #38bdf8; text-shadow: 0 0 6px rgba(56,189,248,0.6); }
.dot-online { 
    color: #38bdf8; 
    animation: dotPulse 1.8s ease-in-out infinite;
}
@keyframes dotPulse {
    0%, 100% { opacity: 1;   text-shadow: 0 0 6px rgba(56,189,248,0.8); }
    50%      { opacity: 0.4; text-shadow: 0 0 16px rgba(56,189,248,1); }
}

/* --- Buttons --- */
div.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #2563eb, #38bdf8) !important;
    color: #f0f9ff !important;
    border: 1px solid #38bdf8 !important;
    font-weight: 600 !important;
    animation: btnGlow 2.4s ease-in-out infinite;
}
@keyframes btnGlow {
    0%, 100% { box-shadow: 0 0 8px rgba(56,189,248,0.4); }
    50%      { box-shadow: 0 0 22px rgba(56,189,248,0.85); }
}
div.stButton > button[kind="secondary"] {
    background-color: #0b1220 !important;
    color: #cbe4ff !important;
    border: 1px solid #1e3a5f !important;
}
div.stButton > button[kind="secondary"]:hover {
    border-color: #38bdf8 !important;
    color: #38bdf8 !important;
    box-shadow: 0 0 10px rgba(56,189,248,0.4);
}

/* --- Tabs: glowing active indicator --- */
button[data-baseweb="tab"] { color: #6b8cb3 !important; }
button[data-baseweb="tab"][aria-selected="true"] {
    color: #38bdf8 !important;
    text-shadow: 0 0 8px rgba(56,189,248,0.5);
}
div[data-baseweb="tab-highlight"] {
    background-color: #38bdf8 !important;
    box-shadow: 0 0 10px rgba(56,189,248,0.8);
}

/* --- AI Summary code block: scanning light sweep --- */
div[data-testid="stCodeBlock"] {
    background-color: #060a14 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 10px !important;
    position: relative;
    overflow: hidden;
}
div[data-testid="stCodeBlock"]::before {
    content: "";
    position: absolute;
    top: 0; left: -30%;
    width: 30%; height: 2px;
    background: linear-gradient(90deg, transparent, #38bdf8, transparent);
    animation: scanLine 3.2s linear infinite;
}
@keyframes scanLine {
    0%   { left: -30%; }
    100% { left: 100%; }
}
div[data-testid="stCodeBlock"] pre {
    background-color: #060a14 !important;
    white-space: pre-wrap !important;
    word-break: break-word !important;
}
div[data-testid="stCodeBlock"] code {
    color: #dff0ff !important;
    background-color: transparent !important;
    font-size: 1.05rem !important;
    line-height: 1.7 !important;
    white-space: pre-wrap !important;
    word-break: break-word !important;
}

/* Expanders (Study Assistant panels) */
div[data-testid="stExpander"] {
    background-color: #0b1220 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 10px !important;
}
div[data-testid="stExpander"] summary {
    color: #dff0ff !important;
    font-weight: 600 !important;
}
div[data-testid="stExpander"] .stMarkdown p,
div[data-testid="stExpander"] .stMarkdown li {
    color: #cbe4ff !important;
}

/* Chat messages */
div[data-testid="stChatMessage"] {
    background-color: #0b1220 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 10px !important;
}
div[data-testid="stChatMessage"] p {
    color: #cbe4ff !important;
}

/* Info/warning/error banners */
div[data-testid="stAlert"] p {
    color: #030712 !important;
}

hr { border-color: #1e3a5f !important; }
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
                status.write("📁 Saving uploaded file…")
                job_id = uuid.uuid4().hex[:10]
                safe_name = f"{job_id}_{uploaded_file.name}"
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
    st.markdown("## 🤖 J.A.R.V.I.S.")
    st.caption("AI Video Summarizer")
    st.divider()

    st.markdown("### ⚙️ Settings")
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
    st.markdown("### 🕘 History")
    if st.session_state.videos:
        for jid, v in reversed(list(st.session_state.videos.items())):
            label = v["title"][:26] + ("…" if len(v["title"]) > 26 else "")
            if st.button(f"📼 {label}", key=f"hist_{jid}", use_container_width=True):
                st.session_state.current_job_id = jid
                st.session_state.video_start_time = 0
                st.rerun()
    else:
        st.caption("No videos processed yet this session.")

    st.divider()
    st.markdown("### 🧰 Tech Stack")
    st.caption("Faster-Whisper · Gemini / Ollama · Streamlit · FFmpeg · ReportLab")


# =============================================================================
# Header
# =============================================================================
st.markdown('<p class="jarvis-title">J.A.R.V.I.S<span>.</span></p>', unsafe_allow_html=True)
st.markdown('<p class="jarvis-sub">AI VIDEO SUMMARIZER DASHBOARD</p>', unsafe_allow_html=True)

model_display = "Gemini (3.7 Flash)" if st.session_state.ai_backend == "gemini" else "Ollama (Llama-3.1)"
st.markdown(
    f'<span class="status-badge"><span class="dot-online">●</span> STATUS: <b>ONLINE</b></span>'
    f'<span class="status-badge">MODEL: <b>{model_display}</b></span>',
    unsafe_allow_html=True,
)

st.write("")
c1, c2, c3, c4 = st.columns(4)
c1.metric("🎬 Videos Processed", st.session_state.stats_videos)
c2.metric("⏱️ Time Saved (hrs)", f"{st.session_state.stats_hours:.1f}")
c3.metric("🗂️ Sources Supported", 4)
c4.metric("✅ Success Rate", "99.8%")

st.divider()

# =============================================================================
# Process New Video
# =============================================================================
st.markdown("### 🎥 Process New Video")

tab_url, tab_upload = st.tabs(["🔗 YouTube URL", "📁 Upload File"])

with tab_url:
    youtube_url = st.text_input("Paste YouTube URL here…", key="yt_url_input", label_visibility="collapsed",
                                 placeholder="Paste YouTube URL here…")

    st.caption("Try an example:")
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

    if st.button("🚀 ANALYZE", type="primary", key="analyze_url_btn"):
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
        "Drop a video file here", type=["mp4", "mov", "webm", "mkv", "avi"],
        label_visibility="collapsed",
    )
    st.caption("MP4, MOV, WebM, MKV — up to 500MB")

    if st.button("🚀 ANALYZE", type="primary", key="analyze_upload_btn"):
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
    st.info("👆 Process a video above to see the AI summary, highlights, chapters, chat, and study tools here.")
else:
    col_preview, col_summary = st.columns([1, 1])

    with col_preview:
        st.markdown("#### 🎬 Video Preview")
        if result.get("source") == "upload":
            st.video(result["file_path"], start_time=st.session_state.video_start_time)
        elif result.get("source_url"):
            st.video(result["source_url"], start_time=st.session_state.video_start_time)
        st.markdown(f"**{result['title']}**")
        st.caption(f"{result.get('channel', 'Unknown')} · {format_duration(result.get('duration_seconds'))} · {result.get('source', 'Unknown')}")

    with col_summary:
        st.markdown("#### 🧠 AI Summary")
        st.code(result["summary"], language=None, wrap_lines=True)

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
        st.markdown("#### ⭐ Key Highlights")
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
        st.markdown("#### 📑 Smart Chapters")
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
        st.markdown("#### 💬 Chat with Video")
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
                        result["transcript"], result["title"], question, history,
                        backend=st.session_state.ai_backend,
                    )
                except Exception as e:
                    answer = f"Error: {e}"
            history.append({"role": "assistant", "content": answer})
            st.rerun()

    # ---------------- Study assistant ----------------
    with col_study:
        st.markdown("#### 📚 Study Assistant")
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
                for i, q in enumerate(study_state["viva-questions"]):
                    st.markdown(f"**Q{i+1}. {q.get('question','')}**")
                    st.caption(q.get("answer", ""))

        if study_state.get("mcq"):
            with st.expander("📋 MCQ Generator", expanded=True):
                for i, m in enumerate(study_state["mcq"]):
                    st.markdown(f"**Q{i+1}. {m.get('question','')}**")
                    for j, opt in enumerate(m.get("options", [])):
                        marker = "✅" if j == m.get("correct_index", -1) else "◻️"
                        st.write(f"{marker} {chr(65+j)}. {opt}")
                    if m.get("explanation"):
                        st.caption(m["explanation"])

        if study_state.get("flashcards"):
            with st.expander("🗂 Flashcards", expanded=True):
                for i, f in enumerate(study_state["flashcards"]):
                    st.markdown(f"**{f.get('front','')}**")
                    st.caption(f.get("back", ""))
                    st.write("")
