"""Market Maya API operations — all HTTP calls shared across every strategy module.

This class consolidates what was split across:
  services/base_market_maya.py   (save_strategy HTTP template)
  services/market_maya_shared.py (list, delete, modify, rename, balance, record)

Each module creates a MarketMaya instance (main.py) configured with its own
save_url + module label. All other operations are URL-agnostic and reused as-is.
"""

import json
import os
import time

import requests

from config import Config
from services.session_context import log_api_call
from marketmaya.Auth import Auth


def _request(method: str, url: str, *, payload=None, params=None, headers=None) -> tuple:
    """Make an HTTP request. Returns (status_code, text, duration_ms) or (None, error_str, duration_ms)."""
    start = time.time()
    try:
        resp = requests.request(
            method, url,
            json=payload,
            params=params,
            headers=headers or Auth.headers(),
            timeout=30,
        )
        return resp.status_code, resp.text, (time.time() - start) * 1000
    except Exception as e:
        return None, str(e), (time.time() - start) * 1000


def _parse_json(text: str) -> tuple:
    """Parse JSON response text. Returns (data, None) on success or (None, error_dict) on failure."""
    try:
        return json.loads(text), None
    except Exception as e:
        return None, {"status": "error", "message": str(e)}


def _resolve_id(strategy_id: str, strategy_name: str, take: int = 20) -> tuple[str, dict | None]:
    """Look up a strategy hash-ID by name. Returns (sid, error_dict | None)."""
    sid = strategy_id
    is_hash = sid and ("$" in sid or len(sid) >= 20)
    if is_hash:
        return sid, None

    search_term = strategy_name or sid
    if not search_term:
        return "", {"status": "error", "message": "Provide strategy_id or strategy_name."}

    result = Operations.get_strategies(search=search_term, take=take)
    if result["status"] != "success":
        return "", result

    strategies = result.get("strategies", [])
    if not strategies:
        return "", {"status": "error", "message": f"No strategy found matching '{search_term}'."}

    exact = [s for s in strategies if s["name"].lower() == search_term.lower()]
    if exact:
        chosen = exact[0]
    elif len(strategies) == 1:
        chosen = strategies[0]
    else:
        names = "\n".join(f"• {s['name']}" for s in strategies[:8])
        return "", {
            "status": "error",
            "message": (
                f"Found {len(strategies)} strategies matching '{search_term}'. "
                f"Please provide the exact strategy name:\n{names}"
            ),
        }

    print(f"[Operations] Resolved '{search_term}' → id={chosen['id']}")
    return chosen["id"], None


def _record_to_modify_payload(data: dict) -> dict:
    """Convert getCustomTradeRecord camelCase response → modify payload snake_case."""
    payload = {
        "id": data["id"],
        "strategy_name": data.get("strategyName", ""),
        "short_description": data.get("shortDescription", ""),
        "long_description": data.get("longDescription", ""),
        "strategy_type_id": data.get("strategyTypeId", ""),
        "product_type": data.get("productType", "NRML"),
        "required_margin": data.get("requiredMargin", 0),
        "is_intraday": data.get("isIntraday", False),
        "target_by": data.get("targetBy", "Money"),
        "intraday_target": data.get("intradayTarget", 0),
        "sl_by": data.get("slBy", "Money"),
        "intraday_sl": data.get("intradaySl", 0),
        "allow_update_parameters": data.get("allowUpdateParameters", True),
        "max_position": data.get("maxPosition", 0),
        "max_position_allocation_percent": data.get("maxPositionAllocationPercent", 100),
        "run_mon": data.get("runMon", True),
        "run_tue": data.get("runTue", True),
        "run_wed": data.get("runWed", True),
        "run_thu": data.get("runThu", True),
        "run_fri": data.get("runFri", True),
        "run_sat": data.get("runSat", False),
        "run_sun": data.get("runSun", False),
        "intraday_exit_time_min": data.get("intradayExitTimeMin", 15),
        "margin_stock_intraday": data.get("marginStockIntraday", 30),
        "margin_stock_positional": data.get("marginStockPositional", 100),
        "margin_futopt_positional": data.get("marginFutoptPositional", 30),
        "auto_sqroff_on_contract_exp": data.get("autoSqroffOnContractExp", True),
        "pause_and_sqroff_trading_on_margin_exeed": data.get("pauseAndSqroffTradingOnMarginExeed", False),
        "sqroffAllLegs": data.get("sqroffAllLegs", False),
        "isEditCode": False,
        "effect_all_sub_strategies": False,
        "sub": [],
    }
    for leg in data.get("sub", []):
        payload["sub"].append({
            "id": leg.get("id", ""),
            "exchange": leg.get("exchange", ""),
            "segment": leg.get("segment", ""),
            "main_strategy_parameter_id": leg.get("mainStrategyParameterId", ""),
            "symbol": leg.get("symbol", ""),
            "contract": leg.get("contract", "NEAR"),
            "expiry": leg.get("expiry", "WEEKLY"),
            "atm": leg.get("atm", 0),
            "option_type": leg.get("optionType", ""),
            "qty_distribution": leg.get("qtyDistribution", "Fix"),
            "qty": leg.get("qty", 0),
            "lot": leg.get("lot", 1),
            "strike_price": leg.get("strikePrice", 0),
            "target": leg.get("target", 0),
            "target_by": leg.get("targetBy", "Money"),
            "sl": leg.get("sl", 0),
            "sl_by": leg.get("slBy", "Money"),
            "trail_sl_market_move": leg.get("trailSlMarketMove", 0),
            "trail_sl_move": leg.get("trailSlMove", 0),
            "no_of_time_trail_sl": leg.get("noOfTimeTrailSl", 0),
            "is_trail_sl": leg.get("isTrailSl", False),
        })
    return payload


