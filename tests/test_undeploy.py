"""
Live API test for undeploy_strategy on strategy "asdasd".
Calls the full flow: resolve → WS connect → checkPendingPayments → undeploy REST → WS jobaction.
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mm_project.settings")

import django
django.setup()

from services.deploy import (
    _resolve_strategy_id,
    _parse_jwt_claims,
    _auth_headers,
)
from services.token_service import get_valid_token
from config import Config
import requests
import websocket
import threading
import time

STRATEGY_NAME = "asdasd"

print("=" * 60)
print(f"UNDEPLOY TEST — strategy: {STRATEGY_NAME}")
print("=" * 60)

# ── Step 1: Resolve strategy ──────────────────────────────────
print("\n[1] Resolving strategy...")
hash_id, resolved_sid, resolved_name, err = _resolve_strategy_id(strategy_name=STRATEGY_NAME)
if err:
    print(f"  ❌ Resolve failed: {err}")
    sys.exit(1)
print(f"  ✅ hash_id   = {hash_id}")
print(f"  ✅ sid       = {resolved_sid}")
print(f"  ✅ name      = {resolved_name}")

# ── Step 2: Parse JWT ─────────────────────────────────────────
print("\n[2] Parsing JWT...")
token_str = get_valid_token()
claims = _parse_jwt_claims(token_str)
ws_id = claims["ws_id"]
raw_token = token_str[7:] if token_str.startswith("Bearer ") else token_str
print(f"  ✅ ws_id       = {ws_id}")
print(f"  ✅ ip_address  = {claims['ip_address']}")
print(f"  ✅ client_uuid = {claims['client_id_uuid']}")

# ── Step 3: WebSocket connect + join ─────────────────────────
print("\n[3] Connecting WebSocket...")
ws_url = (
    f"wss://algosocketserver.marketmaya.com/algo-server"
    f"?usertype=Client&executionLevel=Level%208&id={ws_id}"
)
print(f"  URL: {ws_url}")

try:
    ws = websocket.create_connection(ws_url, timeout=10)
    print("  ✅ WS connected")
except Exception as e:
    print(f"  ❌ WS connection failed: {e}")
    sys.exit(1)

join_payload = {
    "token": raw_token,
    "executionLevel": "Level 8",
    "id": ws_id,
    "type": "Client",
    "ip": claims["ip_address"],
    "ib_id": None,
    "action_from": "Client",
    "action_from_id": ws_id,
}
ws.send(json.dumps({"method": "join", "data": json.dumps(join_payload)}))
print("  ✅ Join sent")

ws.settimeout(5)
join_ok = False
try:
    for _ in range(15):
        msg = ws.recv()
        print(f"  WS recv: {msg[:200]}")
        if "joinSuccess" in msg:
            join_ok = True
            print("  ✅ joinSuccess received")
            break
except Exception as e:
    print(f"  ⚠️  joinSuccess wait ended: {e}")
if not join_ok:
    print("  ⚠️  joinSuccess not received (continuing anyway)")

# ── Step 4: checkPendingPayments ─────────────────────────────
print("\n[4] checkPendingPayments...")
headers = _auth_headers()
try:
    r = requests.post(
        Config.CHECK_PENDING_PAYMENTS_URL,
        json={"id": hash_id},
        headers=headers,
        timeout=15,
    )
    print(f"  HTTP {r.status_code}: {r.text[:300]}")
    if r.status_code == 200:
        body = r.json()
        if body.get("pending"):
            print("  ❌ Pending payments found — cannot undeploy")
            ws.close()
            sys.exit(1)
        print("  ✅ No pending payments")
    else:
        print("  ⚠️  checkPendingPayments failed (continuing)")
except Exception as e:
    print(f"  ⚠️  checkPendingPayments error (continuing): {e}")

# ── Step 5: POST undeploy ─────────────────────────────────────
print(f"\n[5] POST undeploy  payload: {{\"id\": \"{hash_id}\"}}")
try:
    r = requests.post(
        Config.UNDEPLOY_STRATEGY_URL,
        json={"id": hash_id},
        headers=headers,
        timeout=30,
    )
    print(f"  HTTP {r.status_code}")
    try:
        body = r.json()
        print(f"  Response JSON: {json.dumps(body, indent=2)}")
    except Exception:
        print(f"  Response text: {r.text[:500]}")
    undeploy_ok = r.status_code == 200 and r.json().get("statusCode") == 200
except Exception as e:
    print(f"  ❌ Undeploy request failed: {e}")
    ws.close()
    sys.exit(1)

# ── Step 6: WS jobaction/undeploy ────────────────────────────
print("\n[6] Sending WS jobaction/undeploy...")
action_data = {
    "client_id": ws_id,
    "actionname": "undeploy",
    "executionlevel": "Level 8",
    "val1": resolved_sid if resolved_sid is not None else "",
    "val2": "", "val3": "", "val4": "", "val5": "",
    "ip": claims["ip_address"],
    "ib_id": None,
    "action_from": "Client",
    "action_from_id": ws_id,
}
msg = json.dumps({"method": "jobaction", "data": json.dumps(action_data)})
print(f"  Payload: {msg}")
try:
    ws.send(msg)
    print("  ✅ jobaction sent")
    # Listen for jobactionresponse from TradingServer
    ws.settimeout(8)
    try:
        for _ in range(10):
            resp = ws.recv()
            print(f"  WS recv: {resp[:400]}")
            if "jobactionresponse" in resp.lower() and "undeploy" in resp.lower():
                print("  ✅ jobactionresponse received from TradingServer")
                break
    except Exception as e:
        print(f"  ⚠️  WS recv ended: {e}")
except Exception as e:
    print(f"  ❌ jobaction send failed: {e}")

ws.close()
print("\n" + "=" * 60)
if undeploy_ok:
    print("RESULT: ✅ REST undeploy succeeded — check Market Maya now")
else:
    print("RESULT: ❌ REST undeploy failed — see response above")
print("=" * 60)
