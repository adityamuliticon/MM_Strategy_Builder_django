import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from indicator_engine.core.orchestrator import ise_orchestrator

# Separate in-memory session store — isolated from Unified Strategy Builder
ise_memory = {}


def index(request):
    return render(request, 'indicator_engine.html')


@csrf_exempt
def chat(request):
    """
    ISE chat endpoint. Processes user messages via the ISE Orchestrator.
    Completely isolated from the Unified Strategy Builder chat endpoint.
    """
    data = json.loads(request.body)
    user_message = data.get('message')
    session_id = data.get('session_id', 'default')

    if session_id not in ise_memory:
        ise_memory[session_id] = []

    response_text = ise_orchestrator.process_message(user_message, ise_memory[session_id])

    ise_memory[session_id].append({"role": "user", "content": user_message})
    ise_memory[session_id].append({"role": "assistant", "content": response_text})

    return JsonResponse({
        "status": "success",
        "message": response_text
    })
