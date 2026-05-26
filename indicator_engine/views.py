import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from indicator_engine.core.orchestrator import ise_orchestrator
from chat_logs.models import ChatLog
from config import Config

ise_memory = {}


def index(request):
    return render(request, 'indicator_engine.html')


@csrf_exempt
def chat(request):
    data = json.loads(request.body)
    user_message = data.get('message')
    session_id = data.get('session_id', 'default')

    if session_id not in ise_memory:
        ise_memory[session_id] = []

    result = ise_orchestrator.process_message(user_message, ise_memory[session_id])
    response_text  = result.get("message", "") if isinstance(result, dict) else result
    input_tokens   = result.get("input_tokens", 0) if isinstance(result, dict) else 0
    output_tokens  = result.get("output_tokens", 0) if isinstance(result, dict) else 0
    total_tokens   = input_tokens + output_tokens

    cost_usd = (
        input_tokens  * Config.COST_PER_1M_INPUT_TOKENS_USD +
        output_tokens * Config.COST_PER_1M_OUTPUT_TOKENS_USD
    ) / 1_000_000
    cost_inr = cost_usd * Config.USD_TO_INR_RATE

    ChatLog.objects.create(
        module='ISE',
        session_id=session_id,
        user_message=user_message,
        ai_response=response_text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        cost_usd=round(cost_usd, 8),
        cost_inr=round(cost_inr, 4),
        model_used=Config.RUNWARE_MODEL_ID or 'unknown',
    )

    ise_memory[session_id].append({"role": "user", "content": user_message})
    ise_memory[session_id].append({"role": "assistant", "content": response_text})

    return JsonResponse({"status": "success", "message": response_text})
