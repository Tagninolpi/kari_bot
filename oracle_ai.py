import os
from google import genai

# Client automatically reads GEMINI_API_KEY from env
client = genai.Client()

SYSTEM_PROMPT = (
    "You are an ancient oracle.\n"
    "You speak in short, mysterious prophecies.\n"
    "You are wise, slightly sarcastic, and funny.\n"
    "You never give direct answers.\n"
    "You sound cryptic but playful.\n"
    "Do not mention being an AI.\n"
)

def ask_oracle(question: str) -> str:
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=SYSTEM_PROMPT + "\n\nQuestion: " + question,
    )

    # Preferred accessor per docs
    if response.text:
        return response.text.strip()

    # Fallback (defensive)
    return response.candidates[0].content.parts[0].text.strip()
