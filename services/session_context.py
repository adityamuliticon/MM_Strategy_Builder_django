"""Thread-local session context — carries session_id from views into deep service calls without threading parameters through every function."""

import json
import time
import threading

_local = threading.local()


def set_session_id(sid: str):
    _local.session_id = sid


def get_session_id() -> str:
    return getattr(_local, 'session_id', '')


def log_api_call(module, call_type, endpoint, request_payload, response_status, response_body, duration_ms, status):
    """Save an APICallLog record. Called from all market_maya service files after every HTTP call."""
    try:
        from chat_logs.models import APICallLog
        if isinstance(response_body, str):
            try:
                response_body = json.loads(response_body)
            except Exception:
                response_body = {"raw": response_body[:5000]}
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
        )
    except Exception as e:
        print(f"[APICallLog] Logging error: {e}")
