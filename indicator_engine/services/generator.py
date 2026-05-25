import re
import time

# ── Lot sizes per symbol ────────────────────────────────────────────────────
LOT_SIZES = {
    "BANKNIFTY": 30, "NIFTY": 25, "FINNIFTY": 40,
    "MIDCPNIFTY": 75, "SENSEX": 20, "BANKEX": 15,
}

# ── Full indicator definitions — maps code → API parameter structure ────────
INDICATOR_DEFINITIONS = {
    "supertrend": {
        "indicator_name": "Super Trend",
        "parameters": [
            {"param_name": "Length", "param_code": "length", "param_type": "int",
             "default_value": "10", "enum_value": "", "min_value": 1, "max_value": 200},
            {"param_name": "Factor", "param_code": "factor", "param_type": "int",
             "default_value": "3", "enum_value": "", "min_value": 1, "max_value": 200},
        ]
    },
    "ma-cross-over": {
        "indicator_name": "MA Cross Over",
        "parameters": [
            {"param_name": "Short", "param_code": "short", "param_type": "int",
             "default_value": "9", "enum_value": "", "min_value": 1, "max_value": 200},
            {"param_name": "Long", "param_code": "long", "param_type": "int",
             "default_value": "26", "enum_value": "", "min_value": 1, "max_value": 200},
            {"param_name": "Type", "param_code": "type", "param_type": "enum",
             "default_value": "SMA", "enum_value": "SMA|EMA|WMA", "min_value": 0, "max_value": 0},
        ]
    },
    "rsi": {
        "indicator_name": "RSI",
        "parameters": [
            {"param_name": "Length", "param_code": "length", "param_type": "int",
             "default_value": "14", "enum_value": "", "min_value": 1, "max_value": 200},
            {"param_name": "Smoothing Line", "param_code": "smoothing-line", "param_type": "enum",
             "default_value": "SMA", "enum_value": "SMA|EMA|WMA", "min_value": 0, "max_value": 0},
            {"param_name": "Smoothing Length", "param_code": "smoothing-length", "param_type": "int",
             "default_value": "14", "enum_value": "", "min_value": 1, "max_value": 200},
            {"param_name": "Lower Band", "param_code": "lower-band", "param_type": "int",
             "default_value": "30", "enum_value": "", "min_value": 1, "max_value": 50},
            {"param_name": "Upper Band", "param_code": "upper-band", "param_type": "int",
             "default_value": "70", "enum_value": "", "min_value": 50, "max_value": 100},
        ]
    },
    "macd": {
        "indicator_name": "MACD",
        "parameters": [
            {"param_name": "Fast Length", "param_code": "fast-length", "param_type": "int",
             "default_value": "12", "enum_value": "", "min_value": 1, "max_value": 200},
            {"param_name": "Slow Length", "param_code": "slow-length", "param_type": "int",
             "default_value": "26", "enum_value": "", "min_value": 1, "max_value": 200},
            {"param_name": "Source", "param_code": "source", "param_type": "enum",
             "default_value": "Close", "enum_value": "Open|High|Low|Close", "min_value": 0, "max_value": 0},
            {"param_name": "Signal Length", "param_code": "signal-length", "param_type": "int",
             "default_value": "9", "enum_value": "", "min_value": 1, "max_value": 200},
            {"param_name": "Oscillator MA Type", "param_code": "oscillator-ma-type", "param_type": "enum",
             "default_value": "EMA", "enum_value": "EMA|SMA|WMA", "min_value": 0, "max_value": 0},
            {"param_name": "Signal Line MA Type", "param_code": "signal-line-ma-type", "param_type": "enum",
             "default_value": "EMA", "enum_value": "EMA|SMA|WMA", "min_value": 0, "max_value": 0},
        ]
    },
    "stochastic": {
        "indicator_name": "Stochastic",
        "parameters": [
            {"param_name": "%K Length", "param_code": "k-length", "param_type": "int",
             "default_value": "14", "enum_value": "", "min_value": 1, "max_value": 200},
            {"param_name": "%D Length", "param_code": "d-length", "param_type": "int",
             "default_value": "3", "enum_value": "", "min_value": 1, "max_value": 200},
            {"param_name": "Lower Band", "param_code": "lower-band", "param_type": "int",
             "default_value": "20", "enum_value": "", "min_value": 1, "max_value": 50},
            {"param_name": "Upper Band", "param_code": "upper-band", "param_type": "int",
             "default_value": "80", "enum_value": "", "min_value": 50, "max_value": 100},
        ]
    },
    "bollinger-bands": {
        "indicator_name": "Bollinger Bands",
        "parameters": [
            {"param_name": "Length", "param_code": "length", "param_type": "int",
             "default_value": "20", "enum_value": "", "min_value": 1, "max_value": 200},
            {"param_name": "Multiplier", "param_code": "multiplier", "param_type": "int",
             "default_value": "2", "enum_value": "", "min_value": 1, "max_value": 200},
            {"param_name": "Source", "param_code": "source", "param_type": "enum",
             "default_value": "Close", "enum_value": "Open|High|Low|Close", "min_value": 0, "max_value": 0},
        ]
    },
    # Candlestick patterns — no parameters
    "hammer":                {"indicator_name": "Hammer",                "parameters": []},
    "morning-star":          {"indicator_name": "Morning Star",          "parameters": []},
    "evening-star":          {"indicator_name": "Evening Star",          "parameters": []},
    "rising-three-methods":  {"indicator_name": "Rising Three Methods",  "parameters": []},
    "falling-three-methods": {"indicator_name": "Falling Three Methods", "parameters": []},
    "three-black-crows":     {"indicator_name": "Three Black Crows",     "parameters": []},
    "three-white-soldiers":  {"indicator_name": "Three White Soldiers",  "parameters": []},
}

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

        # If any trailing field is set, enable the flag
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
        code = str(ind.get("indicator_code", "")).lower()
        defn = INDICATOR_DEFINITIONS.get(code)

        if not defn:
            # Unknown indicator — return minimal structure
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

        built_params = []
        for p in defn["parameters"]:
            code_key = p["param_code"]
            # Try code key first, then param_name key as fallback
            user_val = user_params.get(code_key, user_params.get(p["param_name"], None))
            value = str(user_val) if user_val is not None else p["default_value"]

            built_params.append({
                "id": "",
                "param_name": p["param_name"],
                "param_code": code_key,
                "param_type": p["param_type"],
                "is_required": True,
                "default_value": p["default_value"],
                "enum_value": p["enum_value"],
                "min_value": p["min_value"],
                "max_value": p["max_value"],
                "value": value,
            })

        return {
            "id": "",
            "index": int(ind.get("index", 1)),
            "indicator_name": defn["indicator_name"],
            "indicator_code": code,
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
