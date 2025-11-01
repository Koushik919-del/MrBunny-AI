import streamlit as st
import requests
import json
from mrbunny_secrets import OPENROUTER_API_KEY

# --- App Setup ---
st.set_page_config(page_title="MrBunny AI", page_icon="🐰", layout="wide")
st.markdown("<h1 style='text-align:center; color:#FF66B2;'>🐰 MrBunny AI</h1>", unsafe_allow_html=True)

# --- Session State Setup ---
if "chats" not in st.session_state:
    st.session_state.chats = {"Chat 1": []}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Chat 1"

# --- Sidebar UI ---
st.sidebar.title("💬 Chats")

# Chat selection dropdown
chat_names = list(st.session_state.chats.keys())
selected_chat = st.sidebar.selectbox(
    "Select a chat:", chat_names, index=chat_names.index(st.session_state.current_chat)
)
st.session_state.current_chat = selected_chat

# New chat button
if st.sidebar.button("➕ New Chat"):
    new_name = f"Chat {len(st.session_state.chats) + 1}"
    st.session_state.chats[new_name] = []
    st.session_state.current_chat = new_name
    st.experimental_rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("Made with 💖 by Bunny")

# --- Chat Display Area ---
messages = st.session_state.chats[st.session_state.current_chat]

for msg in messages:
    if msg["role"] == "user":
        st.markdown(f"<div style='background:#FFD6E8; padding:10px; border-radius:10px; margin:5px 0;'><b>You:</b> {msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='background:#F0F0F0; padding:10px; border-radius:10px; margin:5px 0;'><b>MrBunny:</b> {msg['content']}</div>", unsafe_allow_html=True)

# --- Input Box ---
user_input = st.chat_input("Type your message here...")

if user_input:
    messages.append({"role": "user", "content": user_input})

    # --- OpenRouter API Call ---
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": messages,
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, data=json.dumps(data))
        result = response.json()
        ai_reply = result["choices"][0]["message"]["content"]

    except Exception as e:
        ai_reply = f"⚠️ Error: {e}"

    messages.append({"role": "assistant", "content": ai_reply})

    st.experimental_rerun()
