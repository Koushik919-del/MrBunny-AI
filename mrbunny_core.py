import streamlit as st
from PIL import Image
from uuid import uuid4
import os
import re
import tempfile
import requests
import io
from duckduckgo_search import ddg
import json

# ======= CORE FUNCTIONS (v2) =======

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

# ---------- AI/chat response (v2) ----------
def get_ai_response_v2(prompt: str, api_key: str) -> str:
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
        "model": "deepseek/deepseek-r1-0528:free",
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
        # Safely extract reply
        reply = (result.get("choices", [{}])[0].get("message", {}).get("content", "") or "").strip()

        if not reply or is_uncertain(reply):
            search_info = search_web_duckduckgo(prompt)
            fallback_msg = f"🔍 I wasn't sure, so I searched for you:\n\n{search_info}"
            ai_conversation.append({"role": "assistant", "content": fallback_msg})
            return fallback_msg

        ai_conversation.append({"role": "assistant", "content": reply})
        return reply

    except Exception as e:
        search_info = search_web_duckduckgo(prompt)
        return f"❌ Error calling AI: {e}\n\nFallback search:\n{search_info}"

# ---------- OCR helper ----------
def extract_text_from_image(image: Image.Image, ocr_api_key: str) -> str:
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

# ======= END OF CORE FUNCTIONS =======

# ==== STREAMLIT CONFIG ====
st.set_page_config(page_title="MrBunny AI", page_icon="🐰", layout="wide")

# ==== SESSION STATE ====
if "conversations" not in st.session_state:
    st.session_state.conversations = {}
if "current_convo" not in st.session_state:
    st.session_state.current_convo = None
if "show_image_uploader" not in st.session_state:
    st.session_state.show_image_uploader = False
if "user_text" not in st.session_state:
    st.session_state.user_text = ""
if "busy" not in st.session_state:
    st.session_state.busy = False
if "rename_mode" not in st.session_state:
    st.session_state.rename_mode = set()

# ==== UTILITIES ====
def remove_emojis(text):
    emoji_pattern = re.compile(
        "["u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r"", text)

def speak(text):
    from gtts import gTTS
    clean_text = remove_emojis(text)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        try:
            tts = gTTS(clean_text)
            tts.save(tmp.name)
            st.audio(tmp.name, format="audio/mp3")
        except Exception as e:
            st.warning(f"Audio generation failed: {e}")
        finally:
            try: os.remove(tmp.name)
            except OSError: pass

def add_convo(name):
    convo_id = str(uuid4())
    st.session_state.conversations[convo_id] = {"name": name, "messages": []}
    st.session_state.current_convo = convo_id

def delete_convo(convo_id):
    if convo_id in st.session_state.conversations:
        del st.session_state.conversations[convo_id]
        if st.session_state.current_convo == convo_id:
            st.session_state.current_convo = None

def rename_convo(convo_id, new_name):
    if convo_id in st.session_state.conversations:
        st.session_state.conversations[convo_id]["name"] = new_name

# ==== SIDEBAR ====
with st.sidebar:
    st.title("💬 Conversations")
    with st.form("new_convo_form", clear_on_submit=True):
        new_convo_name = st.text_input("➕ Create New Conversation", key="new_convo_name")
        if st.form_submit_button("Create") and (new_convo_name or "").strip():
            add_convo(new_convo_name.strip())
            st.rerun()
    # Manage existing conversations
    for convo_id, convo in list(st.session_state.conversations.items()):
        is_current = convo_id == st.session_state.current_convo
        row = st.container()
        cols = row.columns([0.75, 0.15, 0.1])
        label = f"👉 {convo['name']}" if is_current else convo["name"]
        if cols[0].button(label, key=f"select_{convo_id}"):
            st.session_state.current_convo = convo_id
            st.rerun()
        if cols[1].button("✏️", key=f"rename_btn_{convo_id}"):
            if convo_id in st.session_state.rename_mode:
                st.session_state.rename_mode.remove(convo_id)
            else:
                st.session_state.rename_mode.add(convo_id)
            st.rerun()
        if convo_id in st.session_state.rename_mode:
            new_name = st.text_input("Rename to:", value=convo["name"], key=f"rename_input_{convo_id}")
            if st.button("💾 Save", key=f"save_rename_{convo_id}"):
                clean_name = (new_name or "").strip()
                if clean_name:
                    rename_convo(convo_id, clean_name)
                st.session_state.rename_mode.remove(convo_id)
                st.rerun()
        if cols[2].button("🗑️", key=f"del_{convo_id}"):
            delete_convo(convo_id)
            st.rerun()

