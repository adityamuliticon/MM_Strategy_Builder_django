"""MLH payload generator — converts LLM-structured multi-leg hedger JSON into the Market Maya CreateMultiLegCallPutStrategy schema."""

import random
import string
from services.exchange_resolver import resolve_exchange_segment, resolve_leg_exchange

STRATEGY_TYPE_ID = "RF8IGNzSfYMaB0$ENiAa4FpGwaC0$aC0$"

LOT_SIZES = {
    "BANKNIFTY": 30, "NIFTY": 65, "FINNIFTY": 40, "MIDCPNIFTY": 75,
    "SENSEX": 20, "BANKEX": 15,
}


class MLHPayloadGenerator:

    def _qty(self, symbol, lot):
        return LOT_SIZES.get(symbol.upper(), 1) * lot

    def _underlying_string(self, exchange, segment, symbol):
        return f"{symbol} {segment} {exchange}"

    def _build_leg(self, leg, parent_exchange="NFO"):
        symbol_raw = leg.get("symbol", "BANKNIFTY")
        symbol = str(symbol_raw).upper()
        if symbol == "NIFTY50":
            symbol = "NIFTY"
        lot = int(leg.get("lot", 1))
        qty = self._qty(symbol, lot)
        segment_hint = leg.get("segment", "FUT")
        # Rule 6: if leg has no explicit exchange, inherit the parent's family
        exchange_hint = leg.get("exchange", "") or parent_exchange
        exchange, segment = resolve_leg_exchange(symbol, segment_hint, exchange_hint)
        option_type = leg.get("option_type", "")
        if segment != "OPT":
            option_type = ""
        atm_type = leg.get("atm_type", "Fix")
        wait_for = leg.get("wait_for", "None")
        is_wait = wait_for not in ("None", "", None) and float(leg.get("wait_value", 0)) > 0
        reentry_on = leg.get("reentry_on", "None")
        reexecute_on = leg.get("reexecute_on", "None")
        sl = float(leg.get("sl", 0))
        # Trail SL on a leg requires a base SL; without it the fields are inaccessible in the UI
        is_trail_sl = bool(leg.get("is_trail_sl", False)) and sl > 0
        return {
            "id": "",
            "exchange": exchange,
            "segment": segment,
            "symbol": symbol,
            "contract": leg.get("contract", "NEAR"),
            "expiry": leg.get("expiry", "MONTHLY"),
            "atm": int(leg.get("atm", 0)),
            "strikePrice": float(leg.get("strike_price", 0)),
            "optionType": option_type,
            "atmType": atm_type,
            "qtyType": leg.get("qty_type", "Qty"),
            "tradeSide": leg.get("trade_side", "BUY"),
            "range_breakout_direction": leg.get("range_breakout_direction", "High"),
            "qty_distribution": "Fix",
            "qty": qty,
            "targetBy": leg.get("target_by", "Money"),
            "target": float(leg.get("target", 0)),
            "slBy": leg.get("sl_by", "Money"),
            "sl": sl,
            "lot": lot,
            "trail_sl_market_move": float(leg.get("trail_sl_market_move", 0)) if is_trail_sl else 0,
            "trail_sl_move": float(leg.get("trail_sl_move", 0)) if is_trail_sl else 0,
            "no_of_time_trail_sl": int(leg.get("no_of_time_trail_sl", 0)) if is_trail_sl else 0,
            "is_trail_sl": is_trail_sl,
            "trail_sl_by": leg.get("trail_sl_by", "Point") if is_trail_sl else "Point",
            "premiumStartRange": float(leg.get("premium_start_range", 0)),
            "premiumEndRange": float(leg.get("premium_end_range", 0)),
            "trail_sl_cost": bool(leg.get("trail_sl_cost", False)),
            "reentry_on": reentry_on,
            "no_of_reentry": int(leg.get("no_of_reentry", 0)),
            "reexecute_delay": int(leg.get("reexecute_delay", 0)),
            "product": None,
            "workingDay": "ALL",
            "is_wait_and_trade": is_wait,
            "wait_for": wait_for if is_wait else "None",
            "wait_value": float(leg.get("wait_value", 0)) if is_wait else 0,
            "reexecute_on": reexecute_on,
            "no_of_reexecute": int(leg.get("no_of_reexecute", 0)),
        }

    def generate_payload(self, s):
        mode = s.get("trading_mode", "Normal")
        is_range = (mode == "Range Breakout")
        is_btst = (mode == "BTST/STBT")
        is_intraday = (not is_btst) and bool(s.get("is_intraday", True))
        product = s.get("product_type", "MIS" if is_intraday else "NRML")
        ul_symbol_raw = s.get("symbol", "BANKNIFTY")
        ul_symbol = str(ul_symbol_raw).upper()
        if ul_symbol == "NIFTY50":
            ul_symbol = "NIFTY"
        ul_segment_hint = s.get("segment", "FUT")
        ul_exchange_hint = s.get("exchange", "")
        ul_exchange, ul_segment = resolve_exchange_segment(ul_symbol, ul_segment_hint, ul_exchange_hint)
        underlying_str = self._underlying_string(ul_exchange, ul_segment, ul_symbol)
        working_days = s.get("working_days", {})
        legs_data = s.get("legs", [])
        sub = [self._build_leg(leg, ul_exchange) for leg in legs_data]
        if not sub:
            sub.append(self._build_leg({"exchange": ul_exchange, "segment": "FUT", "symbol": ul_symbol}, ul_exchange))
        sqroff_all_legs = bool(s.get("sqroff_all_legs", False))
        return {
            "id": "",
            "strategyName": s.get("strategy_name", f"MLH_{''.join(random.choices(string.digits, k=4))}"),
            "shortDescription": s.get("short_description", ""),
            "longDescription": s.get("long_description", ""),
            "exchange": ul_exchange,
            "segment": ul_segment,
            "symbol": ul_symbol,
            "entryTime": s.get("entry_time", "09:16"),
            "exitTime": s.get("exit_time", "15:29"),
            "strategyId": STRATEGY_TYPE_ID,
            "underlying": underlying_str,
            "productType": product,
            "qtyMultiply": int(s.get("qty_multiply", 1)),
            "targetBy": s.get("master_target_by", "Money"),
            "target": float(s.get("master_target", 0)),
            "slBy": s.get("master_sl_by", "Money"),
            "sl": float(s.get("master_sl", 0)),
            "requiredMargin": float(s.get("required_margin", 1)),
            "mon": working_days.get("mon", True),
            "tue": working_days.get("tue", True),
            "wed": working_days.get("wed", True),
            "thu": working_days.get("thu", True),
            "fri": working_days.get("fri", True),
            "sat": working_days.get("sat", False),
            "sun": working_days.get("sun", False),
            "followSimulator": True,
            "squareoffRejection": bool(s.get("sqroff_on_rejection", True)),
            "squareoffLegs": False,
            "paperTrading": True,
            "allowLateTrading": bool(s.get("allow_late_trading", True)),
            "cosider_closed_pnl": bool(s.get("cosider_closed_pnl", False)),
            "allowUpdateParameters": True,
            "isTrailSl": bool(s.get("is_trail_sl", False)),
            "isIntraday": is_intraday,
            "enableVixFilter": bool(s.get("enable_vix_filter", False)),
            "vixStartValue": float(s.get("vix_start_value", 0)),
            "vixEndValue": float(s.get("vix_end_value", 0)),
            "trail_sl_by": s.get("trail_sl_by", "Money"),
            "startTrailAfterProfit": float(s.get("start_trail_after_profit", 0)),
            "profitMove": float(s.get("profit_move", 0)),
            "slMove": float(s.get("sl_move", 0)),
            "noOfTrailSL": int(s.get("no_of_trail_sl", 0)),
            "noOfIntradayCycle": int(s.get("no_of_cycle", 1)),
            "pauseAndSqrOffOnMarginExceed": True,
            "sqroffAllLegs": sqroff_all_legs,
            "sqroffByFixTime": bool(s.get("sqroff_by_fix_time", False)),
            "sqroffWeekDay": s.get("sqroff_week_day", ""),
            "sqroffTime": s.get("sqroff_time", ""),
            "replaceMasterSlWithStartTrailing": False,
            "isResetCycle": bool(s.get("is_reset_cycle", False)),
            "resetCycleIndexPercentage": float(s.get("reset_cycle_index_percentage", 0)),
            "noOfCyclePerDay": int(s.get("no_of_cycle_per_day", 0)),
            "trailType": s.get("trail_type", "Dynamic"),
            "is_btst_stbt": is_btst,
            "is_live_mtm_profit_move": bool(s.get("is_live_mtm_profit_move", False)),
            "intraday_cycle_delay": int(s.get("cycle_delay", 0)),
            "is_range_break_out": is_range,
            "range_time": s.get("range_end_time", "09:17"),
            "index_move_by": s.get("index_move_by", "Percentage(%)"),
            "sqroff_before_expiry_days": int(s.get("sqroff_before_expiry_days", 0)),
            "chk_con_delay_after_market_start": int(s.get("chk_con_delay_after_market_start", 0)),
            "fixTrail": s.get("fix_trail", ""),
            "rebacktest": False,
            "sub": sub,
            "requiredCapital": 1,
            "isEditCode": False,
            "effect_all_sub_strategies": False,
        }


mlh_generator = MLHPayloadGenerator()
