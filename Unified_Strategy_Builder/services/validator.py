"""USB strategy validator — checks required fields and allowed values before payload generation."""

_STRIKE_TYPE_MAP = {
    "ATM":              "Strike By ATM Value",
    "ATM%":             "Strike By ATM %",
    "PREMIUM_RANGE":    "Strike By Premium Range",
    "NEAREST_PREMIUM":  "Strike By Nearest Premium",
    "DELTA_RANGE":      "Strike By Delta Range",
    "NEAREST_DELTA":    "Strike By Nearest Delta",
    "THETA_RANGE":      "Strike By Theta Range",
    "NEAREST_THETA":    "Strike By Nearest Theta",
}
_ALLOWED_STRIKE_TYPES = set(_STRIKE_TYPE_MAP.values())


class StrategyValidator:
    def validate_main_parameters(self, params):
        errors = []

        # Strategy Name — accept both camelCase and snake_case
        name = params.get("strategyName", params.get("strategy_name", ""))
        if not name:
            errors.append("Strategy Name is required.")
        elif not (3 <= len(name) <= 100):
            errors.append("Strategy Name must be between 3 and 100 characters.")

        # Exchange — accept mainExchange (API) or exchange (LLM schema)
        exchange = params.get("mainExchange") or params.get("exchange", "")
        allowed_exchanges = ["NSE", "NFO", "BFO", "BSE", "MCX", "CDS"]
        if exchange not in allowed_exchanges:
            errors.append(f"Invalid Exchange. Must be one of: {', '.join(allowed_exchanges)}")

        # Segment — accept mainSegment (API) or segment (LLM schema); also allow EQ/INDEX
        segment = params.get("mainSegment") or params.get("segment", "")
        allowed_segments = ["FUT", "OPT", "EQ", "INDEX"]
        if segment not in allowed_segments:
            errors.append(f"Invalid Segment. Must be one of: {', '.join(allowed_segments)}")

        # Trading Type — accept isIntraday (bool), is_intraday, or trading_type string
        is_intraday = params.get("isIntraday", params.get("is_intraday", None))
        if is_intraday is None:
            trading_type = str(params.get("trading_type", params.get("tradingType", "intraday"))).lower()
            is_intraday = "positional" not in trading_type
        if not isinstance(is_intraday, bool):
            errors.append("Trading Type must be Intraday (True) or Positional (False).")

        return errors

    def validate_leg_parameters(self, leg):
        errors = []

        # Trade Side — accept tradeSide (API) or action (LLM schema)
        trade_side = leg.get("tradeSide") or leg.get("action", "")
        if str(trade_side).upper() not in ("BUY", "SELL"):
            errors.append("Trade Side must be BUY or SELL.")

        # Lots — accept lot (API) or lots (LLM schema)
        lots_raw = leg.get("lot", leg.get("lots", 0))
        try:
            if int(lots_raw) <= 0:
                errors.append("Lots must be a positive integer.")
        except (TypeError, ValueError):
            errors.append("Lots must be a positive integer.")

        # Option Type — accept optionType (API) or option (LLM schema)
        segment = str(leg.get("segment", "OPT")).upper()
        option_type = leg.get("optionType") or leg.get("option", "")
        if segment == "OPT" and str(option_type).upper() not in ("CE", "PE"):
            errors.append("Option Type must be CE or PE for OPT segment.")

        # Strike Selection — accept atmType (API) or strike_type (LLM schema)
        # Also accept short codes: ATM, ATM%, PREMIUM_RANGE, etc.
        raw = str(leg.get("atmType") or leg.get("strike_type", "ATM")).upper().strip()
        if raw in _STRIKE_TYPE_MAP:
            pass  # short code — valid
        elif raw.title().replace("Atm", "ATM") in _ALLOWED_STRIKE_TYPES:
            pass  # long-form string, case-normalized — valid
        elif any(raw == s.upper() for s in _ALLOWED_STRIKE_TYPES):
            pass  # exact uppercase match — valid
        else:
            errors.append(
                f"Invalid Strike Selection '{raw}'. Must be one of: {', '.join(sorted(_ALLOWED_STRIKE_TYPES))}"
            )

        return errors


# Singleton instance
validator = StrategyValidator()
