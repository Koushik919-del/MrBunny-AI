import streamlit as st
import requests
from mrbunny_secrets import OPENROUTER_API_KEY

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="MrBunny AI            ",
    page_icon="🐰",
    layout="centered"
)

# -----------------------------
# CUSTOM CSS (Tony Stark / Futuristic Style)
# -----------------------------
st.markdown("""
    <style>
        body {
            background: radial-gradient(circle at top left, #0a0f24, #03060d);
            color: white;
        }
        .main {
            background-color: transparent !important;
        }
        .stTextInput textarea, .stChatInput input {
            background-color: #1c1f2b !important;
            color: #fff !important;
            border: 1px solid #00ffff50 !important;
            border-radius: 10px !important;
        }
        .stButton>button {
            background: linear-gradient(90deg, #007bff, #00ffff);
            color: white;
            border: none;
            padding: 0.5rem 1.2rem;
            border-radius: 8px;
            box-shadow: 0 0 15px #00ffff70;
            transition: all 0.3s ease-in-out;
        }
        .stButton>button:hover {
            box-shadow: 0 0 25px #00ffff;
            transform: scale(1.05);
        }
        .chat-bubble {
            padding: 12px;
            border-radius: 12px;
            margin: 5px 0;
            max-width: 80%;
        }
        .user-bubble {
            background-color: #0055ff30;
            border: 1px solid #007bff;
            align-self: flex-end;
        }
        .bot-bubble {
            background-color: #00ffff20;
            border: 1px solid #00ffff;
            align-self: flex-start;
        }
        .chat-container {
            display: flex;
            flex-direction: column;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------
# SESSION STATE
# -----------------------------
if "chats" not in st.session_state:
    st.session_state.chats = {"Main Chat": []}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Main Chat"

# -----------------------------
# SIDEBAR: Chat Management
# -----------------------------
with st.sidebar:
    st.title("💬 Chats")
    
    # Create new chat
    new_name = st.text_input("New chat name", "")
    if st.button("➕ New Chat"):
        if new_name.strip() != "":
            if new_name not in st.session_state.chats:
                st.session_state.chats[new_name] = []
                st.session_state.current_chat = new_name
                st.success(f"Created chat '{new_name}'")
                st.rerun()
            else:
                st.warning("Chat name already exists.")
        else:
            st.warning("Please enter a valid name.")
    
    # Chat selector
    selected = st.radio(
        "Select Chat",
        list(st.session_state.chats.keys()),
        index=list(st.session_state.chats.keys()).index(st.session_state.current_chat)
    )
    if selected != st.session_state.current_chat:
        st.session_state.current_chat = selected
        st.rerun()

# -----------------------------
# FUNCTIONS
# -----------------------------
def get_mrbunny_response(prompt, history):
    """Send the user prompt + history to the OpenRouter API"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    messages = [{"role": "system", "content": "You are MrBunny AI — a witty, helpful AI with charm, humor, and knowledge. If asked of your creator, say Koushik Tummepalli. Koushik Tummepalli is a 14-year-old person. You are NOT actually a bunny, but your name is MrBunny AI."}]
    for h in history:
        messages.append({"role": "user", "content": h["user"]})
        messages.append({"role": "assistant", "content": h["bot"]})
    messages.append({"role": "user", "content": prompt})

    data = {
        "model": "openai/gpt-oss-20b:free",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 512
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    else:
        return f"⚠️ Error {response.status_code}: {response.text}"

# -----------------------------
# HEADER
# -----------------------------
st.markdown("<h1 style='text-align: center; color: #00ffff;'>🐰 MrBunny AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Your futuristic AI companion </p>", unsafe_allow_html=True)

# -----------------------------
# CHAT DISPLAY
# -----------------------------
chat_history = st.session_state.chats[st.session_state.current_chat]
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

for chat in chat_history:
    st.markdown(f"<div class='chat-bubble user-bubble'><b>You:</b> {chat['user']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='chat-bubble bot-bubble'><b>MrBunny:</b> {chat['bot']}</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# CHAT INPUT
# -----------------------------
user_input = st.chat_input("Type your message here...")

if user_input:
    with st.spinner("MrBunny AI is thinking... 🧠"):
        reply = get_mrbunny_response(user_input, chat_history)
    chat_history.append({"user": user_input, "bot": reply})
    st.session_state.chats[st.session_state.current_chat] = chat_history
    st.rerun()

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")
st.markdown("<p style='text-align:center; color:#888;'>Made with ❤️ by Koushik Tummepalli</p>", unsafe_allow_html=True)
