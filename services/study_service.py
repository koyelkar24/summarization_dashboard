"""
Powers the Study Assistant panel: exam notes, viva questions, an MCQ
generator, and flashcards — all derived from the video transcript.
"""
from services.llm_client import chat_completion, safe_json_parse


def generate_exam_notes(transcript_text: str, video_title: str, backend: str = None) -> str:
    system = (
        "You write concise, well-structured exam revision notes from a "
        "video transcript, using headings and bullet points. The transcript "
        "may be in any language — always write the notes in English "
        "regardless of the transcript's language."
    )
    user = (
        f"Video title: {video_title}\n\nTranscript:\n{transcript_text[:12000]}\n\n"
        "Produce revision notes: a short overview, then key concepts as "
        "bullet points grouped under headings, then a 'must remember' list."
    )
    return chat_completion(system, user, backend=backend).strip()


def generate_viva_questions(transcript_text: str, video_title: str, count: int = 8, backend: str = None) -> list:
    system = (
        "You write viva/oral-exam questions with model answers based on a "
        "video transcript. The transcript may be in any language — always "
        "write questions and answers in English regardless of the "
        "transcript's language. Respond ONLY with valid JSON."
    )
    user = (
        f"Video title: {video_title}\n\nTranscript:\n{transcript_text[:12000]}\n\n"
        f'Write {count} viva questions. Return JSON: '
        '{"questions": [{"question": "...", "answer": "short model answer"}]}'
    )
    raw = chat_completion(system, user, json_mode=True, backend=backend)
    return safe_json_parse(raw, {"questions": []}).get("questions", [])


def generate_mcqs(transcript_text: str, video_title: str, count: int = 6, backend: str = None) -> list:
    system = (
        "You write multiple-choice questions from a video transcript. The "
        "transcript may be in any language — always write questions, "
        "options, and explanations in English regardless of the "
        "transcript's language. Respond ONLY with valid JSON."
    )
    user = (
        f"Video title: {video_title}\n\nTranscript:\n{transcript_text[:12000]}\n\n"
        f'Write {count} MCQs. Return JSON: {{"mcqs": [{{"question": "...", '
        '"options": ["A", "B", "C", "D"], "correct_index": 0, "explanation": "..."}}]}}'
    )
    raw = chat_completion(system, user, json_mode=True, backend=backend)
    return safe_json_parse(raw, {"mcqs": []}).get("mcqs", [])


def generate_flashcards(transcript_text: str, video_title: str, count: int = 10, backend: str = None) -> list:
    system = (
        "You write flashcards (term/definition or question/answer pairs) "
        "from a video transcript. The transcript may be in any language — "
        "always write flashcards in English regardless of the transcript's "
        "language. Respond ONLY with valid JSON."
    )
    user = (
        f"Video title: {video_title}\n\nTranscript:\n{transcript_text[:12000]}\n\n"
        f'Write {count} flashcards. Return JSON: {{"flashcards": [{{"front": "...", "back": "..."}}]}}'
    )
    raw = chat_completion(system, user, json_mode=True, backend=backend)
    return safe_json_parse(raw, {"flashcards": []}).get("flashcards", [])