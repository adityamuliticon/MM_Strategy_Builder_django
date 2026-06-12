"""USB views: chat (blocking + SSE streaming) and cross-plugin sidebar helpers."""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def _fetch_count(key, type_id):
    result = get_strategies(take=1, strategy_master_ids=[type_id])
    if result.get("status") == "success":
        return key, result["total"]
    return key, None


def strategy_counts_view(request):
    counts = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_fetch_count, k, v): k for k, v in _STRATEGY_TYPE_IDS.items()}
        for future in as_completed(futures):
            key, count = future.result()
            counts[key] = count
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
    data = json.loads(request.body)
    user_message = data.get('message')
    session_id = data.get('session_id', 'default')
    set_session_id(session_id)

    if session_id not in memory:
        memory[session_id] = []

    result = orchestrator.process_message(user_message, memory[session_id])
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
    )

    memory[session_id].append({"role": "user", "content": user_message})
    memory[session_id].append({"role": "assistant", "content": response_text})

    return JsonResponse({"status": "success", "message": response_text})


@csrf_exempt
def chat_stream(request):
    data = json.loads(request.body)
    user_message = data.get('message')
    session_id = data.get('session_id', 'default')
    set_session_id(session_id)

    if session_id not in memory:
        memory[session_id] = []

    history = memory[session_id][:]

    def event_stream():
        full_response = ""
        in_tok = out_tok = 0
        try:
            for event in orchestrator.stream_message(user_message, history):
                t = event.get('t')
                if t == 'chunk':
                    full_response += event.get('v', '')
                elif t == 'done':
                    in_tok = event.get('in_tok', 0)
                    out_tok = event.get('out_tok', 0)

                yield f"data: {json.dumps(event)}\n\n"

                if t in ('done', 'error'):
                    break
        except Exception as e:
            err = {"t": "error", "v": f"⚠️ Connection error. Please try again. ({e})"}
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
                )
            except Exception:
                pass

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response
