from flask import Flask, render_template, request, jsonify
from ai_engine import get_ai_response
import json

app = Flask(__name__)

# Load memory
with open('memory.json', 'r') as f:
    memory = json.load(f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/message', methods=['POST'])
def message():
    user_input = request.json['message']
    reply = get_ai_response(user_input, memory)

    # Save conversation to memory
    memory['conversation_history'].append({'user': user_input, 'ai': reply})
    with open('memory.json', 'w') as f:
        json.dump(memory, f, indent=4)

    return jsonify({'reply': reply})

if __name__ == '__main__':
    app.run(debug=True)
