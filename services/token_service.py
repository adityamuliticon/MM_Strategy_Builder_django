"""
Auto-refreshing Market Maya bearer token service.

Flow on every API call:
  1. Read the latest BearerToken row from DB.
  2. If token expires in > 30 min → return it immediately (no network call).
  3. If token expires in ≤ 30 min (or no row exists) → call clientLogin,
     save the new JWT to DB, return it.
  4. If login fails → return the cached token (if any) or fall back to
     Config.MARKET_MAYA_BEARER_TOKEN from .env.

Plain-text password is tried first (EncryptPass: false).
If Market Maya ever starts rejecting plain-text, the _call_login function
needs the RSA public key extracted from their frontend JS — that path is
not yet implemented.
"""

import base64
import json
import threading
import requests
from datetime import datetime, timezone, timedelta

from config import Config

_refresh_lock = threading.Lock()


def _decode_jwt_exp(token: str):
    """Extract the exp datetime from a JWT without verifying signature."""
    try:
        # JWT = header.payload.signature — payload is base64url JSON
        payload_b64 = token.split('.')[1]
        payload_b64 += '=' * (-len(payload_b64) % 4)   # restore base64 padding
        payload = json.loads(base64.b64decode(payload_b64))
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
        print(f"[TokenService] Login HTTP {resp.status_code}: {resp.text[:200]}")
        if resp.status_code == 200:
            body = resp.json()
            if body.get("statusCode") == 200:
                return body["data"]["token"]
    except Exception as e:
        print(f"[TokenService] Login request error: {e}")
    return None


def get_valid_token() -> str:
    """
    Return a valid Market Maya bearer token (raw string, no 'Bearer ' prefix).
    Refreshes automatically when the stored token expires within 30 minutes.
    """
    # Late import to avoid circular dependency at module load time
    from chat_logs.models import BearerToken

    now = datetime.now(tz=timezone.utc)

    record = BearerToken.objects.order_by('-updated_at').first()

    # Token still has > 30 min left — return without any network call
    if record and record.expires_at and (record.expires_at - now) > timedelta(minutes=30):
        return record.token

    # Need refresh — lock so only one thread does the login call
    with _refresh_lock:
        # Re-read after acquiring lock: another thread may have already refreshed
        record = BearerToken.objects.order_by('-updated_at').first()
        if record and record.expires_at and (record.expires_at - now) > timedelta(minutes=30):
            return record.token

        print("[TokenService] Token expires soon or missing — refreshing...")
        new_token = _call_login()

        if new_token:
            expires_at = _decode_jwt_exp(new_token)
            if record:
                record.token      = new_token
                record.expires_at = expires_at
                record.save()
            else:
                BearerToken.objects.create(token=new_token, expires_at=expires_at)
            print(f"[TokenService] Token refreshed. Expires: {expires_at}")
            return new_token

        # Login failed — use whatever cached token we have
        print("[TokenService] Login failed. Using fallback token.")
        if record and record.token:
            return record.token
        return Config.MARKET_MAYA_BEARER_TOKEN or ""


def get_auth_header() -> str:
    """Return the full Authorization header value: 'Bearer <token>'."""
    token = get_valid_token()
    if token and not token.startswith("Bearer "):
        return f"Bearer {token}"
    return token
