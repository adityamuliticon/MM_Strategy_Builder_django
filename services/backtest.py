"""Shared backtest service — WebSocket-based flow matching the Market Maya frontend.

Flow for run_backtest:
  1. Resolve strategy → hash_id (REST calls) + numeric_sid (WS trigger)
  2. Balance pre-check
  3. Connect WebSocket + join
  4. POST deductBacktestPoints
  5. Send 'backteststrategy' WS message (triggers the backtest engine)
  6. Keep WS alive in background to receive 'backteststatus' events
"""

import json
import time
import threading
import requests
import base64
import websocket
from datetime import datetime
from config import Config
from services.market_maya_shared import get_strategies


def _resolve_strategy_info(strategy_id="", strategy_name=""):
    """
    Resolve strategy name/id → (hash_id, numeric_sid, plugin_name, error).
    hash_id     → used for all REST API calls (encrypted hash).
    numeric_sid → used for the WebSocket backteststrategy message.
    plugin_name → strategy master/plugin name, also used in WS message.
    """
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
    return chosen["id"], chosen.get("sid"), chosen.get("plugin", ""), None


def _get_client_id_from_token(token):
    if not token:
        return None
    if token.startswith("Bearer "):
        token = token[7:]
    try:
        parts = token.split(".")
        if len(parts) >= 2:
            payload = parts[1]
            payload += "=" * (-len(payload) % 4)
            decoded = base64.b64decode(payload).decode("utf-8")
            data = json.loads(decoded)
            return data.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier")
    except Exception as e:
        print(f"[Backtest] Token decode error: {e}")
    return None


def _auth_headers():
    from services.token_service import get_auth_header
    return {
        "Authorization": get_auth_header(),
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    }


