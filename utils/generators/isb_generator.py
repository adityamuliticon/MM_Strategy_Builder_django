"""ISB payload generator — converts LLM-structured inbound signal strategy JSON into the Market Maya createCustomTradeStrategy schema."""

import re
import time
from services.exchange_resolver import resolve_leg_exchange
from utils.generators.base_generator import BaseGenerator

LOT_SIZES = {
    "BANKNIFTY": 30, "NIFTY": 25, "FINNIFTY": 40,
    "MIDCPNIFTY": 75, "SENSEX": 20, "BANKEX": 15,
}

STRATEGY_TYPE_ID = "XBZs7OE0aMivKaB0$aA0$Wej3PcwaC0$aC0$"

QTY_DISTRIBUTIONS = {"Fix", "Capital(%)", "Capital Risk(%)", "Allocation Method 1"}


class ISBPayloadGenerator(BaseGenerator):

    def generate_payload(self, strategy_json):
        raw_name = strategy_json.get("strategyName", "ISB_Strategy")
        strategy_name = re.sub(r'_\d{4}$', '', raw_name) + f"_{int(time.time()) % 10000}"

        is_intraday = bool(strategy_json.get("isIntraday", False))
        default_product = "MIS" if is_intraday else "NRML"
        product_type = strategy_json.get("productType", default_product)

        # Working days — list of day codes or dict
        working_days = self._parse_working_days(strategy_json.get("workingDays", ["MON", "TUE", "WED", "THU", "FRI"]))

        sub_legs = [self._build_leg(leg) for leg in strategy_json.get("legs", [])]

        payload = {
            "id": "",
            "strategy_name": strategy_name,
            "short_description": strategy_json.get("shortDescription", ""),
            "long_description": strategy_json.get("longDescription", ""),
            "strategy_type_id": STRATEGY_TYPE_ID,
            "product_type": product_type,
            "required_margin": int(strategy_json.get("capital", 0)),
            "is_intraday": is_intraday,
            "target_by": "Money",
            "intraday_target": int(strategy_json.get("masterTarget", 0)),
            "sl_by": "Money",
            "intraday_sl": int(strategy_json.get("masterSl", 0)),
            "allow_update_parameters": True,
            "max_position": int(strategy_json.get("maxPosition", 0)),
            "max_position_allocation_percent": int(strategy_json.get("maxCapitalAllocation", 100)),
            "run_mon": working_days.get("MON", True),
            "run_tue": working_days.get("TUE", True),
            "run_wed": working_days.get("WED", True),
            "run_thu": working_days.get("THU", True),
            "run_fri": working_days.get("FRI", True),
            "run_sat": working_days.get("SAT", False),
            "run_sun": working_days.get("SUN", False),
            "intraday_exit_time_min": int(strategy_json.get("exitMinutes", 15)),
            "margin_stock_intraday": int(strategy_json.get("marginStockIntraday", 30)),
            "margin_stock_positional": int(strategy_json.get("marginStockPositional", 100)),
            "margin_futopt_positional": int(strategy_json.get("marginFutOpt", 30)),
            "auto_sqroff_on_contract_exp": bool(strategy_json.get("autoSqroffOnExpiry", True)),
            "pause_and_sqroff_trading_on_margin_exeed": bool(strategy_json.get("sqroffOnRejection", False)),
            "sqroffAllLegs": bool(strategy_json.get("sqroffAllLegs", False)),
            "effect_all_sub_strategies": False,
            "isEditCode": False,
            "sub": sub_legs,
        }

        return payload

    def _build_leg(self, leg):
        symbol = str(leg.get("symbol", "BANKNIFTY")).upper()
        if symbol == "NIFTY50":
            symbol = "NIFTY"

        segment_hint = str(leg.get("segment", "FUT"))
        exchange_hint = str(leg.get("exchange", ""))
        exchange, segment = resolve_leg_exchange(symbol, segment_hint, exchange_hint)

        # Option type: "" for FUT and EQ
        option_type = str(leg.get("optionType", "")).upper()
        if segment != "OPT":
            option_type = ""
        elif option_type not in ("CE", "PE"):
            option_type = "CE"

        # ATM: 0 for FUT and EQ
        atm = int(leg.get("atm", 0)) if segment == "OPT" else 0

        # Strike price: 0 = use ATM offset
        strike_price = int(leg.get("strikePrice", 0))

        # Qty distribution
        qty_dist = str(leg.get("qtyDistribution", "Fix"))
        if qty_dist not in QTY_DISTRIBUTIONS:
            qty_dist = "Fix"

        lot_val = int(leg.get("lot", 1))

        if qty_dist == "Fix":
            lot_size = LOT_SIZES.get(symbol, 1)
            qty = lot_val * lot_size
            lot = lot_val
        elif qty_dist in ("Capital(%)", "Capital Risk(%)"):
            # lot field holds the percentage value
            lot = lot_val
            qty = 1
        else:
            # Allocation Method 1 — computed at runtime
            qty = 1
            lot = 1

        # Target / SL
        target = int(leg.get("target", 0))
        sl = int(leg.get("sl", 0))

        # Trail SL — requires sl > 0
        is_trail_sl = bool(leg.get("isTrailSl", False))
        trail_market_move = int(leg.get("trailMarketMove", 0))
        trail_sl_move = int(leg.get("trailSlMove", 0))
        no_of_trail = self._parse_trail_count(leg.get("noOfTrailSl", 0))

        if trail_market_move > 0 or trail_sl_move > 0:
            is_trail_sl = True

        # Trail SL cannot be enabled when SL is 0
        if sl == 0:
            is_trail_sl = False
            trail_market_move = 0
            trail_sl_move = 0
            no_of_trail = 0

        return {
            "id": "",
            "exchange": exchange,
            "segment": segment,
            "main_strategy_parameter_id": "",
            "symbol": symbol,
            "contract": str(leg.get("contract", "NEAR")).upper(),
            "expiry": str(leg.get("expiry", "MONTHLY")).upper(),
            "atm": atm,
            "option_type": option_type,
            "qty_distribution": qty_dist,
            "qty": qty,
            "lot": lot,
            "strike_price": strike_price,
            "target": target,
            "target_by": "Money",
            "sl": sl,
            "sl_by": "Money",
            "trail_sl_market_move": trail_market_move if is_trail_sl else 0,
            "trail_sl_move": trail_sl_move if is_trail_sl else 0,
            "no_of_time_trail_sl": no_of_trail if is_trail_sl else 0,
            "is_trail_sl": is_trail_sl,
        }

    def _parse_working_days(self, days):
        """Convert list of day codes ['MON','TUE',...] or dict to a bool dict."""
        if isinstance(days, dict):
            return {k.upper(): bool(v) for k, v in days.items()}
        if isinstance(days, str):
            days = [d.strip().upper() for d in days.split(",")]
        days_upper = [d.upper() for d in days]
        return {
            "MON": "MON" in days_upper,
            "TUE": "TUE" in days_upper,
            "WED": "WED" in days_upper,
            "THU": "THU" in days_upper,
            "FRI": "FRI" in days_upper,
            "SAT": "SAT" in days_upper,
            "SUN": "SUN" in days_upper,
        }

    def _parse_trail_count(self, value):
        if isinstance(value, str) and value.lower() in ("unlimited", "infinite"):
            return 0
        try:
            return int(value)
        except Exception:
            return 0


isb_generator = ISBPayloadGenerator()
