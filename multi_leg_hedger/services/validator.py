class MLHValidator:
    def validate(self, s):
        errors = []
        if not s.get("strategy_name", "").strip():
            errors.append("strategy_name is required")
        mode = s.get("trading_mode", "Normal")
        if mode not in ("Normal", "Range Breakout", "BTST/STBT"):
            errors.append(f"Invalid trading_mode: {mode}")
        if s.get("is_range_break_out") and s.get("is_btst_stbt"):
            errors.append("is_range_break_out and is_btst_stbt cannot both be true")
        legs = s.get("legs", [])
        if not legs:
            errors.append("At least one leg is required")
        for i, leg in enumerate(legs, 1):
            seg = leg.get("segment", "FUT")
            if seg == "OPT" and not leg.get("option_type"):
                errors.append(f"Leg {i}: option_type (CE/PE) required for OPT segment")
            if leg.get("atm_type") == "Dynamic":
                if not float(leg.get("premium_start_range", 0)) or not float(leg.get("premium_end_range", 0)):
                    errors.append(f"Leg {i}: premium_start_range and premium_end_range required for Dynamic ATM type")
        return errors


mlh_validator = MLHValidator()
