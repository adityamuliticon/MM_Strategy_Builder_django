"""USB views: chat (blocking + SSE streaming) and cross-plugin sidebar helpers."""

import json
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt

from Unified_Strategy_Builder.core.orchestrator import orchestrator
from chat_logs.models import ChatLog
from config import Config
from services.market_maya_shared import get_strategies, get_balance
from services.view_helpers import setup_user_context, get_history, save_messages, _AuthError

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

    if strategies and not any(counts.values()):
        plugin_counts = {}
        for s in strategies:
            p = s.get("plugin", "unknown")
            plugin_counts[p] = plugin_counts.get(p, 0) + 1
        print(f"[strategy_counts] master_id unrecognised. Plugin breakdown: {plugin_counts}")

    user_id = request.session.get('user_id')
    if user_id:
        from users.models import UserBearerToken
        from django.utils.timezone import now
        UserBearerToken.objects.filter(user_id=user_id).update(
            cached_strategy_counts=counts,
            data_cached_at=now(),
        )

    return JsonResponse(counts)


def balance_view(request):
    result = get_balance()
    if result.get("status") == "success":
        point_balance = result["point_balance"]
        user_id = request.session.get('user_id')
        if user_id:
            from users.models import UserBearerToken
            from django.utils.timezone import now
            UserBearerToken.objects.filter(user_id=user_id).update(
                cached_point_balance=point_balance,
                data_cached_at=now(),
            )
        return JsonResponse({"point_balance": point_balance})
    return JsonResponse({"point_balance": None})


def index(request):
    user_id = request.session.get('user_id', '')
    display_name = request.session.get('display_name', '')
    return render(request, 'index.html', {'display_name': display_name, 'user_id': user_id})


@csrf_exempt
def chat(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)

    user_message = (data.get('message') or '').strip()
    if not user_message:
        return JsonResponse({'error': 'Message is required'}, status=400)

    try:
        user_id, session_id = setup_user_context(request, 'USB')
    except _AuthError as e:
        return e.response

    history = get_history(user_id, 'USB')
    result = orchestrator.process_message(user_message, history)
    response_text   = result.get("message", "") if isinstance(result, dict) else result
    input_tokens    = result.get("input_tokens", 0) if isinstance(result, dict) else 0
    output_tokens   = result.get("output_tokens", 0) if isinstance(result, dict) else 0
    runware_task_id = result.get("runware_task_id", "") if isinstance(result, dict) else ""
    total_tokens    = input_tokens + output_tokens
    cost_usd = (input_tokens * Config.COST_PER_1M_INPUT_TOKENS_USD +
                output_tokens * Config.COST_PER_1M_OUTPUT_TOKENS_USD) / 1_000_000
    cost_inr = cost_usd * Config.USD_TO_INR_RATE

    save_messages(user_id, 'USB', user_message, response_text)
    ChatLog.objects.create(
        module='USB', session_id=session_id, user_id=user_id,
        user_message=user_message, ai_response=response_text,
        input_tokens=input_tokens, output_tokens=output_tokens, total_tokens=total_tokens,
        cost_usd=round(cost_usd, 8), cost_inr=round(cost_inr, 4),
        model_used=Config.RUNWARE_MODEL_ID or 'unknown',
        runware_task_id=runware_task_id,
    )
    return JsonResponse({"status": "success", "message": response_text})


@csrf_exempt
def chat_stream(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)

    user_message = (data.get('message') or '').strip()
    if not user_message:
        return JsonResponse({'error': 'Message is required'}, status=400)

    try:
        user_id, session_id = setup_user_context(request, 'USB')
    except _AuthError as e:
        return e.response

    history = get_history(user_id, 'USB')

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
            print(f"[USB stream error] {e}")
            yield f"data: {json.dumps({'t': 'error', 'v': '⚠️ Connection error. Please try again.'})}\n\n"
        finally:
            save_messages(user_id, 'USB', user_message, full_response)
            cost_usd = (in_tok * Config.COST_PER_1M_INPUT_TOKENS_USD +
                        out_tok * Config.COST_PER_1M_OUTPUT_TOKENS_USD) / 1_000_000
            cost_inr = cost_usd * Config.USD_TO_INR_RATE
            try:
                ChatLog.objects.create(
                    module='USB', session_id=session_id, user_id=user_id,
                    user_message=user_message, ai_response=full_response,
                    input_tokens=in_tok, output_tokens=out_tok, total_tokens=in_tok + out_tok,
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
