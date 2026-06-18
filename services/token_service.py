"""
Auto-refreshing Market Maya bearer token service.

Flow on every API call:
  1. Read the latest BearerToken row from DB.
  2. If token expires in > 30 min → return it immediately (no network call).
  3. If token expires in ≤ 30 min (or no row exists) → call clientLogin,
     save the new JWT to DB, return it.
  4. If login fails → return the cached token (if any) or fall back to
     Config.MARKET_MAYA_BEARER_TOKEN from .env.

Scheduled refresh (H-1): a background daemon thread refreshes the token at
6:00, 9:00, 12:00, 13:00, and 15:00 IST every day, regardless of expiry
timing, so late-night logins (short-lived tokens) are handled automatically.

On 401 from Market Maya: call force_refresh() to get a fresh token and retry.
"""

import base64
import json
import os
import threading
import time
import requests
from datetime import datetime, timezone, timedelta

from config import Config

_refresh_lock = threading.Lock()

# IST = UTC+5:30
_IST = timezone(timedelta(hours=5, minutes=30))

# Hours (IST) at which token is proactively refreshed
_SCHEDULED_REFRESH_HOURS = {6, 9, 12, 13, 15}

_scheduler_started = False
_scheduler_start_lock = threading.Lock()


def _decode_jwt_exp(token: str):
    """Extract the exp datetime from a JWT without verifying signature."""
    try:
        payload_b64 = token.split('.')[1]
        # H-1 fix: JWT uses URL-safe base64 (- and _ instead of + and /)
        payload_b64 += '=' * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        exp = payload.get('exp')
        if exp:
            return datetime.fromtimestamp(exp, tz=timezone.utc)
    except Exception:
        pass
    return None


def _call_login():
    """POST to clientLogin with plain-text password. Returns raw JWT string or None."""
    payload = {
        "userName":    Config.MARKET_MAYA_EMAIL,
        "password":    Config.MARKET_MAYA_PASSWORD,
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
        # H-9 (log): print status only, never print the token itself
        print(f"[TokenService] Login HTTP {resp.status_code}")
        if resp.status_code == 200:
            body = resp.json()
            if body.get("statusCode") == 200:
                return body["data"]["token"]
    except Exception as e:
        print(f"[TokenService] Login request error: {e}")
    return None


def _do_refresh():
    """Core refresh logic — call login, save to DB. Must be called inside _refresh_lock."""
    from chat_logs.models import BearerToken
    new_token = _call_login()
    if new_token:
        expires_at = _decode_jwt_exp(new_token)
        record = BearerToken.objects.order_by('-updated_at').first()
        if record:
            record.token = new_token
            record.expires_at = expires_at
            record.save()
        else:
            BearerToken.objects.create(token=new_token, expires_at=expires_at)
        print(f"[TokenService] Token refreshed. Expires: {expires_at}")
        return new_token
    return None


def _scheduled_refresh_loop():
    """Daemon thread: proactively refreshes token at fixed IST hours (H-1)."""
    last_refresh_hour = None
    while True:
        try:
            now_ist = datetime.now(_IST)
            current_hour = now_ist.hour
            if current_hour in _SCHEDULED_REFRESH_HOURS and current_hour != last_refresh_hour:
                print(f"[TokenService] Scheduled refresh at {current_hour:02d}:00 IST")
                with _refresh_lock:
                    _do_refresh()
                last_refresh_hour = current_hour
            elif current_hour not in _SCHEDULED_REFRESH_HOURS:
                last_refresh_hour = None
        except Exception as e:
            print(f"[TokenService] Scheduler error: {e}")
        time.sleep(60)


_scheduler_lock_fd = None  # kept open to hold the OS file lock across the process lifetime


def _ensure_scheduler():
    """Start the scheduled refresh daemon once per process, lazily, on first API call.

    Uses a non-blocking OS file lock so only one gunicorn/uwsgi worker starts the
    scheduler. The in-process _scheduler_start_lock prevents double-start within a
    single worker.
    """
    global _scheduler_started, _scheduler_lock_fd
    if _scheduler_started:
        return
    with _scheduler_start_lock:
        if _scheduler_started:
            return
        # Skip in Django's reloader parent process
        if os.environ.get('RUN_MAIN') != 'true' and 'runserver' in ' '.join(
                __import__('sys').argv):
            return
        # Cross-process guard: try to acquire an exclusive non-blocking file lock.
        # The fd is kept open so the lock is held for the lifetime of this worker.
        try:
            import fcntl
            fd = open('/tmp/mm_token_scheduler.lock', 'w')
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            _scheduler_lock_fd = fd  # hold open — releasing fd releases the lock
        except (IOError, OSError):
            # Another worker already holds the lock — it runs the scheduler
            _scheduler_started = True
            return

        t = threading.Thread(
            target=_scheduled_refresh_loop,
            daemon=True,
            name="TokenRefreshScheduler"
        )
        t.start()
        _scheduler_started = True
        print("[TokenService] Scheduled refresh daemon started "
              f"(hours IST: {sorted(_SCHEDULED_REFRESH_HOURS)})")


def get_valid_token() -> str:
    """
    Return a valid Market Maya bearer token (raw string, no 'Bearer ' prefix).
    Refreshes automatically when the stored token expires within 30 minutes.
    """
    _ensure_scheduler()

    from chat_logs.models import BearerToken

    with _refresh_lock:
        record = BearerToken.objects.order_by('-updated_at').first()
        now = datetime.now(tz=timezone.utc)
        if record and record.expires_at and (record.expires_at - now) > timedelta(minutes=30):
            return record.token

        print("[TokenService] Token expires soon or missing — refreshing...")
        new_token = _do_refresh()
        if new_token:
            return new_token

        print("[TokenService] Login failed. Using fallback token.")
        if record and record.token:
            return record.token
        return Config.MARKET_MAYA_BEARER_TOKEN or ""


def force_refresh() -> str:
    """
    Force an immediate token refresh regardless of expiry.
    Call this when a Market Maya API returns HTTP 401 (token expired mid-request).
    """
    print("[TokenService] Force refresh triggered (401 received)...")
    with _refresh_lock:
        new_token = _do_refresh()
        if new_token:
            return new_token
        # Fall back to cached token if login fails
        from chat_logs.models import BearerToken
        record = BearerToken.objects.order_by('-updated_at').first()
        return (record.token if record and record.token else
                Config.MARKET_MAYA_BEARER_TOKEN or "")


def get_auth_header() -> str:
    """Return the full Authorization header value: 'Bearer <token>'."""
    token = get_valid_token()
    if not token:
        print("[TokenService] WARNING: No token available — API call will receive 401.")
        return ""
    if not token.startswith("Bearer "):
        return f"Bearer {token}"
    return token
