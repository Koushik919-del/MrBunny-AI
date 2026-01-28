import streamlit as st
import requests
import io
from gtts import gTTS
from mrbunny_secrets import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, OPENROUTER_API_KEY

# ============================================
# 🌐 GOOGLE AUTH CONFIG (MANUAL FLOW)
# ============================================
REDIRECT_URI = "https://mrbunny-ai.streamlit.app"
# Updated line:
AUTH_URL = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={GOOGLE_CLIENT_ID}&response_type=code&scope=openid%20email%20profile&redirect_uri={REDIRECT_URI}&prompt=select_account"

def get_google_user(code):
    # Exchange code for token
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    res = requests.post(token_url, data=data).json()
    access_token = res.get("access_token")
    # Get user info
    user_res = requests.get(f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}")
    return user_res.json()

# ============================================
# 🧠 AUTH LOGIC
# ============================================
if "user_info" not in st.session_state:
    # Check if we are returning from Google
    query_params = st.query_params
    if "code" in query_params:
        with st.spinner("Authenticating..."):
            user_data = get_google_user(query_params["code"])
            st.session_state.user_info = user_data
            st.query_params.clear()
            st.rerun()
    else:
        st.markdown(f"<h1 style='text-align:center; color:#00ffff;'>🐰 MrBunny AI</h1>", unsafe_allow_html=True)
        st.write("Welcome to the futuristic terminal. Please sign in.")
        st.markdown(f'<a href="{AUTH_URL}" target="_self"><button style="width:100%; padding:15px; background:linear-gradient(90deg, #007bff, #00ffff); border:none; border-radius:10px; color:white; font-weight:bold; cursor:pointer;">🔑 Sign in with Google</button></a>', unsafe_allow_html=True)
        st.stop()

# ============================================
# 🎨 UI & CHAT LOGIC (Unified)
# ============================================
st.set_page_config(page_title="MrBunny AI", page_icon="🐰")

if "conversations" not in st.session_state:
    st.session_state.conversations = {"Main Chat": []}
if "current_convo" not in st.session_state:
    st.session_state.current_convo = "Main Chat"

with st.sidebar:
    st.success(f"User: {st.session_state.user_info.get('name')}")
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()
    
    st.markdown("---")
    new_chat = st.text_input("➕ New Chat")
    if st.button("Create") and new_chat:
        st.session_state.conversations[new_chat] = []
        st.session_state.current_convo = new_chat
        st.rerun()

# --- OpenRouter Call ---
def ask_ai(prompt, history):
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    msgs = [{"role": "system", "content": "You are MrBunny AI, a witty AI created by 14-year-old Koushik Tummepalli."}]
    for h in history:
        msgs.append({"role":"user", "content":h["user"]})
        msgs.append({"role":"assistant", "content":h["bot"]})
    msgs.append({"role":"user", "content":prompt})
    
    r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json={"model": "openrouter/auto", "messages": msgs})
    return r.json()["choices"][0]["message"]["content"]

# --- Chat UI ---
st.title(f"🐰 {st.session_state.current_convo}")
hist = st.session_state.conversations[st.session_state.current_convo]

for m in hist:
    with st.chat_message("user"): st.write(m["user"])
    with st.chat_message("assistant"): st.write(m["bot"])

user_input = st.chat_input("Say something...")
if user_input:
    bot_reply = ask_ai(user_input, hist)
    hist.append({"user": user_input, "bot": bot_reply})
    st.rerun()
