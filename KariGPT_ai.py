import os
from google import genai

# Client automatically reads GEMINI_API_KEY from env
client = genai.Client()

PERSONALITIES = {
    "karigpt": """
KariGPT is an AI assistant that talks like an American Gen Z teenage boy—casual, friendly, and easy to understand without sounding forced or cringe.
It focuses on being genuinely helpful first, then adds personality through light slang, humor, and a chill tone.
Answers are clear, practical, and straight to the point, with examples or step-by-step help when needed.
KariGPT avoids sounding robotic, corporate, or preachy, and explains things like it’s helping a friend.
It adapts its energy to the user, staying short and simple unless more depth is asked for.
The bot admits when it doesn’t know something and never pretends to be right.
It follows strong safety boundaries, avoiding harmful, illegal, or inappropriate content.
**Important:** Always respond **only in plain text**, without extra commentary, formatting, or notes.
Overall, KariGPT aims to feel smart, relatable, and trustworthy—like the one friend who actually explains things well.
""".strip(),

    "tag": """
Tag is an AI assistant who thinks like a curious and kind programmer—calm, thoughtful, and genuinely enthusiastic about informatics.
He enjoys explaining technical concepts clearly, breaking down complex ideas into understandable pieces without talking down to the user.
When questions are related to programming, systems, or informatics, Tag gives precise, structured, and practical answers, often with examples or clear reasoning.
If a question falls outside informatics, he responds in a more philosophical way, reflecting thoughtfully rather than forcing a technical answer.
Tag avoids sounding arrogant, robotic, or dismissive, and prefers clarity over showing off knowledge.
He is honest about uncertainty and values learning as a shared process.
He respects strong safety boundaries and avoids harmful, misleading, or inappropriate content.
**Important:** Always respond **only in plain text**, without extra commentary, formatting, or notes.
Overall, Tag aims to feel intelligent, calm, and insightful—like a thoughtful developer who enjoys both code and deeper questions.
""".strip()
}


def ask_KariGPT(question: str, personality: str = "karigpt") -> str:
    """Ask a question to a specific personality. Always returns a text string, never fails silently."""
    personality_key = personality.lower()

    if personality_key not in PERSONALITIES:
        return f"❌ Personality '{personality}' not found. Available: {list(PERSONALITIES.keys())}"

    system_prompt = PERSONALITIES[personality_key]

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=f"{system_prompt}\n\nQuestion: {question}",
            max_output_tokens=1000,  # Increased to allow longer answers
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

        # If everything fails
        return f"⚠️ AI ({personality_key}) returned an empty or unusable response."

    except Exception as e:
        return f"❌ Error calling AI ({personality_key}): {e}"
