import json
import os
import re
import time

# ── Lot sizes per symbol ────────────────────────────────────────────────────
LOT_SIZES = {
    "BANKNIFTY": 30, "NIFTY": 25, "FINNIFTY": 40,
    "MIDCPNIFTY": 75, "SENSEX": 20, "BANKEX": 15,
}

# ── Load indicator master data (with real IDs from Market Maya API) ─────────
_MASTER_JSON_PATH = os.path.join(os.path.dirname(__file__), "indicator_master.json")
with open(_MASTER_JSON_PATH, "r") as _f:
    _MASTER_LIST = json.load(_f)

# Build lookup: indicator_code → full master entry (with id + parameters with ids)
# Also support short aliases: "hammer" → "candlestick-hammer", etc.
INDICATOR_MASTER = {}
for _entry in _MASTER_LIST:
    code = _entry["indicator_code"]
    INDICATOR_MASTER[code] = _entry
    # Add short alias without "candlestick-" prefix for backward compat
    if code.startswith("candlestick-"):
        short = code.replace("candlestick-", "", 1)
        INDICATOR_MASTER[short] = _entry

STRATEGY_TYPE_ID = "QFwz7gYjmmabUT8SBvZQGgaC0$aC0$"


class ISEPayloadGenerator:

    def generate_payload(self, strategy_json):
        # ── Strategy name — append fresh 4-digit suffix ──────────────────────
        raw_name = strategy_json.get("strategyName", "ISE_Strategy")
        strategy_name = re.sub(r'_\d{4}$', '', raw_name) + f"_{int(time.time()) % 10000}"

        # ── Trading type ─────────────────────────────────────────────────────
        is_intraday = bool(strategy_json.get("isIntraday", True))
        default_product = "MIS" if is_intraday else "NRML"

        # ── Master trail SL ──────────────────────────────────────────────────
        is_trail_sl = bool(strategy_json.get("isTrailSl", False))
        profit_move = int(strategy_json.get("profitMove", 0))
        sl_move = int(strategy_json.get("slMove", 0))
        no_of_trail_sl = self._parse_trail_count(strategy_json.get("noOfTrailSl", 0))

        if profit_move > 0 or sl_move > 0:
            is_trail_sl = True

        # ── Week days ────────────────────────────────────────────────────────
        week_days = strategy_json.get("weekDays", ["MON", "TUE", "WED", "THU", "FRI"])
        if isinstance(week_days, str):
            week_days = [d.strip().upper() for d in week_days.split(",")]
        week_days = [d.upper() for d in week_days]

        # ── Legs (sub) ───────────────────────────────────────────────────────
        sub_legs = [self._build_leg(leg) for leg in strategy_json.get("legs", [])]

        # ── Indicators ───────────────────────────────────────────────────────
        indicators = [self._build_indicator(ind) for ind in strategy_json.get("indicators", [])]

        payload = {
            "id": "",
            "strategyName": strategy_name,
            "requiredMargin": int(strategy_json.get("requiredMargin", 1)),
            "isIntraday": is_intraday,
            "entryOrderProduct": strategy_json.get("entryOrderProduct", default_product),
            "exitOrderProduct": strategy_json.get("exitOrderProduct", default_product),
            "chartType": strategy_json.get("chartType", "Candlestick"),
            "timeFrame": strategy_json.get("timeFrame", "5Min"),
            "signal": strategy_json.get("signal", "Both"),
            "entryTime": strategy_json.get("entryTime", "09:15"),
            "weekDays": week_days,
            "sqroffTime": strategy_json.get("sqroffTime", "15:15"),
            "sqroffBeforeExDays": int(strategy_json.get("sqroffBeforeExDays", 0)),
            "masterTarget": int(strategy_json.get("masterTarget", 0)),
            "masterTargetType": "Money",
            "masterSl": int(strategy_json.get("masterSl", 0)),
            "masterSlType": "Money",
            "isTrailSl": is_trail_sl,
            "profitMove": profit_move,
            "slMove": sl_move,
            "noOfTrailSl": no_of_trail_sl if is_trail_sl else 0,
            "shortDescription": strategy_json.get("shortDescription", ""),
            "longDescription": strategy_json.get("longDescription", ""),
            "strategyTypeId": STRATEGY_TYPE_ID,
            "underlyingType": strategy_json.get("underlyingType", "Future"),
            "rebacktest": True,
            "effectAllSubStrategies": False,
            "sub": sub_legs,
            "indicators": indicators,
        }

        return payload

    def _build_leg(self, leg):
        symbol = str(leg.get("symbol", "BANKNIFTY")).upper()
        if symbol == "NIFTY50":
            symbol = "NIFTY"

        segment = str(leg.get("segment", "FUT")).upper()
        if segment == "STOCK":
            segment = "Stock"

        lot = int(leg.get("lot", 1))
        lot_size = LOT_SIZES.get(symbol, 1)
        qty = lot * lot_size

        # optionType: empty string for FUT/Stock, CE/PE for OPT
        option_type = str(leg.get("optionType", "")).upper()
        if segment != "OPT":
            option_type = ""
        elif option_type not in ("CE", "PE"):
            option_type = "CE"

        # atm: 0 for FUT/Stock
        atm = int(leg.get("atm", 0)) if segment == "OPT" else 0

        # Leg-level trail SL
        is_leg_trail = bool(leg.get("isTrailSl", False))
        trail_market_move = int(leg.get("trailSlMarketMove", 0))
        trail_sl_move = int(leg.get("trailSlMove", 0))
        no_of_trail = self._parse_trail_count(leg.get("noOfTimeTrailSl", 0))

        if trail_market_move > 0 or trail_sl_move > 0:
            is_leg_trail = True

        # Target / SL — 0 means disabled
        target = int(leg.get("target", 0))
        sl = int(leg.get("sl", 0))

        return {
            "id": "",
            "callType": "BUY",
            "exchange": str(leg.get("exchange", "NFO")).upper(),
            "segment": segment,
            "symbol": symbol,
            "contract": str(leg.get("contract", "NEAR")).upper(),
            "expiry": str(leg.get("expiry", "MONTHLY")).upper(),
            "atm": atm,
            "optionType": option_type,
            "qty": qty,
            "lot": lot,
            "target": target,
            "targetBy": "Money",
            "sl": sl,
            "slBy": "Money",
            "trailSlMarketMove": trail_market_move if is_leg_trail else 0,
            "trailSlMove": trail_sl_move if is_leg_trail else 0,
            "noOfTimeTrailSl": no_of_trail if is_leg_trail else 0,
            "isTrailSl": is_leg_trail,
            "isReverseSignal": bool(leg.get("isReverseSignal", False)),
        }

    def _build_indicator(self, ind):
        """Build indicator payload using real IDs from the Market Maya indicator master."""
        code = str(ind.get("indicator_code", "")).lower()
        master = INDICATOR_MASTER.get(code)

        if not master:
            # Unknown indicator — return minimal structure (will likely fail on API)
            print(f"[ISE Generator] WARNING: Unknown indicator code '{code}', no master data found")
            return {
                "id": "",
                "index": int(ind.get("index", 1)),
                "indicator_name": ind.get("indicator_name", code),
                "indicator_code": code,
                "parameter": [],
            }

        # User-supplied parameter values (from AI JSON)
        user_params = ind.get("parameters", {})
        if not isinstance(user_params, dict):
            user_params = {}

        # Build parameter list using master template — preserving real IDs
        built_params = []
        for p in master["parameter"]:
            param_code = p["param_code"]
            # Try param_code first, then param_name as fallback
            user_val = user_params.get(param_code, user_params.get(p["param_name"], None))
            value = str(user_val) if user_val is not None else p["default_value"]

            built_params.append({
                "id": p["id"],
                "param_name": p["param_name"],
                "param_code": param_code,
                "param_type": p["param_type"],
                "is_required": p.get("is_required", True),
                "default_value": p["default_value"],
                "enum_value": p.get("enum_value", ""),
                "min_value": p.get("min_value", 0),
                "max_value": p.get("max_value", 0),
                "value": value,
            })

        return {
            "id": master["id"],
            "index": int(ind.get("index", 1)),
            "indicator_name": master["indicator_name"],
            "indicator_code": master["indicator_code"],
            "parameter": built_params,
        }

    def _parse_trail_count(self, value):
        if isinstance(value, str) and value.lower() in ("unlimited", "infinite"):
            return 0
        try:
            return int(value)
        except Exception:
            return 0


# Singleton instance
ise_generator = ISEPayloadGenerator()
