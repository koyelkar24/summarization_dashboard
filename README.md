# J.A.R.V.I.S. Video Summarizer

A Streamlit app that summarizes YouTube videos and uploaded video files. It
creates a transcript, summary, key highlights, smart chapters, video Q&A, and
study materials (exam notes, viva questions, MCQs, and flashcards). The app can
use a local Ollama model or Google's Gemini API.

## How it works

1. It loads captions from YouTube when available. Otherwise, it downloads the
   video audio, extracts a 16 kHz mono WAV with FFmpeg, and transcribes it with
   Faster Whisper. Uploaded videos use the audio transcription path.
2. The selected language model creates the summary, highlights, chapters, and
   optional Q&A or study materials.
3. The app offers PDF and TXT downloads of the summary.

Video processing is synchronous and runs in the Streamlit session. The app
limits videos to 25,000 seconds and uploaded files to 500 MB.

## Setup

Install FFmpeg (including `ffprobe`), then install the Python dependencies:

```bash
# Debian / Ubuntu
sudo apt install ffmpeg

# macOS
brew install ffmpeg

python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS / Linux:      source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and configure at least one model backend.

**Ollama (local):** Install Ollama, then run `ollama pull llama3.1`. Keep the
Ollama service running while using the app. Ollama is the default backend.

**Gemini (cloud):** Set `GEMINI_API_KEY` in `.env`, then choose Gemini in the
sidebar. `GEMINI_MODEL` can override the model name.

Start the app:

```bash
streamlit run streamlit_app.py
```

Open <http://localhost:8501> if the browser does not open automatically.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `AI_BACKEND` | `ollama` | Initial backend: `ollama` or `gemini` |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.1` | Local model name |
| `GEMINI_API_KEY` | empty | Gemini API key; required for Gemini |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Gemini model name |
| `WHISPER_MODEL_SIZE` | `tiny` | Faster Whisper model size |
| `WHISPER_DEVICE` | `cpu` | Whisper device, such as `cpu` or `cuda` |
| `WHISPER_COMPUTE_TYPE` | `int8` | Whisper compute type |
| `FFMPEG_LOCATION` | empty | Optional folder containing `ffmpeg` and `ffprobe` |
| `YOUTUBE_COOKIES_FILE` | empty | Optional path to a YouTube cookies file |

YouTube cookie contents can also be supplied as `YOUTUBE_COOKIES_CONTENT`.
Keep API keys and cookie data out of source control.

The app keeps video history, chat, and study results in Streamlit session
state. They are cleared when the session or app restarts. Uploaded and
downloaded videos, extracted audio, and exports are written to local folders.