class Operations:
    """All Market Maya API operations.

    save_strategy() is module-specific (needs url, module, log_prefix).
    All other methods are shared across every module and need no configuration.
    """

    # ── Module-specific ───────────────────────────────────────────────────────

    def save_strategy(self, url: str, payload: dict, module: str, log_prefix: str) -> dict:
        """POST a strategy payload to the given endpoint; retries once on 401."""
        status, text, ms = _request("POST", url, payload=payload, headers=Auth.headers())
        if status is not None:
            print(f"\n[{log_prefix}] HTTP {status}: {text[:300]}")

        if status == 401:
            status, text, ms = _request("POST", url, payload=payload, headers=Auth.refreshed_headers())
            if status is not None:
                print(f"\n[{log_prefix}] 401 retry HTTP {status}: {text[:300]}")

        if status is None:
            print(f"[{log_prefix}] Connection error: {text}")
            log_api_call(module, "save_strategy", url, payload, None, text, ms, "connection_error")
            self._write_file_log(payload, "connection_error", None, text)
            return {"status": "error", "message": text}

        if status == 200:
            try:
                api_response = json.loads(text)
            except Exception:
                api_response = text
            log_api_call(module, "save_strategy", url, payload, status, api_response, ms, "success")
            self._write_file_log(payload, "success", status, api_response)
            return {"status": "success", "data": api_response}

        log_api_call(module, "save_strategy", url, payload, status, text, ms, "error")
        self._write_file_log(payload, "error", status, text)
        return {"status": "error", "code": status, "message": text}

    def _write_file_log(self, payload: dict, api_status, api_code, api_response):
        from datetime import datetime
        from django.conf import settings
        entry = {
            "timestamp": datetime.now().isoformat(),
            "strategy_name": payload.get("strategyName", "Unknown"),
            "api_status": api_status,
            "api_code": api_code,
            "api_response": api_response,
            "payload": payload,
        }
        log_path = os.path.join(settings.BASE_DIR, "logs", "saved_strategies.log")
        try:
            with open(log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"Logging error: {e}")

    # ── Shared (URL-agnostic, same for all modules) ───────────────────────────

    @staticmethod
    def get_strategies(search="", skip=0, take=500, trading_type="All", strategy_master_ids=None) -> dict:
        payload = {
            "skip": skip,
            "take": take,
            "search": search,
            "symbols": [],
            "tradingType": trading_type,
            "strategyMasterIds": strategy_master_ids or [],
            "strategyMaster": {"id": "", "strategy_name": "All Plugins", "selected": True},
            "AuthorIds": [],
            "sortBy": "newest",
        }
        status, text, ms = _request("POST", Config.GET_STRATEGIES_URL, payload=payload)
        if status is None:
            log_api_call("SHARED", "get_strategies", Config.GET_STRATEGIES_URL, payload, None, text, ms, "connection_error")
            return {"status": "error", "message": text}
        print(f"[Operations] GET_STRATEGIES HTTP {status}: {text[:200]}")
        if status == 200:
            data, err = _parse_json(text)
            if err:
                log_api_call("SHARED", "get_strategies", Config.GET_STRATEGIES_URL, payload, status, text, ms, "error")
                return err
            strategies = [
                {
                    "id": s.get("id"),
                    "sid": s.get("sid"),
                    "name": s.get("strategy_name"),
                    "plugin": s.get("plugin_name"),
                    "type": s.get("trading_type"),
                    "created": s.get("created_on"),
                    "deployed": s.get("is_deployed"),
                    "legs": s.get("sub_count"),
                    "master_id": (
                        s.get("strategy_master_id") or s.get("strategyMasterId") or
                        s.get("plugin_id") or s.get("pluginId") or ""
                    ),
                }
                for s in data.get("data", [])
            ]
            log_api_call("SHARED", "get_strategies", Config.GET_STRATEGIES_URL, payload, status, data, ms, "success")
            return {"status": "success", "total": data.get("total", 0), "strategies": strategies}
        log_api_call("SHARED", "get_strategies", Config.GET_STRATEGIES_URL, payload, status, text, ms, "error")
        return {"status": "error", "code": status, "message": text}

    @staticmethod
    def get_my_strategies(search="", take=500) -> dict:
        result = Operations.get_strategies(search=search, take=take)
        if result.get("status") != "success":
            return result
        strategies = result.get("strategies", [])
        total = result.get("total", 0)
        lines = [f"Total: {total} strategies (showing {len(strategies)}):"]
        for i, s in enumerate(strategies, 1):
            deployed = "Deployed" if s.get("deployed") else "Not deployed"
            created = (s.get("created") or "")[:10] or "—"
            lines.append(f"{i}. {s['name']} | {s['plugin']} | {deployed} | Created: {created}")
        return {
            "status": "success",
            "total": total,
            "formatted_list": "\n".join(lines),
            "strategies": [{"name": s["name"], "id": s["id"]} for s in strategies],
        }

    @staticmethod
    def delete_strategy(strategy_id="", strategy_name="") -> dict:
        sid, err = _resolve_id(strategy_id, strategy_name)
        if err:
            return err
        req = {"id": sid}
        status, text, ms = _request("POST", Config.DELETE_STRATEGY_URL, payload=req)
        if status is None:
            log_api_call("SHARED", "delete_strategy", Config.DELETE_STRATEGY_URL, req, None, text, ms, "connection_error")
            return {"status": "error", "message": text}
        print(f"[Operations] DELETE HTTP {status}: {text[:200]}")
        if status == 200:
            log_api_call("SHARED", "delete_strategy", Config.DELETE_STRATEGY_URL, req, status, text, ms, "success")
            return {"status": "success", "message": "Strategy deleted successfully."}
        log_api_call("SHARED", "delete_strategy", Config.DELETE_STRATEGY_URL, req, status, text, ms, "error")
        return {"status": "error", "code": status, "message": text}

    @staticmethod
    def get_strategy_record(strategy_id="", strategy_name="") -> dict:
        sid, err = _resolve_id(strategy_id, strategy_name, take=10)
        if err:
            return err
        params = {"strategyId": sid}
        status, text, ms = _request("GET", Config.GET_STRATEGY_RECORD_URL, params=params)
        if status is None:
            log_api_call("SHARED", "get_strategy_record", Config.GET_STRATEGY_RECORD_URL, params, None, text, ms, "connection_error")
            return {"status": "error", "message": text}
        print(f"[Operations] GET_RECORD HTTP {status}: {text[:200]}")
        if status == 200:
            body, err = _parse_json(text)
            if err:
                log_api_call("SHARED", "get_strategy_record", Config.GET_STRATEGY_RECORD_URL, params, status, text, ms, "error")
                return err
            if body.get("statusCode") == 200:
                log_api_call("SHARED", "get_strategy_record", Config.GET_STRATEGY_RECORD_URL, params, status, body, ms, "success")
                return {"status": "success", "strategy": _record_to_modify_payload(body["data"])}
            log_api_call("SHARED", "get_strategy_record", Config.GET_STRATEGY_RECORD_URL, params, status, body, ms, "error")
            return {"status": "error", "message": body.get("message", "Failed to fetch record.")}
        log_api_call("SHARED", "get_strategy_record", Config.GET_STRATEGY_RECORD_URL, params, status, text, ms, "error")
        return {"status": "error", "code": status, "message": text}

    @staticmethod
    def modify_strategy(payload: dict) -> dict:
        if not payload.get("id"):
            return {"status": "error", "message": "Payload must include the strategy 'id' field."}
        status, text, ms = _request("POST", Config.MODIFY_STRATEGY_URL, payload=payload)
        if status is None:
            log_api_call("SHARED", "modify_strategy", Config.MODIFY_STRATEGY_URL, payload, None, text, ms, "connection_error")
            return {"status": "error", "message": text}
        print(f"[Operations] MODIFY HTTP {status}: {text[:200]}")
        if status == 200:
            body, err = _parse_json(text)
            if err:
                log_api_call("SHARED", "modify_strategy", Config.MODIFY_STRATEGY_URL, payload, status, text, ms, "error")
                return err
            if body.get("statusCode") == 200 or body.get("success"):
                log_api_call("SHARED", "modify_strategy", Config.MODIFY_STRATEGY_URL, payload, status, body, ms, "success")
                return {"status": "success", "message": "Strategy modified successfully."}
            log_api_call("SHARED", "modify_strategy", Config.MODIFY_STRATEGY_URL, payload, status, body, ms, "error")
            return {"status": "error", "message": body.get("message", "Modification failed.")}
        log_api_call("SHARED", "modify_strategy", Config.MODIFY_STRATEGY_URL, payload, status, text, ms, "error")
        return {"status": "error", "code": status, "message": text}

    @staticmethod
    def rename_strategy(strategy_id="", strategy_name="", new_name="") -> dict:
        if not new_name:
            return {"status": "error", "message": "new_name is required."}
        sid, err = _resolve_id(strategy_id, strategy_name, take=10)
        if err:
            return err
        req = {"id": sid, "name": new_name}
        status, text, ms = _request("POST", Config.RENAME_STRATEGY_URL, payload=req)
        if status is None:
            log_api_call("SHARED", "rename_strategy", Config.RENAME_STRATEGY_URL, req, None, text, ms, "connection_error")
            return {"status": "error", "message": text}
        print(f"[Operations] RENAME HTTP {status}: {text[:200]}")
        if status == 200:
            data, err = _parse_json(text)
            if err:
                log_api_call("SHARED", "rename_strategy", Config.RENAME_STRATEGY_URL, req, status, text, ms, "error")
                return err
            log_api_call("SHARED", "rename_strategy", Config.RENAME_STRATEGY_URL, req, status, data, ms, "success")
            return {"status": "success", "strategy_name": data.get("strategy_name"), "message": f"Strategy renamed to '{new_name}' successfully."}
        log_api_call("SHARED", "rename_strategy", Config.RENAME_STRATEGY_URL, req, status, text, ms, "error")
        return {"status": "error", "code": status, "message": text}

    @staticmethod
    def get_balance() -> dict:
        status, text, ms = _request("POST", Config.GET_BALANCE_URL, payload={})
        if status is None:
            log_api_call("SHARED", "get_balance", Config.GET_BALANCE_URL, {}, None, text, ms, "connection_error")
            return {"status": "error", "message": text}
        print(f"[Operations] GET_BALANCE HTTP {status}: {text[:200]}")
        if status == 200:
            data, err = _parse_json(text)
            if err:
                log_api_call("SHARED", "get_balance", Config.GET_BALANCE_URL, {}, status, text, ms, "error")
                return err
            log_api_call("SHARED", "get_balance", Config.GET_BALANCE_URL, {}, status, data, ms, "success")
            return {
                "status": "success",
                "balance": data.get("balance", 0.0),
                "hold_balance": data.get("hold_balance", 0.0),
                "point_balance": data.get("point_balance", 0.0),
            }
        log_api_call("SHARED", "get_balance", Config.GET_BALANCE_URL, {}, status, text, ms, "error")
        return {"status": "error", "code": status, "message": text}
