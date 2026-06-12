"""Shared Market Maya API helpers used by all five plugins."""

import requests
from config import Config


def _record_to_modify_payload(data):
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


def _auth_headers():
    from services.token_service import get_auth_header
    return {
        "Authorization": get_auth_header(),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def get_strategies(search="", skip=0, take=50, trading_type="All", strategy_master_ids=None):
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
    try:
        resp = requests.post(
            Config.GET_STRATEGIES_URL,
            json=payload,
            headers=_auth_headers(),
            timeout=30,
        )
        print(f"[SharedAPI] GET_STRATEGIES HTTP {resp.status_code}: {resp.text[:200]}")
        if resp.status_code == 200:
            data = resp.json()
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
                }
                for s in data.get("data", [])
            ]
            return {"status": "success", "total": data.get("total", 0), "strategies": strategies}
        return {"status": "error", "code": resp.status_code, "message": resp.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def delete_strategy(strategy_id="", strategy_name=""):
    """
    Delete by hash ID directly, or by name (auto-looks up the ID first).
    Pass either strategy_id (hash) or strategy_name (human-readable name).
    """
    sid = strategy_id

    # Market Maya hash IDs always contain "$" and are ≥20 chars; anything shorter is a plain name.
    if not sid or ("$" not in sid and len(sid) < 20):
        search_term = strategy_name or sid
        if not search_term:
            return {"status": "error", "message": "Provide strategy_id or strategy_name."}
        search_result = get_strategies(search=search_term, take=20)
        if search_result["status"] != "success":
            return search_result
        strategies = search_result.get("strategies", [])
        if not strategies:
            return {"status": "error", "message": f"No strategy found matching '{search_term}'."}
        # Prefer exact name match, fall back to first result
        exact = [s for s in strategies if s["name"].lower() == search_term.lower()]
        chosen = exact[0] if exact else strategies[0]
        sid = chosen["id"]
        print(f"[SharedAPI] Resolved '{search_term}' → id={sid} (name={chosen['name']})")

    try:
        resp = requests.post(
            Config.DELETE_STRATEGY_URL,
            json={"id": sid},
            headers=_auth_headers(),
            timeout=30,
        )
        print(f"[SharedAPI] DELETE HTTP {resp.status_code}: {resp.text[:200]}")
        if resp.status_code == 200:
            return {"status": "success", "message": "Strategy deleted successfully."}
        return {"status": "error", "code": resp.status_code, "message": resp.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_strategy_record(strategy_id="", strategy_name=""):
    """Fetch full strategy record, returned in modify-ready snake_case payload format."""
    sid = strategy_id
    if not sid or ("$" not in sid and len(sid) < 20):
        search_term = strategy_name or sid
        if not search_term:
            return {"status": "error", "message": "Provide strategy_id or strategy_name."}
        search_result = get_strategies(search=search_term, take=10)
        if search_result["status"] != "success":
            return search_result
        strategies = search_result.get("strategies", [])
        if not strategies:
            return {"status": "error", "message": f"No strategy found matching '{search_term}'."}
        exact = [s for s in strategies if s["name"].lower() == search_term.lower()]
        chosen = exact[0] if exact else strategies[0]
        sid = chosen["id"]
        print(f"[SharedAPI] Resolved '{search_term}' → id={sid}")

    try:
        resp = requests.get(
            Config.GET_STRATEGY_RECORD_URL,
            params={"strategyId": sid},
            headers=_auth_headers(),
            timeout=30,
        )
        print(f"[SharedAPI] GET_RECORD HTTP {resp.status_code}: {resp.text[:200]}")
        if resp.status_code == 200:
            body = resp.json()
            if body.get("statusCode") == 200:
                payload = _record_to_modify_payload(body["data"])
                return {"status": "success", "strategy": payload}
            return {"status": "error", "message": body.get("message", "Failed to fetch record.")}
        return {"status": "error", "code": resp.status_code, "message": resp.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def modify_strategy(payload):
    """Save a modified ISB strategy. Payload must be in modify-payload format with 'id' field."""
    if not payload.get("id"):
        return {"status": "error", "message": "Payload must include the strategy 'id' field."}
    try:
        resp = requests.post(
            Config.MODIFY_STRATEGY_URL,
            json=payload,
            headers=_auth_headers(),
            timeout=30,
        )
        print(f"[SharedAPI] MODIFY HTTP {resp.status_code}: {resp.text[:200]}")
        if resp.status_code == 200:
            body = resp.json()
            if body.get("success"):
                return {"status": "success", "message": "Strategy modified successfully."}
            return {"status": "error", "message": body.get("message", "Modification failed.")}
        return {"status": "error", "code": resp.status_code, "message": resp.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_balance():
    """Fetch account balance: point_balance, hold_balance, balance."""
    try:
        resp = requests.post(
            Config.GET_BALANCE_URL,
            json={},
            headers=_auth_headers(),
            timeout=30,
        )
        print(f"[SharedAPI] GET_BALANCE HTTP {resp.status_code}: {resp.text[:200]}")
        if resp.status_code == 200:
            data = resp.json()
            return {
                "status": "success",
                "balance": data.get("balance", 0.0),
                "hold_balance": data.get("hold_balance", 0.0),
                "point_balance": data.get("point_balance", 0.0),
            }
        return {"status": "error", "code": resp.status_code, "message": resp.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def rename_strategy(strategy_id="", strategy_name="", new_name=""):
    """Rename a strategy. Resolves name→ID automatically if only strategy_name is given."""
    if not new_name:
        return {"status": "error", "message": "new_name is required."}

    sid = strategy_id
    if not sid or ("$" not in sid and len(sid) < 20):
        search_term = strategy_name or sid
        if not search_term:
            return {"status": "error", "message": "Provide strategy_id or strategy_name."}
        search_result = get_strategies(search=search_term, take=10)
        if search_result["status"] != "success":
            return search_result
        strategies = search_result.get("strategies", [])
        if not strategies:
            return {"status": "error", "message": f"No strategy found matching '{search_term}'."}
        exact = [s for s in strategies if s["name"].lower() == search_term.lower()]
        chosen = exact[0] if exact else strategies[0]
        sid = chosen["id"]
        print(f"[SharedAPI] Resolved '{search_term}' → id={sid}")

    try:
        resp = requests.post(
            Config.RENAME_STRATEGY_URL,
            json={"id": sid, "name": new_name},
            headers=_auth_headers(),
            timeout=30,
        )
        print(f"[SharedAPI] RENAME HTTP {resp.status_code}: {resp.text[:200]}")
        if resp.status_code == 200:
            data = resp.json()
            return {
                "status": "success",
                "strategy_name": data.get("strategy_name"),
                "message": f"Strategy renamed to '{new_name}' successfully.",
            }
        return {"status": "error", "code": resp.status_code, "message": resp.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}
