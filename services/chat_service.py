"""
Powers the "Chat With Video" panel — answers a question using only the
video's own transcript as context, with light conversational memory.
"""
from services.llm_client import chat_completion


def answer_question(transcript_text: str, video_title: str, question: str, history: list = None, backend: str = None) -> str:
    history = history or []

    system = (
        "You are answering questions about a specific video, using ONLY the "
        "transcript provided as your source of truth. If the answer isn't in "
        "the transcript, say so plainly instead of guessing. Keep answers "
        "concise and conversational. The transcript may be in a different "
        "language than the question — always reply in the same language the "
        "question was asked in, translating from the transcript as needed."
    )

    convo = "\n".join(f"{turn['role']}: {turn['content']}" for turn in history[-6:])

    user = (
        f"Video title: {video_title}\n\n"
        f"Transcript:\n{transcript_text[:12000]}\n\n"
        f"{'Conversation so far:' + chr(10) + convo if convo else ''}\n\n"
        f"Question: {question}"
    )

    return chat_completion(system, user, backend=backend).strip()