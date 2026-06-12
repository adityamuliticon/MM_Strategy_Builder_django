"""USB strategy validator — checks required fields and allowed values before payload generation."""

import json
from config import Config


class StrategyValidator:
    def __init__(self):
        with open("docs/swagger.json", "r") as f:
            self.swagger = json.load(f)
            
    def validate_main_parameters(self, params):
        errors = []
        
        # Strategy Name
        name = params.get("strategyName", "")
        if not name:
            errors.append("Strategy Name is required.")
        elif len(name) < 3 or len(name) > 100:
            errors.append("Strategy Name must be between 3 and 100 characters.")
            
        # Exchange
        allowed_exchanges = ["NSE", "NFO", "BFO", "BSE", "MCX", "CDS"]
        if params.get("mainExchange") not in allowed_exchanges:
            errors.append(f"Invalid Exchange. Must be one of: {', '.join(allowed_exchanges)}")
            
        # Segment
        allowed_segments = ["FUT", "OPT", "Stock"]
        if params.get("mainSegment") not in allowed_segments:
            errors.append(f"Invalid Segment. Must be one of: {', '.join(allowed_segments)}")
            
        # Trading Type
        if params.get("isIntraday") not in [True, False]:
            errors.append("Trading Type must be Intraday (True) or Positional (False).")
            
        # Time validation (simple regex or datetime check could be added)
        
        return errors

    def validate_leg_parameters(self, leg):
        errors = []
        
        # Trade Side
        if leg.get("tradeSide") not in ["BUY", "SELL"]:
            errors.append("Trade Side must be BUY or SELL.")
            
        # Lots
        lots = leg.get("lot", 0)
        if not isinstance(lots, int) or lots <= 0:
            errors.append("Lots must be a positive integer.")
            
        # Option Type
        if leg.get("segment") == "OPT" and leg.get("optionType") not in ["CE", "PE"]:
            errors.append("Option Type must be CE or PE for OPT segment.")
            
        # Strike Selection
        allowed_strike_types = [
            "Strike By ATM Value", "Strike By ATM %", "Strike By Premium Range",
            "Strike By Nearest Premium", "Strike By Delta Range", "Strike By Nearest Delta",
            "Strike By Theta Range", "Strike By Nearest Theta"
        ]
        if leg.get("atmType") not in allowed_strike_types:
            errors.append(f"Invalid Strike Selection. Must be one of: {', '.join(allowed_strike_types)}")
            
        return errors


# Singleton instance
validator = StrategyValidator()
