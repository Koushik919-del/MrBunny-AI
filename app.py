import subprocess, sys, os
import streamlit as st
import requests
import io
from gtts import gTTS
from streamlit_oauth import OAuth2Component

# 🧩 AUTO-INSTALL REQUIREMENTS
if os.path.exists("requirements.txt"):
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], stdout=subprocess.DEVNULL)

# 🔑 IMPORT SECRETS
try:
    from mrbunny_secrets import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, OPENROUTER_API_KEY
except ImportError:
    st.error("mrbunny_secrets.py not found!")
    st.stop()

# ============================================
# 🌐 GOOGLE SIGN-IN CONFIG (UPDATED SYNTAX)
# ============================================
REDIRECT_URI = "https://mrbunny-ai.streamlit.app"

# The latest version of streamlit-oauth expects 'authorize_endpoint' 
# and 'token_endpoint' as strings.
oauth2 = OAuth2Component(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    authorize_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
    token_endpoint="https://oauth2.googleapis.com/token",
    refresh_token_endpoint="https://oauth2.googleapis.com/token",
    # Notice: some versions don't want redirect_uri here, but 
    # if it's required, keep the line below.
    redirect_uri=REDIRECT_URI
)
# ============================================
# 🎨 CUSTOM CSS
# ============================================
st.markdown("""
    <style>
        .stApp { background: radial-gradient(circle at top left, #0a0f24, #03060d); color: white; }
        .stChatInput input { background-color: #1c1f2b !important; color: #fff !important; border: 1px solid #00ffff50 !important; }
        .stButton>button { background: linear-gradient(90deg, #007bff, #00ffff); color: white; border: none; box-shadow: 0 0 15px #00ffff70; border-radius: 8px; }
        .chat-bubble { padding: 12px; border-radius: 12px; margin: 5px 0; max-width: 80%; line-height: 1.5; }
        .user-bubble { background-color: #0055ff30; border: 1px solid #007bff; margin-left: auto; color: #e0e0e0; }
        .bot-bubble { background-color: #00ffff20; border: 1px solid #00ffff; margin-right: auto; color: #ffffff; }
    </style>
""", unsafe_allow_html=True)

# ============================================
# 🧠 AUTHENTICATION FLOW
# ============================================
if "user_info" not in st.session_state:
    result = oauth2.authorize_button(
        name="Sign in with Google",
        icon="🔑",
        scopes=["openid", "email", "profile"],
        key="google_login",
        redirect_uri=REDIRECT_URI,
    )
    if result and "token" in result:
        st.session_state["user_info"] = oauth2.get_user_info(result["token"])
        st.rerun()
    else:
        st.warning("Please sign in with Google to enter the AI terminal.")
        st.stop()

# ============================================
# ⚙️ CHAT INITIALIZATION
# ============================================
if "conversations" not in st.session_state:
    st.session_state.conversations = {"Main Chat": []}
if "current_convo" not in st.session_state:
    st.session_state.current_convo = "Main Chat"

# ============================================
# 💬 SIDEBAR
# ============================================
with st.sidebar:
    st.title("🐰 MrBunny AI")
    st.success(f"User: {st.session_state.user_info.get('name', 'Auth User')}")
    
    with st.form("new_chat_form", clear_on_submit=True):
        new_name = st.text_input("➕ New Chat")
        if st.form_submit_button("Create") and new_name.strip():
            st.session_state.conversations[new_name.strip()] = []
            st.session_state.current_convo = new_name.strip()
            st.rerun()

    st.markdown("---")
    for name in list(st.session_state.conversations.keys()):
        if st.button(name, key=f"btn_{name}", use_container_width=True):
            st.session_state.current_convo = name
            st.rerun()

# ============================================
# 🤖 AI & VOICE FUNCTIONS
# ============================================
def get_mrbunny_response(prompt, history):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    
    messages = [{"role": "system", "content": "You are MrBunny AI—witty and futuristic. Created by 14-year-old Koushik Tummepalli."}]
    for chat in history:
        messages.append({"role": "user", "content": chat["user"]})
        messages.append({"role": "assistant", "content": chat["bot"]})
    messages.append({"role": "user", "content": prompt})

    try:
        response = requests.post(url, headers=headers, json={"model": "openrouter/auto", "messages": messages})
        return response.json()["choices"][0]["message"]["content"]
    except:
        return "⚠️ Neural connection error."

def speak(text):
    tts = gTTS(text=text, lang='en')
    audio_data = io.BytesIO()
    tts.write_to_fp(audio_data)
    return audio_data

# ============================================
# 🗨️ MAIN CHAT INTERFACE
# ============================================
st.markdown(f"<h1 style='text-align: center; color: #00ffff;'>{st.session_state.current_convo}</h1>", unsafe_allow_html=True)

chat_history = st.session_state.conversations[st.session_state.current_convo]

for chat in chat_history:
    st.markdown(f"<div class='chat-bubble user-bubble'><b>You:</b> {chat['user']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='chat-bubble bot-bubble'><b>MrBunny:</b> {chat['bot']}</div>", unsafe_allow_html=True)

user_input = st.chat_input("Message MrBunny...")

if user_input:
    with st.spinner("Calculating..."):
        reply = get_mrbunny_response(user_input, chat_history)
        chat_history.append({"user": user_input, "bot": reply})
        st.session_state.conversations[st.session_state.current_convo] = chat_history
        st.rerun()

if chat_history:
    with st.sidebar:
        st.markdown("---")
        if st.button("🔊 Voice Sync"):
            audio = speak(chat_history[-1]['bot'])
            st.audio(audio, format="audio/mp3")

st.sidebar.markdown("<p style='text-align:center; font-size: 10px;'>Made by Koushik Tummepalli</p>", unsafe_allow_html=True)