# ==== MAIN UI ====
st.title("🐰 MrBunny AI")
st.caption("Your friendly AI assistant")

# API keys
api_key = st.secrets.get("OPENROUTER_API_KEY")
ocr_api_key = st.secrets.get("OCR_API_KEY", "")

if not api_key:
    st.error("OpenRouter API key missing. Please add `OPENROUTER_API_KEY` to secrets.")
    st.stop()

if st.session_state.current_convo:
    convo = st.session_state.conversations[st.session_state.current_convo]

    # Display messages
    for idx, msg in enumerate(convo["messages"]):
        with st.container():
            st.markdown(f"**You:** {msg['user']}")
            st.markdown(
                f"<div style='background-color:#1f2937;padding:12px;border-radius:8px;color:#f8f9fa;'>🐰 {msg['ai']}</div>",
                unsafe_allow_html=True
            )
            fb_col1, fb_col2, fb_col3 = st.columns([0.1, 0.1, 0.8])
            with fb_col1:
                if st.button("🔊", key=f"speak_{idx}"):
                    speak(msg["ai"])
            with fb_col2:
                liked_key = f"liked_{idx}"
                disliked_key = f"disliked_{idx}"
                if st.button("👍", key=f"like_{idx}"):
                    st.session_state[liked_key] = True
                    st.session_state[disliked_key] = False
                if st.session_state.get(liked_key, False):
                    st.markdown("✅ Liked")
            with fb_col3:
                if st.button("👎", key=f"dislike_{idx}"):
                    st.session_state[f"liked_{idx}"] = False
                    st.session_state[f"disliked_{idx}"] = True
                if st.session_state.get(f"disliked_{idx}", False):
                    st.markdown("❌ Disliked")

    st.divider()

    # Input form
    with st.form("chat_form", clear_on_submit=True):
        input_col, send_col, plus_col = st.columns([6,1,1])
        user_text = input_col.text_input("Type your message:", key="user_text", disabled=st.session_state.busy)
        send_clicked = send_col.form_submit_button("Send")
        plus_clicked = plus_col.form_submit_button("➕")

        if plus_clicked:
            st.session_state.show_image_uploader = not st.session_state.show_image_uploader

        uploaded_file = None
        if st.session_state.show_image_uploader:
            uploaded_file = st.file_uploader("Upload an image", type=["png","jpg","jpeg"])

        if send_clicked and (user_text or "").strip() and not st.session_state.busy:
            st.session_state.busy = True
            combined_prompt = user_text.strip()
            if uploaded_file:
                try:
                    image = Image.open(uploaded_file).convert("RGB")
                    ocr_text = extract_text_from_image(image, ocr_api_key)
                    if ocr_text:
                        combined_prompt = f"[Image text extracted: {ocr_text}]\n\n{user_text.strip()}"
                except Exception as e:
                    st.warning(f"Failed to process uploaded image: {e}")
            with st.spinner("🐰 MrBunny is thinking..."):
                reply = get_ai_response_v2(combined_prompt, api_key)
            convo["messages"].append({"user": user_text.strip(), "ai": reply})
            st.session_state.busy = False
            st.rerun()
else:
    st.info("Create or select a conversation to begin chatting with MrBunny!")
