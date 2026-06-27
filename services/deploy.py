"""Strategy deployment/undeployment service for Market Maya.

Flow for deploy_strategy:
  1. Resolve strategy → hash_id
  2. Parse JWT → extract clientId (UUID), currentUserType, currentUserId, currentUserWlId, ipAddress
  3. Connect WebSocket + join (required — server validates active WS session before deploying)
  4. POST /api/mainStrategy/deploy with full DeployStrategyDto payload
  5. Keep WS alive in background to receive deploy status events

Flow for undeploy_strategy:
  1. Resolve strategy → hash_id + sid
  2. Parse JWT → extract ws_id
  3. Connect WebSocket + join (server validates active WS session before undeploying)
  4. POST checkPendingPayments — block if pending=true
  5. POST /api/mainStrategy/undeploy
  6. Send WS jobaction/undeploy — mirrors algoSocketService.sendAction('undeploy', executionLevel, sid)
  7. Keep WS alive in background to receive undeploy status events
"""

import base64
import json
import threading
import time

import requests
import websocket

from config import Config
from marketmaya.Operations import Operations
get_strategies = Operations.get_strategies
from services.session_context import log_api_call

_CLAIM_NS = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/"
_CLAIM_MS = "http://schemas.microsoft.com/ws/2008/06/identity/claims/"


def _resolve_strategy_id(strategy_id="", strategy_name=""):
    search_term = strategy_name or strategy_id
    if not search_term:
        return None, None, None, "Provide strategy_id or strategy_name."
    result = get_strategies(search=search_term, take=10)
    if result["status"] != "success":
        return None, None, None, result.get("message", "Failed to search strategies.")
    strategies = result.get("strategies", [])
    if not strategies:
        return None, None, None, f"No strategy found matching '{search_term}'."
    exact = [s for s in strategies if s["name"].lower() == search_term.lower()]
    chosen = exact[0] if exact else strategies[0]
    return chosen["id"], chosen.get("sid"), chosen.get("name", search_term), None


def _auth_headers():
    from services.token_service import get_auth_header
    return {
        "Authorization": get_auth_header(),
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    }


def _parse_jwt_claims(token):
    """
    Decode JWT and return a dict with all deploy-relevant claims:
      ws_id           → nameidentifier (numeric user ID, used in WS URL/join)
      client_id_uuid  → primarysid (UUID, used as clientId in DeployStrategyDto)
      user_type       → givenname ("Client")
      user_id         → nameidentifier as int
      wl_id           → locality as int
      ip_address      → serialnumber ("172.x.x.x")
    """
    empty = {"ws_id": None, "client_id_uuid": None, "user_type": "Client",
             "user_id": None, "wl_id": None, "ip_address": None}
    if not token:
        return empty
    if token.startswith("Bearer "):
        token = token[7:]
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return empty
        payload = parts[1]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(base64.b64decode(payload).decode("utf-8"))

        name_id = data.get(f"{_CLAIM_NS}nameidentifier")
        return {
            "ws_id": name_id,
            "client_id_uuid": data.get(f"{_CLAIM_MS}primarysid"),
            "user_type": data.get(f"{_CLAIM_NS}givenname", "Client"),
            "user_id": int(name_id) if name_id and str(name_id).isdigit() else None,
            "wl_id": int(data[f"{_CLAIM_NS}locality"]) if data.get(f"{_CLAIM_NS}locality", "").isdigit() else None,
            "ip_address": data.get(f"{_CLAIM_MS}serialnumber"),
        }
    except Exception as e:
        print(f"[Deploy] JWT parse error: {e}")
        return empty


