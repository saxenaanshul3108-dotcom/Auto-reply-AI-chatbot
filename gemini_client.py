"""
Handles all communication with the Gemini API and keeps a separate
conversation history per WhatsApp contact, so replies stay contextual.
"""

import os
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

from config import PERSONA_PROMPT, MODEL_NAME, MAX_HISTORY_TURNS

load_dotenv()  # reads GEMINI_API_KEY from your .env file

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found. Copy .env.example to .env and add your key."
    )

genai.configure(api_key=api_key)
model = genai.GenerativeModel(MODEL_NAME, system_instruction=PERSONA_PROMPT)

# In-memory chat sessions, one per contact name. Resets when the script restarts.
_chat_sessions = {}


def get_ai_reply(contact_name: str, message: str) -> str:
    """Generate an AI reply for a given contact, keeping conversation context."""
    if contact_name not in _chat_sessions:
        _chat_sessions[contact_name] = model.start_chat(history=[])

    session = _chat_sessions[contact_name]

    # Trim history so we don't send an ever-growing conversation to the API
    if len(session.history) > MAX_HISTORY_TURNS * 2:
        session.history = session.history[-MAX_HISTORY_TURNS * 2:]

    response = session.send_message(message)
    return response.text.strip()