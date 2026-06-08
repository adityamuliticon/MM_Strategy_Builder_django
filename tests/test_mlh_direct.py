"""
Direct unit tests for MLHPayloadGenerator and MLHValidator — no LLM, no API credits.
Each test feeds the exact JSON the LLM would produce into generate_payload()
and validates the Market Maya multi-leg hedger payload output.

Tests cover:
  - All 3 trading modes: Normal, Range Breakout, BTST/STBT
  - All 6 underlying symbols with correct lot sizes
  - FUT vs OPT segment option_type handling
  - Wait-and-trade detection edge cases
  - Working days, VIX filter, trail SL, cycle, sqroff controls
  - Per-leg: trail SL, re-entry, re-execute, Dynamic ATM, premium ranges
  - Fixed invariants: product=None, workingDay="ALL", qty_distribution="Fix", etc.
  - is_live_mtm_profit_move as int 0/1
  - cosider_closed_pnl intentional typo field
  - squareoffLegs / sqroffAllLegs both toggled by sqroff_all_legs
  - Validator: missing name, bad mode, OPT without option_type, Dynamic without ranges
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_leg_hedger.services.generator import mlh_generator, STRATEGY_TYPE_ID
from multi_leg_hedger.services.validator import mlh_validator
from datetime import datetime


# ── helpers ───────────────────────────────────────────────────────────────────
class TR:
    def __init__(self, name):
        self.name = name
        self.passed = []
        self.failed = []

    def check(self, label, actual, expected):
        if actual == expected:
            self.passed.append(f"  ✅ {label}: {actual!r}")
        else:
            self.failed.append(f"  ❌ {label}: expected={expected!r}  got={actual!r}")

    def check_in(self, label, actual, expected_set):
        if actual in expected_set:
            self.passed.append(f"  ✅ {label}: {actual!r} in {expected_set}")
        else:
            self.failed.append(f"  ❌ {label}: {actual!r} not in {expected_set}")

    def check_startswith(self, label, actual, prefix):
        if isinstance(actual, str) and actual.startswith(prefix):
            self.passed.append(f"  ✅ {label} starts with {prefix!r}: {actual!r}")
        else:
            self.failed.append(f"  ❌ {label}: expected starts with {prefix!r}  got={actual!r}")

    def check_none(self, label, actual):
        if actual is None:
            self.passed.append(f"  ✅ {label}: None")
        else:
            self.failed.append(f"  ❌ {label}: expected None  got={actual!r}")

    def print_report(self):
        ok = not self.failed
        icon = "✅" if ok else "❌"
        print(f"\n{icon} {self.name}  [{len(self.passed)}/{len(self.passed)+len(self.failed)}]")
        for l in self.passed: print(l)
        for l in self.failed: print(l)
        return ok


def sub(p, n):
    """Return the nth leg (1-indexed) from payload's sub array."""
    legs = p.get("sub", [])
    return legs[n-1] if len(legs) >= n else {}


