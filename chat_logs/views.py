"""Chat log analytics views: dashboard page and JSON API with filtering and aggregation."""

from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Sum, Count
from django.utils import timezone
from django.utils.timezone import make_aware
from datetime import datetime, timedelta, date
from .models import ChatLog


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


def logs_index(request):
    module_filter = request.GET.get('module', '')
    quick         = request.GET.get('quick', '')
    date_from     = request.GET.get('date_from', '')
    date_to       = request.GET.get('date_to', '')

    today = date.today()

    if quick == 'today':
        date_from = today.strftime('%Y-%m-%d')
        date_to   = today.strftime('%Y-%m-%d')
    elif quick == 'yesterday':
        y = today - timedelta(days=1)
        date_from = date_to = y.strftime('%Y-%m-%d')
    elif quick == 'last7':
        date_from = (today - timedelta(days=6)).strftime('%Y-%m-%d')
        date_to   = today.strftime('%Y-%m-%d')
    elif quick == 'thismonth':
        date_from = today.replace(day=1).strftime('%Y-%m-%d')
        date_to   = today.strftime('%Y-%m-%d')

    base_qs = ChatLog.objects.all()
    filtered_qs = _apply_filters(base_qs, module_filter, date_from, date_to)

    logs = filtered_qs[:200]

    # Stats for current filter
    stats = _aggregate(filtered_qs)

    # All-time stats (no date filter, only module filter)
    all_qs = base_qs.filter(module=module_filter) if module_filter else base_qs
    all_stats = _aggregate(all_qs)

    # Per-module breakdown for current date filter
    module_stats = (
        filtered_qs.values('module')
        .annotate(requests=Count('id'), tokens=Sum('total_tokens'), cost_inr=Sum('cost_inr'))
        .order_by('module')
    )

    # Daily cost chart data (last 30 days or filtered range)
    chart_qs = filtered_qs if (date_from or date_to) else base_qs
    if module_filter:
        chart_qs = chart_qs.filter(module=module_filter)

    daily_raw = (
        chart_qs
        .extra(select={'day': "date(timestamp)"})
        .values('day')
        .annotate(cost_inr=Sum('cost_inr'), requests=Count('id'), tokens=Sum('total_tokens'))
        .order_by('day')
    )
    daily_chart = [
        {'day': r['day'], 'cost_inr': float(r['cost_inr'] or 0),
         'requests': r['requests'], 'tokens': r['tokens'] or 0}
        for r in daily_raw
    ]

    return render(request, 'chat_logs.html', {
        'logs': logs,
        'stats': stats,
        'all_stats': all_stats,
        'module_stats': module_stats,
        'active_module': module_filter,
        'date_from': date_from,
        'date_to': date_to,
        'quick': quick,
        'daily_chart': daily_chart,
        'is_filtered': bool(date_from or date_to),
    })


def logs_api(request):
    module_filter = request.GET.get('module', '')
    date_from     = request.GET.get('date_from', '')
    date_to       = request.GET.get('date_to', '')

    qs = _apply_filters(ChatLog.objects.all(), module_filter, date_from, date_to)

    data = [
        {
            'id': log.id,
            'timestamp': log.timestamp.isoformat(),
            'module': log.module,
            'session_id': log.session_id,
            'user_message': log.user_message,
            'ai_response': log.ai_response,
            'input_tokens': log.input_tokens,
            'output_tokens': log.output_tokens,
            'total_tokens': log.total_tokens,
            'cost_usd': float(log.cost_usd),
            'cost_inr': float(log.cost_inr),
            'model_used': log.model_used,
        }
        for log in qs[:500]
    ]

    totals = _aggregate(qs)
    totals = {k: float(v) if v else 0 for k, v in totals.items()}

    return JsonResponse({'logs': data, 'totals': totals})
