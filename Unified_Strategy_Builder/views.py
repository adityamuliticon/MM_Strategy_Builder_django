"""USB views: chat (blocking + SSE streaming) and cross-plugin sidebar helpers."""

import json
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt

from Unified_Strategy_Builder.core.orchestrator import orchestrator
from chat_logs.models import ChatLog
from config import Config
from services.market_maya_shared import get_strategies, get_balance
from services.session_context import set_session_id

_STRATEGY_TYPE_IDS = {
    "usb": "7D0enBHWMRaf4ebeKaB0$OOMQaC0$aC0$",
    "ise": "QFwz7gYjmmabUT8SBvZQGgaC0$aC0$",
    "isb": "XBZs7OE0aMivKaB0$aA0$Wej3PcwaC0$aC0$",
    "res": "YioJhK5IqBULe8fPLMnXaAaC0$aC0$",
    "mlh": "RF8IGNzSfYMaB0$ENiAa4FpGwaC0$aC0$",
}


_ID_TO_KEY = {v: k for k, v in _STRATEGY_TYPE_IDS.items()}


def strategy_counts_view(request):
    result = get_strategies(take=1000)
    if result.get("status") != "success":
        return JsonResponse({k: None for k in _STRATEGY_TYPE_IDS})

    counts = {k: 0 for k in _STRATEGY_TYPE_IDS}
    strategies = result.get("strategies", [])
    for s in strategies:
        key = _ID_TO_KEY.get(s.get("master_id", ""))
        if key:
            counts[key] += 1

    # Log when master_id values aren't recognised so we can update _STRATEGY_TYPE_IDS
    if strategies and not any(counts.values()):
        plugin_counts = {}
        for s in strategies:
            p = s.get("plugin", "unknown")
            plugin_counts[p] = plugin_counts.get(p, 0) + 1
        print(f"[strategy_counts] master_id unrecognised. Plugin breakdown: {plugin_counts}")
        print(f"[strategy_counts] Sample master_id values: {[s.get('master_id') for s in strategies[:3]]}")

    return JsonResponse(counts)


def balance_view(request):
    result = get_balance()
    if result.get("status") == "success":
        return JsonResponse({"point_balance": result["point_balance"]})
    return JsonResponse({"point_balance": None})

# In-process session store keyed by session_id. Intentionally simple: single server process only.
memory = {}


def index(request):
    return render(request, 'index.html')


@csrf_exempt
def chat(request):
    if request.method != 'POST':  # H-19
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:  # H-16
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    user_message = (data.get('message') or '').strip()
    if not user_message:
        return JsonResponse({'error': 'Message is required'}, status=400)
    session_id = data.get('session_id', 'default')
    set_session_id(session_id)

    if session_id not in memory:
        memory[session_id] = []

    result = orchestrator.process_message(user_message, memory[session_id][:])
    response_text   = result.get("message", "") if isinstance(result, dict) else result
    input_tokens    = result.get("input_tokens", 0) if isinstance(result, dict) else 0
    output_tokens   = result.get("output_tokens", 0) if isinstance(result, dict) else 0
    runware_task_id = result.get("runware_task_id", "") if isinstance(result, dict) else ""
    total_tokens    = input_tokens + output_tokens

    cost_usd = (
        input_tokens  * Config.COST_PER_1M_INPUT_TOKENS_USD +
        output_tokens * Config.COST_PER_1M_OUTPUT_TOKENS_USD
    ) / 1_000_000
    cost_inr = cost_usd * Config.USD_TO_INR_RATE

    ChatLog.objects.create(
        module='USB',
        session_id=session_id,
        user_message=user_message,
        ai_response=response_text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        cost_usd=round(cost_usd, 8),
        cost_inr=round(cost_inr, 4),
        model_used=Config.RUNWARE_MODEL_ID or 'unknown',
        runware_task_id=runware_task_id,
    )

    memory[session_id].append({"role": "user", "content": user_message})
    memory[session_id].append({"role": "assistant", "content": response_text})

    return JsonResponse({"status": "success", "message": response_text})


@csrf_exempt
def chat_stream(request):
    if request.method != 'POST':  # H-19
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:  # H-16
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    user_message = (data.get('message') or '').strip()
    if not user_message:
        return JsonResponse({'error': 'Message is required'}, status=400)
    session_id = data.get('session_id', 'default')
    set_session_id(session_id)

    if session_id not in memory:
        memory[session_id] = []

    history = memory[session_id][:]

    def event_stream():
        full_response = ""
        in_tok = out_tok = 0
        runware_task_id = ""
        try:
            for event in orchestrator.stream_message(user_message, history):
                t = event.get('t')
                if t == 'chunk':
                    full_response += event.get('v', '')
                elif t == 'done':
                    in_tok = event.get('in_tok', 0)
                    out_tok = event.get('out_tok', 0)
                    runware_task_id = event.get('task_id', '')

                yield f"data: {json.dumps(event)}\n\n"

                if t in ('done', 'error'):
                    break
        except Exception as e:
            print(f"[USB stream error] {e}")  # H-17: log detail server-side only
            err = {"t": "error", "v": "⚠️ Connection error. Please try again."}
            yield f"data: {json.dumps(err)}\n\n"
        finally:
            memory[session_id].append({"role": "user", "content": user_message})
            memory[session_id].append({"role": "assistant", "content": full_response})
            cost_usd = (
                in_tok * Config.COST_PER_1M_INPUT_TOKENS_USD +
                out_tok * Config.COST_PER_1M_OUTPUT_TOKENS_USD
            ) / 1_000_000
            cost_inr = cost_usd * Config.USD_TO_INR_RATE
            try:
                ChatLog.objects.create(
                    module='USB', session_id=session_id,
                    user_message=user_message, ai_response=full_response,
                    input_tokens=in_tok, output_tokens=out_tok,
                    total_tokens=in_tok + out_tok,
                    cost_usd=round(cost_usd, 8), cost_inr=round(cost_inr, 4),
                    model_used=Config.RUNWARE_MODEL_ID or 'unknown',
                    runware_task_id=runware_task_id,
                )
            except Exception:
                pass

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response
