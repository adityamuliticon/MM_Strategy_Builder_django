"""RES views: chat (blocking + SSE streaming) for the Rapid Execution Scalper plugin."""

import json
from django.shortcuts import render
from services.session_context import set_session_id
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt

from rapid_execution_scalper.core.orchestrator import res_orchestrator
from chat_logs.models import ChatLog
from config import Config

# In-process session store keyed by session_id. Intentionally simple: single server process only.
res_memory = {}


def index(request):
    return render(request, 'rapid_execution_scalper.html')


@csrf_exempt
def chat(request):
    data = json.loads(request.body)
    user_message = data.get('message')
    session_id = data.get('session_id', 'default')
    set_session_id(session_id)

    if session_id not in res_memory:
        res_memory[session_id] = []

    result = res_orchestrator.process_message(user_message, res_memory[session_id])
    response_text   = result.get("message", "") if isinstance(result, dict) else result
    input_tokens    = result.get("input_tokens", 0) if isinstance(result, dict) else 0
    output_tokens   = result.get("output_tokens", 0) if isinstance(result, dict) else 0
    runware_task_id = result.get("runware_task_id", "") if isinstance(result, dict) else ""
    total_tokens    = input_tokens + output_tokens

    cost_usd = (
        input_tokens * Config.COST_PER_1M_INPUT_TOKENS_USD +
        output_tokens * Config.COST_PER_1M_OUTPUT_TOKENS_USD
    ) / 1_000_000
    cost_inr = cost_usd * Config.USD_TO_INR_RATE

    ChatLog.objects.create(
        module='RES',
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

    res_memory[session_id].append({"role": "user", "content": user_message})
    res_memory[session_id].append({"role": "assistant", "content": response_text})

    return JsonResponse({"status": "success", "message": response_text})


@csrf_exempt
def chat_stream(request):
    data = json.loads(request.body)
    user_message = data.get('message')
    session_id = data.get('session_id', 'default')
    set_session_id(session_id)

    if session_id not in res_memory:
        res_memory[session_id] = []

    history = res_memory[session_id][:]

    def event_stream():
        full_response = ""
        in_tok = out_tok = 0
        runware_task_id = ""
        try:
            for event in res_orchestrator.stream_message(user_message, history):
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
            err = {"t": "error", "v": f"⚠️ Connection error. Please try again. ({e})"}
            yield f"data: {json.dumps(err)}\n\n"
        finally:
            res_memory[session_id].append({"role": "user", "content": user_message})
            res_memory[session_id].append({"role": "assistant", "content": full_response})
            cost_usd = (
                in_tok * Config.COST_PER_1M_INPUT_TOKENS_USD +
                out_tok * Config.COST_PER_1M_OUTPUT_TOKENS_USD
            ) / 1_000_000
            cost_inr = cost_usd * Config.USD_TO_INR_RATE
            try:
                ChatLog.objects.create(
                    module='RES', session_id=session_id,
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
