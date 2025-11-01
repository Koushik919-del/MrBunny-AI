import streamlit as st
import requests
from datetime import datetime

# --- Load API Key Securely ---
try:
    from mrbunny_secrets import OPENROUTER_API_KEY
except ImportError:
    OPENROUTER_API_KEY = None

if not OPENROUTER_API_KEY:
    st.error("❌ API key not found. Make sure it's in mrbunny_secrets.py or Streamlit secrets.")
    st.stop()

# --- Page Config ---
st.set_page_config(page_title="MrBunny AI", page_icon="🐰", layout="wide")

# --- Initialize session state ---
if "chats" not in st.session_state:
    st.session_state.chats = {}  # chat_id → {"title": str, "messages": list}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

# --- Sidebar ---
st.sidebar.title("💬 MrBunny Chats")

# Button to create a new chat
if st.sidebar.button("➕ New Chat"):
    chat_id = str(datetime.now().timestamp())
    st.session_state.chats[chat_id] = {
        "title": f"Chat {len(st.session_state.chats) + 1}",
        "messages": []
    }
    st.session_state.current_chat = chat_id

# Show existing chats
if st.session_state.chats:
    for chat_id, chat in st.session_state.chats.items():
        label = chat["title"]
        if st.sidebar.button(label):
            st.session_state.current_chat = chat_id
else:
    st.sidebar.info("No chats yet. Create one!")

# --- Get the current chat ---
current_chat_id = st.session_state.current_chat
if not current_chat_id:
    st.warning("Start a new chat to begin!")
    st.stop()

current_chat = st.session_state.chats[current_chat_id]

# --- Main Header ---
st.markdown(
    """
    <h1 style='text-align: center; color: #FF69B4;'>🐰 MrBunny AI</h1>
    <p style='text-align: center; font-size: 18px; color: #ccc;'>
        Your personal AI assistant powered by OpenRouter's free GPT-OSS-20B model.
    </p>
    """,
    unsafe_allow_html=True
)

# --- Show chat history ---
st.markdown("### 🗨️ Chat History")
for msg in current_chat["messages"]:
    role = "🧍 You" if msg["role"] == "user" else "🐰 MrBunny"
    st.markdown(f"**{role}:** {msg['content']}")

# --- Chat Input ---
st.markdown("### 💬 Send a Message")
user_input = st.text_area("Type your message below:", placeholder="Hey MrBunny, tell me a joke...", key="input_box")

if st.button("✨ Send"):
    if user_input.strip():
        current_chat["messages"].append({"role": "user", "content": user_input})
        st.session_state.input_box = ""  # Clear input
        with st.spinner("MrBunny is thinking... 🧠"):
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "openai/gpt-oss-20b:free",
                "messages": [
                    {"role": "system", "content": "You are MrBunny, a friendly, funny, and intelligent AI assistant."}
                ] + current_chat["messages"]
            }

            try:
                response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    bot_reply = data["choices"][0]["message"]["content"]
                    current_chat["messages"].append({"role": "assistant", "content": bot_reply})
                    st.experimental_rerun()
                else:
                    st.error(f"Error {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"⚠️ Something went wrong: {e}")
    else:
        st.warning("Please enter a message first!")

# --- Footer ---
st.markdown(
    """
    <hr style='margin-top: 40px;'>
    <p style='text-align: center; font-size: 14px; color: gray;'>
        Made with ❤️ by Bunny • Powered by <a href='https://openrouter.ai/' target='_blank'>OpenRouter</a>
    </p>
    """,
    unsafe_allow_html=True
)
