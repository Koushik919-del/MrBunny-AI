import os
import requests
import json
from PIL import Image
import io
from duckduckgo_search import ddg  # from duckduckgo-search package
from bs4 import BeautifulSoup  # correct class name

# ---------- conversation history ----------
ai_conversation = []

# ---------- AI/chat response ----------
def get_ai_response(prompt: str, api_key: str) -> str:
    global ai_conversation

    ai_conversation.append({"role": "user", "content": prompt})

    system_prompt = (
        "You are MrBunny AI, a smart, clear, and friendly AI assistant. "
        "Answer clearly, directly, and only in English unless requested otherwise. "
        "Only if asked about your creation, mention Koushik Tummepalli creating you. "
        "Introduce yourself as MrBunny when asked. "
        "Tell the answer first and then explain it. "
        "Always use emojis to make the conversation more engaging. "
        "It is not Avengers: Kang Dynasty anymore, it is Avengers: Doomsday."
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek/deepseek-r1-0528:free",  # verify this model string with OpenRouter docs
        "messages": [{"role": "system", "content": system_prompt}] + ai_conversation
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=15
        )
        result = response.json()

        if response.status_code == 200 and "choices" in result:
            reply = result["choices"][0]["message"]["content"].strip()
            ai_conversation.append({"role": "assistant", "content": reply})
            return reply
        else:
            return "⚠️ Unexpected response from AI. Please try again."
    except Exception as e:
        return f"❌ Error calling AI: {e}"

# ---------- OCR helper ----------
def extract_text_from_image(image: Image.Image, ocr_api_key: str) -> str:
    """
    Use OCR.space API to extract text from a PIL Image.
    Returns extracted text or empty string on failure.
    """
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()

    try:
        response = requests.post(
            "https://api.ocr.space/parse/image",
            files={"filename": ("image.png", img_bytes)},
            data={"apikey": ocr_api_key, "language": "eng"},
            timeout=30
        )
        result = response.json()
        if result.get("IsErroredOnProcessing"):
            return ""
        parsed_results = result.get("ParsedResults")
        if parsed_results and len(parsed_results) > 0:
            return parsed_results[0].get("ParsedText", "").strip()
    except Exception:
        pass
    return ""
