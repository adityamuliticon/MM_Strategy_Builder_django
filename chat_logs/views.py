"""Chat log JSON APIs with filtering and aggregation."""

from django.http import JsonResponse
from django.db.models import Sum, Count, Avg, Q
from django.utils.timezone import make_aware
from django.core.paginator import Paginator
from datetime import datetime, timedelta, date
from .models import ChatLog, APICallLog


def _apply_filters(qs, module_filter, date_from, date_to):
    if module_filter:
        qs = qs.filter(module=module_filter)
    if date_from:
        try:
            dt = make_aware(datetime.strptime(date_from, '%Y-%m-%d'))
            qs = qs.filter(timestamp__gte=dt)
        except ValueError:
            pass
    if date_to:
        try:
            dt = make_aware(datetime.strptime(date_to, '%Y-%m-%d')) + timedelta(days=1)
            qs = qs.filter(timestamp__lt=dt)
        except ValueError:
            pass
    return qs


def _aggregate(qs):
    return qs.aggregate(
        total_requests=Count('id'),
        total_input_tokens=Sum('input_tokens'),
        total_output_tokens=Sum('output_tokens'),
        total_tokens=Sum('total_tokens'),
        total_cost_inr=Sum('cost_inr'),
        total_cost_usd=Sum('cost_usd'),
    )


_PAGE_SIZE = 100


def logs_api(request):
    module_filter = request.GET.get('module', '')
    date_from     = request.GET.get('date_from', '')
    date_to       = request.GET.get('date_to', '')
    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (ValueError, TypeError):
        page = 1

    qs = _apply_filters(
        ChatLog.objects.all().order_by('-timestamp'),
        module_filter, date_from, date_to,
    )

    paginator = Paginator(qs, _PAGE_SIZE)
    page_obj  = paginator.get_page(page)

    data = [
        {
            'id':            log.id,
            'timestamp':     log.timestamp.isoformat(),
            'module':        log.module,
            'session_id':    log.session_id,
            'user_message':  log.user_message,
            'ai_response':   log.ai_response,
            'input_tokens':  log.input_tokens,
            'output_tokens': log.output_tokens,
            'total_tokens':  log.total_tokens,
            'cost_usd':      float(log.cost_usd),
            'cost_inr':      float(log.cost_inr),
            'model_used':    log.model_used,
        }
        for log in page_obj
    ]

    totals = _aggregate(qs)
    totals = {k: float(v) if v else 0 for k, v in totals.items()}

    return JsonResponse({
        'logs':   data,
        'totals': totals,
        'pagination': {
            'page':        page_obj.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'per_page':    _PAGE_SIZE,
            'has_next':    page_obj.has_next(),
            'has_prev':    page_obj.has_previous(),
        },
    })


def _apply_api_filters(qs, module, call_type, status, session_id, date_from, date_to):
    if module:
        qs = qs.filter(module=module)
    if call_type:
        qs = qs.filter(call_type=call_type)
    if status:
        qs = qs.filter(status=status)
    if session_id:
        qs = qs.filter(session_id__icontains=session_id)
    if date_from:
        try:
            dt = make_aware(datetime.strptime(date_from, '%Y-%m-%d'))
            qs = qs.filter(timestamp__gte=dt)
        except ValueError:
            pass
    if date_to:
        try:
            dt = make_aware(datetime.strptime(date_to, '%Y-%m-%d')) + timedelta(days=1)
            qs = qs.filter(timestamp__lt=dt)
        except ValueError:
            pass
    return qs


def api_logs_api(request):
    module     = request.GET.get('module', '')
    call_type  = request.GET.get('call_type', '')
    status     = request.GET.get('status', '')
    session_id = request.GET.get('session_id', '')
    date_from  = request.GET.get('date_from', '')
    date_to    = request.GET.get('date_to', '')
    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (ValueError, TypeError):
        page = 1

    qs = _apply_api_filters(
        APICallLog.objects.all().order_by('-timestamp'),
        module, call_type, status, session_id, date_from, date_to,
    )

    paginator = Paginator(qs, _PAGE_SIZE)
    page_obj  = paginator.get_page(page)

    data = [
        {
            'id':              log.id,
            'timestamp':       log.timestamp.isoformat(),
            'module':          log.module,
            'call_type':       log.call_type,
            'endpoint':        log.endpoint,
            'method':          log.method,
            'response_status': log.response_status,
            'duration_ms':     log.duration_ms,
            'status':          log.status,
            'session_id':      log.session_id,
            'request_payload': log.request_payload,
            'response_body':   log.response_body,
        }
        for log in page_obj
    ]

    return JsonResponse({
        'logs': data,
        'pagination': {
            'page':        page_obj.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'per_page':    _PAGE_SIZE,
            'has_next':    page_obj.has_next(),
            'has_prev':    page_obj.has_previous(),
        },
    })
