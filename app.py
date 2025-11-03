# ============================================
# 🧩 AUTO-INSTALL REQUIREMENTS (ON STARTUP)
# ============================================
import subprocess, sys, os

if os.path.exists("requirements.txt"):
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], stdout=subprocess.DEVNULL)

# ============================================
# 🚀 IMPORTS
# ============================================
import streamlit as st
from mrbunny_secrets import GOOGLE_CLIENT_ID
import requests
from mrbunny_secrets import OPENROUTER_API_KEY

# ============================================
# 🌐 GOOGLE SIGN-IN
# ============================================
st.set_page_config(
    page_title="MrBunny AI",
    page_icon="🐰",
    layout="centered"
)

st.title("MrBunny AI 🐰")

user_info = login(
    auth_provider="google",
    client_id=GOOGLE_CLIENT_ID,
    logout_button_text="Sign out",
    key="auth"
)

if not user_info:
    st.stop()

st.sidebar.success(f"Welcome, {user_info['name']} 👋")
st.sidebar.caption(user_info['email'])

# Create unique memory file per user
user_email = user_info["email"].replace("@", "_").replace(".", "_")
chat_file = f"chats_{user_email}.json"

# ============================================
# 🎨 CUSTOM CSS (Tony Stark / Futuristic Style)
# ============================================
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

# ============================================
# 🧠 SESSION STATE
# ============================================
if "chats" not in st.session_state:
    st.session_state.chats = {"Main Chat": []}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Main Chat"

if "conversations" not in st.session_state:
    st.session_state.conversations = {}
if "current_convo" not in st.session_state:
    st.session_state.current_convo = None
if "rename_mode" not in st.session_state:
    st.session_state.rename_mode = set()

# ============================================
# ⚙️ CONVERSATION MANAGEMENT
# ============================================
def add_convo(name: str):
    convo_id = str(len(st.session_state.conversations) + 1)
    st.session_state.conversations[convo_id] = {"name": name, "messages": []}
    st.session_state.current_convo = convo_id

def rename_convo(convo_id: str, new_name: str):
    if convo_id in st.session_state.conversations:
        st.session_state.conversations[convo_id]["name"] = new_name

def delete_convo(convo_id: str):
    if convo_id in st.session_state.conversations:
        del st.session_state.conversations[convo_id]
        if st.session_state.current_convo == convo_id:
            st.session_state.current_convo = None

# ============================================
# 💬 SIDEBAR (Chat Management)
# ============================================
with st.sidebar:
    st.title("💬 Conversations")

    with st.form("new_convo_form", clear_on_submit=True):
        new_convo_name = st.text_input("➕ Create New Conversation", key="new_convo_name")
        create_clicked = st.form_submit_button("Create")
        if create_clicked and (new_convo_name or "").strip():
            add_convo(new_convo_name.strip())
            st.rerun()

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

# ============================================
# 🤖 OPENROUTER RESPONSE
# ============================================
def get_mrbunny_response(prompt, history):
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

# ============================================
# 🗨️ CHAT DISPLAY
# ============================================
st.markdown("<h1 style='text-align: center; color: #00ffff;'>🐰 MrBunny AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Your futuristic AI companion</p>", unsafe_allow_html=True)

chat_history = st.session_state.chats[st.session_state.current_chat]
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

for chat in chat_history:
    st.markdown(f"<div class='chat-bubble user-bubble'><b>You:</b> {chat['user']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='chat-bubble bot-bubble'><b>MrBunny:</b> {chat['bot']}</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ============================================
# ⌨️ CHAT INPUT
# ============================================
user_input = st.chat_input("Type your message here...")

if user_input:
    with st.spinner("MrBunny AI is thinking... 🧠"):
        reply = get_mrbunny_response(user_input, chat_history)
    chat_history.append({"user": user_input, "bot": reply})
    st.session_state.chats[st.session_state.current_chat] = chat_history
    st.rerun()

# ============================================
# ❤️ FOOTER
# ============================================
st.markdown("---")
st.markdown("<p style='text-align:center; color:#888;'>Made with ❤️ by Koushik Tummepalli</p>", unsafe_allow_html=True)
