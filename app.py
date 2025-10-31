from flask import Flask, request, jsonify
import json
import os
import requests

# -----------------------------
# CONFIG: OpenRouter API
# -----------------------------
OPENROUTER_API_KEY = "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"  # <-- Put your real API key here
MODEL_NAME = "openai/gpt-oss-20b:free"

# -----------------------------
# Flask App
# -----------------------------
app = Flask(__name__)

# -----------------------------
# Memory
# -----------------------------
MEMORY_FILE = 'memory.json'
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, 'r') as f:
        memory = json.load(f)
else:
    memory = {"user_name": "Koushik", "conversation_history": []}

def save_memory():
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=4)

# -----------------------------
# OpenRouter AI Request
# -----------------------------
def get_ai_response(user_input):
    """
    Sends user_input and conversation context to OpenRouter API
    and returns the AI response from GPT-OSS-20B.
    """
    # Build context: last 5 messages
    context = ""
    for conv in memory['conversation_history'][-5:]:
        context += f"User: {conv['user']}\nAI: {conv['ai']}\n"
    context += f"User: {user_input}\nAI:"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "input": context,
        "max_output_tokens": 200
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        reply = result["completion"]["output_text"]
    except Exception as e:
        print("OpenRouter API error:", e)
        reply = "Oops! Something went wrong, but I’m still MrBunny 😅"

    return reply

# -----------------------------
# Routes
# -----------------------------
@app.route('/')
def index():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MrBunny AI</title>
<style>
body { background:#0a0a0a;color:#fff;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;}
#app { width:400px; background:#111;border-radius:20px; display:flex; flex-direction:column; overflow:hidden;}
header { text-align:center; padding:20px; background:#0d0d0d; border-bottom:1px solid #00ffff33;}
header h1 { color:#00ffff; margin:0;}
#chat-box { flex-grow:1; padding:15px; overflow-y:auto; display:flex; flex-direction:column; gap:10px;}
.message { padding:10px 15px; border-radius:15px; max-width:75%; line-height:1.4;}
.user { align-self:flex-end; background:#00ffff33;}
.bot { align-self:flex-start; background:#222; border:1px solid #00ffff33;}
footer { display:flex; padding:10px; border-top:1px solid #00ffff33; background:#0d0d0d;}
#user-input { flex-grow:1; padding:10px; border:none; border-radius:10px; outline:none; background:#222; color:#fff;}
#send-btn { background:#00ffff; color:#000; font-weight:bold; border:none; border-radius:10px; margin-left:8px; padding:10px 15px; cursor:pointer;}
#send-btn:hover { background:#00cccc;}
</style>
</head>
<body>
<div id="app">
<header><h1>🐰 MrBunny AI</h1><p>Your Python-powered assistant</p></header>
<main id="chat-box"></main>
<footer>
<input id="user-input" type="text" placeholder="Type your message...">
<button id="send-btn">Send</button>
</footer>
</div>
<script>
const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

function addMessage(text, sender) {
  const msg = document.createElement('div');
  msg.classList.add('message', sender);
  msg.textContent = text;
  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', function(e) { if(e.key==='Enter') sendMessage(); });

function sendMessage() {
  const message = userInput.value.trim();
  if(!message) return;
  addMessage("You: " + message, 'user');
  userInput.value = '';
  
  fetch('/message', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({message:message})
  })
  .then(res=>res.json())
  .then(data=> addMessage("MrBunny: " + data.reply, 'bot'));
}
</script>
</body>
</html>
"""

@app.route('/message', methods=['POST'])
def message():
    user_input = request.json['message']
    reply = get_ai_response(user_input)

    memory['conversation_history'].append({'user': user_input, 'ai': reply})
    save_memory()
    
    return jsonify({'reply': reply})

# -----------------------------
# Run App
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)
