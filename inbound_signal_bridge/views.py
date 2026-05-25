import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from inbound_signal_bridge.core.orchestrator import isb_orchestrator

isb_memory = {}


def index(request):
    return render(request, 'inbound_signal_bridge.html')


@csrf_exempt
def chat(request):
    data = json.loads(request.body)
    user_message = data.get('message')
    session_id = data.get('session_id', 'default')
    if session_id not in isb_memory:
        isb_memory[session_id] = []
    response_text = isb_orchestrator.process_message(user_message, isb_memory[session_id])
    isb_memory[session_id].append({"role": "user", "content": user_message})
    isb_memory[session_id].append({"role": "assistant", "content": response_text})
    return JsonResponse({"status": "success", "message": response_text})
