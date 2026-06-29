"""
Shared view factory for all 5 strategy module chat interfaces.

All chat/stream logic lives here once.
Each strategy's views file calls make_chat_views() with its 3 config values
and gets back ready-to-use (index, chat, chat_stream) view functions.
"""

import json
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt

from chat_logs.models import ChatLog
from config import Config
from services.view_helpers import setup_user_context, get_history, save_messages, _AuthError
from services.request_queue import request_queue


def make_chat_views(module, orchestrator, template, pass_user_id=False):
    """
    Returns (index, chat, chat_stream) views configured for the given module.

    module       — module code string: 'USB', 'MLH', 'RES', 'ISB', 'ISE'
    orchestrator — the singleton orchestrator instance for this module
    template     — Django template name rendered by index()
    pass_user_id — True for USB only: adds user_id to the index template context
    """

    def index(request):
        display_name = request.session.get('display_name', '')
        ctx = {'display_name': display_name}
        if pass_user_id:
            ctx['user_id'] = request.session.get('user_id', '')
        return render(request, template, ctx)

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
            user_id, session_id = setup_user_context(request, module)
        except _AuthError as e:
            return e.response

        history = get_history(user_id, module)
        with request_queue:
            result = orchestrator.process_message(user_message, history)
        response_text   = result.get("message", "") if isinstance(result, dict) else result
        input_tokens    = result.get("input_tokens", 0) if isinstance(result, dict) else 0
        output_tokens   = result.get("output_tokens", 0) if isinstance(result, dict) else 0
        runware_task_id = result.get("runware_task_id", "") if isinstance(result, dict) else ""
        total_tokens    = input_tokens + output_tokens
        cost_usd = (input_tokens * Config.COST_PER_1M_INPUT_TOKENS_USD +
                    output_tokens * Config.COST_PER_1M_OUTPUT_TOKENS_USD) / 1_000_000
        cost_inr = cost_usd * Config.USD_TO_INR_RATE

        save_messages(user_id, module, user_message, response_text)
        ChatLog.objects.create(
            module=module, session_id=session_id, user_id=user_id,
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
            user_id, session_id = setup_user_context(request, module)
        except _AuthError as e:
            return e.response

        history = get_history(user_id, module)
        start_time = request_queue.acquire()

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
                print(f"[{module} stream error] {e}")
                yield f"data: {json.dumps({'t': 'error', 'v': '⚠️ Connection error. Please try again.'})}\n\n"
            finally:
                request_queue.release(start_time)
                save_messages(user_id, module, user_message, full_response)
                cost_usd = (in_tok * Config.COST_PER_1M_INPUT_TOKENS_USD +
                            out_tok * Config.COST_PER_1M_OUTPUT_TOKENS_USD) / 1_000_000
                cost_inr = cost_usd * Config.USD_TO_INR_RATE
                try:
                    ChatLog.objects.create(
                        module=module, session_id=session_id, user_id=user_id,
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

    return index, chat, chat_stream
