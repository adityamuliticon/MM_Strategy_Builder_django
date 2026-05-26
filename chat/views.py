import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from chat.core.orchestrator import orchestrator

# Memory for session history (same as original app.py)
memory = {}


def index(request):
    return render(request, 'index.html')


@csrf_exempt
def chat(request):
    """
    Main chat endpoint. Processes user messages via the AI Orchestrator.
    Expects JSON input with 'message' and optional 'session_id'.
    """
    data = json.loads(request.body)
    user_message = data.get('message')
    session_id = data.get('session_id', 'default')

    if session_id not in memory:
        memory[session_id] = []

    response_text = orchestrator.process_message(user_message, memory[session_id])

    # Update memory
    memory[session_id].append({"role": "user", "content": user_message})
    memory[session_id].append({"role": "assistant", "content": response_text})

    return JsonResponse({
        "status": "success",
        "message": response_text
    })
