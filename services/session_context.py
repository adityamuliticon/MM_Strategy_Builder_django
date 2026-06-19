"""Thread-local session context — carries session_id from views into deep service calls without threading parameters through every function."""

import json
import time
import threading

_local = threading.local()


def set_session_id(sid: str):
    _local.session_id = sid


def get_session_id() -> str:
    return getattr(_local, 'session_id', '')


def set_user_token(token: str):
    """Store the current request user's Market Maya JWT in thread-local."""
    _local.user_token = token


def get_user_token() -> str:
    """Return the per-user token set for this request thread, or empty string."""
    return getattr(_local, 'user_token', '')


def set_user_id(user_id):
    _local.user_id = user_id


def get_user_id():
    return getattr(_local, 'user_id', None)


def log_api_call(module, call_type, endpoint, request_payload, response_status, response_body, duration_ms, status):
    """Save an APICallLog record. Called from all market_maya service files after every HTTP call."""
    try:
        from chat_logs.models import APICallLog
        if isinstance(response_body, str):
            try:
                response_body = json.loads(response_body)
            except Exception:
                response_body = {"raw": response_body[:5000]}
        user_id = getattr(_local, 'user_id', None)
        APICallLog.objects.create(
            module=module,
            call_type=call_type,
            endpoint=endpoint,
            request_payload=request_payload,
            response_status=response_status,
            response_body=response_body,
            duration_ms=round(duration_ms, 2) if duration_ms is not None else None,
            status=status,
            session_id=get_session_id(),
            user_id=user_id,
        )
    except Exception as e:
        print(f"[APICallLog] Logging error: {e}")