# ─────────────────────────────────────────────────────────────────────────────
# TEST 1 — Normal mode, BankNifty Straddle, Intraday MIS
# Covers: mode=Normal, is_intraday, productType, underlying string, sub legs, fixed values
# ─────────────────────────────────────────────────────────────────────────────
def test_1():
    p = mlh_generator.generate_payload({
        "strategy_name": "BNF Straddle",
        "trading_mode": "Normal",
        "is_intraday": True,
        "product_type": "MIS",
        "symbol": "BANKNIFTY",
        "exchange": "NFO",
        "segment": "FUT",
        "entry_time": "09:20",
        "exit_time": "15:15",
        "master_target_by": "Money",
        "master_target": 5000,
        "master_sl_by": "Money",
        "master_sl": 3000,
        "legs": [
            {"symbol": "BANKNIFTY", "segment": "OPT", "option_type": "CE",
             "trade_side": "SELL", "lot": 1, "atm": 0, "expiry": "WEEKLY"},
            {"symbol": "BANKNIFTY", "segment": "OPT", "option_type": "PE",
             "trade_side": "SELL", "lot": 1, "atm": 0, "expiry": "WEEKLY"},
        ]
    })
    t = TR("T01 — Normal BankNifty Straddle Intraday MIS")
    t.check("strategyName",      p["strategyName"],      "BNF Straddle")
    t.check("isIntraday",        p["isIntraday"],         True)
    t.check("productType",       p["productType"],        "MIS")
    t.check("symbol",            p["symbol"],             "BANKNIFTY")
    t.check("exchange",          p["exchange"],           "NFO")
    t.check("underlying",        p["underlying"],         "BANKNIFTY FUT NFO")
    t.check("target",            p["target"],             5000.0)
    t.check("sl",                p["sl"],                 3000.0)
    t.check("entryTime",         p["entryTime"],          "09:20")
    t.check("exitTime",          p["exitTime"],           "15:15")
    t.check("is_btst_stbt",      p["is_btst_stbt"],       False)
    t.check("is_range_break_out",p["is_range_break_out"], False)
    t.check("strategyId",        p["strategyId"],         STRATEGY_TYPE_ID)
    # leg 1
    l1 = sub(p, 1)
    t.check("l1.tradeSide",       l1["tradeSide"],         "SELL")
    t.check("l1.optionType",      l1["optionType"],        "CE")
    t.check("l1.segment",         l1["segment"],           "OPT")
    t.check("l1.lot",             l1["lot"],               1)
    t.check("l1.qty",             l1["qty"],               30)  # BANKNIFTY lot_size=30
    t.check("l1.expiry",          l1["expiry"],            "WEEKLY")
    # leg 2
    l2 = sub(p, 2)
    t.check("l2.optionType",      l2["optionType"],        "PE")
    t.check("l2.qty",             l2["qty"],               30)
    # fixed invariants on legs
    t.check_none("l1.product",    l1["product"])
    t.check("l1.workingDay",      l1["workingDay"],        "ALL")
    t.check("l1.qty_distribution",l1["qty_distribution"], "Fix")
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 2 — Normal mode, Positional NRML
# Covers: is_intraday=False, productType=NRML
# ─────────────────────────────────────────────────────────────────────────────
def test_2():
    p = mlh_generator.generate_payload({
        "strategy_name": "NIFTY Positional",
        "trading_mode": "Normal",
        "is_intraday": False,
        "product_type": "NRML",
        "symbol": "NIFTY",
        "exchange": "NFO",
        "segment": "FUT",
        "legs": [
            {"symbol": "NIFTY", "segment": "OPT", "option_type": "CE",
             "trade_side": "SELL", "lot": 2, "atm": 0, "expiry": "MONTHLY"},
        ]
    })
    t = TR("T02 — Normal NIFTY Positional NRML")
    t.check("isIntraday",   p["isIntraday"],   False)
    t.check("productType",  p["productType"],  "NRML")
    t.check("symbol",       p["symbol"],       "NIFTY")
    t.check("underlying",   p["underlying"],   "NIFTY FUT NFO")
    l1 = sub(p, 1)
    t.check("l1.lot",  l1["lot"],  2)
    t.check("l1.qty",  l1["qty"],  50)  # NIFTY=25 * 2
    t.check("l1.expiry", l1["expiry"], "MONTHLY")
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 3 — Range Breakout mode
# Covers: mode="Range Breakout" → is_range_break_out=True, is_btst_stbt=False, range_time
#         per-leg range_breakout_direction "High" and "Low"
# ─────────────────────────────────────────────────────────────────────────────
def test_3():
    p = mlh_generator.generate_payload({
        "strategy_name": "BNF Range BO",
        "trading_mode": "Range Breakout",
        "symbol": "BANKNIFTY",
        "exchange": "NFO",
        "segment": "FUT",
        "range_end_time": "09:30",
        "legs": [
            {"symbol": "BANKNIFTY", "segment": "OPT", "option_type": "CE",
             "trade_side": "BUY", "lot": 1, "range_breakout_direction": "High"},
            {"symbol": "BANKNIFTY", "segment": "OPT", "option_type": "PE",
             "trade_side": "BUY", "lot": 1, "range_breakout_direction": "Low"},
        ]
    })
    t = TR("T03 — Range Breakout mode")
    t.check("is_range_break_out", p["is_range_break_out"], True)
    t.check("is_btst_stbt",       p["is_btst_stbt"],       False)
    t.check("range_time",         p["range_time"],         "09:30")
    l1 = sub(p, 1)
    l2 = sub(p, 2)
    t.check("l1.range_breakout_direction", l1["range_breakout_direction"], "High")
    t.check("l2.range_breakout_direction", l2["range_breakout_direction"], "Low")
    # In range breakout, is_intraday should still be True (not btst)
    t.check("isIntraday", p["isIntraday"], True)
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 4 — BTST/STBT mode
# Covers: mode="BTST/STBT" → is_btst_stbt=True, is_intraday=False (forced), productType=NRML
# ─────────────────────────────────────────────────────────────────────────────
def test_4():
    p = mlh_generator.generate_payload({
        "strategy_name": "BNF BTST",
        "trading_mode": "BTST/STBT",
        "symbol": "BANKNIFTY",
        "exchange": "NFO",
        "segment": "FUT",
        "legs": [
            {"symbol": "BANKNIFTY", "segment": "OPT", "option_type": "CE",
             "trade_side": "SELL", "lot": 1},
        ]
    })
    t = TR("T04 — BTST/STBT mode forces isIntraday=False, NRML")
    t.check("is_btst_stbt",       p["is_btst_stbt"],       True)
    t.check("is_range_break_out", p["is_range_break_out"], False)
    t.check("isIntraday",         p["isIntraday"],          False)
    t.check("productType",        p["productType"],         "NRML")
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 5 — All lot sizes for all underlying symbols
# Covers: LOT_SIZES mapping for BANKNIFTY, NIFTY, FINNIFTY, MIDCPNIFTY, SENSEX, BANKEX
# ─────────────────────────────────────────────────────────────────────────────
def test_5():
    t = TR("T05 — All underlying symbol lot sizes")
    cases = [
        ("BANKNIFTY", 1, 30), ("BANKNIFTY", 2, 60),
        ("NIFTY",     1, 25), ("NIFTY",     3, 75),
        ("FINNIFTY",  1, 40), ("FINNIFTY",  2, 80),
        ("MIDCPNIFTY",1, 75), ("MIDCPNIFTY",2, 150),
        ("SENSEX",    1, 20), ("SENSEX",    2, 40),
        ("BANKEX",    1, 15), ("BANKEX",    2, 30),
    ]
    for sym, lot, expected_qty in cases:
        p = mlh_generator.generate_payload({
            "strategy_name": f"TEST {sym}",
            "trading_mode": "Normal",
            "symbol": sym, "exchange": "NFO", "segment": "FUT",
            "legs": [{"symbol": sym, "segment": "OPT", "option_type": "CE",
                      "trade_side": "SELL", "lot": lot}]
        })
        l = sub(p, 1)
        t.check(f"{sym} lot={lot} qty", l["qty"], expected_qty)
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 6 — OPT segment: option_type preserved; FUT segment: option_type cleared
# Covers: segment logic in _build_leg
# ─────────────────────────────────────────────────────────────────────────────
def test_6():
    p = mlh_generator.generate_payload({
        "strategy_name": "Seg Test",
        "trading_mode": "Normal",
        "symbol": "NIFTY", "exchange": "NFO", "segment": "FUT",
        "legs": [
            {"symbol": "NIFTY", "segment": "OPT", "option_type": "CE",
             "trade_side": "SELL", "lot": 1},
            {"symbol": "NIFTY", "segment": "OPT", "option_type": "PE",
             "trade_side": "SELL", "lot": 1},
            {"symbol": "NIFTY", "segment": "FUT",
             "trade_side": "BUY", "lot": 1},
        ]
    })
    t = TR("T06 — OPT keeps option_type, FUT clears it")
    l1, l2, l3 = sub(p, 1), sub(p, 2), sub(p, 3)
    t.check("l1.optionType CE", l1["optionType"], "CE")
    t.check("l2.optionType PE", l2["optionType"], "PE")
    t.check("l3.optionType empty (FUT)", l3["optionType"], "")
    t.check("l3.segment FUT", l3["segment"], "FUT")
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 7 — Wait-and-trade detection edge cases
# Covers: is_wait_and_trade=True only when wait_for is non-empty/None AND wait_value > 0
# ─────────────────────────────────────────────────────────────────────────────
def test_7():
    def make_leg(wait_for, wait_value):
        p = mlh_generator.generate_payload({
            "strategy_name": "W&T",
            "trading_mode": "Normal",
            "symbol": "NIFTY", "exchange": "NFO", "segment": "FUT",
            "legs": [{"symbol": "NIFTY", "segment": "OPT", "option_type": "CE",
                      "trade_side": "BUY", "lot": 1,
                      "wait_for": wait_for, "wait_value": wait_value}]
        })
        return sub(p, 1)

    t = TR("T07 — Wait-and-trade detection")
    l = make_leg("Up%", 0.5)
    t.check("Up% 0.5 → is_wait=True",  l["is_wait_and_trade"], True)
    t.check("Up% 0.5 → wait_for",      l["wait_for"],          "Up%")
    t.check("Up% 0.5 → wait_value",    l["wait_value"],         0.5)

    l = make_leg("Down pts", 100)
    t.check("Down pts 100 → is_wait=True", l["is_wait_and_trade"], True)
    t.check("Down pts 100 → wait_for",     l["wait_for"],           "Down pts")
    t.check("Down pts 100 → wait_value",   l["wait_value"],          100.0)

    l = make_leg("None", 0.5)
    t.check("'None' → is_wait=False",   l["is_wait_and_trade"], False)
    t.check("'None' → wait_for",        l["wait_for"],           "None")
    t.check("'None' → wait_value",      l["wait_value"],          0)

    l = make_leg("Up%", 0)
    t.check("Up% value=0 → is_wait=False", l["is_wait_and_trade"], False)

    l = make_leg("", 100)
    t.check("empty wait_for → is_wait=False", l["is_wait_and_trade"], False)

    l = make_leg(None, 1)
    t.check("None wait_for → is_wait=False", l["is_wait_and_trade"], False)
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 8 — Working days mapping
# Covers: working_days dict → mon/tue/wed/thu/fri/sat/sun in payload
# ─────────────────────────────────────────────────────────────────────────────
def test_8():
    p = mlh_generator.generate_payload({
        "strategy_name": "Day Filter",
        "trading_mode": "Normal",
        "symbol": "BANKNIFTY", "exchange": "NFO", "segment": "FUT",
        "working_days": {"mon": True, "tue": False, "wed": True, "thu": False,
                         "fri": True, "sat": False, "sun": False},
        "legs": [{"symbol": "BANKNIFTY", "segment": "OPT", "option_type": "CE",
                  "trade_side": "SELL", "lot": 1}]
    })
    t = TR("T08 — Working days Mon/Wed/Fri only")
    t.check("mon", p["mon"], True)
    t.check("tue", p["tue"], False)
    t.check("wed", p["wed"], True)
    t.check("thu", p["thu"], False)
    t.check("fri", p["fri"], True)
    t.check("sat", p["sat"], False)
    t.check("sun", p["sun"], False)
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 9 — Empty working_days → all weekdays default True, sat/sun False
# ─────────────────────────────────────────────────────────────────────────────
def test_9():
    p = mlh_generator.generate_payload({
        "strategy_name": "Default Days",
        "trading_mode": "Normal",
        "symbol": "NIFTY", "exchange": "NFO", "segment": "FUT",
        "legs": [{"symbol": "NIFTY", "segment": "OPT", "option_type": "CE",
                  "trade_side": "SELL", "lot": 1}]
    })
    t = TR("T09 — Empty working_days → weekdays True, weekend False")
    t.check("mon default True",  p["mon"], True)
    t.check("tue default True",  p["tue"], True)
    t.check("wed default True",  p["wed"], True)
    t.check("thu default True",  p["thu"], True)
    t.check("fri default True",  p["fri"], True)
    t.check("sat default False", p["sat"], False)
    t.check("sun default False", p["sun"], False)
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 10 — VIX filter
# Covers: enable_vix_filter, vix_start_value, vix_end_value → enableVixFilter, vixStartValue, vixEndValue
# ─────────────────────────────────────────────────────────────────────────────
def test_10():
    p = mlh_generator.generate_payload({
        "strategy_name": "VIX Controlled",
        "trading_mode": "Normal",
        "symbol": "NIFTY", "exchange": "NFO", "segment": "FUT",
        "enable_vix_filter": True,
        "vix_start_value": 12.5,
        "vix_end_value": 22.0,
        "legs": [{"symbol": "NIFTY", "segment": "OPT", "option_type": "CE",
                  "trade_side": "SELL", "lot": 1}]
    })
    t = TR("T10 — VIX filter on")
    t.check("enableVixFilter",  p["enableVixFilter"],  True)
    t.check("vixStartValue",    p["vixStartValue"],     12.5)
    t.check("vixEndValue",      p["vixEndValue"],       22.0)

    p2 = mlh_generator.generate_payload({
        "strategy_name": "No VIX",
        "trading_mode": "Normal",
        "symbol": "NIFTY", "exchange": "NFO", "segment": "FUT",
        "legs": [{"symbol": "NIFTY", "segment": "OPT", "option_type": "CE",
                  "trade_side": "SELL", "lot": 1}]
    })
    t.check("enableVixFilter default False", p2["enableVixFilter"], False)
    t.check("vixStartValue default 0",       p2["vixStartValue"],    0.0)
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 11 — Master trail SL fields
# Covers: is_trail_sl, trail_sl_by, start_trail_after_profit, profit_move, sl_move, no_of_trail_sl
# ─────────────────────────────────────────────────────────────────────────────
def test_11():
    p = mlh_generator.generate_payload({
        "strategy_name": "Trail SL",
        "trading_mode": "Normal",
        "symbol": "BANKNIFTY", "exchange": "NFO", "segment": "FUT",
        "is_trail_sl": True,
        "trail_sl_by": "Point",
        "start_trail_after_profit": 1000.0,
        "profit_move": 500.0,
        "sl_move": 300.0,
        "no_of_trail_sl": 5,
        "legs": [{"symbol": "BANKNIFTY", "segment": "OPT", "option_type": "CE",
                  "trade_side": "SELL", "lot": 1}]
    })
    t = TR("T11 — Master trail SL")
    t.check("isTrailSl",             p["isTrailSl"],              True)
    t.check("trail_sl_by",           p["trail_sl_by"],            "Point")
    t.check("startTrailAfterProfit", p["startTrailAfterProfit"],  1000.0)
    t.check("profitMove",            p["profitMove"],             500.0)
    t.check("slMove",                p["slMove"],                 300.0)
    t.check("noOfTrailSL",           p["noOfTrailSL"],            5)
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 12 — sqroff_all_legs mirrors to both squareoffLegs and sqroffAllLegs
# ─────────────────────────────────────────────────────────────────────────────
def test_12():
    def make(sqroff_all):
        return mlh_generator.generate_payload({
            "strategy_name": "Sqroff",
            "trading_mode": "Normal",
            "symbol": "NIFTY", "exchange": "NFO", "segment": "FUT",
            "sqroff_all_legs": sqroff_all,
            "legs": [{"symbol": "NIFTY", "segment": "OPT", "option_type": "CE",
                      "trade_side": "SELL", "lot": 1}]
        })

    t = TR("T12 — sqroff_all_legs → squareoffLegs AND sqroffAllLegs both toggle")
    p_true = make(True)
    t.check("squareoffLegs True",  p_true["squareoffLegs"], True)
    t.check("sqroffAllLegs True",  p_true["sqroffAllLegs"], True)
    p_false = make(False)
    t.check("squareoffLegs False", p_false["squareoffLegs"], False)
    t.check("sqroffAllLegs False", p_false["sqroffAllLegs"], False)
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 13 — is_live_mtm_profit_move stored as int 0/1
# ─────────────────────────────────────────────────────────────────────────────
def test_13():
    def make(val):
        return mlh_generator.generate_payload({
            "strategy_name": "MTM",
            "trading_mode": "Normal",
            "symbol": "NIFTY", "exchange": "NFO", "segment": "FUT",
            "is_live_mtm_profit_move": val,
            "legs": [{"symbol": "NIFTY", "segment": "OPT", "option_type": "CE",
                      "trade_side": "SELL", "lot": 1}]
        })

    t = TR("T13 — is_live_mtm_profit_move as int 0/1")
    t.check("True  → 1", make(True)["is_live_mtm_profit_move"],  1)
    t.check("False → 0", make(False)["is_live_mtm_profit_move"], 0)
    t.check("1     → 1", make(1)["is_live_mtm_profit_move"],     1)
    t.check("0     → 0", make(0)["is_live_mtm_profit_move"],     0)
    t.check("default → 0", make(None)["is_live_mtm_profit_move"], 0)
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 14 — cosider_closed_pnl (intentional single-n typo in field name)
# ─────────────────────────────────────────────────────────────────────────────
def test_14():
    p_on = mlh_generator.generate_payload({
        "strategy_name": "PNL Test",
        "trading_mode": "Normal",
        "symbol": "NIFTY", "exchange": "NFO", "segment": "FUT",
        "cosider_closed_pnl": True,
        "legs": [{"symbol": "NIFTY", "segment": "OPT", "option_type": "CE",
                  "trade_side": "SELL", "lot": 1}]
    })
    p_off = mlh_generator.generate_payload({
        "strategy_name": "PNL Off",
        "trading_mode": "Normal",
        "symbol": "NIFTY", "exchange": "NFO", "segment": "FUT",
        "legs": [{"symbol": "NIFTY", "segment": "OPT", "option_type": "CE",
                  "trade_side": "SELL", "lot": 1}]
    })
    t = TR("T14 — cosider_closed_pnl (typo field)")
    t.check("cosider_closed_pnl True",         p_on["cosider_closed_pnl"],  True)
    t.check("cosider_closed_pnl default False", p_off["cosider_closed_pnl"], False)
    # verify correct key name (single 'n')
    t.check("key exists", "cosider_closed_pnl" in p_on, True)
    t.check("wrong key absent", "consider_closed_pnl" in p_on, False)
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 15 — Cycle, reset cycle, no_of_cycle_per_day, cycle_delay
# Covers: no_of_cycle, cycle_delay, is_reset_cycle, reset_cycle_index_percentage, no_of_cycle_per_day
# ─────────────────────────────────────────────────────────────────────────────
def test_15():
    p = mlh_generator.generate_payload({
        "strategy_name": "Cycle Test",
        "trading_mode": "Normal",
        "symbol": "BANKNIFTY", "exchange": "NFO", "segment": "FUT",
        "no_of_cycle": 3,
        "cycle_delay": 10,
        "is_reset_cycle": True,
        "reset_cycle_index_percentage": 2.5,
        "no_of_cycle_per_day": 5,
        "legs": [{"symbol": "BANKNIFTY", "segment": "OPT", "option_type": "CE",
                  "trade_side": "SELL", "lot": 1}]
    })
    t = TR("T15 — Cycle and reset cycle")
    t.check("noOfIntradayCycle",         p["noOfIntradayCycle"],         3)
    t.check("intraday_cycle_delay",      p["intraday_cycle_delay"],      10)
    t.check("isResetCycle",              p["isResetCycle"],              True)
    t.check("resetCycleIndexPercentage", p["resetCycleIndexPercentage"], 2.5)
    t.check("noOfCyclePerDay",           p["noOfCyclePerDay"],           5)
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 16 — Sqroff by fix time + sqroff_before_expiry_days
# ─────────────────────────────────────────────────────────────────────────────
def test_16():
    p = mlh_generator.generate_payload({
        "strategy_name": "Sqroff Time",
        "trading_mode": "Normal",
        "symbol": "BANKNIFTY", "exchange": "NFO", "segment": "FUT",
        "sqroff_by_fix_time": True,
        "sqroff_week_day": "FRI",
        "sqroff_time": "14:30",
        "sqroff_before_expiry_days": 2,
        "chk_con_delay_after_market_start": 30,
        "legs": [{"symbol": "BANKNIFTY", "segment": "OPT", "option_type": "CE",
                  "trade_side": "SELL", "lot": 1}]
    })
    t = TR("T16 — Sqroff by fix time + before-expiry days")
    t.check("sqroffByFixTime",                 p["sqroffByFixTime"],                 True)
    t.check("sqroffWeekDay",                   p["sqroffWeekDay"],                   "FRI")
    t.check("sqroffTime",                      p["sqroffTime"],                      "14:30")
    t.check("sqroff_before_expiry_days",       p["sqroff_before_expiry_days"],       2)
    t.check("chk_con_delay_after_market_start",p["chk_con_delay_after_market_start"],30)
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 17 — Per-leg trail SL fields
# Covers: is_trail_sl, trail_sl_market_move, trail_sl_move, no_of_time_trail_sl,
#         trail_sl_by, trail_sl_cost per leg
# ─────────────────────────────────────────────────────────────────────────────
def test_17():
    p = mlh_generator.generate_payload({
        "strategy_name": "Leg Trail SL",
        "trading_mode": "Normal",
        "symbol": "NIFTY", "exchange": "NFO", "segment": "FUT",
        "legs": [
            {"symbol": "NIFTY", "segment": "OPT", "option_type": "CE",
             "trade_side": "SELL", "lot": 1,
             "is_trail_sl": True,
             "trail_sl_market_move": 500.0,
             "trail_sl_move": 200.0,
             "no_of_time_trail_sl": 3,
             "trail_sl_by": "Point",
             "trail_sl_cost": True},
            {"symbol": "NIFTY", "segment": "OPT", "option_type": "PE",
             "trade_side": "SELL", "lot": 1,
             "is_trail_sl": False},
        ]
    })
    t = TR("T17 — Per-leg trail SL")
    l1, l2 = sub(p, 1), sub(p, 2)
    t.check("l1.is_trail_sl",          l1["is_trail_sl"],          True)
    t.check("l1.trail_sl_market_move", l1["trail_sl_market_move"], 500.0)
    t.check("l1.trail_sl_move",        l1["trail_sl_move"],        200.0)
    t.check("l1.no_of_time_trail_sl",  l1["no_of_time_trail_sl"],  3)
    t.check("l1.trail_sl_by",          l1["trail_sl_by"],          "Point")
    t.check("l1.trail_sl_cost",        l1["trail_sl_cost"],        True)
    t.check("l2.is_trail_sl",          l2["is_trail_sl"],          False)
    t.check("l2.trail_sl_cost",        l2["trail_sl_cost"],        False)
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 18 — Per-leg re-entry and re-execute
# Covers: reentry_on, no_of_reentry, reexecute_delay, reexecute_on, no_of_reexecute
# ─────────────────────────────────────────────────────────────────────────────
def test_18():
    p = mlh_generator.generate_payload({
        "strategy_name": "Re-entry",
        "trading_mode": "Normal",
        "symbol": "BANKNIFTY", "exchange": "NFO", "segment": "FUT",
        "legs": [
            {"symbol": "BANKNIFTY", "segment": "OPT", "option_type": "CE",
             "trade_side": "SELL", "lot": 1,
             "reentry_on": "SL", "no_of_reentry": 2, "reexecute_delay": 5},
            {"symbol": "BANKNIFTY", "segment": "OPT", "option_type": "PE",
             "trade_side": "SELL", "lot": 1,
             "reexecute_on": "Target", "no_of_reexecute": 3, "reexecute_delay": 10},
        ]
    })
    t = TR("T18 — Per-leg re-entry and re-execute")
    l1, l2 = sub(p, 1), sub(p, 2)
    t.check("l1.reentry_on",      l1["reentry_on"],      "SL")
    t.check("l1.no_of_reentry",   l1["no_of_reentry"],   2)
    t.check("l1.reexecute_delay", l1["reexecute_delay"], 5)
    t.check("l2.reexecute_on",    l2["reexecute_on"],    "Target")
    t.check("l2.no_of_reexecute", l2["no_of_reexecute"], 3)
    t.check("l2.reexecute_delay", l2["reexecute_delay"], 10)
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 19 — Dynamic ATM + premium ranges per leg
# Covers: atm_type="Dynamic", premium_start_range, premium_end_range
# ─────────────────────────────────────────────────────────────────────────────
def test_19():
    p = mlh_generator.generate_payload({
        "strategy_name": "Dynamic ATM",
        "trading_mode": "Normal",
        "symbol": "BANKNIFTY", "exchange": "NFO", "segment": "FUT",
        "legs": [
            {"symbol": "BANKNIFTY", "segment": "OPT", "option_type": "CE",
             "trade_side": "SELL", "lot": 1,
             "atm_type": "Dynamic",
             "premium_start_range": 100.0,
             "premium_end_range": 200.0},
            {"symbol": "BANKNIFTY", "segment": "OPT", "option_type": "PE",
             "trade_side": "SELL", "lot": 1,
             "atm_type": "Fix"},
        ]
    })
    t = TR("T19 — Dynamic ATM and premium ranges per leg")
    l1, l2 = sub(p, 1), sub(p, 2)
    t.check("l1.atmType",          l1["atmType"],          "Dynamic")
    t.check("l1.premiumStartRange",l1["premiumStartRange"], 100.0)
    t.check("l1.premiumEndRange",  l1["premiumEndRange"],   200.0)
    t.check("l2.atmType Fix",      l2["atmType"],           "Fix")
    t.check("l2.premiumStartRange default 0", l2["premiumStartRange"], 0.0)
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 20 — BFO exchange (SENSEX / BANKEX)
# Covers: exchange="BFO", underlying string, correct lot sizes
# ─────────────────────────────────────────────────────────────────────────────
def test_20():
    p = mlh_generator.generate_payload({
        "strategy_name": "SENSEX Straddle",
        "trading_mode": "Normal",
        "is_intraday": True,
        "symbol": "SENSEX",
        "exchange": "BFO",
        "segment": "FUT",
        "legs": [
            {"symbol": "SENSEX", "exchange": "BFO", "segment": "OPT", "option_type": "CE",
             "trade_side": "SELL", "lot": 2},
            {"symbol": "BANKEX", "exchange": "BFO", "segment": "OPT", "option_type": "PE",
             "trade_side": "SELL", "lot": 1},
        ]
    })
    t = TR("T20 — BFO exchange SENSEX/BANKEX")
    t.check("exchange",   p["exchange"],   "BFO")
    t.check("symbol",     p["symbol"],     "SENSEX")
    t.check("underlying", p["underlying"], "SENSEX FUT BFO")
    l1, l2 = sub(p, 1), sub(p, 2)
    t.check("SENSEX lot=2 qty=40", l1["qty"], 40)
    t.check("BANKEX lot=1 qty=15", l2["qty"], 15)
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 21 — strategy_name: random fallback when not provided
# ─────────────────────────────────────────────────────────────────────────────
def test_21():
    p_no_name = mlh_generator.generate_payload({
        "trading_mode": "Normal",
        "symbol": "NIFTY", "exchange": "NFO", "segment": "FUT",
        "legs": [{"symbol": "NIFTY", "segment": "OPT", "option_type": "CE",
                  "trade_side": "SELL", "lot": 1}]
    })
    p_named = mlh_generator.generate_payload({
        "strategy_name": "My Custom Strategy",
        "trading_mode": "Normal",
        "symbol": "NIFTY", "exchange": "NFO", "segment": "FUT",
        "legs": [{"symbol": "NIFTY", "segment": "OPT", "option_type": "CE",
                  "trade_side": "SELL", "lot": 1}]
    })
    t = TR("T21 — strategy_name fallback and custom name")
    t.check_startswith("no name → MLH_ prefix", p_no_name["strategyName"], "MLH_")
    t.check("named → exact name", p_named["strategyName"], "My Custom Strategy")
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 22 — No legs provided → default leg auto-added
# Covers: empty legs list fallback
# ─────────────────────────────────────────────────────────────────────────────
def test_22():
    p = mlh_generator.generate_payload({
        "strategy_name": "No Legs",
        "trading_mode": "Normal",
        "symbol": "NIFTY",
        "exchange": "NFO",
        "segment": "FUT",
        "legs": []
    })
    t = TR("T22 — Empty legs → default FUT leg auto-added")
    t.check("sub length = 1", len(p["sub"]), 1)
    l = sub(p, 1)
    t.check("default segment FUT", l["segment"], "FUT")
    t.check("default symbol NIFTY", l["symbol"], "NIFTY")
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 23 — Fixed invariants always present in payload and legs
# Covers: followSimulator, paperTrading, allowUpdateParameters,
#         pauseAndSqrOffOnMarginExceed, rebacktest, isEditCode,
#         effect_all_sub_strategies, requiredCapital, strategyId
#         per-leg: product=None, workingDay="ALL", qty_distribution="Fix"
# ─────────────────────────────────────────────────────────────────────────────
def test_23():
    p = mlh_generator.generate_payload({
        "strategy_name": "Fixed Values",
        "trading_mode": "Normal",
        "symbol": "BANKNIFTY", "exchange": "NFO", "segment": "FUT",
        "legs": [
            {"symbol": "BANKNIFTY", "segment": "OPT", "option_type": "CE",
             "trade_side": "SELL", "lot": 1},
            {"symbol": "BANKNIFTY", "segment": "OPT", "option_type": "PE",
             "trade_side": "SELL", "lot": 1},
        ]
    })
    t = TR("T23 — Fixed invariants in payload and per-leg")
    t.check("followSimulator",              p["followSimulator"],              True)
    t.check("paperTrading",                 p["paperTrading"],                 True)
    t.check("allowUpdateParameters",        p["allowUpdateParameters"],        True)
    t.check("pauseAndSqrOffOnMarginExceed", p["pauseAndSqrOffOnMarginExceed"], True)
    t.check("rebacktest",                   p["rebacktest"],                   False)
    t.check("isEditCode",                   p["isEditCode"],                   False)
    t.check("effect_all_sub_strategies",    p["effect_all_sub_strategies"],    False)
    t.check("requiredCapital",              p["requiredCapital"],              1)
    t.check("strategyId",                   p["strategyId"],                   STRATEGY_TYPE_ID)
    for i in [1, 2]:
        l = sub(p, i)
        t.check_none(f"l{i}.product = None",        l["product"])
        t.check(f"l{i}.workingDay = ALL",        l["workingDay"],        "ALL")
        t.check(f"l{i}.qty_distribution = Fix",  l["qty_distribution"], "Fix")
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 24 — Per-leg target/SL fields and trade direction
# Covers: target_by, target, sl_by, sl, trade_side BUY/SELL, atm, strike_price
# ─────────────────────────────────────────────────────────────────────────────
def test_24():
    p = mlh_generator.generate_payload({
        "strategy_name": "Per-Leg TP SL",
        "trading_mode": "Normal",
        "symbol": "BANKNIFTY", "exchange": "NFO", "segment": "FUT",
        "legs": [
            {"symbol": "BANKNIFTY", "segment": "OPT", "option_type": "CE",
             "trade_side": "SELL", "lot": 2, "atm": 500, "strike_price": 47500.0,
             "target_by": "Money", "target": 2000,
             "sl_by": "Money", "sl": 1000},
            {"symbol": "BANKNIFTY", "segment": "OPT", "option_type": "PE",
             "trade_side": "BUY",  "lot": 1, "atm": -500, "strike_price": 46000.0,
             "target_by": "Money", "target": 1500,
             "sl_by": "Money", "sl": 800},
        ]
    })
    t = TR("T24 — Per-leg target/SL, atm, strike_price, trade_side")
    l1, l2 = sub(p, 1), sub(p, 2)
    t.check("l1.tradeSide SELL",  l1["tradeSide"],   "SELL")
    t.check("l1.atm 500",         l1["atm"],          500)
    t.check("l1.strikePrice",     l1["strikePrice"],  47500.0)
    t.check("l1.targetBy",        l1["targetBy"],     "Money")
    t.check("l1.target",          l1["target"],       2000.0)
    t.check("l1.slBy",            l1["slBy"],         "Money")
    t.check("l1.sl",              l1["sl"],           1000.0)
    t.check("l1.lot=2 qty=60",    l1["qty"],          60)
    t.check("l2.tradeSide BUY",   l2["tradeSide"],    "BUY")
    t.check("l2.atm -500",        l2["atm"],          -500)
    t.check("l2.strikePrice",     l2["strikePrice"],  46000.0)
    t.check("l2.lot=1 qty=30",    l2["qty"],          30)
    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 25 — Validator: valid strategy passes, error cases caught
