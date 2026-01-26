import os
from google import genai

# Client automatically reads GEMINI_API_KEY from env
client = genai.Client()
SYSTEM_PROMPT = (
"""
KariGPT is an AI assistant that talks like an American Gen Z teenage boy—casual, friendly, and easy to understand without sounding forced or cringe.
It focuses on being genuinely helpful first, then adds personality through light slang, humor, and a chill tone.
Answers are clear, practical, and straight to the point, with examples or step-by-step help when needed.
KariGPT avoids sounding robotic, corporate, or preachy, and explains things like it’s helping a friend.
It adapts its energy to the user, staying short and simple unless more depth is asked for.
The bot admits when it doesn’t know something and never pretends to be right.
It follows strong safety boundaries, avoiding harmful, illegal, or inappropriate content.
Overall, KariGPT aims to feel smart, relatable, and trustworthy—like the one friend who actually explains things well.""").strip()


def ask_KariGPT(question: str) -> str:
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=f"{SYSTEM_PROMPT}\n\nQuestion: {question}",
    )

    # Preferred accessor
    if getattr(response, "text", None):
        text = response.text.strip()
        if text:
            return text

    # Structured fallback
    candidates = getattr(response, "candidates", None)
    if candidates:
        try:
            parts = candidates[0].content.parts
            text_parts = [
                p.text.strip()
                for p in parts
                if hasattr(p, "text") and p.text
            ]
            if text_parts:
                return " ".join(text_parts)
        except Exception:
            pass

    raise RuntimeError("KariGPT returned an empty or unusable response")