def _fetch_point_balance(headers):
    try:
        r = requests.post(Config.GET_BALANCE_URL, json={}, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json().get("point_balance", 0.0)
    except Exception as e:
        print(f"[Backtest] Balance fetch error: {e}")
    return None


def _calculate_points(start_date_str, end_date_str, per_day_charge, free_days):
    """
    Same formula as the frontend BacktestDialogComponent.updatePoints():
      days = (end - start).days + 1
      if days <= free_days → points = 0
      else → points = round(days * per_day_charge * 100) / 100
    """
    try:
        d1 = datetime.strptime(start_date_str[:10], "%Y-%m-%d").date()
        d2 = datetime.strptime(end_date_str[:10], "%Y-%m-%d").date()
        days = (d2 - d1).days + 1
        if days <= (free_days or 0):
            return 0.0
        return round(days * per_day_charge * 100) / 100
    except Exception as e:
        print(f"[Backtest] Points calc error: {e}")
        return 0.0


def _keep_ws_alive(websocket_conn, duration=120):
    """
    Background thread: keeps WS alive with heartbeats and listens for
    'backteststatus' events. Exits when Completed/Failed or timeout.
    """
    print(f"[Backtest] WS thread started, keeping alive for up to {duration}s")
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
                print(f"[Backtest] WS msg: {msg[:300]}")

                if "backteststatus" in msg:
                    if "Completed" in msg or "Failed" in msg:
                        print("[Backtest] backteststatus terminal event received.")
                        break

            except websocket.WebSocketTimeoutException:
                pass
            except Exception as loop_e:
                print(f"[Backtest] WS loop error: {loop_e}")
                break
    except Exception as e:
        print(f"[Backtest] WS thread outer error: {e}")
    finally:
        try:
            websocket_conn.close()
            print("[Backtest] WS connection closed.")
        except Exception:
            pass


def get_backtest_options(strategy_id="", strategy_name=""):
    """Fetch available backtest time periods, point costs, and current point balance."""
    hash_id, numeric_sid, plugin_name, err = _resolve_strategy_info(strategy_id, strategy_name)
    if err:
        return {"status": "error", "message": err}

    headers = _auth_headers()

    try:
        resp = requests.post(
            Config.BACKTEST_OPTIONS_URL,
            json={"id": hash_id},
            headers=headers,
            timeout=30,
        )
        print(f"[Backtest] GET_OPTIONS HTTP {resp.status_code}: {resp.text[:200]}")
        if resp.status_code != 200:
            return {"status": "error", "code": resp.status_code, "message": resp.text}

        data = resp.json()
        items = [
            {
                "title": item.get("title"),
                "start_date": item.get("start_date", "")[:10],
                "end_date": item.get("end_date", "")[:10],
                "points": item.get("points", 0),
            }
            for item in data.get("items", [])
        ]

        point_balance = _fetch_point_balance(headers)

        return {
            "status": "success",
            "strategy_id": hash_id,
            "numeric_sid": numeric_sid,
            "plugin_name": plugin_name,
            "title": data.get("title", ""),
            "sub_title": data.get("subTitle", ""),
            "per_day_charge": data.get("per_day_charge", 0.1),
            "free_days": data.get("wl_backtest_free_days", 30),
            "min_date": data.get("min_date", ""),
            "current_point_balance": point_balance,
            "items": items,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def run_backtest(strategy_id="", strategy_name="", start_date="", end_date=""):
    """
    Full backtest flow matching the Market Maya frontend:
      1. Resolve strategy → hash_id (for REST) + numeric_sid (for WS)
      2. Balance pre-check
      3. Connect WebSocket + join
      4. POST deductBacktestPoints (deducts points)
      5. Send 'backteststrategy' WS message (THIS triggers the actual backtest engine)
      6. Keep WS alive in background to receive 'backteststatus' events
    """
    hash_id, numeric_sid, plugin_name, err = _resolve_strategy_info(strategy_id, strategy_name)
    if err:
        return {"status": "error", "message": err}
    if not numeric_sid:
        return {"status": "error", "message": "Strategy numeric ID (sid) is missing — cannot trigger backtest. The strategy may not have been fully indexed yet."}
    if not start_date or not end_date:
        return {"status": "error", "message": "start_date and end_date are required (YYYY-MM-DD)."}

    start_date = start_date[:10]
    end_date = end_date[:10]
    print(f"[Backtest] Starting for {hash_id} (sid={numeric_sid}) from {start_date} to {end_date}")

    headers = _auth_headers()

    # ── Step 1: Fetch options for balance check + points calculation ──────────
    per_day_charge = 0.1
    free_days = 30
    required_points = None
    try:
        options_resp = requests.post(
            Config.BACKTEST_OPTIONS_URL,
            json={"id": hash_id},
            headers=headers,
            timeout=30,
        )
        if options_resp.status_code == 200:
            options_data = options_resp.json()
            per_day_charge = options_data.get("per_day_charge", 0.1)
            free_days = options_data.get("wl_backtest_free_days", 30)

            # Try to find exact slab match first
            for item in options_data.get("items", []):
                if item.get("start_date", "")[:10] == start_date and item.get("end_date", "")[:10] == end_date:
                    required_points = item.get("points", 0)
                    break

            # Fallback: calculate exactly like the frontend does
            if required_points is None:
                required_points = _calculate_points(start_date, end_date, per_day_charge, free_days)

            if required_points and required_points > 0:
                point_balance = _fetch_point_balance(headers) or 0.0
                if point_balance < required_points:
                    return {
                        "status": "error",
                        "insufficient_balance": True,
                        "message": (
                            f"Insufficient point balance. This backtest requires {required_points} points "
                            f"but your current balance is {point_balance} points. "
                            f"Please top up your account to proceed."
                        ),
                        "required_points": required_points,
                        "available_points": point_balance,
                    }
    except Exception as e:
        print(f"[Backtest] Pre-check error (proceeding): {e}")

    # Calculate points for WS message (same formula as frontend)
    points_for_ws = required_points if required_points is not None else _calculate_points(
        start_date, end_date, per_day_charge, free_days
    )

    # ── Step 2: Get client_id from JWT ────────────────────────────────────────
    from services.token_service import get_valid_token
    token_str = get_valid_token()
    client_id = _get_client_id_from_token(token_str)
    if not client_id:
        return {"status": "error", "message": "Could not extract client_id from token for WebSocket."}

    if token_str.startswith("Bearer "):
        token_str = token_str[7:]

    ws = None
    try:
        # ── Step 3: Connect WebSocket and join ────────────────────────────────
        ws_url = (
            f"wss://algosocketserver.marketmaya.com/algo-server"
            f"?usertype=Client&executionLevel=Level%208&id={client_id}"
        )
        print(f"[Backtest] Connecting WS: {ws_url}")
        ws = websocket.create_connection(ws_url, timeout=10)

        join_payload = {
            "token": token_str,
            "executionLevel": "Level 8",
            "id": client_id,
            "type": "Client",
            "ip": None,
            "ib_id": None,
            "action_from": "Client",
            "action_from_id": client_id,
        }
        ws.send(json.dumps({"method": "join", "data": json.dumps(join_payload)}))
        print("[Backtest] Join sent")

        # Wait for joinSuccess
        ws.settimeout(5)
        try:
            for _ in range(15):
                msg = ws.recv()
                if "joinSuccess" in msg:
                    print("[Backtest] joinSuccess received.")
                    break
        except Exception as e:
            print(f"[Backtest] joinSuccess wait timeout: {e}")

        # ── Step 4: POST deductBacktestPoints (deducts points only) ──────────
        deduct_payload = {
            "id": hash_id,
            "startDate": start_date,
            "endDate": end_date,
            "executionLevel": "Level 8",
        }
        compact_json = json.dumps(deduct_payload, separators=(',', ':'))
        print(f"[Backtest] POST deductBacktestPoints: {compact_json}")

        resp = requests.post(
            Config.DEDUCT_BACKTEST_POINTS_URL,
            data=compact_json,
            headers=headers,
            timeout=30,
        )
        print(f"[Backtest] DEDUCT HTTP {resp.status_code}: {resp.text[:200]}")
        if resp.status_code not in (200, 201):
            err_msg = None
            try:
                body = resp.json()
                err_msg = body.get("message") or body.get("error") or body.get("msg")
            except Exception:
                pass
            return {"status": "error", "message": err_msg or resp.text}

        # ── Step 5: Send 'backteststrategy' WS message ────────────────────────
        # strategyId must be the numeric sid (NOT the hash id).
        # strategyName is the plugin/master name.
        bt_payload = {
            "clientId": client_id,
            "strategyId": numeric_sid,
            "strategyName": plugin_name,
            "dataStartDate": start_date,
            "dataEndDate": end_date,
            "points": points_for_ws,
            "executionLevel": "Level 8",
            "ip": None,
            "ib_id": None,
            "action_from": "Client",
            "action_from_id": client_id,
        }
        ws.send(json.dumps({"method": "backteststrategy", "data": json.dumps(bt_payload)}))
        print(f"[Backtest] backteststrategy WS sent: {json.dumps(bt_payload)[:300]}")

        # ── Step 6: Keep WS alive in background — listens for 'backteststatus' ─
        t = threading.Thread(target=_keep_ws_alive, args=(ws,), daemon=True)
        t.start()
        ws = None  # background thread owns the connection now

    except Exception as e:
        print(f"[Backtest] Flow error: {e}")
        return {"status": "error", "message": f"Failed to run backtest: {e}"}
    finally:
        if ws:
            try:
                ws.close()
            except Exception:
                pass

    return {
        "status": "processing",
        "message": (
            "The backtest has been successfully triggered and is processing in the background. "
            "Please wait about 15–30 seconds, then use get_backtest_result to fetch the results."
        ),
    }


def get_backtest_result(strategy_id="", strategy_name=""):
    """
    Fetch stored backtest results (no points charged).
    Calls 4 history APIs: strategy detail, day history, month history, year history.
    """
    hash_id, _sid, _plugin, err = _resolve_strategy_info(strategy_id, strategy_name)
    if err:
        return {"status": "error", "message": err}

    headers = _auth_headers()

    try:
        resp = requests.get(
            Config.GET_BACKTEST_RESULT_URL,
            params={"id": hash_id},
            headers=headers,
            timeout=30,
        )
        print(f"[Backtest] GET_RESULT HTTP {resp.status_code}: {resp.text[:200]}")
        if resp.status_code != 200:
            return {"status": "error", "code": resp.status_code, "message": resp.text}
        body = resp.json()
        if body.get("statusCode") != 200:
            return {"status": "error", "message": body.get("message", "Failed to fetch strategy detail.")}
        detail_data = body.get("data", {})
    except Exception as e:
        return {"status": "error", "message": str(e)}

    period_start = detail_data.get("backtestDataStartDate", "")
    period_end = detail_data.get("backtestDataEndDate", "")

    if not period_start or detail_data.get("status") != "Completed":
        return {
            "status": "no_backtest",
            "message": "No completed backtest found for this strategy. Use get_backtest_options to start one.",
        }

    start_dt = period_start[:10]
    end_dt = period_end[:10]
    start_full = f"{start_dt}T00:00:00"
    end_full = f"{end_dt}T23:59:59"

    day_history = []
    try:
        r = requests.get(Config.GET_DAY_TRADE_HISTORY_URL, params={
            "strategyId": hash_id, "startDate": start_full, "endDate": end_full,
            "entryType": "BackTest", "pnlStart": 0, "pnlEnd": 0,
        }, headers=headers, timeout=30)
        print(f"[Backtest] DAY_HISTORY HTTP {r.status_code}")
        if r.status_code == 200:
            day_history = r.json().get("data", [])
    except Exception as e:
        print(f"[Backtest] DayHistory error: {e}")

    start_year = int(start_dt[:4])
    end_year = int(end_dt[:4])
    month_history = []
    for year in range(start_year, end_year + 1):
        try:
            r = requests.get(Config.GET_MONTH_TRADE_HISTORY_URL, params={
                "year": year, "strategyId": hash_id, "entryType": "BackTest",
            }, headers=headers, timeout=30)
            print(f"[Backtest] MONTH_HISTORY {year} HTTP {r.status_code}")
            if r.status_code == 200:
                month_history.extend(r.json().get("data", []))
        except Exception as e:
            print(f"[Backtest] MonthHistory error {year}: {e}")
    month_history.sort(key=lambda x: x.get("tradingdate", ""))

    year_history = []
    try:
        r = requests.get(Config.GET_YEAR_TRADE_HISTORY_URL, params={
            "id": hash_id, "entryType": "BackTest",
        }, headers=headers, timeout=30)
        print(f"[Backtest] YEAR_HISTORY HTTP {r.status_code}")
        if r.status_code == 200:
            year_history = r.json().get("data", [])
    except Exception as e:
        print(f"[Backtest] YearHistory error: {e}")

    result = _format_detail_result(detail_data)
    result["day_trade_history"] = day_history
    result["month_trade_history"] = month_history
    result["year_trade_history"] = year_history
    return result


def _extract_analysis_value(items):
    result = {}
    for item in items or []:
        name = item.get("name", "")
        val = item.get("valueStr") or item.get("valueInt") or item.get("valueDouble")
        result[name] = val
    return result


def _format_detail_result(data):
    period_start = data.get("backtestDataStartDate", "")
    period_end = data.get("backtestDataEndDate", "")

    if not period_start:
        return {
            "status": "no_backtest",
            "message": "No backtest has been run for this strategy yet. Use 'get_backtest_options' to run one.",
        }

    return {
        "status": "success",
        "strategy_name": data.get("strategyName", ""),
        "backtest_run_date": data.get("backtestJobStartDate", ""),
        "period_start": period_start,
        "period_end": period_end,
        "max_drawdown_recover_days": data.get("maxDrawDownRecoverDays"),
        "capital": data.get("capital"),
        "year_roi": data.get("yearRoi"),
        "drawdown_percent": data.get("drawDownPercent"),
        "day_analysis": _extract_analysis_value(data.get("dayAnalysis")),
        "month_analysis": _extract_analysis_value(data.get("monthAnalysis")),
        "year_analysis": _extract_analysis_value(data.get("yearAnalysis")),
        "trade_analysis": _extract_analysis_value(data.get("tradeAnalysis")),
        "period_analyses": {
            "all_data": _strip_charts(_parse_analysis(data.get("allDataAnalysis"))),
            "1_year": _strip_charts(_parse_analysis(data.get("lastOneYearAnalysis"))),
            "6_months": _strip_charts(_parse_analysis(data.get("lastSixMonthsAnalysis"))),
            "3_months": _strip_charts(_parse_analysis(data.get("lastThreeMonthsAnalysis"))),
            "1_month": _strip_charts(_parse_analysis(data.get("lastMonthAnalysis"))),
        },
    }


def _parse_analysis(s):
    if not s:
        return {}
    try:
        return json.loads(s)
    except Exception:
        return {}


def _strip_charts(d):
    if not isinstance(d, dict):
        return d
    return {k: v for k, v in d.items() if k != "chart"}