# Covers: strategy_name required, trading_mode valid, OPT without option_type,
#         Dynamic ATM without premium ranges, empty legs
# ─────────────────────────────────────────────────────────────────────────────
def test_25():
    t = TR("T25 — Validator error cases")

    # Valid — no errors
    errs = mlh_validator.validate({
        "strategy_name": "Valid",
        "trading_mode": "Normal",
        "legs": [{"segment": "OPT", "option_type": "CE"}]
    })
    t.check("valid → 0 errors", len(errs), 0)

    # Missing strategy_name
    errs = mlh_validator.validate({
        "strategy_name": "",
        "trading_mode": "Normal",
        "legs": [{"segment": "OPT", "option_type": "CE"}]
    })
    t.check("empty name → error", any("strategy_name" in e for e in errs), True)

    # Invalid trading_mode
    errs = mlh_validator.validate({
        "strategy_name": "Test",
        "trading_mode": "Invalid",
        "legs": [{"segment": "OPT", "option_type": "CE"}]
    })
    t.check("bad mode → error", any("trading_mode" in e for e in errs), True)

    # Empty legs
    errs = mlh_validator.validate({
        "strategy_name": "Test",
        "trading_mode": "Normal",
        "legs": []
    })
    t.check("empty legs → error", any("leg" in e.lower() for e in errs), True)

    # OPT segment without option_type
    errs = mlh_validator.validate({
        "strategy_name": "Test",
        "trading_mode": "Normal",
        "legs": [{"segment": "OPT"}]
    })
    t.check("OPT no option_type → error", any("option_type" in e for e in errs), True)

    # Dynamic ATM without premium ranges
    errs = mlh_validator.validate({
        "strategy_name": "Test",
        "trading_mode": "Normal",
        "legs": [{"segment": "OPT", "option_type": "CE", "atm_type": "Dynamic",
                  "premium_start_range": 0, "premium_end_range": 0}]
    })
    t.check("Dynamic no ranges → error", any("premium" in e for e in errs), True)

    # Dynamic ATM with both ranges — valid
    errs = mlh_validator.validate({
        "strategy_name": "Test",
        "trading_mode": "Normal",
        "legs": [{"segment": "OPT", "option_type": "CE", "atm_type": "Dynamic",
                  "premium_start_range": 100, "premium_end_range": 200}]
    })
    t.check("Dynamic with ranges → 0 errors", len(errs), 0)

    return t.print_report()


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        test_1, test_2, test_3, test_4, test_5,
        test_6, test_7, test_8, test_9, test_10,
        test_11, test_12, test_13, test_14, test_15,
        test_16, test_17, test_18, test_19, test_20,
        test_21, test_22, test_23, test_24, test_25,
    ]

    print("\n" + "=" * 70)
    print("  MLH DIRECT GENERATOR UNIT TESTS — No LLM / No API Credits")
    print("=" * 70)

    passed = sum(fn() for fn in tests)
    failed = len(tests) - passed

    print("\n" + "=" * 70)
    print(f"  RESULT: {passed}/{len(tests)} PASSED   {failed}/{len(tests)} FAILED")
    print("=" * 70)

    report = f"tests/reports/mlh_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    os.makedirs("tests/reports", exist_ok=True)
    with open(report, "w") as f:
        f.write(f"MLH Direct Generator Test — {datetime.now().isoformat()}\n")
        f.write(f"Result: {passed}/{len(tests)} passed\n")
    print(f"\n  Report saved to: {report}\n")
