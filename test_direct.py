"""
Direct unit tests for PayloadGenerator — no LLM, no API credits needed.
Each test feeds the exact JSON the LLM would produce into generate_v3_payload()
and validates the Market Maya payload output.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.generator import PayloadGenerator
from datetime import datetime

gen = PayloadGenerator()

# ── helpers ──────────────────────────────────────────────────────────────────
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

    def check_contains(self, label, actual, sub):
        if sub in str(actual):
            self.passed.append(f"  ✅ {label} contains {sub!r}")
        else:
            self.failed.append(f"  ❌ {label}: expected to contain {sub!r}  got={actual!r}")

    def print_report(self):
        ok = not self.failed
        icon = "✅" if ok else "❌"
        print(f"\n{icon} {self.name}  [{len(self.passed)}/{len(self.passed)+len(self.failed)}]")
        for l in self.passed: print(l)
        for l in self.failed: print(l)
        return ok


def L(p, n):
    legs = p.get("legs", [])
    return legs[n-1] if len(legs) >= n else {}


# ── TEST 1 — BankNifty Straddle ───────────────────────────────────────────────
def test_1():
    p = gen.generate_v3_payload({
        "strategyName": "BankNifty Straddle 1234",
        "symbol": "BANKNIFTY", "exchange": "NFO", "segment": "FUT",
        "isIntraday": True, "productType": "MIS",
        "entry_time": "09:20:00", "exit_time": "15:15:00",
        "intradayTarget": 2500, "target_by": "Combined Profit",
        "intradaySl": 1500, "sl_by": "Combined Loss",
    }, [
        {"action": "SELL", "option": "CE", "strike_type": "ATM", "strike": 0, "lots": 1, "expiry": "Current Week"},
        {"action": "SELL", "option": "PE", "strike_type": "ATM", "strike": 0, "lots": 1, "expiry": "Current Week"},
    ])
    t = TR("P1 — BankNifty Straddle")
    t.check("mainExchange", p["mainExchange"], "NFO")
    t.check("mainSymbol",   p["mainSymbol"],   "BANKNIFTY")
    t.check("isIntraday",   p["isIntraday"],   True)
    t.check("productType",  p["productType"],  "MIS")
    t.check("tradingStartTime", p["tradingStartTime"], "09:20:00")
    t.check("tradingEndTime",   p["tradingEndTime"],   "15:15:00")
    l1, l2 = L(p,1), L(p,2)
    t.check("leg1.tradeSide",  l1["tradeSide"],  "SELL")
    t.check("leg1.optionType", l1["optionType"], "CE")
    t.check("leg1.atm",        l1["atm"],        0)
    t.check("leg1.expiry",     l1["expiry"],     "Current Week")
    t.check("leg1.lot",        l1["lot"],        1)
    t.check("leg1.isIdle",     l1["isIdle"],     False)
    t.check("leg2.tradeSide",  l2["tradeSide"],  "SELL")
    t.check("leg2.optionType", l2["optionType"], "PE")
    t.check("leg2.atm",        l2["atm"],        0)
    t.check("leg2.expiry",     l2["expiry"],     "Current Week")
    t.check("leg2.lot",        l2["lot"],        1)
    t.check("isEnableMasterTarget", p["isEnableMasterTarget"], True)
    t.check("intradayTarget",       p["intradayTarget"],       2500)
    t.check("targetBy",             p["targetBy"],             "Combined Profit")
    t.check("isEnableMasterSl",     p["isEnableMasterSl"],     True)
    t.check("intradaySl",           p["intradaySl"],           1500)
    t.check("slBy",                 p["slBy"],                 "Combined Loss")
    return t.print_report()


# ── TEST 2 — Nifty Strangle + Leg TP/SL ──────────────────────────────────────
def test_2():
    p = gen.generate_v3_payload({
        "symbol": "NIFTY", "exchange": "NFO", "segment": "FUT",
        "isIntraday": True,
        "entry_time": "09:16:00", "exit_time": "15:10:00",
    }, [
        {"action": "SELL", "option": "CE", "strike_type": "ATM", "strike": 200,  "lots": 2, "expiry": "Current Week",
         "target_by": "Target by Point", "target": 30, "sl_by": "SL by Point", "sl": 50},
        {"action": "SELL", "option": "PE", "strike_type": "ATM", "strike": -200, "lots": 2, "expiry": "Current Week",
         "target_by": "Target by Point", "target": 30, "sl_by": "SL by Point", "sl": 50},
    ])
    t = TR("P2 — Nifty Strangle + Leg TP/SL")
    t.check("mainSymbol",       p["mainSymbol"],       "NIFTY")
    t.check("tradingStartTime", p["tradingStartTime"], "09:16:00")
    t.check("tradingEndTime",   p["tradingEndTime"],   "15:10:00")
    l1, l2 = L(p,1), L(p,2)
    t.check("leg1.tradeSide",  l1["tradeSide"],  "SELL")
    t.check("leg1.optionType", l1["optionType"], "CE")
    t.check("leg1.atmType",    l1["atmType"],    "Strike By ATM Value")
    t.check("leg1.atm",        l1["atm"],        200)
    t.check("leg1.lot",        l1["lot"],        2)
    t.check("leg1.targetBy",   l1["targetBy"],   "Target by Point")
    t.check("leg1.target",     l1["target"],     30)
    t.check("leg1.slBy",       l1["slBy"],       "SL by Point")
    t.check("leg1.sl",         l1["sl"],         50)
    t.check("leg2.atm",        l2["atm"],        -200)
    t.check("leg2.lot",        l2["lot"],        2)
    t.check("leg2.target",     l2["target"],     30)
    t.check("leg2.sl",         l2["sl"],         50)
    t.check("isEnableMasterTarget", p["isEnableMasterTarget"], False)
    t.check("isEnableMasterSl",     p["isEnableMasterSl"],     False)
    return t.print_report()


# ── TEST 3 — BankNifty Iron Condor 4 Legs ────────────────────────────────────
def test_3():
    p = gen.generate_v3_payload({
        "symbol": "BANKNIFTY", "exchange": "NFO", "segment": "FUT",
        "isIntraday": True, "entry_time": "09:20:00",
        "intradayTarget": 3000, "target_by": "Combined Profit",
    }, [
        {"action": "SELL", "option": "CE", "strike_type": "ATM", "strike":  300, "lots": 1, "expiry": "Current Week"},
        {"action": "SELL", "option": "PE", "strike_type": "ATM", "strike": -300, "lots": 1, "expiry": "Current Week"},
        {"action": "BUY",  "option": "CE", "strike_type": "ATM", "strike":  500, "lots": 1, "expiry": "Current Week"},
        {"action": "BUY",  "option": "PE", "strike_type": "ATM", "strike": -500, "lots": 1, "expiry": "Current Week"},
    ])
    t = TR("P3 — BankNifty Iron Condor")
    t.check("mainSymbol",  p["mainSymbol"],          "BANKNIFTY")
    t.check("leg_count",   len(p.get("legs", [])),   4)
    l1,l2,l3,l4 = L(p,1),L(p,2),L(p,3),L(p,4)
    t.check("leg1 SELL CE +300", (l1["tradeSide"],l1["optionType"],l1["atm"]), ("SELL","CE",300))
    t.check("leg2 SELL PE -300", (l2["tradeSide"],l2["optionType"],l2["atm"]), ("SELL","PE",-300))
    t.check("leg3 BUY  CE +500", (l3["tradeSide"],l3["optionType"],l3["atm"]), ("BUY","CE",500))
    t.check("leg4 BUY  PE -500", (l4["tradeSide"],l4["optionType"],l4["atm"]), ("BUY","PE",-500))
    for i,l in enumerate([l1,l2,l3,l4],1):
        t.check(f"leg{i}.lot",    l["lot"],    1)
        t.check(f"leg{i}.expiry", l["expiry"], "Current Week")
    t.check("intradayTarget",   p["intradayTarget"],   3000)
    t.check("isEnableMasterSl", p["isEnableMasterSl"], False)
    t.check("tradingStartTime", p["tradingStartTime"], "09:20:00")
    return t.print_report()


# ── TEST 4 — Premium Range + Combined Premium Entry ───────────────────────────
def test_4():
    p = gen.generate_v3_payload({
        "symbol": "BANKNIFTY", "exchange": "NFO", "segment": "FUT",
        "isIntraday": True,
        "total_combined_prem": 220,
        "intradayTarget": 2000, "target_by": "Combined Profit",
    }, [
        {"action": "SELL", "option": "CE", "strike_type": "PREMIUM_RANGE",
         "premium_start_range": 100, "premium_end_range": 150, "direction": "OTM",
         "lots": 1, "expiry": "Current Week"},
        {"action": "SELL", "option": "PE", "strike_type": "PREMIUM_RANGE",
         "premium_start_range": 100, "premium_end_range": 150, "direction": "OTM",
         "lots": 1, "expiry": "Current Week"},
    ])
    t = TR("P4 — Premium Range + Combined Premium Entry")
    l1, l2 = L(p,1), L(p,2)
    t.check("leg1.atmType",           l1["atmType"],           "Strike By Premium Range")
    t.check("leg1.premiumStartRange", l1["premiumStartRange"], 100)
    t.check("leg1.premiumEndRange",   l1["premiumEndRange"],   150)
    t.check("leg1.strikeDirection",   l1["strikeDirection"],   "OTM")
    t.check("leg1.optionType",        l1["optionType"],        "CE")
    t.check("leg2.atmType",           l2["atmType"],           "Strike By Premium Range")
    t.check("leg2.premiumStartRange", l2["premiumStartRange"], 100)
    t.check("leg2.premiumEndRange",   l2["premiumEndRange"],   150)
    t.check("leg2.strikeDirection",   l2["strikeDirection"],   "OTM")
    t.check("leg2.optionType",        l2["optionType"],        "PE")
    t.check("isCombinedPremEntry",    p["isCombinedPremEntry"],    True)
    t.check("totalCombinedPremium",   p["totalCombinedPremium"],   220)
    t.check("intradayTarget",         p["intradayTarget"],         2000)
    return t.print_report()


# ── TEST 5 — Delta-Based Strike + Condition + Direction ──────────────────────
def test_5():
    p = gen.generate_v3_payload({
        "symbol": "NIFTY", "exchange": "NFO", "segment": "FUT",
        "isIntraday": True,
        "intradaySl": 2000, "sl_by": "Combined Loss",
    }, [
        {"action": "SELL", "option": "PE", "strike_type": "NEAREST_DELTA", "strike": 0.3,
         "direction": "OTM", "condition": "AboveEqual", "lots": 1, "expiry": "Current Week"},
        {"action": "BUY",  "option": "PE", "strike_type": "ATM", "strike": -500,
         "lots": 1, "expiry": "Current Week"},
    ])
    t = TR("P5 — Delta Strike + Condition")
    l1, l2 = L(p,1), L(p,2)
    t.check("leg1.tradeSide",      l1["tradeSide"],      "SELL")
    t.check("leg1.optionType",     l1["optionType"],     "PE")
    t.check("leg1.atmType",        l1["atmType"],        "Strike By Nearest Delta")
    t.check("leg1.atm",            l1["atm"],            0.3)
    t.check("leg1.strikeCondition",l1["strikeCondition"],"AboveEqual (>=)")
    t.check("leg1.strikeDirection",l1["strikeDirection"],"OTM")
    t.check("leg2.tradeSide",      l2["tradeSide"],      "BUY")
    t.check("leg2.optionType",     l2["optionType"],     "PE")
    t.check("leg2.atmType",        l2["atmType"],        "Strike By ATM Value")
    t.check("leg2.atm",            l2["atm"],            -500)
    t.check("intradaySl",          p["intradaySl"],      2000)
    t.check("isEnableMasterTarget",p["isEnableMasterTarget"], False)
    return t.print_report()


# ── TEST 6 — Master Profit Locking + Master SL Trailing ──────────────────────
def test_6():
    p = gen.generate_v3_payload({
        "symbol": "BANKNIFTY", "exchange": "NFO", "segment": "FUT",
        "isIntraday": True, "entry_time": "09:20:00",
        "intradayTarget": 5000, "target_by": "Combined Profit",
        "intradaySl": 2000, "sl_by": "Combined Loss",
        "master_profit_locking": {
            "if_profit_reaches": 3000, "lock_minimum_profit": 1500,
            "increse_in_profit_by": 500, "trail_profit_by": 300, "noOfTimeTrailTp": 5,
        },
        "master_sl_trailing": {"profit_move": 1000, "sl_move": 500, "no_of_trail_sl": 3},
    }, [
        {"action": "SELL", "option": "CE", "strike_type": "ATM", "strike": 0, "lots": 1, "expiry": "Current Week"},
        {"action": "SELL", "option": "PE", "strike_type": "ATM", "strike": 0, "lots": 1, "expiry": "Current Week"},
    ])
    t = TR("P6 — Master Profit Locking + Master SL Trailing")
    t.check("intradayTarget",              p["intradayTarget"],              5000)
    t.check("intradaySl",                  p["intradaySl"],                  2000)
    t.check("isEnableProfitLockingTrailing",p["isEnableProfitLockingTrailing"],True)
    t.check("ifProfitReaches",             p["ifProfitReaches"],             3000)
    t.check("lockMinimumProfit",           p["lockMinimumProfit"],           1500)
    t.check("increseInProfitBy",           p["increseInProfitBy"],           500)
    t.check("trailProfitBy",               p["trailProfitBy"],               300)
    t.check("noOfTimeTrailTp",             p["noOfTimeTrailTp"],             5)
    t.check("isEnableStoplossTrailing",    p["isEnableStoplossTrailing"],    True)
    t.check("profitMove",                  p["profitMove"],                  1000)
    t.check("slMove",                      p["slMove"],                      500)
    t.check("noOfTrailSl",                 p["noOfTrailSl"],                 3)
    return t.print_report()


# ── TEST 7 — Leg-Level Profit Locking + SL Trailing ──────────────────────────
def test_7():
    p = gen.generate_v3_payload({
        "symbol": "NIFTY", "exchange": "NFO", "segment": "FUT", "isIntraday": True,
    }, [
        {"action": "SELL", "option": "CE", "strike_type": "ATM", "strike": 100, "lots": 1, "expiry": "Current Week",
         "profit_locking": {"if_profit_reaches": 2000, "lock_minimum_profit": 1000,
                            "increse_in_profit_by": 400, "trail_profit_by": 200, "no_of_time_trail": 4},
         "trail_sl": {"trail_sl_market_move": 800, "trail_sl_move": 300, "no_of_time_trail": 0}},
        {"action": "SELL", "option": "PE", "strike_type": "ATM", "strike": -100, "lots": 1, "expiry": "Current Week",
         "profit_locking": {"if_profit_reaches": 1500, "lock_minimum_profit": 800,
                            "increse_in_profit_by": 300, "trail_profit_by": 150, "no_of_time_trail": 3}},
    ])
    t = TR("P7 — Leg Profit Locking + SL Trailing")
    l1, l2 = L(p,1), L(p,2)
    t.check("leg1.isProfitLockingAndTrailing", l1["isProfitLockingAndTrailing"], True)
    t.check("leg1.ifProfitReaches",            l1["ifProfitReaches"],            2000)
    t.check("leg1.lockMinimumProfit",          l1["lockMinimumProfit"],          1000)
    t.check("leg1.increseInProfitBy",          l1["increseInProfitBy"],          400)
    t.check("leg1.trailProfitBy",              l1["trailProfitBy"],              200)
    t.check("leg1.noOfTimeTrailTp",            l1["noOfTimeTrailTp"],            4)
    t.check("leg1.isEnableStoplossTrailing",   l1["isEnableStoplossTrailing"],   True)
    t.check("leg1.trailSlMarketMove",          l1["trailSlMarketMove"],          800)
    t.check("leg1.trailSlMove",                l1["trailSlMove"],                300)
    t.check("leg1.noOfTimeTrailSl",            l1["noOfTimeTrailSl"],            9999)
    t.check("leg2.isProfitLockingAndTrailing", l2["isProfitLockingAndTrailing"], True)
    t.check("leg2.ifProfitReaches",            l2["ifProfitReaches"],            1500)
    t.check("leg2.lockMinimumProfit",          l2["lockMinimumProfit"],          800)
    t.check("leg2.increseInProfitBy",          l2["increseInProfitBy"],          300)
    t.check("leg2.trailProfitBy",              l2["trailProfitBy"],              150)
    t.check("leg2.noOfTimeTrailTp",            l2["noOfTimeTrailTp"],            3)
    t.check("leg2.isEnableStoplossTrailing",   l2["isEnableStoplossTrailing"],   False)
    return t.print_report()


# ── TEST 8 — Idle Legs + Action on Target/SL ─────────────────────────────────
def test_8():
    p = gen.generate_v3_payload({
        "symbol": "BANKNIFTY", "exchange": "NFO", "segment": "FUT", "isIntraday": True,
    }, [
        {"action": "SELL", "option": "CE", "strike_type": "ATM", "strike": 0, "lots": 1,
         "expiry": "Current Week", "is_idle": False,
         "target_by": "Target by Point", "target": 40,
         "sl_by": "SL by Point", "sl": 60,
         "action_on_target": "Execute Leg", "target_action_leg_no": 2, "target_action_delay": 5,
         "action_on_sl":    "Execute Leg", "sl_action_leg_no":    3, "sl_action_delay":    3},
        {"action": "SELL", "option": "PE", "strike_type": "ATM", "strike": 0, "lots": 1,
         "expiry": "Current Week", "is_idle": True},
        {"action": "BUY",  "option": "CE", "strike_type": "ATM", "strike": 500, "lots": 1,
         "expiry": "Current Week", "is_idle": True},
    ])
    t = TR("P8 — Idle Legs + Action on Target/SL")
    l1, l2, l3 = L(p,1), L(p,2), L(p,3)
    t.check("leg1.isIdle",                l1["isIdle"],                False)
    t.check("leg1.targetBy",              l1["targetBy"],              "Target by Point")
    t.check("leg1.target",                l1["target"],                40)
    t.check("leg1.slBy",                  l1["slBy"],                  "SL by Point")
    t.check("leg1.sl",                    l1["sl"],                    60)
    t.check("leg1.isEnableActionOnTarget",l1["isEnableActionOnTarget"],True)
    t.check("leg1.actionOnTarget",        l1["actionOnTarget"],        "Execute Leg")
    t.check("leg1.actionOnTargetLegNo",   l1["actionOnTargetLegNo"],   2)
    t.check("leg1.actionOnTargetDelay",   l1["actionOnTargetDelay"],   5)
    t.check("leg1.isEnableActionOnSl",    l1["isEnableActionOnSl"],    True)
    t.check("leg1.actionOnSl",            l1["actionOnSl"],            "Execute Leg")
    t.check("leg1.actionOnSlLegNo",       l1["actionOnSlLegNo"],       3)
    t.check("leg1.actionOnSlDelay",       l1["actionOnSlDelay"],       3)
    t.check("leg2.isIdle",                l2["isIdle"],                True)
    t.check("leg3.isIdle",                l3["isIdle"],                True)
    return t.print_report()


# ── TEST 9 — Reenter Leg + Sqroff Leg ────────────────────────────────────────
def test_9():
    p = gen.generate_v3_payload({
        "symbol": "NIFTY", "exchange": "NFO", "segment": "FUT", "isIntraday": True,
    }, [
        {"action": "SELL", "option": "CE", "strike_type": "ATM", "strike": 0, "lots": 1,
         "expiry": "Current Week",
         "target_by": "Target by Point", "target": 50, "sl_by": "SL by Point", "sl": 70,
         "action_on_target": "Reenter Leg", "target_action_leg_no": 1, "target_action_delay": 10},
        {"action": "SELL", "option": "PE", "strike_type": "ATM", "strike": 0, "lots": 1,
         "expiry": "Current Week",
         "target_by": "Target by Point", "target": 50, "sl_by": "SL by Point", "sl": 70,
         "action_on_target": "Execute Leg", "target_action_leg_no": 3, "target_action_delay": 0,
         "action_on_sl":    "Sqroff Leg",  "sl_action_leg_no":    1, "sl_action_delay":    2},
        {"action": "BUY", "option": "CE", "strike_type": "ATM", "strike": 400, "lots": 1,
         "expiry": "Current Week", "is_idle": True},
    ])
    t = TR("P9 — Reenter Leg + Sqroff Leg")
    l1, l2, l3 = L(p,1), L(p,2), L(p,3)
    t.check("leg1.actionOnTarget",      l1["actionOnTarget"],      "Reenter Leg")
    t.check("leg1.actionOnTargetLegNo", l1["actionOnTargetLegNo"], 1)
    t.check("leg1.actionOnTargetDelay", l1["actionOnTargetDelay"], 10)
    t.check("leg2.actionOnSl",          l2["actionOnSl"],          "Sqroff Leg")
    t.check("leg2.actionOnSlLegNo",     l2["actionOnSlLegNo"],     1)
    t.check("leg2.actionOnSlDelay",     l2["actionOnSlDelay"],     2)
    t.check("leg2.actionOnTarget",      l2["actionOnTarget"],      "Execute Leg")
    t.check("leg2.actionOnTargetLegNo", l2["actionOnTargetLegNo"], 3)
    t.check("leg3.isIdle",              l3["isIdle"],              True)
    return t.print_report()


# ── TEST 10 — Range Breakout + Wait & Trade ───────────────────────────────────
def test_10():
    p = gen.generate_v3_payload({
        "symbol": "BANKNIFTY", "exchange": "NFO", "segment": "FUT", "isIntraday": True,
        "is_range_breakout": True, "range_end_time": "09:30:00",
        "intradayTarget": 2000, "target_by": "Combined Profit",
        "intradaySl": 1500, "sl_by": "Combined Loss",
    }, [
        {"action": "SELL", "option": "CE", "strike_type": "ATM", "strike": 0, "lots": 1,
         "expiry": "Current Week", "is_execute_on_range_breakout": True},
        {"action": "SELL", "option": "PE", "strike_type": "ATM", "strike": 0, "lots": 1,
         "expiry": "Current Week", "wait_and_trade": True, "wait_for": "Down %", "wait_value": 0.5},
    ])
    t = TR("P10 — Range Breakout + Wait & Trade")
    l1, l2 = L(p,1), L(p,2)
    t.check("isRangeBreakOut",           p["isRangeBreakOut"],           True)
    t.check("rangeEndTime",              p["rangeEndTime"],              "09:30:00")
    t.check("intradayTarget",            p["intradayTarget"],            2000)
    t.check("intradaySl",                p["intradaySl"],                1500)
    t.check("leg1.isExecuteOnRangeBreakout", l1["isExecuteOnRangeBreakout"], True)
    t.check("leg1.isWaitAndTrade",           l1["isWaitAndTrade"],           False)
    t.check("leg2.isWaitAndTrade",           l2["isWaitAndTrade"],           True)
    t.check("leg2.waitFor",                  l2["waitFor"],                  "Down %")
    t.check("leg2.waitValue",          float(l2["waitValue"]),               0.5)
    t.check("leg2.isExecuteOnRangeBreakout", l2["isExecuteOnRangeBreakout"], False)
    return t.print_report()


# ── TEST 11 — Positional + BTST + Pre-Expiry Sqroff ──────────────────────────
def test_11():
    p = gen.generate_v3_payload({
        "symbol": "BANKNIFTY", "exchange": "NFO", "segment": "FUT",
        "isIntraday": False, "productType": "NRML",
        "is_btst_stbt": True, "btst_gap_days": 2,
        "sqroff_before_expiry": True, "sqroff_before_expiry_days": 1, "sqroff_time": "15:10:00",
        "intradayTarget": 8000, "target_by": "Combined Profit",
        "intradaySl": 5000, "sl_by": "Combined Loss",
    }, [
        {"action": "SELL", "option": "CE", "strike_type": "ATM", "strike": 0, "lots": 1, "expiry": "Current Month"},
        {"action": "SELL", "option": "PE", "strike_type": "ATM", "strike": 0, "lots": 1, "expiry": "Current Month"},
    ])
    t = TR("P11 — Positional + BTST + Pre-Expiry")
    l1, l2 = L(p,1), L(p,2)
    t.check("isIntraday",                   p["isIntraday"],                   False)
    t.check("productType",                  p["productType"],                  "NRML")
    t.check("isBtstStbt",                   p["isBtstStbt"],                   True)
    t.check("btstGapDays",                  p["btstGapDays"],                  2)
    t.check("leg1.expiry",                  l1["expiry"],                      "Current Month")
    t.check("leg2.expiry",                  l2["expiry"],                      "Current Month")
    t.check("isEnableSqroffBeforeExpiryDays",p["isEnableSqroffBeforeExpiryDays"],True)
    t.check("sqroffBeforeExpiryDays",       p["sqroffBeforeExpiryDays"],       1)
    t.check("sqroffTime",                   p["sqroffTime"],                   "15:10:00")
    t.check("intradayTarget",               p["intradayTarget"],               8000)
    t.check("intradaySl",                   p["intradaySl"],                   5000)
    return t.print_report()


# ── TEST 12 — VIX Filter + Working Days ──────────────────────────────────────
def test_12():
    p = gen.generate_v3_payload({
        "symbol": "NIFTY", "exchange": "NFO", "segment": "FUT",
        "isIntraday": True, "entry_time": "09:20:00",
        "trading_days": ["Mon", "Wed", "Fri"],
        "enableVixFilter": True, "vix_start_value": 12, "vix_end_value": 20,
        "intradayTarget": 1500, "target_by": "Combined Profit",
    }, [
        {"action": "SELL", "option": "CE", "strike_type": "ATM", "strike": 0, "lots": 1, "expiry": "Current Week"},
        {"action": "SELL", "option": "PE", "strike_type": "ATM", "strike": 0, "lots": 1, "expiry": "Current Week"},
    ])
    t = TR("P12 — VIX Filter + Working Days")
    t.check("enableVixFilter",  p["enableVixFilter"],  True)
    t.check("vixStartValue",    p["vixStartValue"],    12)
    t.check("vixEndValue",      p["vixEndValue"],      20)
    t.check("runMon",           p["runMon"],           True)
    t.check("runTue",           p["runTue"],           False)
    t.check("runWed",           p["runWed"],           True)
    t.check("runThu",           p["runThu"],           False)
    t.check("runFri",           p["runFri"],           True)
    t.check("runSat",           p["runSat"],           False)
    t.check("intradayTarget",   p["intradayTarget"],   1500)
    t.check("isEnableMasterSl", p["isEnableMasterSl"], False)
    t.check("tradingStartTime", p["tradingStartTime"], "09:20:00")
    return t.print_report()


# ── TEST 13 — Master Reexecution ──────────────────────────────────────────────
def test_13():
    p = gen.generate_v3_payload({
        "symbol": "BANKNIFTY", "exchange": "NFO", "segment": "FUT",
        "isIntraday": True, "entry_time": "09:20:00",
        "intradayTarget": 2000, "target_by": "Combined Profit",
        "reexecute_on_target_count": 3, "reexecute_on_target_delay": 15,
        "intradaySl": 1200, "sl_by": "Combined Loss",
        "reexecute_on_sl_count": 2, "reexecute_on_sl_delay": 20,
    }, [
        {"action": "SELL", "option": "CE", "strike_type": "ATM", "strike": 0, "lots": 1, "expiry": "Current Week"},
        {"action": "SELL", "option": "PE", "strike_type": "ATM", "strike": 0, "lots": 1, "expiry": "Current Week"},
    ])
    t = TR("P13 — Master Reexecution")
    t.check("intradayTarget",      p["intradayTarget"],      2000)
    t.check("noOfIntradayCycle",   p["noOfIntradayCycle"],   3)
    t.check("intradayCycleDelay",  p["intradayCycleDelay"],  15)
    t.check("intradaySl",          p["intradaySl"],          1200)
    t.check("noOfReexecuteOnSl",   p["noOfReexecuteOnSl"],   2)
    t.check("reexecuteDelayOnSl",  p["reexecuteDelayOnSl"],  20)
    t.check("tradingStartTime",    p["tradingStartTime"],    "09:20:00")
    return t.print_report()


# ── TEST 14 — Safety Switches + Required Margin ───────────────────────────────
def test_14():
    p = gen.generate_v3_payload({
        "symbol": "BANKNIFTY", "exchange": "NFO", "segment": "FUT", "isIntraday": True,
        "sqroff_all_legs": True,
        "sqroff_on_rejection": True,
        "enable_tp_sl_on_pause": True,
        "required_margin": 125000,
        "intradayTarget": 2500, "target_by": "Combined Profit",
    }, [
        {"action": "SELL", "option": "CE", "strike_type": "ATM", "strike":  200, "lots": 1, "expiry": "Current Week"},
        {"action": "SELL", "option": "PE", "strike_type": "ATM", "strike": -200, "lots": 1, "expiry": "Current Week"},
        {"action": "BUY",  "option": "CE", "strike_type": "ATM", "strike":  400, "lots": 1, "expiry": "Current Week"},
        {"action": "BUY",  "option": "PE", "strike_type": "ATM", "strike": -400, "lots": 1, "expiry": "Current Week"},
    ])
    t = TR("P14 — Safety Switches + Required Margin")
    t.check("sqroffAllLegs",                         p["sqroffAllLegs"],                         True)
    t.check("pauseAndSqroffTradingOnMarginExeed",     p["pauseAndSqroffTradingOnMarginExeed"],     True)
    t.check("enableTpSlOnPauseStrategy",              p["enableTpSlOnPauseStrategy"],              True)
    t.check("requiredMargin",                         p["requiredMargin"],                         125000)
    t.check("intradayTarget",                         p["intradayTarget"],                         2500)
    t.check("leg_count",                              len(p.get("legs",[])),                       4)
    return t.print_report()


# ── TEST 15 — Theta-Based Strike + Point% TP/SL ──────────────────────────────
def test_15():
    p = gen.generate_v3_payload({
        "symbol": "BANKNIFTY", "exchange": "NFO", "segment": "FUT",
        "isIntraday": True, "entry_time": "09:25:00",
    }, [
        {"action": "SELL", "option": "CE", "strike_type": "THETA_RANGE",
         "premium_start_range": 5, "premium_end_range": 15, "direction": "OTM",
         "lots": 1, "expiry": "Current Week",
         "target_by": "Target by Point%", "target": 40,
         "sl_by": "SL by Point%", "sl": 60},
        {"action": "SELL", "option": "PE", "strike_type": "NEAREST_THETA", "strike": 10,
         "condition": "BelowEqual", "direction": "OTM",
         "lots": 1, "expiry": "Current Week",
         "target_by": "Target by Point%", "target": 40,
         "sl_by": "SL by Point%", "sl": 60},
    ])
    t = TR("P15 — Theta Strike + Point% TP/SL")
    l1, l2 = L(p,1), L(p,2)
    t.check("leg1.atmType",           l1["atmType"],           "Strike By Theta Range")
    t.check("leg1.premiumStartRange", l1["premiumStartRange"], 5)
    t.check("leg1.premiumEndRange",   l1["premiumEndRange"],   15)
    t.check("leg1.strikeDirection",   l1["strikeDirection"],   "OTM")
    t.check("leg1.optionType",        l1["optionType"],        "CE")
    t.check("leg2.atmType",           l2["atmType"],           "Strike By Nearest Theta")
    t.check("leg2.atm",               l2["atm"],               10)
    t.check("leg2.strikeCondition",   l2["strikeCondition"],   "BelowEqual (<=)")
    t.check("leg2.strikeDirection",   l2["strikeDirection"],   "OTM")
    t.check("leg1.targetBy",          l1["targetBy"],          "Target by Point%")
    t.check("leg1.target",            l1["target"],            40)
    t.check("leg1.slBy",              l1["slBy"],              "SL by Point%")
    t.check("leg1.sl",                l1["sl"],                60)
    t.check("leg2.targetBy",          l2["targetBy"],          "Target by Point%")
    t.check("leg2.slBy",              l2["slBy"],              "SL by Point%")
    return t.print_report()


# ── TEST 16 — ATM% Strike + Delta/Theta TP/SL + FUT Leg ──────────────────────
def test_16():
    p = gen.generate_v3_payload({
        "symbol": "NIFTY", "exchange": "NFO", "segment": "FUT",
        "isIntraday": True,
        "intradayTarget": 3000, "target_by": "Combined Profit",
    }, [
        {"action": "SELL", "option": "CE", "strike_type": "ATM%", "strike": 0.5,
         "direction": "OTM", "lots": 1, "expiry": "Current Week",
         "target_by": "Target by Delta", "target": 0.2,
         "sl_by": "SL by Theta", "sl": 8.0},
        {"action": "BUY", "segment": "FUT", "lots": 1, "expiry": "Current Month"},
    ])
    t = TR("P16 — ATM% + Delta/Theta TP/SL + FUT Leg")
    l1, l2 = L(p,1), L(p,2)
    t.check("leg1.atmType", l1["atmType"],       "Strike By ATM %")
    t.check("leg1.atm",     float(l1["atm"]),    0.5)
    t.check("leg1.targetBy",l1["targetBy"],      "Target by Delta")
    t.check("leg1.target",  float(l1["target"]), 0.2)
    t.check("leg1.slBy",    l1["slBy"],          "SL by Theta")
    t.check("leg1.sl",      float(l1["sl"]),     8.0)
    t.check("leg2.segment", l2["segment"],       "FUT")
    t.check("leg2.tradeSide",l2["tradeSide"],    "BUY")
    t.check("leg2.expiry",  l2["expiry"],        "Current Month")
    t.check("intradayTarget",p["intradayTarget"],3000)
    return t.print_report()


# ── TEST 17 — Ratio Spread + Master SL Trailing ──────────────────────────────
def test_17():
    p = gen.generate_v3_payload({
        "symbol": "BANKNIFTY", "exchange": "NFO", "segment": "FUT",
        "isIntraday": True, "entry_time": "09:20:00",
        "intradayTarget": 4000, "target_by": "Combined Profit",
        "intradaySl": 2500, "sl_by": "Combined Loss",
        "master_sl_trailing": {"profit_move": 1500, "sl_move": 700, "no_of_trail_sl": 4},
    }, [
        {"action": "SELL", "option": "CE", "strike_type": "ATM", "strike":    0, "lots": 2, "expiry": "Current Week"},
        {"action": "BUY",  "option": "CE", "strike_type": "ATM", "strike":  300, "lots": 1, "expiry": "Current Week"},
        {"action": "SELL", "option": "PE", "strike_type": "ATM", "strike":    0, "lots": 2, "expiry": "Current Week"},
        {"action": "BUY",  "option": "PE", "strike_type": "ATM", "strike": -300, "lots": 1, "expiry": "Current Week"},
    ])
    t = TR("P17 — Ratio Spread + Master SL Trailing")
    l1,l2,l3,l4 = L(p,1),L(p,2),L(p,3),L(p,4)
    t.check("leg1 SELL CE", (l1["tradeSide"],l1["optionType"]), ("SELL","CE"))
    t.check("leg1.lot",     l1["lot"],   2)
    t.check("leg1.atm",     l1["atm"],   0)
    t.check("leg2 BUY CE",  (l2["tradeSide"],l2["optionType"]), ("BUY","CE"))
    t.check("leg2.lot",     l2["lot"],   1)
    t.check("leg2.atm",     l2["atm"],   300)
    t.check("leg3 SELL PE", (l3["tradeSide"],l3["optionType"]), ("SELL","PE"))
    t.check("leg3.lot",     l3["lot"],   2)
    t.check("leg3.atm",     l3["atm"],   0)
    t.check("leg4 BUY PE",  (l4["tradeSide"],l4["optionType"]), ("BUY","PE"))
    t.check("leg4.lot",     l4["lot"],   1)
    t.check("leg4.atm",     l4["atm"],   -300)
    t.check("intradayTarget",           p["intradayTarget"],           4000)
    t.check("intradaySl",               p["intradaySl"],               2500)
    t.check("isEnableStoplossTrailing", p["isEnableStoplossTrailing"], True)
    t.check("profitMove",               p["profitMove"],               1500)
    t.check("slMove",                   p["slMove"],                   700)
    t.check("noOfTrailSl",              p["noOfTrailSl"],              4)
    return t.print_report()


# ── TEST 18 — Calendar Spread Multi-Expiry + Nearest Premium ─────────────────
def test_18():
    p = gen.generate_v3_payload({
        "symbol": "NIFTY", "exchange": "NFO", "segment": "FUT", "isIntraday": True,
    }, [
        {"action": "SELL", "option": "CE", "strike_type": "NEAREST_PREMIUM", "strike": 200,
         "direction": "BOTH", "condition": "Any", "lots": 1, "expiry": "Current Week"},
        {"action": "BUY",  "option": "CE", "strike_type": "NEAREST_PREMIUM", "strike": 200,
         "direction": "BOTH", "condition": "Any", "lots": 1, "expiry": "Month 1"},
    ])
    t = TR("P18 — Calendar Spread + Nearest Premium")
    l1, l2 = L(p,1), L(p,2)
    t.check("leg1.atmType",        l1["atmType"],        "Strike By Nearest Premium")
    t.check("leg1.atm",            int(l1["atm"]),       200)
    t.check("leg1.strikeDirection",l1["strikeDirection"],"BOTH")
    t.check("leg1.strikeCondition",l1["strikeCondition"],"Any")
    t.check("leg1.expiry",         l1["expiry"],         "Current Week")
    t.check("leg1.tradeSide",      l1["tradeSide"],      "SELL")
    t.check("leg2.atmType",        l2["atmType"],        "Strike By Nearest Premium")
    t.check("leg2.atm",            int(l2["atm"]),       200)
    t.check("leg2.strikeDirection",l2["strikeDirection"],"BOTH")
    t.check("leg2.strikeCondition",l2["strikeCondition"],"Any")
    t.check("leg2.expiry",         l2["expiry"],         "Month 1")
    t.check("leg2.tradeSide",      l2["tradeSide"],      "BUY")
    t.check("isEnableMasterTarget",p["isEnableMasterTarget"],False)
    t.check("isEnableMasterSl",    p["isEnableMasterSl"],    False)
    return t.print_report()


# ── TEST 19 — BFO/SENSEX + Combined Premium Target + Wait & Trade pts ─────────
def test_19():
    p = gen.generate_v3_payload({
        "symbol": "SENSEX", "exchange": "BFO", "segment": "FUT",
        "isIntraday": True,
        "entry_time": "09:20:00", "exit_time": "15:00:00",
        "intradayTarget": 150, "target_by": "Combined Premium",
        "intradaySl": 3000, "sl_by": "Combined Loss",
    }, [
        {"action": "SELL", "option": "CE", "strike_type": "ATM", "strike": 0, "lots": 1,
         "expiry": "Current Week", "wait_and_trade": True, "wait_for": "Up pts", "wait_value": 100},
        {"action": "SELL", "option": "PE", "strike_type": "ATM", "strike": 0, "lots": 1,
         "expiry": "Current Week"},
    ])
    t = TR("P19 — BFO/SENSEX + Combined Premium + Wait & Trade pts")
    l1 = L(p,1)
    t.check("mainExchange",      p["mainExchange"],      "BFO")
    t.check("mainSymbol",        p["mainSymbol"],        "SENSEX")
    t.check("underlying",        p["underlying"],        "SENSEX FUT BFO")
    t.check("tradingStartTime",  p["tradingStartTime"],  "09:20:00")
    t.check("tradingEndTime",    p["tradingEndTime"],    "15:00:00")
    t.check("leg1.isWaitAndTrade",l1["isWaitAndTrade"],  True)
    t.check("leg1.waitFor",       l1["waitFor"],         "Up pts")
    t.check("leg1.waitValue",   int(l1["waitValue"]),    100)
    t.check("targetBy",          p["targetBy"],          "Combined Premium")
    t.check("intradayTarget",    p["intradayTarget"],    150)
    t.check("slBy",              p["slBy"],              "Combined Loss")
    t.check("intradaySl",        p["intradaySl"],        3000)
    return t.print_report()


# ── TEST 20 — Maximum Complexity ──────────────────────────────────────────────
def test_20():
    # Note: leg1 has SL trailing → mutual exclusion disables master SL trailing.
    # This is current generator behaviour (prevents API 400).
    p = gen.generate_v3_payload({
        "strategyName": "Full Hedge Machine 1234",
        "symbol": "BANKNIFTY", "exchange": "NFO", "segment": "FUT",
        "isIntraday": False, "productType": "NRML",
        "entry_time": "09:20:00",
        "is_range_breakout": True, "range_end_time": "09:25:00",
        "is_btst_stbt": True, "btst_gap_days": 3,
        "total_combined_prem": 280,
        "trading_days": ["Mon","Tue","Wed","Thu"],
        "enableVixFilter": True, "vix_start_value": 11, "vix_end_value": 19,
        "intradayTarget": 6000, "target_by": "Combined Profit",
        "reexecute_on_target_count": 2, "reexecute_on_target_delay": 10,
        "intradaySl": 4000, "sl_by": "Combined Loss",
        "reexecute_on_sl_count": 1, "reexecute_on_sl_delay": 15,
        "master_profit_locking": {
            "if_profit_reaches": 4000, "lock_minimum_profit": 2000,
            "increse_in_profit_by": 600, "trail_profit_by": 300, "noOfTimeTrailTp": 5,
        },
        "master_sl_trailing": {"profit_move": 2000, "sl_move": 800, "no_of_trail_sl": 3},
        "sqroff_before_expiry": True, "sqroff_before_expiry_days": 2, "sqroff_time": "15:00:00",
        "sqroff_all_legs": True, "sqroff_on_rejection": True, "enable_tp_sl_on_pause": True,
        "required_margin": 200000,
        "shortDescription": "Full hedge positional BNF with premium + VIX control.",
        "detailedDescription": "Multi-leg positional BankNifty hedge using premium range + delta strikes, idle leg execution chaining, master MTM control with profit locking and SL trailing, VIX and day filtering, pre-expiry exit.",
    }, [
        {"action": "SELL", "option": "CE", "strike_type": "PREMIUM_RANGE",
         "premium_start_range": 120, "premium_end_range": 180, "direction": "OTM",
         "lots": 2, "expiry": "Current Month", "is_idle": False,
         "target_by": "Target by Point", "target": 50, "sl_by": "SL by Point", "sl": 80,
         "profit_locking": {"if_profit_reaches": 3000, "lock_minimum_profit": 1500,
                            "increse_in_profit_by": 500, "trail_profit_by": 200, "no_of_time_trail": 4},
         "trail_sl": {"trail_sl_market_move": 1000, "trail_sl_move": 400, "no_of_time_trail": 3},
         "action_on_target": "Execute Leg", "target_action_leg_no": 3, "target_action_delay": 5,
         "action_on_sl":    "Sqroff Leg",  "sl_action_leg_no":    2, "sl_action_delay":    2},
        {"action": "SELL", "option": "PE", "strike_type": "NEAREST_DELTA", "strike": 0.25,
         "condition": "AboveEqual", "direction": "OTM",
         "lots": 2, "expiry": "Current Month",
         "target_by": "Target by Point", "target": 50, "sl_by": "SL by Point", "sl": 80},
        {"action": "BUY",  "option": "CE", "strike_type": "ATM", "strike":  500,
         "lots": 1, "expiry": "Current Month", "is_idle": True},
        {"action": "BUY",  "option": "PE", "strike_type": "ATM", "strike": -500,
         "lots": 1, "expiry": "Current Month", "is_idle": True},
    ])
    t = TR("P20 — Maximum Complexity")
    l1,l2,l3,l4 = L(p,1),L(p,2),L(p,3),L(p,4)
    t.check("mainSymbol",   p["mainSymbol"],          "BANKNIFTY")
    t.check("isIntraday",   p["isIntraday"],          False)
    t.check("productType",  p["productType"],         "NRML")
    t.check("tradingStartTime",p["tradingStartTime"], "09:20:00")
    t.check("isRangeBreakOut", p["isRangeBreakOut"],  True)
    t.check("rangeEndTime",    p["rangeEndTime"],     "09:25:00")
    t.check("isBtstStbt",      p["isBtstStbt"],       True)
    t.check("btstGapDays",     p["btstGapDays"],      3)
    t.check("isCombinedPremEntry",   p["isCombinedPremEntry"],   True)
    t.check("totalCombinedPremium",  p["totalCombinedPremium"],  280)
    t.check("leg_count",             len(p.get("legs",[])),      4)
    t.check("leg1.atmType",          l1["atmType"],              "Strike By Premium Range")
    t.check("leg1.premiumStartRange",l1["premiumStartRange"],    120)
    t.check("leg1.premiumEndRange",  l1["premiumEndRange"],      180)
    t.check("leg1.strikeDirection",  l1["strikeDirection"],      "OTM")
    t.check("leg1.lot",              l1["lot"],                  2)
    t.check("leg1.isIdle",           l1["isIdle"],               False)
    t.check("leg1.isProfitLockingAndTrailing",l1["isProfitLockingAndTrailing"],True)
    t.check("leg1.ifProfitReaches",  l1["ifProfitReaches"],      3000)
    t.check("leg1.lockMinimumProfit",l1["lockMinimumProfit"],    1500)
    t.check("leg1.isEnableStoplossTrailing",l1["isEnableStoplossTrailing"],True)
    t.check("leg1.trailSlMarketMove",l1["trailSlMarketMove"],    1000)
    t.check("leg1.trailSlMove",      l1["trailSlMove"],          400)
    t.check("leg1.noOfTimeTrailSl",  l1["noOfTimeTrailSl"],      3)
    t.check("leg1.actionOnTarget",       l1["actionOnTarget"],       "Execute Leg")
    t.check("leg1.actionOnTargetLegNo",  l1["actionOnTargetLegNo"],  3)
    t.check("leg1.actionOnTargetDelay",  l1["actionOnTargetDelay"],  5)
    t.check("leg1.actionOnSl",           l1["actionOnSl"],           "Sqroff Leg")
    t.check("leg1.actionOnSlLegNo",      l1["actionOnSlLegNo"],      2)
    t.check("leg1.actionOnSlDelay",      l1["actionOnSlDelay"],      2)
    t.check("leg2.atmType",          l2["atmType"],              "Strike By Nearest Delta")
    t.check("leg2.atm",              l2["atm"],                  0.25)
    t.check("leg2.strikeCondition",  l2["strikeCondition"],      "AboveEqual (>=)")
    t.check("leg2.strikeDirection",  l2["strikeDirection"],      "OTM")
    t.check("leg2.lot",              l2["lot"],                  2)
    t.check("leg3.isIdle",           l3["isIdle"],               True)
    t.check("leg3.tradeSide",        l3["tradeSide"],            "BUY")
    t.check("leg4.isIdle",           l4["isIdle"],               True)
    t.check("leg4.tradeSide",        l4["tradeSide"],            "BUY")
    t.check("intradayTarget",        p["intradayTarget"],        6000)
    t.check("targetBy",              p["targetBy"],              "Combined Profit")
    t.check("noOfIntradayCycle",     p["noOfIntradayCycle"],     2)
    t.check("intradayCycleDelay",    p["intradayCycleDelay"],    10)
    t.check("intradaySl",            p["intradaySl"],            4000)
    t.check("noOfReexecuteOnSl",     p["noOfReexecuteOnSl"],     1)
    t.check("reexecuteDelayOnSl",    p["reexecuteDelayOnSl"],    15)
    t.check("ifProfitReaches",       p["ifProfitReaches"],       4000)
    t.check("lockMinimumProfit",     p["lockMinimumProfit"],     2000)
    t.check("increseInProfitBy",     p["increseInProfitBy"],     600)
    t.check("trailProfitBy",         p["trailProfitBy"],         300)
    t.check("noOfTimeTrailTp",       p["noOfTimeTrailTp"],       5)
    t.check("isEnableStoplossTrailing", p["isEnableStoplossTrailing"], True)
    t.check("profitMove",  p["profitMove"],  2000)
    t.check("slMove",      p["slMove"],      800)
    t.check("noOfTrailSl", p["noOfTrailSl"], 3)
    t.check("isEnableSqroffBeforeExpiryDays",p["isEnableSqroffBeforeExpiryDays"],True)
    t.check("sqroffBeforeExpiryDays",p["sqroffBeforeExpiryDays"],2)
    t.check("sqroffTime",            p["sqroffTime"],            "15:00:00")
    t.check("runMon",  p["runMon"],  True)
    t.check("runTue",  p["runTue"],  True)
    t.check("runWed",  p["runWed"],  True)
    t.check("runThu",  p["runThu"],  True)
    t.check("runFri",  p["runFri"],  False)
    t.check("enableVixFilter", p["enableVixFilter"], True)
    t.check("vixStartValue",   p["vixStartValue"],   11)
    t.check("vixEndValue",     p["vixEndValue"],      19)
    t.check("sqroffAllLegs",                     p["sqroffAllLegs"],                     True)
    t.check("pauseAndSqroffTradingOnMarginExeed",p["pauseAndSqroffTradingOnMarginExeed"],True)
    t.check("enableTpSlOnPauseStrategy",         p["enableTpSlOnPauseStrategy"],         True)
    t.check("requiredMargin",                    p["requiredMargin"],                    200000)
    t.check_contains("shortDescription",   p.get("shortDescription",""),   "Full hedge")
    t.check_contains("detailedDescription",p.get("detailedDescription",""),"positional")
    return t.print_report()


# ── Runner ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [test_1,test_2,test_3,test_4,test_5,test_6,test_7,test_8,test_9,test_10,
             test_11,test_12,test_13,test_14,test_15,test_16,test_17,test_18,test_19,test_20]

    print("\n" + "="*70)
    print("  DIRECT GENERATOR UNIT TESTS — No LLM / No API Credits Required")
    print("="*70)

    passed = sum(fn() for fn in tests)
    failed = len(tests) - passed

    print("\n" + "="*70)
    print(f"  RESULT: {passed}/20 PASSED   {failed}/20 FAILED")
    print("="*70)

    report = f"direct_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report, "w") as f:
        f.write(f"Direct Generator Test — {datetime.now().isoformat()}\n")
        f.write(f"Result: {passed}/20 passed\n")
    print(f"\n  Report saved to: {report}\n")
