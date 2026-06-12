"""RES payload generator — converts LLM-structured scalping strategy JSON into the Market Maya createScalpingStrategy schema."""

import re
import time
from services.exchange_resolver import resolve_exchange_segment, resolve_leg_exchange

LOT_SIZES = {
    "BANKNIFTY": 30, "NIFTY": 65, "FINNIFTY": 40,
    "MIDCPNIFTY": 75, "SENSEX": 20, "BANKEX": 15,
}

STRATEGY_TYPE_ID = "YioJhK5IqBULe8fPLMnXaAaC0$aC0$"


class RESPayloadGenerator:

    def generate_payload(self, strategy_json):
        raw_name = strategy_json.get("strategy_name", "RES_Strategy")
        strategy_name = re.sub(r'_\d{4}$', '', raw_name) + f"_{int(time.time()) % 10000}"

        symbol = str(strategy_json.get("main_symbol", "BANKNIFTY")).upper()
        if symbol == "NIFTY50":
            symbol = "NIFTY"
        segment_hint = str(strategy_json.get("main_segment", "FUT"))
        exchange_hint = str(strategy_json.get("main_exchange", ""))
        # RES trades the instrument directly — segment IS the traded segment (can be OPT).
        # Use the resolver only for exchange selection, then normalise segment separately.
        exchange, _ = resolve_exchange_segment(symbol, segment_hint, exchange_hint)
        _seg = segment_hint.upper()
        if _seg in ("STOCK", "EQUITY", "CASH"):
            segment = "EQ"
        elif _seg == "INDEX":
            segment = "FUT"   # INDEX is not a valid traded segment
        elif _seg in ("EQ", "FUT", "OPT"):
            segment = _seg
        else:
            segment = "FUT"

        contract = str(strategy_json.get("main_contract", "NEAR")).upper()
        expiry = str(strategy_json.get("main_expiry", "MONTHLY")).upper()
        atm = int(strategy_json.get("atm", 0)) if segment == "OPT" else 0
        option_type = str(strategy_json.get("option_type", "")).upper()
        if segment != "OPT":
            option_type = ""
        elif option_type not in ("CE", "PE"):
            option_type = "CE"
        strike_price = int(strategy_json.get("strike_price", 0))

        mix_name = self._build_mix_name(symbol, segment, contract, expiry, atm, option_type)

        lot = int(strategy_json.get("lot", 1))
        lot_size = LOT_SIZES.get(symbol, 1)
        qty = lot * lot_size
        qty_type = str(strategy_json.get("qty_type", "Qty"))

        is_intraday = bool(strategy_json.get("is_intraday", True))
        default_product = "MIS" if is_intraday else "NRML"
        product_type = str(strategy_json.get("product_type", default_product))
        exit_product = str(strategy_json.get("exit_order_product_type", ""))

        entry_time = str(strategy_json.get("intraday_entry_time", "09:20"))
        exit_time = str(strategy_json.get("intraday_exit_time", "15:00"))

        jobbing_side = str(strategy_json.get("jobbing_side", "BUY")).upper()
        average_by = str(strategy_json.get("average_by", "Point"))
        average_value = float(strategy_json.get("average_value", 100))
        target_by = str(strategy_json.get("target_by", "Point"))
        target = float(strategy_json.get("target", 0))
        intraday_target = float(strategy_json.get("intraday_target", 0))
        # Market Maya reads intraday_target (not target) for intraday RES strategies
        if is_intraday and intraday_target == 0 and target > 0:
            intraday_target = target

        jobbing_start_price = float(strategy_json.get("jobbing_start_price", 0))
        jobbing_end_price = float(strategy_json.get("jobbing_end_price", 0))
        maximum_steps = int(strategy_json.get("maximum_steps", 50))
        maximum_target_steps = int(strategy_json.get("maximum_target_steps", 0))
        reset_cycle_on_positive_mtm = int(strategy_json.get("reset_cycle_on_positive_mtm", 0))
        required_margin = float(strategy_json.get("required_margin", 1))
        scalping_opening_qty = int(strategy_json.get("scalping_opening_qty", 0))

        increase_qty_on_avg = bool(strategy_json.get("increase_qty_on_avg", False))
        increase_qty = float(strategy_json.get("increase_qty", 1))
        increase_qty_type = str(strategy_json.get("increase_qty_type", "Increase"))

        sqroff_on_maximum_steps = bool(strategy_json.get("sqroff_on_maximum_steps", False))
        calculate_qty_on_market_jump = bool(strategy_json.get("calculate_qty_on_market_jump", False))

        reset_cycle_by_master_tpsl = bool(strategy_json.get("reset_cycle_by_master_tpsl", False))
        master_tp_money = float(strategy_json.get("master_tp_money", 0))
        master_sl_money = float(strategy_json.get("master_sl_money", 0))

        is_trail_sl = bool(strategy_json.get("is_trail_sl", False))
        profit_move = float(strategy_json.get("profit_move", 0))
        sl_move = float(strategy_json.get("sl_move", 0))
        no_of_trail_sl = self._parse_trail_count(strategy_json.get("no_of_trail_sl", 0))

        if (profit_move > 0 or sl_move > 0) and reset_cycle_by_master_tpsl:
            is_trail_sl = True

        is_auto_rollover = bool(strategy_json.get("is_auto_rollover", False))
        rollover_before_days = int(strategy_json.get("rollover_before_days", 0))
        rollover_time = str(strategy_json.get("rollover_time", "0:0"))
        if not is_auto_rollover:
            rollover_time = "0:0"

        is_add_hedge_leg = bool(strategy_json.get("is_add_hedge_leg", False))
        hedge_legs = strategy_json.get("hedge_legs", [])
        sub = []
        if is_add_hedge_leg and hedge_legs:
            for hl in hedge_legs:
                sub.append(self._build_hedge_leg(hl))

        short_description = str(strategy_json.get("short_description", ""))
        long_description = str(strategy_json.get("long_description", ""))

        payload = {
            "id": "",
            "strategy_name": strategy_name,
            "short_description": short_description,
            "long_description": long_description,
            "strategy_id": STRATEGY_TYPE_ID,
            "mix_name": mix_name,
            "main_exchange": exchange,
            "main_segment": segment,
            "main_symbol": symbol,
            "main_contract": contract,
            "main_expiry": expiry,
            "product_type": product_type,
            "exit_order_product_type": exit_product,
            "qty_type": qty_type,
            "qty": qty,
            "lot": lot,
            "atm": atm,
            "strike_price": strike_price,
            "option_type": option_type,
            "intraday_entry_time": entry_time,
            "intraday_exit_time": exit_time,
            "is_intraday": is_intraday,
            "jobbing_side": jobbing_side,
            "jobbing_start_price": jobbing_start_price,
            "jobbing_end_price": jobbing_end_price,
            "average_by": average_by,
            "average_value": average_value,
            "target_by": target_by,
            "target": target,
            "intraday_target": intraday_target,
            "maximum_steps": maximum_steps,
            "maximum_target_steps": maximum_target_steps,
            "sqroff_on_maximum_steps": sqroff_on_maximum_steps,
            "calculate_qty_on_market_jump": calculate_qty_on_market_jump,
            "allow_update_parameters": True,
            "order_type": "Market Order",
            "no_of_limit_order_retry": 0,
            "retry_at_every_seconds": 0,
            "market_order_after_retry": False,
            "reset_cycle_by_master_tpsl": reset_cycle_by_master_tpsl,
            "master_tp_money": master_tp_money,
            "master_sl_money": master_sl_money,
            "is_trail_sl": is_trail_sl,
            "profit_move": profit_move,
            "sl_move": sl_move,
            "no_of_trail_sl": no_of_trail_sl if is_trail_sl else 0,
            "rollover_before_days": rollover_before_days,
            "is_auto_rollover": is_auto_rollover,
            "rollover_time": rollover_time,
            "is_add_hedge_leg": is_add_hedge_leg,
            "reset_cycle_on_positive_mtm": reset_cycle_on_positive_mtm,
            "required_margin": required_margin,
            "scalping_opening_qty": scalping_opening_qty,
            "increase_qty_on_avg": increase_qty_on_avg,
            "increase_qty": increase_qty,
            "increase_qty_type": increase_qty_type,
            "rebacktest": False,
            "sub": sub,
            "effect_all_sub_strategies": False,
        }

        return payload

    def _build_mix_name(self, symbol, segment, contract, expiry, atm, option_type):
        if segment == "OPT":
            return f"{symbol} OPT {contract} {expiry} {atm} {option_type}"
        elif segment == "EQ":
            return f"{symbol} EQ"
        else:
            return f"{symbol} {segment} {contract} {expiry}"

    def _build_hedge_leg(self, hl):
        sym_hl = str(hl.get("symbol", "BANKNIFTY")).upper()
        if sym_hl == "NIFTY50":
            sym_hl = "NIFTY"
        seg_hint = str(hl.get("segment", "FUT"))
        exch_hint = str(hl.get("exchange", ""))
        seg = resolve_leg_exchange(sym_hl, seg_hint, exch_hint)[1]

        hl_exch, seg = resolve_leg_exchange(sym_hl, seg_hint, exch_hint)

        option_type = str(hl.get("option_type", "")).upper()
        if seg != "OPT":
            option_type = ""
        elif option_type not in ("CE", "PE"):
            option_type = "CE"

        atm = int(hl.get("atm", 0)) if seg == "OPT" else 0
        trade_side = str(hl.get("trade_side", "BUY")).upper()
        call_type = str(hl.get("call_type", "BUY")).upper()

        hedge_lot = int(hl.get("lot", 1))
        # OPT legs: send actual qty so MM has it; FUT/EQ legs: MM expects 0
        hedge_qty = LOT_SIZES.get(sym_hl, 1) * hedge_lot if seg == "OPT" else 0
        return {
            "call_type": call_type,
            "exchange": hl_exch,
            "segment": seg,
            "symbol": sym_hl,
            "contract": str(hl.get("contract", "NEAR")).upper(),
            "expiry": str(hl.get("expiry", "MONTHLY")).upper(),
            "atm": atm,
            "option_type": option_type,
            "qty": hedge_qty,
            "lot": hedge_lot,
            "trade_side": trade_side,
            "target": 0,
            "target_by": "Money",
            "sl": 0,
            "sl_by": "Money",
            "trail_sl_market_move": 0,
            "trail_sl_move": 0,
            "no_of_time_trail_sl": 0,
            "is_trail_sl": False,
            "is_reverse_signal": False,
        }

    def _parse_trail_count(self, value):
        if isinstance(value, str) and value.lower() in ("unlimited", "infinite"):
            return 0
        try:
            return int(value)
        except Exception:
            return 0


res_generator = RESPayloadGenerator()
