import json
import requests
import os
from google import genai
from google.genai import types

from config import (
    OLLAMA_HOST, OLLAMA_MODEL,
    GEMINI_API_KEY, GEMINI_MODEL
)

# Initialize official Gemini client
gemini_client = None
if GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception:
        gemini_client = None


def chat_completion(system_prompt: str, user_prompt: str, backend: str = "gemini", json_mode: bool = False) -> str:
    """
    Routes requests to either Gemini (Cloud) or Ollama (Local).
    """
    
    # We map any "cloud" backend string directly to Gemini
    if backend in ("gemini", "openai", "groq"):  
        if not GEMINI_API_KEY or not gemini_client:
            raise ValueError("GEMINI_API_KEY is missing or invalid in your secrets.toml or .env file.")

        # Combine system and user prompt for Gemini
        prompt = f"System Instructions:\n{system_prompt}\n\nUser Request:\n{user_prompt}"
        
        config = types.GenerateContentConfig(
            response_mime_type="application/json" if json_mode else "text/plain",
            temperature=0.3
        )
        
        # --- BULLETPROOF MODEL CLEANING ---
        # 1. Get the raw string or fallback
        raw_model = GEMINI_MODEL if GEMINI_MODEL else "gemini-3.6-flash"
        
        # 2. Strip hidden spaces and invisible newlines
        valid_model = raw_model.strip()
        
        # 3. Strip any accidental quotation marks
        valid_model = valid_model.strip("'\"")
        
        # 4. Force lowercase and replace spaces with hyphens (Catch-all for typos like "Gemini 1.5 Pro")
        valid_model = valid_model.lower().replace(" ", "-")
        
        # 5. Strip the old "models/" prefix if it's still there
        if valid_model.startswith("models/"):
            valid_model = valid_model.lower().replace(" ", "-")   # <-- add this line
            valid_model = valid_model.replace("models/", "")
        # ----------------------------------
        
        response = gemini_client.models.generate_content(
            model=valid_model,
            contents=prompt,
            config=config
        )
        return response.text

    else:
        # Local Ollama
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        payload = {
            "model": OLLAMA_MODEL or "llama3.1:8b",
            "messages": messages,
            "stream": False
        }
        if json_mode:
            payload["format"] = "json"

        # Increased timeout to 5 minutes (300 seconds) for local processing
        response = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=300)
        response.raise_for_status()
        return response.json()["message"]["content"]


def safe_json_parse(text: str, default=None):
    """Safely extracts and parses JSON out of Markdown code fences."""
    if default is None:
        default = {}
    try:
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return json.loads(cleaned.strip())
    except Exception:
        return default