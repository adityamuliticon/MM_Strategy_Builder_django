import json
import base64
import requests
from datetime import datetime, timezone

from django.http import JsonResponse
from django.utils.timezone import now

from users.models import AppUser, UserBearerToken
from marketmaya.config import Config


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


# ── Auth ──────────────────────────────────────────────────────────────────────

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

    from services.crypto import encrypt_password
    encrypted_pw = encrypt_password(password)

    user, _ = AppUser.objects.update_or_create(
        email=email,
        defaults={'display_name': display_name, 'is_active': True, 'last_login': now()},
    )
    UserBearerToken.objects.update_or_create(
        user=user,
        defaults={'token': token, 'expires_at': expires_at, 'encrypted_password': encrypted_pw},
    )

    request.session.cycle_key()
    request.session['user_id'] = str(user.id)
    request.session['user_email'] = email
    request.session['display_name'] = display_name

    return JsonResponse({'status': 'ok', 'display_name': display_name})


def auth_logout(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    request.session.flush()
    return JsonResponse({'status': 'logged_out'})


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

