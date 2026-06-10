import json
import math
import re
from config import Config
from services.exchange_resolver import resolve_exchange_segment

class PayloadGenerator:
    def __init__(self):
        self.strategy_type_id = "7D0enBHWMRaf4ebeKaB0$OOMQaC0$aC0$"

    def generate_v3_payload(self, main_params, legs):
        symbol_raw = main_params.get("symbol", main_params.get("mainSymbol", main_params.get("underlying", "NIFTY")))
        symbol = symbol_raw.upper().split()[0] if symbol_raw else "NIFTY"
        if symbol == "NIFTY50":
            symbol = "NIFTY"

        segment_hint = main_params.get("segment", main_params.get("mainSegment", "FUT"))
        exchange_hint = main_params.get("exchange", main_params.get("mainExchange", ""))

        exchange, segment = resolve_exchange_segment(symbol, segment_hint, exchange_hint)

        underlying = f"{symbol} {segment} {exchange}"

        # ── Legs ─────────────────────────────────────────────────────────────
        is_range_breakout = main_params.get("isRangeBreakOut", main_params.get("is_range_breakout", False))
        generated_legs = []
        for leg_input in (legs if isinstance(legs, list) else []):
            leg_payload = self._generate_leg_payload(leg_input, exchange, symbol)
            # If range breakout is ON at strategy level and the leg is not idle
            # and doesn't explicitly disable it, force isExecuteOnRangeBreakout to True.
            # Idle legs are triggered by another leg's action — they must NOT auto-execute on breakout.
            is_idle = leg_input.get("isIdle", leg_input.get("is_idle", False))
            if is_range_breakout and not is_idle and not leg_input.get("isExecuteOnRangeBreakout", leg_input.get("is_execute_on_range_breakout", None)) is False:
                leg_payload["isExecuteOnRangeBreakout"] = True
            generated_legs.append(leg_payload)

        # ── Master Target / SL ────────────────────────────────────────────────
        target_val = int(main_params.get("intradayTarget", main_params.get("master_target", main_params.get("target", 0))))
        sl_val = int(main_params.get("intradaySl", main_params.get("master_stop_loss", main_params.get("sl", 0))))

        # ── Master SL Trailing — now read from dedicated object ──────────────
        # Schema: "master_sl_trailing": {"profit_move": N, "sl_move": N, "no_of_trail_sl": N}
        msl_trail = main_params.get("master_sl_trailing", {})
        if isinstance(msl_trail, dict) and msl_trail:
            profit_move = int(msl_trail.get("profit_move", msl_trail.get("profitMove", 0)))
            sl_move = int(msl_trail.get("sl_move", msl_trail.get("slMove", 0)))
            no_of_trail_sl = self._parse_trail_count(msl_trail.get("no_of_trail_sl", msl_trail.get("noOfTrailSl", 0)))
        else:
            # Legacy: single trailing_sl number treated as both moves
            trail_input = main_params.get("trailing_sl", main_params.get("trail_sl", 0))
            if isinstance(trail_input, dict):
                profit_move = int(trail_input.get("profit_move", trail_input.get("activation", trail_input.get("increment", 0))))
                sl_move = int(trail_input.get("sl_move", trail_input.get("slMove", profit_move)))
            else:
                try:
                    profit_move = sl_move = int(trail_input)
                except:
                    profit_move = sl_move = 0
            no_of_trail_sl = self._parse_trail_count(main_params.get("no_of_trail_sl", 0))

        is_master_tsl_enabled = (profit_move > 0 or sl_move > 0)

        # ── Master Profit Locking ─────────────────────────────────────────────
        mpl = main_params.get("master_profit_locking", {})
        mpl_if_profit = int(mpl.get("if_profit_reaches", mpl.get("ifProfitReaches", 0)))
        mpl_lock_min  = int(mpl.get("lock_minimum_profit", mpl.get("lockMinimumProfit", 0)))
        mpl_increase  = int(mpl.get("increse_in_profit_by", mpl.get("increseInProfitBy", 0)))
        mpl_trail_by  = int(mpl.get("trail_profit_by", mpl.get("trailProfitBy", 0)))
        # Read noOfTimeTrailTp from both camelCase (LLM schema) and snake_case
        mpl_no_trail_raw = mpl.get("noOfTimeTrailTp", mpl.get("no_of_time_trail", 0))
        mpl_no_trail = self._parse_trail_count(mpl_no_trail_raw)

        # ── Trading Days ──────────────────────────────────────────────────────
        trading_days = main_params.get("trading_days", main_params.get("days", main_params.get("runDays", [])))
        if isinstance(trading_days, str):
            trading_days = [d.strip() for d in trading_days.split(",")]

        days_map = {
            "runMon": any(d.lower().startswith("mon") for d in trading_days) if trading_days else True,
            "runTue": any(d.lower().startswith("tue") for d in trading_days) if trading_days else True,
            "runWed": any(d.lower().startswith("wed") for d in trading_days) if trading_days else True,
            "runThu": any(d.lower().startswith("thu") for d in trading_days) if trading_days else True,
            "runFri": any(d.lower().startswith("fri") for d in trading_days) if trading_days else True,
            "runSat": any(d.lower().startswith("sat") for d in trading_days) if trading_days else False,
        }
        # Only treat as explicitly set when the user picked a non-default subset.
        # Mon-Fri (all 5 weekdays, no Saturday) is the system default —
        # the LLM often outputs it even when the user said nothing about days.
        _lower_days = [d.lower() for d in trading_days]
        _all_weekdays = all(p in " ".join(_lower_days) for p in ("mon", "tue", "wed", "thu", "fri"))
        _has_sat = any(d.startswith("sat") for d in _lower_days)
        _has_sun = any(d.startswith("sun") for d in _lower_days)
        _is_full_default = _all_weekdays and not _has_sat and not _has_sun and len(trading_days) == 5
        is_explicit_days = len(trading_days) > 0 and not _is_full_default

        # ── isIntraday — support trading_type string fallback ─────────────────
        is_intraday = main_params.get("isIntraday", main_params.get("is_intraday", None))
        if is_intraday is None:
            trading_type_str = str(main_params.get("trading_type", main_params.get("tradingType", "intraday"))).lower()
            is_intraday = "positional" not in trading_type_str
        else:
            is_intraday = bool(is_intraday)

        # ── sqroffTime — read from JSON (for pre-expiry sqroff override) ─────
        sqroff_time = main_params.get("sqroffTime", main_params.get("sqroff_time", "15:15:00"))

        # ── enableTpSlOnPauseStrategy — read from JSON ────────────────────────
        enable_tp_sl_pause = main_params.get(
            "enableTpSlOnPauseStrategy",
            main_params.get("enable_tp_sl_on_pause", main_params.get("tp_sl_on_pause", False))
        )

        payload = {
            "id": "",
            "strategyName": re.sub(r'_\d{4}$', '', main_params.get("strategyName", main_params.get("strategy_name", "Strategy"))) + f"_{int(__import__('time').time()) % 10000}",
            "underlying": underlying,
            "mainExchange": exchange,
            "mainSegment": segment,
            "mainSymbol": symbol,
            "isIntraday": is_intraday,
            "productType": main_params.get("productType", "NRML" if not is_intraday else "MIS"),
            "tradingStartTime": main_params.get("tradingStartTime", main_params.get("entry_time", "09:15:00")),
            "tradingEndTime": main_params.get("tradingEndTime", main_params.get("exit_time", "15:15:00")),
            "isRangeBreakOut": main_params.get("isRangeBreakOut", main_params.get("is_range_breakout", False)),
            "rangeEndTime": main_params.get("rangeEndTime", main_params.get("range_end_time", "09:20:00")),
            "isBtstStbt": main_params.get("isBtstStbt", main_params.get("is_btst_stbt", False)),
            "btstGapDays": int(main_params.get("btstGapDays", main_params.get("btst_gap_days", 1))),
            "isCombinedPremEntry": (
                True if int(main_params.get("total_combined_premium", main_params.get("total_combined_prem", 0))) > 0
                else main_params.get("is_combined_premium_entry", main_params.get("is_combined_prem_entry", False))
            ),
            "totalCombinedPremium": int(main_params.get("total_combined_premium", main_params.get("total_combined_prem", 0))),

            # Master Target
            "isEnableMasterTarget": True if target_val > 0 else False,
            "targetBy": main_params.get("target_by", main_params.get("targetBy", "Combined Profit")),
            "intradayTarget": target_val,
            "isEnableActionOnTarget": main_params.get("isEnableActionOnTarget", main_params.get("enable_action_on_target", int(main_params.get("reexecute_on_target_count", -1)) >= 0)),
            "actionOnTarget": main_params.get("actionOnTarget", main_params.get("action_on_master_target", "Reexecute")),

            # Master Profit Locking
            "isEnableProfitLockingTrailing": True if mpl_if_profit > 0 else False,
            "ifProfitReaches": mpl_if_profit,
            "lockMinimumProfit": mpl_lock_min,
            "increseInProfitBy": mpl_increase,
            "trailProfitBy": mpl_trail_by,
            "noOfTimeTrailTp": mpl_no_trail if mpl_if_profit > 0 else 0,
            "noOfIntradayCycle": int(main_params.get("reexecute_on_target_count", 0)),
            "intradayCycleDelay": int(main_params.get("reexecute_on_target_delay", 0)),

            # Master SL
            "isEnableMasterSl": True if sl_val > 0 else False,
            "slBy": main_params.get("sl_by", main_params.get("slBy", "Combined Loss")),
            "intradaySl": sl_val,
            "isEnableActionOnMasterSl": main_params.get("isEnableActionOnMasterSl", main_params.get("enable_action_on_master_sl", int(main_params.get("reexecute_on_sl_count", -1)) >= 0)),
            "actionOnSl": main_params.get("actionOnSl", main_params.get("action_on_master_sl", "Reexecute")),

            # Master SL Trailing
            "isEnableStoplossTrailing": is_master_tsl_enabled,
            "profitMove": profit_move,
            "slMove": sl_move,
            "noOfTrailSl": no_of_trail_sl if is_master_tsl_enabled else 0,

            "noOfReexecuteOnSl": int(main_params.get("reexecute_on_sl_count", 0)),
            "reexecuteDelayOnSl": int(main_params.get("reexecute_on_sl_delay", 0)),
            "isEnableSqroffBeforeExpiryDays": main_params.get("isEnableSqroffBeforeExpiryDays", main_params.get("sqroff_before_expiry", False)),
            "sqroffBeforeExpiryDays": int(main_params.get("sqroffBeforeExpiryDays", main_params.get("sqroff_before_expiry_days", 0))),
            "sqroffTime": sqroff_time,

            # Working Days
            "isEnableWorkingDays": is_explicit_days,
            "runMon": days_map["runMon"],
            "runTue": days_map["runTue"],
            "runWed": days_map["runWed"],
            "runThu": days_map["runThu"],
            "runFri": days_map["runFri"],
            "runSat": days_map["runSat"],
            "runSun": False,

            # VIX
            "enableVixFilter": main_params.get("enableVixFilter", main_params.get("vix_filter", False)),
            "vixStartValue": int(main_params.get("vixStartValue", main_params.get("vix_start_value", 1))),
            "vixEndValue": int(main_params.get("vixEndValue", main_params.get("vix_end_value", 5))),

            # Safety flags
            "enableTpSlOnPauseStrategy": enable_tp_sl_pause,
            "sqroffAllLegs": main_params.get("sqroffAllLegs", main_params.get("sqroff_all_legs", main_params.get("squareOffAllLegs", False))),
            "pauseAndSqroffTradingOnMarginExeed": main_params.get("pauseAndSqroffTradingOnMarginExeed", main_params.get("sqroff_on_rejection", main_params.get("sqroffPositionOnRejection", False))),
            "requiredMargin": self._parse_margin(main_params.get("requiredMargin", main_params.get("required_margin", 1))),

            "shortDescription": main_params.get("shortDescription", ""),
            "detailedDescription": main_params.get("detailedDescription", ""),
            "strategyTypeId": self.strategy_type_id,
            "rebacktest": False,
            "effectAllSubStrategies": False,
            "legs": generated_legs
        }

        return payload

    def _generate_leg_payload(self, leg, default_exchange, symbol):
        strike_type_map = {
            "ATM": "Strike By ATM Value",
            "ATM%": "Strike By ATM %",
            "PREMIUM_RANGE": "Strike By Premium Range",
            "NEAREST_PREMIUM": "Strike By Nearest Premium",
            "DELTA_RANGE": "Strike By Delta Range",
            "NEAREST_DELTA": "Strike By Nearest Delta",
            "THETA_RANGE": "Strike By Theta Range",
            "NEAREST_THETA": "Strike By Nearest Theta",
            "STRIKE BY ATM VALUE": "Strike By ATM Value",
            "STRIKE BY ATM %": "Strike By ATM %",
        }

        raw_atm = str(leg.get("atmType", leg.get("strike_type", "ATM"))).upper()
        if "STRIKE BY" in raw_atm:
            atm_type = raw_atm.title().replace("Atm", "ATM")
        else:
            atm_type = strike_type_map.get(raw_atm, "Strike By ATM Value")

        # Ranges
        s_range = int(float(leg.get("premium_start_range", leg.get("premiumStartRange", 10))))
        e_range = int(float(leg.get("premium_end_range", leg.get("premiumEndRange", 20))))

        # Strike/ATM value — keep as float for Delta, Theta, AND ATM%
        atm_val = leg.get("strike", leg.get("atm", 0))
        if isinstance(atm_val, str):
            nums = re.findall(r"[-+]?\d*\.?\d+", atm_val)
            atm_val = float(nums[0]) if nums else 0.0
        else:
            atm_val = float(atm_val)

        # Cast to int only for pure ATM Value types (not ATM%, Delta, Theta)
        needs_float = any(k in atm_type for k in ("Delta", "Theta", "ATM %"))
        if not needs_float:
            atm_val = int(atm_val)

        # For Nearest Premium: the single premium amount belongs in premiumStartRange,
        # not atm. LLM typically puts it in "strike" → atm_val. Reroute it.
        if atm_type == "Strike By Nearest Premium" and atm_val != 0:
            s_range = int(atm_val)
            atm_val = 0

        # For Delta/Theta types: Market Maya reads the value from premiumStartRange,
        # not atm. LLM puts the user's delta/theta number in atm_val — reroute it.
        if atm_type in ("Strike By Nearest Delta", "Strike By Nearest Theta") and atm_val != 0:
            s_range = int(atm_val)
            atm_val = 0.0
        if atm_type in ("Strike By Delta Range", "Strike By Theta Range") and atm_val != 0:
            s_range = int(atm_val)  # start of range; end comes from premiumEndRange
            atm_val = 0.0

        # Target / SL — API always requires integer
        raw_t_by = str(leg.get("targetBy", leg.get("target_by", "Target by Money")))
        raw_s_by = str(leg.get("slBy", leg.get("sl_by", "SL by Money")))
        t_raw = float(leg.get("target", 0))
        s_raw = float(leg.get("sl", 0))
        t_val = max(1, math.ceil(t_raw)) if t_raw > 0 else 0
        s_val = max(1, math.ceil(s_raw)) if s_raw > 0 else 0

        # Profit locking
        pl = leg.get("profit_locking", leg.get("profitLocking", {}))

        # SL trailing
        tsl = leg.get("trail_sl", leg.get("trailSl", {}))
        tsl_market_move = int(tsl.get("trail_sl_market_move", leg.get("trail_sl_market_move", leg.get("trailSlMarketMove", 0))))
        tsl_move        = int(tsl.get("trail_sl_move", leg.get("trail_sl_move", leg.get("trailSlMove", 0))))
        has_tsl = tsl_market_move > 0 or tsl_move > 0

        # SL trail count
        raw_trail_sl = self._parse_trail_count(
            tsl.get("no_of_time_trail", leg.get("noOfTimeTrailSl", leg.get("no_of_time_trail", 0)))
        )
        if not has_tsl:
            raw_trail_sl = 0

        # Profit locking trail count
        raw_no_trail_tp = pl.get("no_of_time_trail", pl.get("noOfTimeTrailTp",
                          leg.get("noOfTimeTrailTp", leg.get("no_of_time_trail", 0))))
        no_trail_tp = self._parse_trail_count(raw_no_trail_tp)

        # ── isEnableActionOnTarget — auto-enable when leg_no > 0 or Reenter ──
        action_on_target    = leg.get("actionOnTarget", leg.get("action_on_target", "Execute Leg"))
        target_action_leg   = int(leg.get("actionOnTargetLegNo", leg.get("target_action_leg_no", leg.get("action_on_target_leg_no", 0))))
        target_action_delay = int(leg.get("actionOnTargetDelay", leg.get("target_action_delay", leg.get("action_on_target_delay", 0))))
        is_enable_aot = leg.get("isEnableActionOnTarget", leg.get("is_enable_action_on_target", False))
        # Only auto-enable when there IS a real leg target — Market Maya rejects
        # isEnableActionOnTarget=true when isEnableLegTarget=false (no target set).
        has_real_target = t_val > 0
        if (target_action_leg > 0 or action_on_target == "Reenter Leg") and has_real_target:
            is_enable_aot = True
        # Market Maya requires delay >= 1 for Reenter/Execute Leg actions
        if action_on_target in ("Reenter Leg", "Execute Leg") and target_action_delay == 0 and is_enable_aot:
            target_action_delay = 5

        # ── isEnableActionOnSl — auto-enable when leg_no > 0 or Reenter ──────
        action_on_sl    = leg.get("actionOnSl", leg.get("action_on_sl", "Execute Leg"))
        sl_action_leg   = int(leg.get("actionOnSlLegNo", leg.get("sl_action_leg_no", leg.get("action_on_sl_leg_no", 0))))
        sl_action_delay = int(leg.get("actionOnSlDelay", leg.get("sl_action_delay", leg.get("action_on_sl_delay", 0))))
        is_enable_aosl = leg.get("isEnableActionOnSl", leg.get("is_enable_action_on_sl", False))
        if sl_action_leg > 0 or action_on_sl == "Reenter Leg":
            is_enable_aosl = True
        # Market Maya requires delay >= 1 for Reenter/Execute Leg actions
        if action_on_sl in ("Reenter Leg", "Execute Leg") and sl_action_delay == 0 and is_enable_aosl:
            sl_action_delay = 5

        # ── isWaitAndTrade — auto-enable when waitValue > 0 ──────────────────
        wait_and_trade = leg.get("isWaitAndTrade", leg.get("wait_and_trade", leg.get("is_wait_and_trade", False)))
        wait_for  = self._map_wait_direction(leg.get("waitFor", leg.get("wait_for", "Up %")))
        wait_value_raw = float(leg.get("waitValue", leg.get("wait_value", 0)))
        wait_value = math.ceil(wait_value_raw)   # round up so 0.5% → 1
        if wait_value > 0 and not wait_and_trade:
            wait_and_trade = True
        if wait_and_trade and wait_value == 0:
            wait_value = 1   # API rejects 0 when isWaitAndTrade=True

        leg_seg_raw = str(leg.get("segment", "OPT")).upper()
        if leg_seg_raw in ("STOCK", "EQUITY", "CASH"):
            leg_segment = "EQ"
        elif leg_seg_raw == "INDEX":
            leg_segment = "FUT"   # INDEX is not valid for legs
        elif leg_seg_raw in ("EQ", "FUT", "OPT"):
            leg_segment = leg_seg_raw
        else:
            leg_segment = "OPT"

        return {
            "id": "",
            "isIdle": leg.get("isIdle", leg.get("is_idle", False)),
            "tradeSide": str(leg.get("tradeSide", leg.get("action", "BUY"))).upper(),
            "lot": int(leg.get("lot", leg.get("lots", 1))),
            "segment": leg_segment,
            "expiry": self._resolve_expiry(leg.get("expiry", leg.get("expiry_bucket")), symbol),
            "optionType": (lambda v: v if v not in ("", "NONE", "NULL", "N/A", "FUT") else "CE")(str(leg.get("optionType", leg.get("option", "CE"))).upper()),
            "atmType": atm_type,
            "premiumStartRange": s_range,
            "premiumEndRange": e_range,
            "strikeDirection": self._map_strike_direction(leg.get("strikeDirection", leg.get("direction", leg.get("strike_direction", "BOTH")))),
            "atm": atm_val,
            "strikeCondition": self._map_condition(leg.get("strikeCondition", leg.get("condition", leg.get("strike_condition", "Any")))),
            "isEnableLegTarget": True if (t_val > 0 or "Range" in raw_t_by) else False,
            "targetBy": self._map_target_by(leg.get("targetBy", leg.get("target_by", "Target by Money")), "Target"),
            "target": t_val,
            "isEnableActionOnTarget": is_enable_aot,
            "actionOnTarget": action_on_target,
            "actionOnTargetLegNo": target_action_delay,  # MM API: legNo field stores delay
            "actionOnTargetDelay": target_action_leg,    # MM API: delay field stores leg no
            "isProfitLockingAndTrailing": True if int(pl.get("if_profit_reaches", pl.get("ifProfitReaches", leg.get("if_profit_reaches", 0)))) > 0 else False,
            "ifProfitReaches": int(pl.get("if_profit_reaches", pl.get("ifProfitReaches", leg.get("if_profit_reaches", 0)))),
            "lockMinimumProfit": int(pl.get("lock_minimum_profit", pl.get("lockMinimumProfit", leg.get("lock_minimum_profit", 0)))),
            "increseInProfitBy": int(pl.get("increse_in_profit_by", pl.get("increseInProfitBy", leg.get("increse_in_profit_by", 0)))),
            "trailProfitBy": int(pl.get("trail_profit_by", pl.get("trailProfitBy", leg.get("trail_profit_by", 0)))),
            "noOfTimeTrailTp": no_trail_tp if int(pl.get("if_profit_reaches", pl.get("ifProfitReaches", leg.get("if_profit_reaches", 0)))) > 0 else 0,
            "isEnableLegStoploss": True if (s_val > 0 or "Range" in raw_s_by or leg.get("isEnableLegStoploss", leg.get("is_enable_leg_stoploss", False))) else False,
            "slBy": self._map_target_by(leg.get("slBy", leg.get("sl_by", "SL by Money")), "SL"),
            "sl": s_val,
            "isEnableActionOnSl": is_enable_aosl,
            "actionOnSl": action_on_sl,
            "actionOnSlLegNo": sl_action_delay,  # MM API: legNo field stores delay
            "actionOnSlDelay": sl_action_leg,    # MM API: delay field stores leg no
            "isEnableStoplossTrailing": has_tsl,
            "trailSlMarketMove": tsl_market_move if has_tsl else 0,
            "trailSlMove": tsl_move if has_tsl else 0,
            "noOfTimeTrailSl": raw_trail_sl,
            "isWaitAndTrade": wait_and_trade,
            "waitFor": wait_for,
            "waitValue": wait_value,
            "isExecuteOnRangeBreakout": leg.get("isExecuteOnRangeBreakout", leg.get("is_execute_on_range_breakout", False)),
            "executeOnRangeBreakout": leg.get("executeOnRangeBreakout", leg.get("execute_on_range_breakout", "Range High Break"))
        }

    def _parse_margin(self, value):
        if isinstance(value, (int, float)):
            return int(value)
        try:
            s = str(value).lower().replace("~", "").replace(",", "").replace(" ", "").replace("approx", "")
            multiplier = 1
            if 'cr' in s:
                multiplier = 10000000
                s = s.replace('cr', '')
            elif 'l' in s:
                multiplier = 100000
                s = s.replace('l', '')
            elif 'k' in s:
                multiplier = 1000
                s = s.replace('k', '')
            numeric_part = re.findall(r"[-+]?\d*\.\d+|\d+", s)
            if numeric_part:
                return int(float(numeric_part[0]) * multiplier)
            return 1
        except:
            return 1

    def _parse_trail_count(self, value):
        if isinstance(value, str):
            if value.lower() in ("unlimited", "infinite"):
                return 9999
        try:
            val = int(value)
            if val == 0:
                return 9999
            return val
        except:
            return 9999

    def _resolve_expiry(self, expiry, symbol):
        """
        Only apply the Current Week default when expiry is genuinely absent.
        An explicitly set "Current Month" must be respected.
        """
        if not expiry or str(expiry).lower() in ("none", "null", ""):
            symbol = str(symbol).upper()
            if "NIFTY" in symbol or "SENSEX" in symbol or "BANKEX" in symbol:
                return "Current Week"
            return "Current Month"
        return str(expiry)

    def _map_condition(self, value):
        val = str(value)
        if "(" in val:
            return val
        mapping = {
            "ABOVEEQUAL": "AboveEqual (>=)",
            "ABOVE_EQUAL": "AboveEqual (>=)",
            "ABOVE EQUAL": "AboveEqual (>=)",
            ">=": "AboveEqual (>=)",
            "BELOWEQUAL": "BelowEqual (<=)",
            "BELOW_EQUAL": "BelowEqual (<=)",
            "BELOW EQUAL": "BelowEqual (<=)",
            "<=": "BelowEqual (<=)",
            "ANY": "Any",
        }
        return mapping.get(val.upper(), "Any")

    def _map_strike_direction(self, value):
        # USB uses signed atm value for direction; strikeDirection is always "BOTH"
        return "BOTH"

    def _map_target_by(self, value, category):
        val = str(value).strip()
        # Strip prefix ("Target by " / "SL by ") to normalize to just the type keyword
        lower = val.lower()
        for prefix in ("target by ", "sl by "):
            if lower.startswith(prefix):
                val = val[len(prefix):]
                break
        mapping = {
            "MONEY": f"{category} by Money",
            "POINT": f"{category} by Point",
            "POINT%": f"{category} by Point (%)",
            "POINT (%)": f"{category} by Point (%)",
            "POINT(%)": f"{category} by Point (%)",
            "PERCENTAGE": f"{category} by Point (%)",
            "PERCENT": f"{category} by Point (%)",
            "RANGE": f"{category} by Range High/Low",
            "RANGE HIGH/LOW": f"{category} by Range High/Low",
        }
        return mapping.get(val.upper(), f"{category} by Money")

    def _map_wait_direction(self, value):
        val = str(value).strip().lower()
        mapping = {
            "up %": "Up %", "up%": "Up %", "up_percent": "Up %", "up percent": "Up %",
            "down %": "Down %", "down%": "Down %", "down_percent": "Down %", "down percent": "Down %",
            "up pts": "Up pts", "up points": "Up pts", "upward points": "Up pts", "up_pts": "Up pts",
            "down pts": "Down pts", "down points": "Down pts", "downward points": "Down pts", "down_pts": "Down pts",
        }
        return mapping.get(val, value)

# Singleton instance
generator = PayloadGenerator()
