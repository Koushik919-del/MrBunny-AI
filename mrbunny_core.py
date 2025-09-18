import os
import requests
import json
from PIL import Image
import io
from duckduckgo_search import ddg
from bs4 import BeautifulSoup

# ---------- uncertainty detection ----------
UNCERTAIN_PHRASES = [
    "no evidence", "not confirmed", "no official announcement",
    "i couldn't find", "not available", "uncertain", "speculative",
    "does not exist", "not verified", "unconfirmed", "unknown",
    "nothing has been announced", "as of now"
]

def is_uncertain(response: str) -> bool:
    response_lower = response.lower()
    return any(phrase in response_lower for phrase in UNCERTAIN_PHRASES)

# ---------- conversation history ----------
ai_conversation = []

# ---------- fallback web search ----------
def search_web_duckduckgo(query: str, max_results: int = 3) -> str:
    results = ddg(query, max_results=max_results)
    if not results:
        return "No useful search results found."

    summary_lines = []
    for i, item in enumerate(results, start=1):
        title = item.get("title") or "No title"
        snippet = item.get("body") or ""
        url = item.get("href") or item.get("link") or ""
        summary_lines.append(f"{i}. {title}\n{snippet}\n{url}\n")
    return "\n".join(summary_lines)

# ---------- AI/chat response ----------
def get_ai_response_v2(prompt: str, api_key: str) -> str:
    """
    Sends the prompt to OpenRouter AI and returns the response.
    Falls back to DuckDuckGo search if AI response is empty, malformed, or uncertain.
    """
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
        "model": "deepseek/deepseek-r1-0528:free",  # check with your OpenRouter docs
        "messages": [{"role": "system", "content": system_prompt}] + ai_conversation
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=15
        )
        response.raise_for_status()
        result = response.json()

        # Robustly extract AI reply
        reply = ""
        try:
            reply = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        except Exception:
            reply = ""

        if not reply or is_uncertain(reply):
            # fallback to web search if AI reply is empty or uncertain
            search_info = search_web_duckduckgo(prompt)
            fallback_msg = (
                "🔍 I wasn't confident about the answer, so I searched it for you:\n\n"
                f"{search_info}"
            )
            ai_conversation.append({"role": "assistant", "content": fallback_msg})
            return fallback_msg

        # Save valid reply to conversation history
        ai_conversation.append({"role": "assistant", "content": reply})
        return reply

    except requests.exceptions.RequestException as e:
        # network or HTTP error -> fallback
        search_info = search_web_duckduckgo(prompt)
        return f"❌ Network error: {e}\n\nFallback search:\n{search_info}"
    except json.JSONDecodeError:
        # malformed JSON -> fallback
        search_info = search_web_duckduckgo(prompt)
        return f"❌ Malformed AI response\n\nFallback search:\n{search_info}"
    except Exception as e:
        # unexpected error -> fallback
        search_info = search_web_duckduckgo(prompt)
        return f"❌ Unexpected error: {e}\n\nFallback search:\n{search_info}"

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