def _fetch_point_balance(headers):
    try:
        r = requests.post(Config.GET_BALANCE_URL, json={}, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json().get("point_balance", 0.0)
    except Exception as e:
        print(f"[Deploy] Balance fetch error: {e}")
    return None


def _keep_ws_alive_deploy(websocket_conn, duration=120):
    """Background thread: keeps WS alive and listens for deploy status events."""
    print(f"[Deploy] WS thread started, keeping alive for up to {duration}s")
    try:
        websocket_conn.settimeout(5)
        start = time.time()
        last_heartbeat = start

        while time.time() - start < duration:
            try:
                if time.time() - last_heartbeat > 20:
                    websocket_conn.send(json.dumps({"method": "heartbeat"}))
                    last_heartbeat = time.time()

                msg = websocket_conn.recv()
                print(f"[Deploy] WS msg: {msg[:300]}")

                msg_lower = msg.lower()
                if any(k in msg_lower for k in ("deploystatus", "deploysuccess", "deployedfail")):
                    if any(t in msg for t in ("Completed", "Failed", "Success", "Error")):
                        print("[Deploy] WS deploy terminal event received.")
                        break

            except websocket.WebSocketTimeoutException:
                pass
            except Exception as loop_e:
                print(f"[Deploy] WS loop error: {loop_e}")
                break
    except Exception as e:
        print(f"[Deploy] WS thread outer error: {e}")
    finally:
        try:
            websocket_conn.close()
            print("[Deploy] WS connection closed.")
        except Exception:
            pass


def _keep_ws_alive_undeploy(websocket_conn, duration=60):
    """Background thread: keeps WS alive and listens for undeploy status events."""
    print(f"[Undeploy] WS thread started, keeping alive for up to {duration}s")
    try:
        websocket_conn.settimeout(5)
        start = time.time()
        last_heartbeat = start

        while time.time() - start < duration:
            try:
                if time.time() - last_heartbeat > 20:
                    websocket_conn.send(json.dumps({"method": "heartbeat"}))
                    last_heartbeat = time.time()

                msg = websocket_conn.recv()
                print(f"[Undeploy] WS msg: {msg[:300]}")

                msg_lower = msg.lower()
                # jobactionresponse is the TradingServer's ack for our jobaction/undeploy
                if "jobactionresponse" in msg_lower and "undeploy" in msg_lower:
                    print(f"[Undeploy] WS jobactionresponse received: {msg[:200]}")
                    break
                if any(k in msg_lower for k in ("undeploystatus", "undeploysuccess", "undeployed")):
                    if any(t in msg for t in ("Completed", "Failed", "Success", "Error")):
                        print("[Undeploy] WS undeploy terminal event received.")
                        break

            except websocket.WebSocketTimeoutException:
                pass
            except Exception as loop_e:
                print(f"[Undeploy] WS loop error: {loop_e}")
                break
    except Exception as e:
        print(f"[Undeploy] WS thread outer error: {e}")
    finally:
        try:
            websocket_conn.close()
            print("[Undeploy] WS connection closed.")
        except Exception:
            pass


def get_deploy_options(strategy_id="", strategy_name=""):
    """
    Fetch point balance + charges before deploying.
    Shows the user: current balance, live/paper charge per order, and disclaimer.
    """
    hash_id, _, resolved_name, err = _resolve_strategy_id(strategy_id, strategy_name)
    if err:
        return {"status": "error", "message": err}

    headers = _auth_headers()
    balance = _fetch_point_balance(headers)

    charges = {}
    start = time.time()
    try:
        r = requests.post(Config.GET_CHARGES_URL, json={}, headers=headers, timeout=15)
        duration_ms = (time.time() - start) * 1000
        print(f"[Deploy] GET_CHARGES HTTP {r.status_code}: {r.text[:200]}")
        if r.status_code == 200:
            charges = r.json()
            log_api_call('SHARED', 'get_charges', Config.GET_CHARGES_URL, {}, r.status_code, charges, duration_ms, 'success')
        else:
            log_api_call('SHARED', 'get_charges', Config.GET_CHARGES_URL, {}, r.status_code, r.text, duration_ms, 'error')
    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        log_api_call('SHARED', 'get_charges', Config.GET_CHARGES_URL, {}, None, str(e), duration_ms, 'connection_error')
        print(f"[Deploy] Charges fetch error: {e}")

    return {
        "status": "success",
        "strategy_id": hash_id,
        "strategy_name": resolved_name,
        "point_balance": balance,
        "live_trade_charge_per_order": charges.get("mm_live_trade_charge", 1.0),
        "paper_trade_charge_per_order": charges.get("mm_paper_trade_charge", 0.25),
        "disclaimer": charges.get("strategy_deploy_disclaimer", ""),
        "default_settings": {
            "trading_mode": "Live",
            "qty_multiply": 1,
            "entry_execution_type": "PSUEDO",
            "entry_psuedo_value": 0,
            "entry_psuedo_type": "Auto",
            "entry_wait_seconds": 30,
            "entry_no_of_try": 2,
            "entry_market_order_after_retry": False,
            "exit_execution_type": "PSUEDO",
            "exit_psuedo_value": 0,
            "exit_psuedo_type": "Auto",
            "exit_wait_seconds": 30,
            "exit_no_of_try": 2,
            "exit_market_order_after_retry": False,
        }
    }


def deploy_strategy(
    strategy_id="", strategy_name="",
    trading_mode="Live",
    charges_acknowledged=False,
    qty_multiply=1,
    entry_execution_type="PSUEDO",
    entry_psuedo_value=0,
    entry_psuedo_type="Auto",
    entry_wait_seconds=30,
    entry_no_of_try=2,
    entry_market_order_after_retry=False,
    exit_execution_type="PSUEDO",
    exit_psuedo_value=0,
    exit_psuedo_type="Auto",
    exit_wait_seconds=30,
    exit_no_of_try=2,
    exit_market_order_after_retry=False,
):
    """
    Deploy a saved strategy to Live or Paper trading on Market Maya.

    Flow:
      1. Resolve strategy → hash_id
      2. Parse JWT → clientId, currentUserType, currentUserId, currentUserWlId, ipAddress
      3. Connect WebSocket + join (server requires active WS session to accept deploy)
      4. POST /api/mainStrategy/deploy with full DeployStrategyDto
      5. Keep WS alive in background for deploy status events
    """
    hash_id, _, resolved_name, err = _resolve_strategy_id(strategy_id, strategy_name)
    if err:
        return {"status": "error", "message": err}

    # H-8: require explicit charges acknowledgement before live deployment
    if not charges_acknowledged:
        charges_result = get_deploy_options(strategy_id=hash_id)
        if charges_result.get("status") == "success":
            charges_result["requires_confirmation"] = True
            charges_result["message"] = (
                f"Please confirm deployment for '{resolved_name}'. "
                f"Live charge: {charges_result.get('live_trade_charge_per_order')} pts/order, "
                f"Paper charge: {charges_result.get('paper_trade_charge_per_order')} pts/order, "
                f"Balance: {charges_result.get('point_balance')} pts. "
                "Call deploy_strategy again with charges_acknowledged=True to proceed."
            )
        return charges_result

    # ── Step 1: Parse JWT for user context fields ─────────────────────────────
    from services.token_service import get_valid_token
    token_str = get_valid_token()
    claims = _parse_jwt_claims(token_str)
    ws_id = claims["ws_id"]
    if not ws_id:
        return {"status": "error", "message": "Could not extract user ID from token for WebSocket connection."}

    raw_token = token_str[7:] if token_str.startswith("Bearer ") else token_str

    headers = _auth_headers()
    paper_trading = str(trading_mode).lower() in ("paper", "paper trading", "papertrading")

    ws = None
    try:
        # ── Step 2: Connect WebSocket + join ──────────────────────────────────
        ws_url = (
            f"wss://algosocketserver.marketmaya.com/algo-server"
            f"?usertype=Client&executionLevel=Level%208&id={ws_id}"
        )
        print(f"[Deploy] Connecting WS: {ws_url}")
        ws = websocket.create_connection(ws_url, timeout=10)

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
        print("[Deploy] Join sent")

        ws.settimeout(5)
        try:
            for _ in range(15):
                msg = ws.recv()
                if "joinSuccess" in msg:
                    print("[Deploy] joinSuccess received.")
                    break
        except Exception as e:
            print(f"[Deploy] joinSuccess wait timeout: {e}")

        # ── Step 3: POST /api/mainStrategy/deploy with full payload ───────────
        payload = {
            "strategyId": hash_id,
            "qtyMultiply": int(qty_multiply) if qty_multiply else 1,
            "followSimulator": False,
            "paperTrading": paper_trading,
            "entryExecutionType": entry_execution_type or "PSUEDO",
            "entryPsuedoValue": entry_psuedo_value if entry_psuedo_value is not None else 0,
            "entryPsuedoType": entry_psuedo_type or "Auto",
            "entryWaitSeconds": entry_wait_seconds if entry_wait_seconds is not None else 30,
            "entryNoOfTry": entry_no_of_try if entry_no_of_try is not None else 2,
            "entryMarketOrderAfterRetry": bool(entry_market_order_after_retry),
            "exitExecutionType": exit_execution_type or "PSUEDO",
            "exitPsuedoValue": exit_psuedo_value if exit_psuedo_value is not None else 0,
            "exitPsuedoType": exit_psuedo_type or "Auto",
            "exitWaitSeconds": exit_wait_seconds if exit_wait_seconds is not None else 30,
            "exitNoOfTry": exit_no_of_try if exit_no_of_try is not None else 2,
            "exitMarketOrderAfterRetry": bool(exit_market_order_after_retry),
            "understandTheRisks": True,
        }

        print(f"[Deploy] POST deploy payload: {json.dumps(payload)[:400]}")
        start = time.time()

        r = requests.post(Config.DEPLOY_STRATEGY_URL, json=payload, headers=headers, timeout=30)
        duration_ms = (time.time() - start) * 1000
        print(f"[Deploy] HTTP {r.status_code}: {r.text[:300]}")

        if r.status_code == 200:
            resp_data = r.json()
            if resp_data.get("statusCode") == 200:
                log_api_call('SHARED', 'deploy_strategy', Config.DEPLOY_STRATEGY_URL, payload, r.status_code, resp_data, duration_ms, 'success')
                updated_balance = _fetch_point_balance(headers)

                # ── Step 4: Keep WS alive for deploy status events ────────────
                t = threading.Thread(target=_keep_ws_alive_deploy, args=(ws,), daemon=True)
                t.start()
                ws = None  # background thread owns the connection now

                return {
                    "status": "success",
                    "message": f"Strategy '{resolved_name}' deployed successfully to {('Paper' if paper_trading else 'Live')} Trading.",
                    "deployment_id": resp_data.get("data"),
                    "trading_mode": "Paper Trading" if paper_trading else "Live Trading",
                    "updated_point_balance": updated_balance,
                }
            else:
                log_api_call('SHARED', 'deploy_strategy', Config.DEPLOY_STRATEGY_URL, payload, r.status_code, resp_data, duration_ms, 'error')
                return {
                    "status": "error",
                    "message": resp_data.get("message", "Deploy failed. Strategy may already be deployed or account may not have live trading enabled."),
                    "api_response": resp_data,
                }
        else:
            try:
                err_body = r.json()
                err_msg = err_body.get("message") or err_body.get("error") or r.text
            except Exception:
                err_body = r.text
                err_msg = r.text
            log_api_call('SHARED', 'deploy_strategy', Config.DEPLOY_STRATEGY_URL, payload, r.status_code, err_body, duration_ms, 'error')
            return {"status": "error", "code": r.status_code, "message": err_msg}

    except Exception as e:
        print(f"[Deploy] Flow error: {e}")
        return {"status": "error", "message": f"Failed to deploy strategy: {e}"}
    finally:
        if ws:
            try:
                ws.close()
            except Exception:
                pass


def undeploy_strategy(strategy_id="", strategy_name=""):
    """
    Undeploy a deployed strategy from Live or Paper trading.

    Flow:
      1. Resolve strategy → hash_id
      2. Parse JWT → extract ws_id for WebSocket connection
      3. Connect WebSocket + join (server validates active WS session before undeploying)
      4. POST checkPendingPayments — block if pending=true
      5. POST /api/mainStrategy/undeploy
      6. Keep WS alive in background for undeploy status events
    """
    hash_id, resolved_sid, resolved_name, err = _resolve_strategy_id(strategy_id, strategy_name)
    if err:
        return {"status": "error", "message": err}

    # ── Step 1: Parse JWT for WebSocket user context ──────────────────────────
    from services.token_service import get_valid_token
    token_str = get_valid_token()
    claims = _parse_jwt_claims(token_str)
    ws_id = claims["ws_id"]
    if not ws_id:
        return {"status": "error", "message": "Could not extract user ID from token for WebSocket connection."}

    raw_token = token_str[7:] if token_str.startswith("Bearer ") else token_str
    headers = _auth_headers()

    ws = None
    try:
        # ── Step 2: Connect WebSocket + join ──────────────────────────────────
        ws_url = (
            f"wss://algosocketserver.marketmaya.com/algo-server"
            f"?usertype=Client&executionLevel=Level%208&id={ws_id}"
        )
        print(f"[Undeploy] Connecting WS: {ws_url}")
        ws = websocket.create_connection(ws_url, timeout=10)

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
        print("[Undeploy] Join sent")

        ws.settimeout(5)
        try:
            for _ in range(15):
                msg = ws.recv()
                if "joinSuccess" in msg:
                    print("[Undeploy] joinSuccess received.")
                    break
        except Exception as e:
            print(f"[Undeploy] joinSuccess wait timeout: {e}")

        # ── Step 3: Check pending payments ────────────────────────────────────
        start = time.time()
        try:
            r = requests.post(
                Config.CHECK_PENDING_PAYMENTS_URL,
                json={"id": hash_id},
                headers=headers,
                timeout=15,
            )
            duration_ms = (time.time() - start) * 1000
            print(f"[Undeploy] checkPendingPayments HTTP {r.status_code}: {r.text[:200]}")
            if r.status_code == 200:
                body = r.json()
                log_api_call('SHARED', 'check_pending_payments', Config.CHECK_PENDING_PAYMENTS_URL,
                             {"id": hash_id}, r.status_code, body, duration_ms, 'success')
                if body.get("pending"):
                    return {
                        "status": "error",
                        "message": (
                            f"Cannot undeploy '{resolved_name}' — there are pending payments for this strategy. "
                            "Please resolve all pending payments first and try again."
                        ),
                    }
            else:
                log_api_call('SHARED', 'check_pending_payments', Config.CHECK_PENDING_PAYMENTS_URL,
                             {"id": hash_id}, r.status_code, r.text, duration_ms, 'error')
        except Exception as e:
            print(f"[Undeploy] Pending payments check error (proceeding): {e}")

        # ── Step 4: POST undeploy ──────────────────────────────────────────────
        start = time.time()
        r = requests.post(
            Config.UNDEPLOY_STRATEGY_URL,
            json={"id": hash_id},
            headers=headers,
            timeout=30,
        )
        duration_ms = (time.time() - start) * 1000
        print(f"[Undeploy] HTTP {r.status_code}: {r.text[:300]}")

        if r.status_code == 200:
            body = r.json()
            if body.get("statusCode") == 200:
                log_api_call('SHARED', 'undeploy_strategy', Config.UNDEPLOY_STRATEGY_URL,
                             {"id": hash_id}, r.status_code, body, duration_ms, 'success')

                # ── Step 5: Send WS jobaction/undeploy (mirrors frontend algoSocketService.sendAction) ──
                # sendAction('undeploy', executionLevel, sid) → send("jobaction", {client_id, actionname, executionlevel, val1=sid, ...})
                try:
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
                    ws.send(json.dumps({"method": "jobaction", "data": json.dumps(action_data)}))
                    print(f"[Undeploy] WS jobaction/undeploy sent for sid={resolved_sid}")
                except Exception as e:
                    print(f"[Undeploy] WS action send error (non-fatal): {e}")

                # ── Step 6: Keep WS alive for undeploy status events ──────────
                t = threading.Thread(target=_keep_ws_alive_undeploy, args=(ws,), daemon=True)
                t.start()
                ws = None  # background thread owns the connection now

                return {
                    "status": "success",
                    "message": f"Strategy '{resolved_name}' undeployed successfully.",
                }

            log_api_call('SHARED', 'undeploy_strategy', Config.UNDEPLOY_STRATEGY_URL,
                         {"id": hash_id}, r.status_code, body, duration_ms, 'error')
            return {"status": "error", "message": body.get("message", "Undeploy failed.")}

        try:
            err_body = r.json()
            err_msg = err_body.get("message") or err_body.get("error") or r.text
        except Exception:
            err_body = r.text
            err_msg = r.text
        log_api_call('SHARED', 'undeploy_strategy', Config.UNDEPLOY_STRATEGY_URL,
                     {"id": hash_id}, r.status_code, err_body, duration_ms, 'error')
        return {"status": "error", "code": r.status_code, "message": err_msg}

    except Exception as e:
        print(f"[Undeploy] Flow error: {e}")
        return {"status": "error", "message": f"Failed to undeploy strategy: {e}"}
    finally:
        if ws:
            try:
                ws.close()
            except Exception:
                pass
