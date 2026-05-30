import json
import time
import requests
from config import Config
from services.market_maya_shared import get_strategies


def _resolve_strategy_id(strategy_id="", strategy_name=""):
    """Resolve name → hash ID if needed. Returns (sid, error_msg)."""
    if strategy_id and ("$" in strategy_id or len(strategy_id) > 20):
        return strategy_id, None
    search_term = strategy_name or strategy_id
    if not search_term:
        return None, "Provide strategy_id or strategy_name."
    result = get_strategies(search=search_term, take=10)
    if result["status"] != "success":
        return None, result.get("message", "Failed to search strategies.")
    strategies = result.get("strategies", [])
    if not strategies:
        return None, f"No strategy found matching '{search_term}'."
    exact = [s for s in strategies if s["name"].lower() == search_term.lower()]
    chosen = exact[0] if exact else strategies[0]
    return chosen["id"], None


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
    """Helper: fetch current point balance. Returns float or None on failure."""
    try:
        r = requests.post(Config.GET_BALANCE_URL, json={}, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json().get("point_balance", 0.0)
    except Exception as e:
        print(f"[Backtest] Balance fetch error: {e}")
    return None


def get_backtest_options(strategy_id="", strategy_name=""):
    """Fetch available backtest time periods, point costs, and current point balance."""
    sid, err = _resolve_strategy_id(strategy_id, strategy_name)
    if err:
        return {"status": "error", "message": err}

    headers = _auth_headers()

    try:
        resp = requests.post(
            Config.BACKTEST_OPTIONS_URL,
            json={"id": sid},
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

        # Fetch current point balance so the AI can warn if insufficient
        point_balance = _fetch_point_balance(headers)

        return {
            "status": "success",
            "strategy_id": sid,
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
    """Deduct backtest points, trigger the run, and poll until completed (up to 60s)."""
    sid, err = _resolve_strategy_id(strategy_id, strategy_name)
    if err:
        return {"status": "error", "message": err}
    if not start_date or not end_date:
        return {"status": "error", "message": "start_date and end_date are required (YYYY-MM-DD)."}

    headers = _auth_headers()

    # Step 1: Balance check — verify sufficient points before deducting
    try:
        options_resp = requests.post(
            Config.BACKTEST_OPTIONS_URL,
            json={"id": sid},
            headers=headers,
            timeout=30,
        )
        if options_resp.status_code == 200:
            options_data = options_resp.json()
            # Find the cost for the requested period
            required_points = None
            for item in options_data.get("items", []):
                item_start = item.get("start_date", "")[:10]
                item_end = item.get("end_date", "")[:10]
                if item_start == start_date[:10] and item_end == end_date[:10]:
                    required_points = item.get("points", 0)
                    break

            if required_points is not None and required_points > 0:
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
        print(f"[Backtest] Balance pre-check error (proceeding anyway): {e}")

    # Step 2: Trigger backtest
    try:
        resp = requests.post(
            Config.DEDUCT_BACKTEST_POINTS_URL,
            json={"id": sid, "startDate": start_date, "endDate": end_date, "executionLevel": "Level 8"},
            headers=headers,
            timeout=30,
        )
        print(f"[Backtest] DEDUCT_POINTS HTTP {resp.status_code}: {resp.text[:200]}")
        if resp.status_code not in (200, 201):
            # Try to extract a meaningful server error message
            err_msg = None
            try:
                body = resp.json()
                err_msg = body.get("message") or body.get("error") or body.get("msg")
            except Exception:
                pass
            if err_msg:
                # Real error from the server — surface it, do not proceed
                return {"status": "error", "message": err_msg}
            # No message body (e.g. transient 5xx overload) — still try to poll
    except Exception as e:
        return {"status": "error", "message": f"Failed to trigger backtest: {e}"}

    # Step 3: Poll up to 5 times with 3s gap (max ~15s wait).
    # deductBacktestPoints is only ever called ONCE above — these are free GET polls.
    last_error_msg = None
    for attempt in range(5):
        time.sleep(3)
        try:
            result_resp = requests.get(
                f"{Config.GET_BACKTEST_RESULT_URL}?id={sid}",
                headers=_auth_headers(),
                timeout=30,
            )
            print(f"[Backtest] GET_RESULT attempt {attempt+1} HTTP {result_resp.status_code}")
            if result_resp.status_code == 200:
                body = result_resp.json()
                data = body.get("data") or {}
                if isinstance(data, dict) and data.get("status") == "Completed":
                    return _format_result(data)
            elif result_resp.status_code == 404:
                try:
                    last_error_msg = result_resp.json().get("message")
                except Exception:
                    pass
        except Exception as e:
            print(f"[Backtest] Poll error attempt {attempt+1}: {e}")

    # If all polls got a 404 with a server message, the strategy likely can't be backtested
    if last_error_msg:
        return {"status": "error", "message": last_error_msg}

    return {
        "status": "processing",
        "message": (
            "The backtest has been triggered and is still processing on Market Maya's servers. "
            "Use get_backtest_result in about 30 seconds to retrieve the completed result for free."
        ),
    }


def get_backtest_result(strategy_id="", strategy_name=""):
    """Fetch full stored backtest results (no points charged).
    Calls all 4 history APIs: strategy detail, day history, month history, year history."""
    sid, err = _resolve_strategy_id(strategy_id, strategy_name)
    if err:
        return {"status": "error", "message": err}

    headers = _auth_headers()

    # Step 1: Strategy detail + stored summary stats
    try:
        resp = requests.get(Config.GET_STRATEGY_DETAIL_URL, params={"id": sid}, headers=headers, timeout=30)
        print(f"[Backtest] GET_DETAIL HTTP {resp.status_code}: {resp.text[:200]}")
        if resp.status_code != 200:
            return {"status": "error", "code": resp.status_code, "message": resp.text}
        body = resp.json()
        if body.get("statusCode") != 200:
            return {"status": "error", "message": body.get("message", "Failed to fetch strategy detail.")}
        detail_data = body.get("data", {})
    except Exception as e:
        return {"status": "error", "message": str(e)}

    # Check if any backtest has been run
    stats = detail_data.get("statistics") or {}
    backtest_dates = detail_data.get("backtestDates") or {}
    period_start = (backtest_dates.get("backtestDataStartDate") or stats.get("backtestDataStartDate", ""))
    period_end = (backtest_dates.get("backtestDataEndDate") or stats.get("backtestDataEndDate", ""))

    if not period_start:
        return {
            "status": "no_backtest",
            "message": "No backtest has been run for this strategy yet. Use get_backtest_options to start one.",
        }

    start_dt = period_start[:10]   # YYYY-MM-DD
    end_dt = period_end[:10]
    start_full = f"{start_dt}T00:00:00"
    end_full = f"{end_dt}T23:59:59"

    # Step 2: Day-by-day P&L history
    day_history = []
    try:
        r = requests.get(Config.GET_DAY_TRADE_HISTORY_URL, params={
            "strategyId": sid, "startDate": start_full, "endDate": end_full,
            "entryType": "BackTest", "pnlStart": 0, "pnlEnd": 0,
        }, headers=headers, timeout=30)
        print(f"[Backtest] DAY_HISTORY HTTP {r.status_code}")
        if r.status_code == 200:
            day_history = r.json().get("data", [])
    except Exception as e:
        print(f"[Backtest] DayHistory error: {e}")

    # Step 3: Monthly P&L history (one call per year in the backtest range)
    start_year = int(start_dt[:4])
    end_year = int(end_dt[:4])
    month_history = []
    for year in range(start_year, end_year + 1):
        try:
            r = requests.get(Config.GET_MONTH_TRADE_HISTORY_URL, params={
                "year": year, "strategyId": sid, "entryType": "BackTest",
            }, headers=headers, timeout=30)
            print(f"[Backtest] MONTH_HISTORY {year} HTTP {r.status_code}")
            if r.status_code == 200:
                month_history.extend(r.json().get("data", []))
        except Exception as e:
            print(f"[Backtest] MonthHistory error for {year}: {e}")
    # Sort chronologically oldest → newest
    month_history.sort(key=lambda x: x.get("tradingdate", ""))

    # Step 4: Yearly P&L history
    year_history = []
    try:
        r = requests.get(Config.GET_YEAR_TRADE_HISTORY_URL, params={
            "id": sid, "entryType": "BackTest",
        }, headers=headers, timeout=30)
        print(f"[Backtest] YEAR_HISTORY HTTP {r.status_code}")
        if r.status_code == 200:
            year_history = r.json().get("data", [])
    except Exception as e:
        print(f"[Backtest] YearHistory error: {e}")

    result = _format_detail_result(detail_data)
    result["day_trade_history"] = day_history       # [{tradingdate, trades, positive, negative, profit, ...}]
    result["month_trade_history"] = month_history   # [{tradingmonth, trades, positive, negative, profit, ...}]
    result["year_trade_history"] = year_history     # [{tradingyear, trades, positive, negative, profit, ...}]
    return result


def _extract_analysis_value(items):
    """Convert analysis array [{name, valueInt/valueStr/valueDouble}] → {name: value} dict."""
    result = {}
    for item in items or []:
        name = item.get("name", "")
        val = item.get("valueStr") or item.get("valueInt") or item.get("valueDouble")
        result[name] = val
    return result


def _format_detail_result(data):
    """Extract and format stored backtest result from getClientMyStrategyDetail response."""
    stats = data.get("statistics") or {}
    backtest_dates = data.get("backtestDates") or {}

    # Prefer statistics for dates if backtestDates not populated
    period_start = (backtest_dates.get("backtestDataStartDate")
                    or stats.get("backtestDataStartDate", ""))
    period_end = (backtest_dates.get("backtestDataEndDate")
                  or stats.get("backtestDataEndDate", ""))

    if not period_start:
        return {
            "status": "no_backtest",
            "message": "No backtest has been run for this strategy yet. Use 'get_backtest_options' to run one.",
        }

    return {
        "status": "success",
        "strategy_name": data.get("strategyName", ""),
        "backtest_run_date": backtest_dates.get("backtestJobStartDate") or stats.get("backtestJobStartDate", ""),
        "period_start": period_start,
        "period_end": period_end,
        "max_drawdown_recover_days": (backtest_dates.get("maxDrawDownRecoverDays")
                                      or stats.get("maxDrawDownRecoverDays")),
        "capital": stats.get("capital"),
        "year_roi": stats.get("yearRoi"),
        "drawdown_percent": stats.get("drawDownPercent"),
        "day_analysis": _extract_analysis_value(data.get("dayAnalysis")),
        "month_analysis": _extract_analysis_value(data.get("monthAnalysis")),
        "year_analysis": _extract_analysis_value(data.get("yearAnalysis")),
        "trade_analysis": _extract_analysis_value(data.get("tradeAnalysis")),
        "period_analyses": {
            "all_data": _strip_charts(_parse_analysis(stats.get("allDataAnalysis"))),
            "1_year": _strip_charts(_parse_analysis(stats.get("lastOneYearAnalysis"))),
            "6_months": _strip_charts(_parse_analysis(stats.get("lastSixMonthsAnalysis"))),
            "3_months": _strip_charts(_parse_analysis(stats.get("lastThreeMonthsAnalysis"))),
            "1_month": _strip_charts(_parse_analysis(stats.get("lastMonthAnalysis"))),
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
    """Remove the chart array from a parsed period analysis dict (not needed for AI tables)."""
    if not isinstance(d, dict):
        return d
    return {k: v for k, v in d.items() if k != "chart"}


def _format_result(data):
    """Extract and return key metrics from completed backtest data."""
    return {
        "status": "success",
        "summary": {
            "capital": data.get("capital"),
            "capital_fmt": data.get("capitalFormat"),
            "profit": data.get("profit"),
            "profit_fmt": data.get("plFormat"),
            "roi_percent": data.get("totalReturnPercent"),
            "drawdown": data.get("drawDown"),
            "drawdown_fmt": data.get("drawDownFormat"),
            "drawdown_percent": data.get("drawDownPercent"),
            "period_start": data.get("backtestDataStartDate"),
            "period_end": data.get("backtestDataEndDate"),
            "duration_days": data.get("backtestDurationDays"),
            "trading_days": data.get("totalTradingDays"),
        },
        "trades": {
            "total": data.get("totalTrades"),
            "positive": data.get("positiveTrades"),
            "negative": data.get("negativeTrades"),
            "buy": data.get("buyTrades"),
            "sell": data.get("sellTrades"),
            "sl": data.get("slTrades"),
            "target": data.get("targetTrades"),
            "cover": data.get("coverTrades"),
            "consecutive_pos_days": data.get("consecutivePosDays"),
            "consecutive_neg_days": data.get("consecutiveNegDays"),
        },
        "profit_metrics": {
            "day_avg": data.get("dayAverageProfit"),
            "day_max": data.get("dayMaxProfit"),
            "day_max_loss": data.get("dayMaxLoss"),
            "day_roi_pct": data.get("dayRoi"),
            "month_avg": data.get("monthAvgProfit"),
            "month_max": data.get("monthMaxProfit"),
            "month_max_loss": data.get("monthMaxLoss"),
            "month_min": data.get("monthMinProfit"),
            "month_roi_pct": data.get("monthRoi"),
            "year_avg": data.get("yearAvgProfit"),
            "year_max": data.get("yearMaxProfit"),
            "year_max_loss": data.get("yearMaxLoss"),
            "year_roi_pct": data.get("yearRoi"),
        },
        "day_of_week_pnl": {
            "Mon": data.get("allMonProfit"),
            "Tue": data.get("allTueProfit"),
            "Wed": data.get("allWedProfit"),
            "Thu": data.get("allThuProfit"),
            "Fri": data.get("allFriProfit"),
        },
        "risk": {
            "risk_profile": data.get("riskProfile"),
            "recovery_ratio": data.get("recoveryRatio"),
            "max_drawdown_recover_days": data.get("maxDrawDownRecoverDays"),
            "positive_days": data.get("totalPositiveDays"),
            "negative_days": data.get("totalNegativeDays"),
            "positive_months": data.get("totalPositiveMonths"),
            "negative_months": data.get("totalNegativeMonths"),
        },
        "period_analyses": {
            "1_month": _strip_charts(_parse_analysis(data.get("lastMonthAnalysis"))),
            "3_months": _strip_charts(_parse_analysis(data.get("lastThreeMonthsAnalysis"))),
            "6_months": _strip_charts(_parse_analysis(data.get("lastSixMonthsAnalysis"))),
            "1_year": _strip_charts(_parse_analysis(data.get("lastOneYearAnalysis"))),
            "all_data": _strip_charts(_parse_analysis(data.get("allDataAnalysis"))),
        },
    }
