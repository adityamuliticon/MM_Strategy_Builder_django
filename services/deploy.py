"""Strategy deployment service: fetches charges, resolves strategy ID, posts to Market Maya deploy endpoint."""

import requests
from config import Config
from services.market_maya_shared import get_strategies


def _resolve_strategy_id(strategy_id="", strategy_name=""):
    search_term = strategy_name or strategy_id
    if not search_term:
        return None, None, "Provide strategy_id or strategy_name."
    result = get_strategies(search=search_term, take=10)
    if result["status"] != "success":
        return None, None, result.get("message", "Failed to search strategies.")
    strategies = result.get("strategies", [])
    if not strategies:
        return None, None, f"No strategy found matching '{search_term}'."
    exact = [s for s in strategies if s["name"].lower() == search_term.lower()]
    chosen = exact[0] if exact else strategies[0]
    return chosen["id"], chosen.get("name", search_term), None


def _auth_headers():
    token = Config.MARKET_MAYA_BEARER_TOKEN or ""
    if token and not token.startswith("Bearer "):
        token = f"Bearer {token}"
    return {
        "Authorization": token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _fetch_point_balance(headers):
    try:
        r = requests.post(Config.GET_BALANCE_URL, json={}, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json().get("point_balance", 0.0)
    except Exception as e:
        print(f"[Deploy] Balance fetch error: {e}")
    return None


def get_deploy_options(strategy_id="", strategy_name=""):
    """
    Fetch point balance + charges before deploying.
    Shows the user: current balance, live/paper charge per order, and disclaimer.
    """
    hash_id, resolved_name, err = _resolve_strategy_id(strategy_id, strategy_name)
    if err:
        return {"status": "error", "message": err}

    headers = _auth_headers()

    balance = _fetch_point_balance(headers)

    charges = {}
    try:
        r = requests.post(Config.GET_CHARGES_URL, json={}, headers=headers, timeout=15)
        print(f"[Deploy] GET_CHARGES HTTP {r.status_code}: {r.text[:200]}")
        if r.status_code == 200:
            charges = r.json()
    except Exception as e:
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
    Flow: resolve strategy → POST /mainStrategy/deploy → refresh balance.
    """
    hash_id, resolved_name, err = _resolve_strategy_id(strategy_id, strategy_name)
    if err:
        return {"status": "error", "message": err}

    headers = _auth_headers()
    paper_trading = str(trading_mode).lower() in ("paper", "paper trading", "papertrading")

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

    print(f"[Deploy] POST deploy payload: {payload}")

    try:
        r = requests.post(Config.DEPLOY_STRATEGY_URL, json=payload, headers=headers, timeout=30)
        print(f"[Deploy] HTTP {r.status_code}: {r.text[:300]}")

        if r.status_code == 200:
            resp_data = r.json()
            if resp_data.get("statusCode") == 200:
                updated_balance = _fetch_point_balance(headers)
                return {
                    "status": "success",
                    "message": f"Strategy '{resolved_name}' deployed successfully to {('Paper' if paper_trading else 'Live')} Trading.",
                    "deployment_id": resp_data.get("data"),
                    "trading_mode": "Paper Trading" if paper_trading else "Live Trading",
                    "updated_point_balance": updated_balance,
                }
            else:
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
                err_msg = r.text
            return {"status": "error", "code": r.status_code, "message": err_msg}

    except Exception as e:
        return {"status": "error", "message": str(e)}
