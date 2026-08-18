# J.A.R.V.I.S. — AI Video Summarizer (Streamlit)

A single Streamlit app that takes a YouTube URL or an uploaded video file
and produces an AI summary, key highlights, smart chapters, a
chat-with-video assistant, and a study assistant (exam notes / viva
questions / MCQs / flashcards) — with a switchable local (Ollama) or cloud
(OpenAI) LLM backend, selectable right from the sidebar.

No Flask, no HTML/CSS/JS files — the whole UI is Python, rendered by
Streamlit.

## Pipeline

```
Get Video → Extract Audio → Transcribe → Analyze Content → Generate Summary → Deliver Results
```

1. **Get video** — `yt-dlp` pulls the YouTube video, or the uploaded file is saved directly.
2. **Extract audio** — `ffmpeg` converts the video to a 16kHz mono WAV.
3. **Transcribe** — `faster-whisper` produces a timestamped transcript, fully offline.
4. **Analyze** — an LLM call extracts key highlights and smart chapters from the transcript.
5. **Summarize** — an LLM call writes the final AI summary (short/medium/long).

All five steps run synchronously inside a live `st.status(...)` block, so
you see each stage update in real time without any polling or background
threads.

## Project layout

```
video-summarizer/
├── streamlit_app.py         # The entire UI + pipeline orchestration (single file)
├── config.py                 # Settings, paths, default AI backend
├── requirements.txt
├── .env.example                # Copy to .env and edit
├── services/
│   ├── downloader.py           # yt-dlp download / upload registration
│   ├── audio_extractor.py      # ffmpeg audio extraction
│   ├── transcriber.py          # faster-whisper transcription (cached via st.cache_resource)
│   ├── llm_client.py           # Ollama/OpenAI switch (chat_completion(), backend overridable per call)
│   ├── summarizer.py           # Summary, highlights, chapters
│   ├── chat_service.py         # Chat-with-video Q&A
│   ├── study_service.py        # Exam notes / viva / MCQ / flashcards
│   └── exporter.py             # PDF/TXT export (ReportLab)
├── uploads/                    # Uploaded/downloaded video files
├── transcripts/                 # Extracted audio + transcripts
└── outputs/                      # Exported PDF/TXT summaries
```

## Setup

### 1. System dependency: ffmpeg

```bash
sudo apt install ffmpeg        # Debian/Ubuntu
brew install ffmpeg            # macOS
```

### 2. Python environment

```bash
python -m venv venv
source venv/bin/activate       # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 3. Configure the AI backend

```bash
cp .env.example .env
```

This sets the *default* backend on first launch — you can also switch
between Ollama and OpenAI live from the sidebar dropdown without restarting.

**Option A — Ollama (free, local, works offline):**
```bash
# Install from https://ollama.com, then:
ollama pull llama3.1
ollama serve
```

**Option B — OpenAI (cloud):**
Set `OPENAI_API_KEY=sk-...` in `.env`, then pick "OpenAI (Cloud)" in the
sidebar once the app is running.

### 4. Run

```bash
streamlit run streamlit_app.py
```

Streamlit will open **http://localhost:8501** automatically.

## Notes for your viva/demo

- The AI Model dropdown in the sidebar is a *live* switch — every request
  (summary, highlights, chapters, chat, study tools) uses whichever backend
  is currently selected, no restart needed.
- Whisper's `base` model (set in `.env`) is a good speed/accuracy tradeoff
  for a laptop demo. Bump `WHISPER_MODEL_SIZE` to `small` or `medium` for
  better accuracy if you have the CPU budget.
- History, chat, and study results are stored in `st.session_state`, so
  they persist while you navigate the app but reset if you restart
  Streamlit — this is a single-user demo app, not a persisted database.
- The `st.code(...)` block used for the AI Summary has a built-in copy
  icon in its top-right corner — no custom "Copy" button needed.
- If a YouTube download fails, it's almost always `yt-dlp` needing an
  update (`pip install -U yt-dlp`) to keep up with YouTube's changes.
