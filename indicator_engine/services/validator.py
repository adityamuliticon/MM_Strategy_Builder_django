"""ISE strategy validator — checks required fields, allowed values, and indicator configuration."""

VALID_EXCHANGES = ["NSE", "NFO", "BFO", "BSE", "MCX", "CDS"]
VALID_SEGMENTS = ["FUT", "OPT", "EQ"]
VALID_CONTRACTS = ["NEAR", "NEXT", "FAR"]
VALID_EXPIRIES = ["MONTHLY", "WEEKLY"]
VALID_OPTION_TYPES = ["CE", "PE", ""]
VALID_TIMEFRAMES = ["5Min", "10Min", "15Min", "30Min", "1Hr", "4Hr", "1Hour", "4Hour", "1Day"]
VALID_CHART_TYPES = ["Candlestick", "Heikin-Ashi"]
VALID_SIGNALS = ["BUY", "SELL", "Both"]
VALID_UNDERLYING_TYPES = ["Future", "Spot/Index"]
VALID_PRODUCTS = ["MIS", "NRML", "CNC", "MTF"]


def _get_valid_indicator_codes():
    # H-12: derive valid codes from the same master JSON the generator uses,
    # so adding a new indicator to indicator_master.json automatically unlocks it here too.
    try:
        from indicator_engine.services.generator import _MASTER_LIST
        codes = {entry.get("indicatorCode") or entry.get("indicator_code") or entry.get("code")
                 for entry in _MASTER_LIST if entry}
        codes.discard(None)
        if codes:
            return codes
    except Exception:
        pass
    # Fallback list (used only if master JSON is unavailable)
    return {
        "supertrend", "ma-cross-over", "rsi", "macd", "stochastic", "bollinger-bands",
        "hammer", "morning-star", "evening-star",
        "rising-three-methods", "falling-three-methods",
        "three-black-crows", "three-white-soldiers",
    }


class ISEValidator:
    def validate_strategy(self, strategy_json):
        errors = []

        name = strategy_json.get("strategyName", "")
        if not name or len(name) < 3 or len(name) > 100:
            errors.append("strategyName must be 3–100 characters.")

        if strategy_json.get("isIntraday") not in [True, False]:
            errors.append("isIntraday must be true or false.")

        if strategy_json.get("chartType") not in VALID_CHART_TYPES:
            errors.append(f"chartType must be one of: {VALID_CHART_TYPES}")

        if strategy_json.get("timeFrame") not in VALID_TIMEFRAMES:
            errors.append(f"timeFrame must be one of: {VALID_TIMEFRAMES}")

        if strategy_json.get("signal") not in VALID_SIGNALS:
            errors.append(f"signal must be one of: {VALID_SIGNALS}")

        if strategy_json.get("entryOrderProduct") not in VALID_PRODUCTS:
            errors.append(f"entryOrderProduct must be one of: {VALID_PRODUCTS}")

        if strategy_json.get("exitOrderProduct") not in VALID_PRODUCTS:
            errors.append(f"exitOrderProduct must be one of: {VALID_PRODUCTS}")

        if strategy_json.get("underlyingType") not in VALID_UNDERLYING_TYPES:
            errors.append(f"underlyingType must be one of: {VALID_UNDERLYING_TYPES}")

        legs = strategy_json.get("legs", [])
        if not legs:
            errors.append("At least one leg is required.")

        for i, leg in enumerate(legs, 1):
            errors.extend(self._validate_leg(leg, i))

        indicators = strategy_json.get("indicators", [])
        if not indicators:
            errors.append("At least one indicator is required.")

        for i, ind in enumerate(indicators, 1):
            errors.extend(self._validate_indicator(ind, i))

        return errors

    def _validate_leg(self, leg, idx):
        errors = []
        prefix = f"Leg {idx}: "

        if leg.get("exchange") not in VALID_EXCHANGES:
            errors.append(f"{prefix}exchange must be one of: {VALID_EXCHANGES}")

        seg = leg.get("segment")
        if seg not in VALID_SEGMENTS:
            errors.append(f"{prefix}segment must be one of: {VALID_SEGMENTS}")

        if not leg.get("symbol"):
            errors.append(f"{prefix}symbol is required.")

        if leg.get("contract") not in VALID_CONTRACTS:
            errors.append(f"{prefix}contract must be one of: {VALID_CONTRACTS}")

        if leg.get("expiry") not in VALID_EXPIRIES:
            errors.append(f"{prefix}expiry must be MONTHLY or WEEKLY.")

        if seg == "OPT" and leg.get("optionType") not in ["CE", "PE"]:
            errors.append(f"{prefix}optionType must be CE or PE for OPT segment.")

        lot = leg.get("lot", 0)
        if not isinstance(lot, int) or lot <= 0:
            errors.append(f"{prefix}lot must be a positive integer.")

        return errors

    def _validate_indicator(self, ind, idx):
        errors = []
        prefix = f"Indicator {idx}: "

        if ind.get("indicator_code") not in _get_valid_indicator_codes():
            errors.append(f"{prefix}indicator_code '{ind.get('indicator_code')}' is not valid.")

        if not isinstance(ind.get("index", None), int) or ind.get("index", 0) < 1:
            errors.append(f"{prefix}index must be a positive integer (1, 2, 3...) for AND/OR grouping.")

        return errors


# Singleton instance
ise_validator = ISEValidator()
