import os
from flask import Flask, render_template, request, jsonify
from config import Config


from core.orchestrator import orchestrator

# Initialize the Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Memory for session history (simplistic for demo)
memory = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint. Processes user messages via the AI Orchestrator.
    Expects JSON input with 'message' and optional 'history'.
    """
    data = request.json
    user_message = data.get('message')
    session_id = data.get('session_id', 'default')
    
    if session_id not in memory:
        memory[session_id] = []
        
    response_text = orchestrator.process_message(user_message, memory[session_id])
    
    # Update memory
    memory[session_id].append({"role": "user", "content": user_message})
    memory[session_id].append({"role": "assistant", "content": response_text})
    
    return jsonify({
        "status": "success",
        "message": response_text
    })

if __name__ == '__main__':
    # Ensure necessary directories exist
    os.makedirs('rag/store', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
