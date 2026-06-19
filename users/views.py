import json
import base64
import requests
from datetime import datetime, timezone, timedelta

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from django.db.models import Sum, Count

from users.models import AppUser, UserBearerToken
from config import Config


_ADMIN_USERNAME = "aditya"
_ADMIN_PASSWORD = "12345"


def _decode_jwt_exp(token: str):
    try:
        payload_b64 = token.split('.')[1]
        payload_b64 += '=' * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        exp = payload.get('exp')
        if exp:
            return datetime.fromtimestamp(exp, tz=timezone.utc)
    except Exception:
        pass
    return None


# ── Login / Logout ────────────────────────────────────────────────────────────

def login_page(request):
    if request.session.get('user_id'):
        return redirect('/')
    return render(request, 'login.html')


@csrf_exempt
def auth_login(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    email = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '').strip()

    if not email or not password:
        return JsonResponse({'error': 'Email and password are required'}, status=400)

    payload = {
        "userName":    email,
        "password":    password,
        "EncryptPass": False,
        "rememberMe":  True,
        "agreements":  True,
        "domain":      "terminal.marketmaya.com",
        "isTOTPCheck": False,
    }
    try:
        resp = requests.post(
            Config.MM_LOGIN_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Origin":       "https://terminal.marketmaya.com",
                "Referer":      "https://terminal.marketmaya.com/",
            },
            timeout=30,
        )
    except requests.RequestException as e:
        return JsonResponse({'error': f'Market Maya unreachable: {e}'}, status=503)

    if resp.status_code != 200:
        return JsonResponse({'error': 'Invalid email or password'}, status=401)

    body = resp.json()
    if body.get('statusCode') != 200:
        msg = body.get('message', 'Authentication failed')
        return JsonResponse({'error': msg}, status=401)

    token = body['data']['token']
    data_obj = body['data']
    display_name = (
        data_obj.get('displayName') or
        data_obj.get('name') or
        data_obj.get('fullName') or
        email.split('@')[0]
    )
    expires_at = _decode_jwt_exp(token)

    user, _ = AppUser.objects.update_or_create(
        email=email,
        defaults={'display_name': display_name, 'is_active': True, 'last_login': now()},
    )
    UserBearerToken.objects.update_or_create(
        user=user,
        defaults={'token': token, 'expires_at': expires_at},
    )

    request.session.cycle_key()
    request.session['user_id'] = str(user.id)
    request.session['user_email'] = email
    request.session['display_name'] = display_name

    return JsonResponse({'status': 'ok', 'display_name': display_name})


def auth_logout(request):
    request.session.flush()
    return redirect('/login/')


# ── Chat history API ──────────────────────────────────────────────────────────

def history_api(request):
    """Return the last 100 messages for (user, module) for page-load display."""
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    module = (request.GET.get('module') or 'USB').upper()
    from chat_logs.models import ChatMessage
    msgs = (
        ChatMessage.objects
        .filter(user_id=user_id, module=module)
        .order_by('-timestamp')[:100]
    )
    history = [
        {'role': m.role, 'content': m.content, 'ts': m.timestamp.isoformat()}
        for m in reversed(list(msgs))
    ]
    return JsonResponse({'history': history})


# ── Admin Panel ───────────────────────────────────────────────────────────────

def admin_login_page(request):
    if request.session.get('admin_logged_in'):
        return redirect('/admin-panel/')
    return render(request, 'admin_login.html')


@csrf_exempt
def admin_auth_login(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if data.get('username') == _ADMIN_USERNAME and data.get('password') == _ADMIN_PASSWORD:
        request.session['admin_logged_in'] = True
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'Invalid credentials'}, status=401)


def admin_logout(request):
    request.session.pop('admin_logged_in', None)
    return redirect('/admin-login/')


def admin_panel(request):
    if not request.session.get('admin_logged_in'):
        return redirect('/admin-login/')

    from chat_logs.models import ChatLog, APICallLog, ChatMessage

    users = list(AppUser.objects.all().order_by('-last_login'))

    msg_counts = {
        r['user_id']: r['cnt']
        for r in ChatMessage.objects.values('user_id').annotate(cnt=Count('id'))
    }
    api_counts = {
        r['user_id']: r['cnt']
        for r in APICallLog.objects.exclude(user_id=None).values('user_id').annotate(cnt=Count('id'))
    }
    token_totals = {
        r['user_id']: r['tot']
        for r in ChatLog.objects.exclude(user_id=None).values('user_id').annotate(tot=Sum('total_tokens'))
    }
    cost_usd_totals = {
        r['user_id']: float(r['tot'])
        for r in ChatLog.objects.exclude(user_id=None).values('user_id').annotate(tot=Sum('cost_usd'))
    }
    cost_inr_totals = {
        r['user_id']: float(r['tot'])
        for r in ChatLog.objects.exclude(user_id=None).values('user_id').annotate(tot=Sum('cost_inr'))
    }

    threshold = now() - timedelta(days=30)
    active_count = 0
    user_rows = []
    for u in users:
        is_active = bool(u.last_login and u.last_login >= threshold)
        if is_active:
            active_count += 1
        token_record = UserBearerToken.objects.filter(user=u).first()
        token_expires = token_record.expires_at if token_record else None
        user_rows.append({
            'id': str(u.id),
            'email': u.email,
            'display_name': u.display_name or u.email.split('@')[0],
            'last_login': u.last_login,
            'is_active': is_active,
            'token_expires': token_expires,
            'messages': msg_counts.get(u.id, 0),
            'api_calls': api_counts.get(u.id, 0),
            'tokens': token_totals.get(u.id, 0) or 0,
            'cost_usd': round(cost_usd_totals.get(u.id, 0.0), 6),
            'cost_inr': round(cost_inr_totals.get(u.id, 0.0), 4),
        })

    total_tokens = ChatLog.objects.aggregate(t=Sum('total_tokens'))['t'] or 0
    total_cost_usd = float(ChatLog.objects.aggregate(t=Sum('cost_usd'))['t'] or 0)
    total_cost_inr = float(ChatLog.objects.aggregate(t=Sum('cost_inr'))['t'] or 0)

    context = {
        'users': user_rows,
        'total_users': len(user_rows),
        'active_users': active_count,
        'inactive_users': len(user_rows) - active_count,
        'total_messages': ChatMessage.objects.count(),
        'total_api_calls': APICallLog.objects.count(),
        'total_tokens': total_tokens,
        'total_cost_usd': round(total_cost_usd, 6),
        'total_cost_inr': round(total_cost_inr, 4),
    }
    return render(request, 'admin_panel.html', context)
