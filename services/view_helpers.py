"""Shared helpers used by all 5 module chat views."""

from django.http import JsonResponse
from services.session_context import set_session_id, set_user_token, set_user_id


def setup_user_context(request, module):
    """
    Loads user from session, sets per-user token + session_id in thread-local.
    Returns (user_id, session_id) or raises a JsonResponse on auth failure.
    Middleware already sets the token for normal requests; this re-sets it to
    ensure SSE generator threads also have the right token captured.
    """
    from users.models import AppUser, UserBearerToken
    from datetime import datetime, timezone

    user_id = request.session.get('user_id')
    if not user_id:
        raise _AuthError(JsonResponse(
            {'error': 'Not authenticated', 'redirect': '/login/'}, status=401,
        ))

    token_record = UserBearerToken.objects.filter(user_id=user_id).first()
    if token_record:
        # Check token expiry
        if token_record.expires_at:
            now_utc = datetime.now(timezone.utc)
            if token_record.expires_at <= now_utc:
                raise _AuthError(JsonResponse(
                    {'error': 'Market Maya session expired. Please log in again.', 'redirect': '/login/'},
                    status=401,
                ))
        set_user_token(token_record.token)

    set_user_id(user_id)
    session_id = f"{user_id}_{module}"
    set_session_id(session_id)
    return user_id, session_id


def get_history(user_id, module, limit=10):
    """Return the last `limit` messages for (user, module) as [{role, content}, ...]."""
    from chat_logs.models import ChatMessage
    msgs = (
        ChatMessage.objects
        .filter(user_id=user_id, module=module)
        .order_by('-timestamp')[:limit]
    )
    return [{"role": m.role, "content": m.content} for m in reversed(list(msgs))]


def save_messages(user_id, module, user_msg, ai_msg):
    """Persist a user/assistant exchange to ChatMessage."""
    from chat_logs.models import ChatMessage
    ChatMessage.objects.create(user_id=user_id, module=module, role='user', content=user_msg)
    ChatMessage.objects.create(user_id=user_id, module=module, role='assistant', content=ai_msg)


class _AuthError(Exception):
    def __init__(self, response):
        self.response = response
