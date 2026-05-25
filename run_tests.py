"""
Unified Strategy Builder – Automated Test Runner
Runs all 20 test prompts, captures deployed payloads, validates against expected values.
"""
import requests
import json
import time
import os
from datetime import datetime

BASE_URL = "http://localhost:5000/api/chat"
LOG_FILE = "deployed_strategies.log"

# ─────────────────────────────────────────────────────────────────────────────
# Helper: send one chat turn
# ─────────────────────────────────────────────────────────────────────────────
def chat(message, session_id):
    try:
        r = requests.post(BASE_URL, json={"message": message, "session_id": session_id}, timeout=120)
        r.raise_for_status()
        return r.json().get("message", "")
    except Exception as e:
        return f"ERROR: {e}"

# ─────────────────────────────────────────────────────────────────────────────
# Helper: get last deployed payload from log
# ─────────────────────────────────────────────────────────────────────────────
def last_log_count():
    if not os.path.exists(LOG_FILE):
        return 0
    with open(LOG_FILE) as f:
        return sum(1 for line in f if line.strip())

def get_last_log_entry(before_count):
    """Returns (payload, api_status, api_code, api_response) from the last new log line."""
    if not os.path.exists(LOG_FILE):
        return None, None, None, None
    with open(LOG_FILE) as f:
        lines = [l.strip() for l in f if l.strip()]
    if len(lines) <= before_count:
        return None, None, None, None
    try:
        entry = json.loads(lines[-1])
        return (
            entry.get("payload"),
            entry.get("api_status"),
            entry.get("api_code"),
            entry.get("api_response"),
        )
    except Exception as e:
        print(f"  !! Log parse error: {e}")
        return None, None, None, None

# ─────────────────────────────────────────────────────────────────────────────
# Validation helpers
# ─────────────────────────────────────────────────────────────────────────────
class TestResult:
    def __init__(self, name):
        self.name = name
        self.passed = []
        self.failed = []

    def check(self, label, actual, expected):
        if actual == expected:
            self.passed.append(f"  ✅ {label}: {actual}")
        else:
            self.failed.append(f"  ❌ {label}: expected={expected!r}, got={actual!r}")

    def check_contains(self, label, actual, expected_substring):
        if expected_substring in str(actual):
            self.passed.append(f"  ✅ {label} contains '{expected_substring}'")
        else:
            self.failed.append(f"  ❌ {label}: expected to contain '{expected_substring}', got={actual!r}")

    def summary(self):
        total = len(self.passed) + len(self.failed)
        status = "PASS" if not self.failed else "FAIL"
        return status, len(self.passed), total

    def print_report(self):
        status, p, total = self.summary()
        icon = "✅" if status == "PASS" else "❌"
        print(f"\n{icon} {self.name}  [{p}/{total} checks passed]")
        for line in self.passed:
            print(line)
        for line in self.failed:
            print(line)


def leg(p, n):
    """Return leg n (1-indexed) from payload or empty dict."""
    legs = p.get("legs", [])
    return legs[n - 1] if len(legs) >= n else {}


# ─────────────────────────────────────────────────────────────────────────────
# 20 Test Case definitions
# ─────────────────────────────────────────────────────────────────────────────
TESTS = []

def add_test(name, prompt, validator_fn):
    TESTS.append((name, prompt, validator_fn))


# ── PROMPT 1 ──────────────────────────────────────────────────────────────────
def validate_1(p, r):
    t = TestResult("PROMPT 1 – Basic BankNifty Straddle")
    t.check("mainExchange", p.get("mainExchange"), "NFO")
    t.check("mainSymbol", p.get("mainSymbol"), "BANKNIFTY")
    t.check("isIntraday", p.get("isIntraday"), True)
    t.check("productType", p.get("productType"), "MIS")
    t.check("tradingStartTime", p.get("tradingStartTime"), "09:20:00")
    t.check("tradingEndTime", p.get("tradingEndTime"), "15:15:00")
    # Legs
    l1, l2 = leg(p, 1), leg(p, 2)
    t.check("leg1.tradeSide", l1.get("tradeSide"), "SELL")
    t.check("leg1.optionType", l1.get("optionType"), "CE")
    t.check("leg1.atm", l1.get("atm"), 0)
    t.check("leg1.expiry", l1.get("expiry"), "Current Week")
    t.check("leg1.lot", l1.get("lot"), 1)
    t.check("leg1.isIdle", l1.get("isIdle"), False)
    t.check("leg2.tradeSide", l2.get("tradeSide"), "SELL")
    t.check("leg2.optionType", l2.get("optionType"), "PE")
    t.check("leg2.atm", l2.get("atm"), 0)
    t.check("leg2.expiry", l2.get("expiry"), "Current Week")
    t.check("leg2.lot", l2.get("lot"), 1)
    t.check("leg2.isIdle", l2.get("isIdle"), False)
    # Advance
    t.check("isEnableMasterTarget", p.get("isEnableMasterTarget"), True)
    t.check("intradayTarget", p.get("intradayTarget"), 2500)
    t.check("targetBy", p.get("targetBy"), "Combined Profit")
    t.check("isEnableMasterSl", p.get("isEnableMasterSl"), True)
    t.check("intradaySl", p.get("intradaySl"), 1500)
    t.check("slBy", p.get("slBy"), "Combined Loss")
    return t

add_test("PROMPT 1",
    "Create a BankNifty intraday straddle. Sell ATM CE and ATM PE at 9:20 with exit at 15:15. Set master target 2500 and master stoploss 1500. Use 1 lot per leg, weekly expiry.",
    validate_1)


# ── PROMPT 2 ──────────────────────────────────────────────────────────────────
def validate_2(p, r):
    t = TestResult("PROMPT 2 – Nifty Strangle ATM Offset + Leg TP/SL")
    t.check("mainSymbol", p.get("mainSymbol"), "NIFTY")
    t.check("tradingStartTime", p.get("tradingStartTime"), "09:16:00")
    t.check("tradingEndTime", p.get("tradingEndTime"), "15:10:00")
    l1, l2 = leg(p, 1), leg(p, 2)
    t.check("leg1.tradeSide", l1.get("tradeSide"), "SELL")
    t.check("leg1.optionType", l1.get("optionType"), "CE")
    t.check("leg1.atmType", l1.get("atmType"), "Strike By ATM Value")
    t.check("leg1.atm", l1.get("atm"), 200)
    t.check("leg1.lot", l1.get("lot"), 2)
    t.check("leg1.targetBy", l1.get("targetBy"), "Target by Point")
    t.check("leg1.target", l1.get("target"), 30)
    t.check("leg1.slBy", l1.get("slBy"), "SL by Point")
    t.check("leg1.sl", l1.get("sl"), 50)
    t.check("leg2.tradeSide", l2.get("tradeSide"), "SELL")
    t.check("leg2.optionType", l2.get("optionType"), "PE")
    t.check("leg2.atm", l2.get("atm"), -200)
    t.check("leg2.lot", l2.get("lot"), 2)
    t.check("leg2.target", l2.get("target"), 30)
    t.check("leg2.sl", l2.get("sl"), 50)
    t.check("isEnableMasterTarget", p.get("isEnableMasterTarget"), False)
    t.check("isEnableMasterSl", p.get("isEnableMasterSl"), False)
    return t

add_test("PROMPT 2",
    "Build a Nifty strangle for current week. Sell CE at ATM+200 and Sell PE at ATM-200. Set per-leg target at 30 points and per-leg stoploss at 50 points. Start at 9:16, sqroff at 15:10. 2 lots each.",
    validate_2)


# ── PROMPT 3 ──────────────────────────────────────────────────────────────────
def validate_3(p, r):
    t = TestResult("PROMPT 3 – BankNifty Iron Condor 4 Legs")
    t.check("mainSymbol", p.get("mainSymbol"), "BANKNIFTY")
    t.check("leg_count", len(p.get("legs", [])), 4)
    l1, l2, l3, l4 = leg(p,1), leg(p,2), leg(p,3), leg(p,4)
    t.check("leg1 SELL CE ATM+300", (l1.get("tradeSide"), l1.get("optionType"), l1.get("atm")), ("SELL","CE",300))
    t.check("leg2 SELL PE ATM-300", (l2.get("tradeSide"), l2.get("optionType"), l2.get("atm")), ("SELL","PE",-300))
    t.check("leg3 BUY CE ATM+500", (l3.get("tradeSide"), l3.get("optionType"), l3.get("atm")), ("BUY","CE",500))
    t.check("leg4 BUY PE ATM-500", (l4.get("tradeSide"), l4.get("optionType"), l4.get("atm")), ("BUY","PE",-500))
    for i, l in enumerate([l1,l2,l3,l4], 1):
        t.check(f"leg{i}.lot", l.get("lot"), 1)
        t.check(f"leg{i}.expiry", l.get("expiry"), "Current Week")
    t.check("intradayTarget", p.get("intradayTarget"), 3000)
    t.check("isEnableMasterSl", p.get("isEnableMasterSl"), False)
    t.check("tradingStartTime", p.get("tradingStartTime"), "09:20:00")
    return t

add_test("PROMPT 3",
    "Create an iron condor on BankNifty weekly. Sell CE ATM+300, Sell PE ATM-300, Buy CE ATM+500, Buy PE ATM-500. 1 lot each leg. Master target 3000, no stoploss. Intraday, start 9:20.",
    validate_3)


# ── PROMPT 4 ──────────────────────────────────────────────────────────────────
def validate_4(p, r):
    t = TestResult("PROMPT 4 – Premium Range Strike + Combined Premium Entry")
    l1, l2 = leg(p,1), leg(p,2)
    t.check("leg1.atmType", l1.get("atmType"), "Strike By Premium Range")
    t.check("leg1.premiumStartRange", l1.get("premiumStartRange"), 100)
    t.check("leg1.premiumEndRange", l1.get("premiumEndRange"), 150)
    t.check("leg1.strikeDirection", l1.get("strikeDirection"), "OTM")
    t.check("leg1.optionType", l1.get("optionType"), "CE")
    t.check("leg2.atmType", l2.get("atmType"), "Strike By Premium Range")
    t.check("leg2.premiumStartRange", l2.get("premiumStartRange"), 100)
    t.check("leg2.premiumEndRange", l2.get("premiumEndRange"), 150)
    t.check("leg2.strikeDirection", l2.get("strikeDirection"), "OTM")
    t.check("leg2.optionType", l2.get("optionType"), "PE")
    t.check("isCombinedPremEntry", p.get("isCombinedPremEntry"), True)
    t.check("totalCombinedPremium", p.get("totalCombinedPremium"), 220)
    t.check("intradayTarget", p.get("intradayTarget"), 2000)
    return t

add_test("PROMPT 4",
    "Sell BankNifty CE where premium is between 100 and 150, OTM only. Also sell PE in premium range 100 to 150 OTM. Enter only when combined premium of both legs reaches 220. Weekly expiry, intraday, 1 lot each. Master target 2000.",
    validate_4)


# ── PROMPT 5 ──────────────────────────────────────────────────────────────────
def validate_5(p, r):
    t = TestResult("PROMPT 5 – Delta-Based Strike + Condition + Direction")
    l1, l2 = leg(p,1), leg(p,2)
    t.check("leg1.tradeSide", l1.get("tradeSide"), "SELL")
    t.check("leg1.optionType", l1.get("optionType"), "PE")
    t.check("leg1.atmType", l1.get("atmType"), "Strike By Nearest Delta")
    t.check("leg1.atm", l1.get("atm"), 0.3)
    t.check("leg1.strikeCondition", l1.get("strikeCondition"), "AboveEqual (>=)")
    t.check("leg1.strikeDirection", l1.get("strikeDirection"), "OTM")
    t.check("leg2.tradeSide", l2.get("tradeSide"), "BUY")
    t.check("leg2.optionType", l2.get("optionType"), "PE")
    t.check("leg2.atmType", l2.get("atmType"), "Strike By ATM Value")
    t.check("leg2.atm", l2.get("atm"), -500)
    t.check("intradaySl", p.get("intradaySl"), 2000)
    t.check("isEnableMasterTarget", p.get("isEnableMasterTarget"), False)
    return t

add_test("PROMPT 5",
    "Create a Nifty strategy: Sell PE nearest delta 0.3, condition above-equal, OTM direction. Buy PE at ATM-500 as hedge. Current week expiry, 1 lot, intraday. Master SL 2000, no target.",
    validate_5)


# ── PROMPT 6 ──────────────────────────────────────────────────────────────────
def validate_6(p, r):
    t = TestResult("PROMPT 6 – Master Profit Locking + Master SL Trailing")
    t.check("intradayTarget", p.get("intradayTarget"), 5000)
    t.check("intradaySl", p.get("intradaySl"), 2000)
    t.check("isEnableProfitLockingTrailing", p.get("isEnableProfitLockingTrailing"), True)
    t.check("ifProfitReaches", p.get("ifProfitReaches"), 3000)
    t.check("lockMinimumProfit", p.get("lockMinimumProfit"), 1500)
    t.check("increseInProfitBy", p.get("increseInProfitBy"), 500)
    t.check("trailProfitBy", p.get("trailProfitBy"), 300)
    t.check("noOfTimeTrailTp", p.get("noOfTimeTrailTp"), 5)
    t.check("isEnableStoplossTrailing", p.get("isEnableStoplossTrailing"), True)
    t.check("profitMove", p.get("profitMove"), 1000)
    t.check("slMove", p.get("slMove"), 500)
    t.check("noOfTrailSl", p.get("noOfTrailSl"), 3)
    return t

add_test("PROMPT 6",
    "BankNifty straddle, sell ATM CE and PE, 1 lot, weekly, intraday, start 9:20. Master target 5000. When overall profit reaches 3000, lock minimum profit at 1500. Then for every 500 increase, trail profit by 300, max 5 times. Also trail master SL: for every 1000 profit increase trail SL by 500, max 3 times. Master SL 2000.",
    validate_6)


# ── PROMPT 7 ──────────────────────────────────────────────────────────────────
def validate_7(p, r):
    t = TestResult("PROMPT 7 – Leg-Level Profit Locking + SL Trailing")
    l1, l2 = leg(p,1), leg(p,2)
    # CE leg profit locking
    t.check("leg1.isProfitLockingAndTrailing", l1.get("isProfitLockingAndTrailing"), True)
    t.check("leg1.ifProfitReaches", l1.get("ifProfitReaches"), 2000)
    t.check("leg1.lockMinimumProfit", l1.get("lockMinimumProfit"), 1000)
    t.check("leg1.increseInProfitBy", l1.get("increseInProfitBy"), 400)
    t.check("leg1.trailProfitBy", l1.get("trailProfitBy"), 200)
    t.check("leg1.noOfTimeTrailTp", l1.get("noOfTimeTrailTp"), 4)
    # CE leg SL trailing (unlimited → 9999)
    t.check("leg1.isEnableStoplossTrailing", l1.get("isEnableStoplossTrailing"), True)
    t.check("leg1.trailSlMarketMove", l1.get("trailSlMarketMove"), 800)
    t.check("leg1.trailSlMove", l1.get("trailSlMove"), 300)
    t.check("leg1.noOfTimeTrailSl", l1.get("noOfTimeTrailSl"), 9999)
    # PE leg profit locking
    t.check("leg2.isProfitLockingAndTrailing", l2.get("isProfitLockingAndTrailing"), True)
    t.check("leg2.ifProfitReaches", l2.get("ifProfitReaches"), 1500)
    t.check("leg2.lockMinimumProfit", l2.get("lockMinimumProfit"), 800)
    t.check("leg2.increseInProfitBy", l2.get("increseInProfitBy"), 300)
    t.check("leg2.trailProfitBy", l2.get("trailProfitBy"), 150)
    t.check("leg2.noOfTimeTrailTp", l2.get("noOfTimeTrailTp"), 3)
    # PE leg: no SL trailing
    t.check("leg2.isEnableStoplossTrailing", l2.get("isEnableStoplossTrailing"), False)
    return t

add_test("PROMPT 7",
    "Nifty weekly strangle intraday. Sell CE ATM+100, Sell PE ATM-100, 1 lot each. For CE leg: if profit reaches 2000, lock 1000, trail by 200 for every 400 increase, max 4 trails. SL trail: for every 800 profit, trail SL by 300, unlimited times. For PE leg: if profit reaches 1500, lock 800, trail by 150 for every 300 increase, max 3 trails. No SL trailing for PE leg.",
    validate_7)


# ── PROMPT 8 ──────────────────────────────────────────────────────────────────
def validate_8(p, r):
    t = TestResult("PROMPT 8 – Idle Legs + Action on Target/SL Chaining")
    l1, l2, l3 = leg(p,1), leg(p,2), leg(p,3)
    t.check("leg1.isIdle", l1.get("isIdle"), False)
    t.check("leg1.targetBy", l1.get("targetBy"), "Target by Point")
    t.check("leg1.target", l1.get("target"), 40)
    t.check("leg1.slBy", l1.get("slBy"), "SL by Point")
    t.check("leg1.sl", l1.get("sl"), 60)
    t.check("leg1.isEnableActionOnTarget", l1.get("isEnableActionOnTarget"), True)
    t.check("leg1.actionOnTarget", l1.get("actionOnTarget"), "Execute Leg")
    t.check("leg1.actionOnTargetLegNo", l1.get("actionOnTargetLegNo"), 5)   # swapped: holds delay
    t.check("leg1.actionOnTargetDelay", l1.get("actionOnTargetDelay"), 2)   # swapped: holds leg no
    t.check("leg1.isEnableActionOnSl", l1.get("isEnableActionOnSl"), True)
    t.check("leg1.actionOnSl", l1.get("actionOnSl"), "Execute Leg")
    t.check("leg1.actionOnSlLegNo", l1.get("actionOnSlLegNo"), 3)           # swapped: holds delay
    t.check("leg1.actionOnSlDelay", l1.get("actionOnSlDelay"), 3)           # swapped: holds leg no
    t.check("leg2.isIdle", l2.get("isIdle"), True)
    t.check("leg3.isIdle", l3.get("isIdle"), True)
    return t

add_test("PROMPT 8",
    "BankNifty intraday weekly. Leg 1: Sell ATM CE, 1 lot, target 40 points, SL 60 points. Leg 2: idle, Sell ATM PE, 1 lot. Leg 3: idle, Buy CE ATM+500, 1 lot. When Leg 1 hits target, execute Leg 2 after 5 second delay. When Leg 1 hits SL, execute Leg 3 after 3 second delay.",
    validate_8)


# ── PROMPT 9 ──────────────────────────────────────────────────────────────────
def validate_9(p, r):
    t = TestResult("PROMPT 9 – Sqroff Leg + Execute Leg actions")
    l1, l2, l3 = leg(p,1), leg(p,2), leg(p,3)
    # Leg 1 executes idle Leg 3 on target (only Leg 1 can use Execute Leg via MM API)
    t.check("leg1.isEnableActionOnTarget", l1.get("isEnableActionOnTarget"), True)
    t.check("leg1.actionOnTarget", l1.get("actionOnTarget"), "Execute Leg")
    t.check("leg1.actionOnTargetLegNo", l1.get("actionOnTargetLegNo"), 10)  # swapped: holds delay
    t.check("leg1.actionOnTargetDelay", l1.get("actionOnTargetDelay"), 3)   # swapped: holds leg no
    # Leg 2 sqroffs Leg 1 on SL (Sqroff Leg from non-first legs is allowed)
    t.check("leg2.isEnableActionOnSl", l2.get("isEnableActionOnSl"), True)
    t.check("leg2.actionOnSl", l2.get("actionOnSl"), "Sqroff Leg")
    t.check("leg2.actionOnSlLegNo", l2.get("actionOnSlLegNo"), 2)           # swapped: holds delay
    t.check("leg2.actionOnSlDelay", l2.get("actionOnSlDelay"), 1)           # swapped: holds leg no
    t.check("leg3.isIdle", l3.get("isIdle"), True)
    return t

add_test("PROMPT 9",
    "Nifty weekly intraday. Leg 1: Sell CE ATM, target 50 points, SL 70 points. Leg 3: idle, Buy CE ATM+400. When Leg 1 hits target → execute Leg 3 with 10 sec delay. Leg 2: Sell PE ATM, target 50 points, SL 70 points. When Leg 2 hits SL → sqroff Leg 1 with 2 sec delay.",
    validate_9)


# ── PROMPT 10 ─────────────────────────────────────────────────────────────────
def validate_10(p, r):
    t = TestResult("PROMPT 10 – Range Breakout + Wait & Trade")
    t.check("isRangeBreakOut", p.get("isRangeBreakOut"), True)
    t.check("rangeEndTime", p.get("rangeEndTime"), "09:30:00")
    t.check("intradayTarget", p.get("intradayTarget"), 2000)
    t.check("intradaySl", p.get("intradaySl"), 1500)
    l1, l2 = leg(p,1), leg(p,2)
    t.check("leg1.isExecuteOnRangeBreakout", l1.get("isExecuteOnRangeBreakout"), True)
    t.check("leg1.isWaitAndTrade", l1.get("isWaitAndTrade"), False)
    t.check("leg2.isWaitAndTrade", l2.get("isWaitAndTrade"), True)
    t.check("leg2.waitFor", l2.get("waitFor"), "Down %")
    t.check("leg2.waitValue", l2.get("waitValue"), 1)  # 0.5% → ceil → 1 (API min)
    t.check("leg2.isExecuteOnRangeBreakout", l2.get("isExecuteOnRangeBreakout"), False)
    return t

add_test("PROMPT 10",
    "BankNifty intraday. Enable range breakout, range end time 9:30. Leg 1: Sell CE ATM, execute on range breakout. Leg 2: Sell PE ATM, use wait and trade — enter after underlying moves down 0.5%. Weekly, 1 lot each. Master target 2000, master SL 1500.",
    validate_10)


# ── PROMPT 11 ─────────────────────────────────────────────────────────────────
def validate_11(p, r):
    t = TestResult("PROMPT 11 – Positional + BTST + Pre-Expiry Sqroff")
    t.check("isIntraday", p.get("isIntraday"), False)
    t.check("productType", p.get("productType"), "NRML")
    t.check("isBtstStbt", p.get("isBtstStbt"), True)
    t.check("btstGapDays", p.get("btstGapDays"), 2)
    l1, l2 = leg(p,1), leg(p,2)
    t.check("leg1.expiry", l1.get("expiry"), "Current Month")
    t.check("leg2.expiry", l2.get("expiry"), "Current Month")
    t.check("isEnableSqroffBeforeExpiryDays", p.get("isEnableSqroffBeforeExpiryDays"), True)
    t.check("sqroffBeforeExpiryDays", p.get("sqroffBeforeExpiryDays"), 1)
    t.check("sqroffTime", p.get("sqroffTime"), "15:10:00")
    t.check("intradayTarget", p.get("intradayTarget"), 8000)
    t.check("intradaySl", p.get("intradaySl"), 5000)
    return t

add_test("PROMPT 11",
    "Create a positional BankNifty strategy with NRML product. Sell CE ATM and PE ATM, monthly expiry, 1 lot. Enable BTST with 2 gap days. Square off positions 1 day before expiry at 15:10. Master target 8000, master SL 5000.",
    validate_11)


# ── PROMPT 12 ─────────────────────────────────────────────────────────────────
def validate_12(p, r):
    t = TestResult("PROMPT 12 – VIX Filter + Working Days")
    t.check("enableVixFilter", p.get("enableVixFilter"), True)
    t.check("vixStartValue", p.get("vixStartValue"), 12)
    t.check("vixEndValue", p.get("vixEndValue"), 20)
    t.check("runMon", p.get("runMon"), True)
    t.check("runTue", p.get("runTue"), False)
    t.check("runWed", p.get("runWed"), True)
    t.check("runThu", p.get("runThu"), False)
    t.check("runFri", p.get("runFri"), True)
    t.check("runSat", p.get("runSat"), False)
    t.check("intradayTarget", p.get("intradayTarget"), 1500)
    t.check("isEnableMasterSl", p.get("isEnableMasterSl"), False)
    t.check("tradingStartTime", p.get("tradingStartTime"), "09:20:00")
    return t

add_test("PROMPT 12",
    "Nifty weekly straddle, sell ATM CE+PE, intraday, 1 lot. Only trade on Monday, Wednesday and Friday. Enable VIX filter: trade only when VIX is between 12 and 20. Master target 1500, no SL. Start 9:20.",
    validate_12)


# ── PROMPT 13 ─────────────────────────────────────────────────────────────────
def validate_13(p, r):
    t = TestResult("PROMPT 13 – Master Reexecution Target + SL")
    t.check("intradayTarget", p.get("intradayTarget"), 2000)
    t.check("noOfIntradayCycle", p.get("noOfIntradayCycle"), 3)
    t.check("intradayCycleDelay", p.get("intradayCycleDelay"), 15)
    t.check("intradaySl", p.get("intradaySl"), 1200)
    t.check("noOfReexecuteOnSl", p.get("noOfReexecuteOnSl"), 2)
    t.check("reexecuteDelayOnSl", p.get("reexecuteDelayOnSl"), 20)
    t.check("tradingStartTime", p.get("tradingStartTime"), "09:20:00")
    return t

add_test("PROMPT 13",
    "BankNifty straddle sell ATM CE PE weekly intraday 1 lot. Master target 2000, on target hit reexecute max 3 times with 15 second delay. Master SL 1200, on SL hit reexecute max 2 times with 20 second delay. Start 9:20.",
    validate_13)


# ── PROMPT 14 ─────────────────────────────────────────────────────────────────
def validate_14(p, r):
    t = TestResult("PROMPT 14 – Safety Switches + Required Margin")
    t.check("sqroffAllLegs", p.get("sqroffAllLegs"), True)
    t.check("pauseAndSqroffTradingOnMarginExeed", p.get("pauseAndSqroffTradingOnMarginExeed"), True)
    t.check("enableTpSlOnPauseStrategy", p.get("enableTpSlOnPauseStrategy"), True)
    t.check("requiredMargin", p.get("requiredMargin"), 125000)
    t.check("intradayTarget", p.get("intradayTarget"), 2500)
    t.check("leg_count", len(p.get("legs", [])), 4)
    return t

add_test("PROMPT 14",
    "BankNifty iron condor weekly intraday. Sell CE ATM+200, Sell PE ATM-200, Buy CE ATM+400, Buy PE ATM-400. 1 lot each. Enable: square off all legs if any single leg hits TP/SL, square off on order rejection, and keep TP/SL monitoring even when strategy is paused. Set required margin 125000. Master target 2500.",
    validate_14)


# ── PROMPT 15 ─────────────────────────────────────────────────────────────────
def validate_15(p, r):
    t = TestResult("PROMPT 15 – Theta-Based Strike + Target/SL by Point%")
    l1, l2 = leg(p,1), leg(p,2)
    t.check("leg1.atmType", l1.get("atmType"), "Strike By Theta Range")
    t.check("leg1.premiumStartRange", l1.get("premiumStartRange"), 5)
    t.check("leg1.premiumEndRange", l1.get("premiumEndRange"), 15)
    t.check("leg1.strikeDirection", l1.get("strikeDirection"), "OTM")
    t.check("leg1.optionType", l1.get("optionType"), "CE")
    t.check("leg2.atmType", l2.get("atmType"), "Strike By Nearest Theta")
    t.check("leg2.atm", l2.get("atm"), 10)
    t.check("leg2.strikeCondition", l2.get("strikeCondition"), "BelowEqual (<=)")
    t.check("leg2.strikeDirection", l2.get("strikeDirection"), "OTM")
    t.check("leg1.targetBy", l1.get("targetBy"), "Target by Point (%)")
    t.check("leg1.target", l1.get("target"), 40)
    t.check("leg1.slBy", l1.get("slBy"), "SL by Point (%)")
    t.check("leg1.sl", l1.get("sl"), 60)
    t.check("leg2.targetBy", l2.get("targetBy"), "Target by Point (%)")
    t.check("leg2.slBy", l2.get("slBy"), "SL by Point (%)")
    return t

add_test("PROMPT 15",
    "Sell BankNifty CE weekly where theta is between 5 and 15, OTM direction. Sell PE nearest theta 10, condition below-equal, OTM. Set leg target at 40% of entry price and leg SL at 60% of entry price. 1 lot each, intraday, start 9:25.",
    validate_15)


# ── PROMPT 16 ─────────────────────────────────────────────────────────────────
def validate_16(p, r):
    t = TestResult("PROMPT 16 – ATM% Strike + Delta/Theta TP/SL + FUT Leg")
    l1, l2 = leg(p,1), leg(p,2)
    t.check("leg1.atmType", l1.get("atmType"), "Strike By ATM %")
    t.check("leg1.atm", float(l1.get("atm", 0)), 0.5)   # float atm is accepted
    t.check("leg1.targetBy", l1.get("targetBy"), "Target by Delta")
    t.check("leg1.target", l1.get("target"), 1)          # 0.2 → ceil → 1 (API int-only)
    t.check("leg1.slBy", l1.get("slBy"), "SL by Theta")
    t.check("leg1.sl", l1.get("sl"), 8)                  # 8.0 → int → 8
    t.check("leg2.segment", l2.get("segment"), "FUT")
    t.check("leg2.tradeSide", l2.get("tradeSide"), "BUY")
    t.check("leg2.expiry", l2.get("expiry"), "Current Month")
    t.check("intradayTarget", p.get("intradayTarget"), 3000)
    return t

add_test("PROMPT 16",
    "Nifty strategy: Leg 1 — Sell CE at ATM% 0.50 OTM weekly, target by delta 0.2, SL by theta 8. Leg 2 — Buy 1 lot Nifty Futures current month as hedge. Intraday, 1 lot each. Master target 3000.",
    validate_16)


# ── PROMPT 17 ─────────────────────────────────────────────────────────────────
def validate_17(p, r):
    t = TestResult("PROMPT 17 – Ratio Spread + Master SL Trailing")
    l1, l2, l3, l4 = leg(p,1), leg(p,2), leg(p,3), leg(p,4)
    t.check("leg1.tradeSide SELL CE", (l1.get("tradeSide"), l1.get("optionType")), ("SELL","CE"))
    t.check("leg1.lot", l1.get("lot"), 2)
    t.check("leg1.atm", l1.get("atm"), 0)
    t.check("leg2.tradeSide BUY CE", (l2.get("tradeSide"), l2.get("optionType")), ("BUY","CE"))
    t.check("leg2.lot", l2.get("lot"), 1)
    t.check("leg2.atm", l2.get("atm"), 300)
    t.check("leg3.tradeSide SELL PE", (l3.get("tradeSide"), l3.get("optionType")), ("SELL","PE"))
    t.check("leg3.lot", l3.get("lot"), 2)
    t.check("leg3.atm", l3.get("atm"), 0)
    t.check("leg4.tradeSide BUY PE", (l4.get("tradeSide"), l4.get("optionType")), ("BUY","PE"))
    t.check("leg4.lot", l4.get("lot"), 1)
    t.check("leg4.atm", l4.get("atm"), -300)
    t.check("intradayTarget", p.get("intradayTarget"), 4000)
    t.check("intradaySl", p.get("intradaySl"), 2500)
    t.check("isEnableStoplossTrailing", p.get("isEnableStoplossTrailing"), True)
    t.check("profitMove", p.get("profitMove"), 1500)
    t.check("slMove", p.get("slMove"), 700)
    t.check("noOfTrailSl", p.get("noOfTrailSl"), 4)
    return t

add_test("PROMPT 17",
    "BankNifty ratio spread weekly intraday: Sell 2 lots ATM CE, Buy 1 lot CE ATM+300 as hedge. Sell 2 lots ATM PE, Buy 1 lot PE ATM-300 as hedge. Master target 4000, master SL 2500. Trail master SL: increase profit by 1500 trail SL by 700, max 4 times. Start 9:20.",
    validate_17)


# ── PROMPT 18 ─────────────────────────────────────────────────────────────────
def validate_18(p, r):
    t = TestResult("PROMPT 18 – Calendar Spread Multi-Expiry + Nearest Premium")
    l1, l2 = leg(p,1), leg(p,2)
    t.check("leg1.atmType", l1.get("atmType"), "Strike By Nearest Premium")
    t.check("leg1.premiumStartRange", l1.get("premiumStartRange"), 200)  # premium amount → premiumStartRange
    t.check("leg1.atm", l1.get("atm"), 0)                                # atm must be 0 for Nearest Premium
    t.check("leg1.strikeDirection", l1.get("strikeDirection"), "BOTH")
    t.check("leg1.strikeCondition", l1.get("strikeCondition"), "Any")
    t.check("leg1.expiry", l1.get("expiry"), "Current Week")
    t.check("leg1.tradeSide", l1.get("tradeSide"), "SELL")
    t.check("leg2.atmType", l2.get("atmType"), "Strike By Nearest Premium")
    t.check("leg2.premiumStartRange", l2.get("premiumStartRange"), 200)  # premium amount → premiumStartRange
    t.check("leg2.atm", l2.get("atm"), 0)                                # atm must be 0 for Nearest Premium
    t.check("leg2.strikeDirection", l2.get("strikeDirection"), "BOTH")
    t.check("leg2.strikeCondition", l2.get("strikeCondition"), "Any")
    t.check("leg2.expiry", l2.get("expiry"), "Month 1")
    t.check("leg2.tradeSide", l2.get("tradeSide"), "BUY")
    t.check("isEnableMasterTarget", p.get("isEnableMasterTarget"), False)
    t.check("isEnableMasterSl", p.get("isEnableMasterSl"), False)
    return t

add_test("PROMPT 18",
    "Nifty calendar spread. Sell CE nearest premium 200 current week expiry, direction BOTH, condition any. Buy CE nearest premium 200 next month expiry, direction BOTH, condition any. 1 lot each, intraday, no master target or SL.",
    validate_18)


# ── PROMPT 19 ─────────────────────────────────────────────────────────────────
def validate_19(p, r):
    t = TestResult("PROMPT 19 – BFO Exchange + Master Target by Combined Premium + Wait & Trade pts")
    t.check("mainExchange", p.get("mainExchange"), "BFO")
    t.check("mainSymbol", p.get("mainSymbol"), "SENSEX")
    t.check("tradingStartTime", p.get("tradingStartTime"), "09:20:00")
    t.check("tradingEndTime", p.get("tradingEndTime"), "15:00:00")
    l1 = leg(p,1)
    t.check("leg1.isWaitAndTrade", l1.get("isWaitAndTrade"), True)
    t.check("leg1.waitFor", l1.get("waitFor"), "Up pts")
    t.check("leg1.waitValue", int(l1.get("waitValue", 0)), 100)
    t.check("targetBy (Combined Premium)", p.get("targetBy"), "Combined Premium")
    t.check("intradayTarget", p.get("intradayTarget"), 150)
    t.check("slBy", p.get("slBy"), "Combined Loss")
    t.check("intradaySl", p.get("intradaySl"), 3000)
    return t

add_test("PROMPT 19",
    "Create strategy on BSE exchange (BFO), SENSEX symbol, weekly expiry. Sell CE ATM and PE ATM, 1 lot each. Leg 1 should wait for underlying to move up 100 points before entering. Master target by combined premium, target value 150. Master SL by combined loss, SL value 3000. Intraday, start 9:20, sqroff 15:00.",
    validate_19)


# ── PROMPT 20 ─────────────────────────────────────────────────────────────────
def validate_20(p, r):
    t = TestResult("PROMPT 20 – Maximum Complexity (ALL Parameters)")
    # Main
    t.check("mainSymbol", p.get("mainSymbol"), "BANKNIFTY")
    t.check("isIntraday", p.get("isIntraday"), False)
    t.check("productType", p.get("productType"), "NRML")
    t.check("tradingStartTime", p.get("tradingStartTime"), "09:20:00")
    t.check("isRangeBreakOut", p.get("isRangeBreakOut"), True)
    t.check("rangeEndTime", p.get("rangeEndTime"), "09:25:00")
    t.check("isBtstStbt", p.get("isBtstStbt"), True)
    t.check("btstGapDays", p.get("btstGapDays"), 3)
    t.check("isCombinedPremEntry", p.get("isCombinedPremEntry"), True)
    t.check("totalCombinedPremium", p.get("totalCombinedPremium"), 280)
    # Legs structure
    t.check("leg_count", len(p.get("legs", [])), 4)
    l1, l2, l3, l4 = leg(p,1), leg(p,2), leg(p,3), leg(p,4)
    t.check("leg1.atmType", l1.get("atmType"), "Strike By Premium Range")
    t.check("leg1.premiumStartRange", l1.get("premiumStartRange"), 120)
    t.check("leg1.premiumEndRange", l1.get("premiumEndRange"), 180)
    t.check("leg1.strikeDirection", l1.get("strikeDirection"), "OTM")
    t.check("leg1.lot", l1.get("lot"), 2)
    t.check("leg1.isIdle", l1.get("isIdle"), False)
    t.check("leg1.isProfitLockingAndTrailing", l1.get("isProfitLockingAndTrailing"), True)
    t.check("leg1.ifProfitReaches", l1.get("ifProfitReaches"), 3000)
    t.check("leg1.lockMinimumProfit", l1.get("lockMinimumProfit"), 1500)
    t.check("leg1.isEnableStoplossTrailing", l1.get("isEnableStoplossTrailing"), True)
    t.check("leg1.trailSlMarketMove", l1.get("trailSlMarketMove"), 1000)
    t.check("leg1.trailSlMove", l1.get("trailSlMove"), 400)
    t.check("leg1.noOfTimeTrailSl", l1.get("noOfTimeTrailSl"), 3)
    t.check("leg1.actionOnTarget", l1.get("actionOnTarget"), "Execute Leg")
    t.check("leg1.actionOnTargetLegNo", l1.get("actionOnTargetLegNo"), 5)   # swapped: holds delay
    t.check("leg1.actionOnTargetDelay", l1.get("actionOnTargetDelay"), 3)   # swapped: holds leg no
    t.check("leg1.actionOnSl", l1.get("actionOnSl"), "Sqroff Leg")
    t.check("leg1.actionOnSlLegNo", l1.get("actionOnSlLegNo"), 2)           # swapped: holds delay
    t.check("leg1.actionOnSlDelay", l1.get("actionOnSlDelay"), 2)           # swapped: holds leg no
    t.check("leg2.atmType", l2.get("atmType"), "Strike By Nearest Delta")
    t.check("leg2.atm", l2.get("atm"), 0.25)
    t.check("leg2.strikeCondition", l2.get("strikeCondition"), "AboveEqual (>=)")
    t.check("leg2.strikeDirection", l2.get("strikeDirection"), "OTM")
    t.check("leg2.lot", l2.get("lot"), 2)
    t.check("leg3.isIdle", l3.get("isIdle"), True)
    t.check("leg3.tradeSide", l3.get("tradeSide"), "BUY")
    t.check("leg4.isIdle", l4.get("isIdle"), True)
    t.check("leg4.tradeSide", l4.get("tradeSide"), "BUY")
    # Advance – Master Target
    t.check("intradayTarget", p.get("intradayTarget"), 6000)
    t.check("targetBy", p.get("targetBy"), "Combined Profit")
    t.check("noOfIntradayCycle", p.get("noOfIntradayCycle"), 2)
    t.check("intradayCycleDelay", p.get("intradayCycleDelay"), 10)
    t.check("intradaySl", p.get("intradaySl"), 4000)
    t.check("noOfReexecuteOnSl", p.get("noOfReexecuteOnSl"), 1)
    t.check("reexecuteDelayOnSl", p.get("reexecuteDelayOnSl"), 15)
    # Master profit locking
    t.check("ifProfitReaches", p.get("ifProfitReaches"), 4000)
    t.check("lockMinimumProfit", p.get("lockMinimumProfit"), 2000)
    t.check("increseInProfitBy", p.get("increseInProfitBy"), 600)
    t.check("trailProfitBy", p.get("trailProfitBy"), 300)
    t.check("noOfTimeTrailTp", p.get("noOfTimeTrailTp"), 5)
    # Master SL trailing
    t.check("profitMove", p.get("profitMove"), 2000)
    t.check("slMove", p.get("slMove"), 800)
    t.check("noOfTrailSl", p.get("noOfTrailSl"), 3)
    # Pre-expiry
    t.check("isEnableSqroffBeforeExpiryDays", p.get("isEnableSqroffBeforeExpiryDays"), True)
    t.check("sqroffBeforeExpiryDays", p.get("sqroffBeforeExpiryDays"), 2)
    t.check("sqroffTime", p.get("sqroffTime"), "15:00:00")
    # Working days
    t.check("runMon", p.get("runMon"), True)
    t.check("runTue", p.get("runTue"), True)
    t.check("runWed", p.get("runWed"), True)
    t.check("runThu", p.get("runThu"), True)
    t.check("runFri", p.get("runFri"), False)
    # VIX
    t.check("enableVixFilter", p.get("enableVixFilter"), True)
    t.check("vixStartValue", p.get("vixStartValue"), 11)
    t.check("vixEndValue", p.get("vixEndValue"), 19)
    # Safety switches
    t.check("sqroffAllLegs", p.get("sqroffAllLegs"), True)
    t.check("pauseAndSqroffTradingOnMarginExeed", p.get("pauseAndSqroffTradingOnMarginExeed"), True)
    t.check("enableTpSlOnPauseStrategy", p.get("enableTpSlOnPauseStrategy"), True)
    t.check("requiredMargin", p.get("requiredMargin"), 200000)
    # Descriptions
    t.check_contains("shortDescription", p.get("shortDescription",""), "Full hedge")
    t.check_contains("detailedDescription", p.get("detailedDescription",""), "positional")
    return t

add_test("PROMPT 20",
    """Create a positional BankNifty strategy called 'Full Hedge Machine' on NFO, NRML product, monthly expiry.

Leg 1: Sell CE at premium range 120-180, OTM, 2 lots. Target 50 points, SL 80 points. Profit locking: if reaches 3000 lock 1500, trail by 200 every 500 increase, max 4 times. SL trailing: increase 1000 trail SL by 400, 3 times. On target execute Leg 3 after 5 sec. On SL sqroff Leg 2 after 2 sec.

Leg 2: Sell PE at nearest delta 0.25, above-equal, OTM, 2 lots. Target 50 points, SL 80 points.

Leg 3: idle, Buy CE ATM+500, 1 lot. No TP/SL.

Leg 4: idle, Buy PE ATM-500, 1 lot. No TP/SL.

Entry only when combined premium reaches 280. Enable range breakout with range end time 9:25. Enable VIX filter 11 to 19. Trade only Mon, Tue, Wed, Thu. Start 9:20.

Master target 6000 (combined profit), reexecute 2 times with 10 sec delay. Master SL 4000, reexecute 1 time with 15 sec delay. Master profit locking: if reaches 4000 lock 2000, trail 300 every 600, max 5. Master SL trailing: increase 2000 trail SL 800, max 3.

Enable BTST 3 gap days. Pre-expiry sqroff 2 days before at 15:00. Enable sqroff all legs on any TP/SL. Enable sqroff on rejection. Enable TP/SL monitoring on pause. Required margin 200000.

Short description: 'Full hedge positional BNF with premium + VIX control.' Detailed description: 'Multi-leg positional BankNifty hedge using premium range + delta strikes, idle leg execution chaining, master MTM control with profit locking and SL trailing, VIX and day filtering, pre-expiry exit.'""",
    validate_20)


# ─────────────────────────────────────────────────────────────────────────────
# Main runner
# ─────────────────────────────────────────────────────────────────────────────
def run_all():
    overall_pass = 0
    overall_fail = 0
    all_results = []

    print("\n" + "="*70)
    print("  UNIFIED STRATEGY BUILDER — AUTOMATED TEST SUITE")
    print("  20 Prompts × Full Payload Validation")
    print("="*70)

    deploy_ok_count = 0
    deploy_fail_count = 0

    for idx, (name, prompt, validator_fn) in enumerate(TESTS, 1):
        print(f"\n{'─'*70}")
        print(f"▶  Running {name} ...")

        session_id = f"autotest_{idx}_{int(time.time())}"
        before = last_log_count()

        # Step 1: Send the strategy prompt
        print("  → Sending strategy prompt ...")
        ai_preview = chat(prompt, session_id)

        # Step 2: Confirm deployment
        print("  → Confirming deployment ...")
        ai_final = chat("yes proceed deploy it", session_id)

        # Step 3: Wait and grab log entry (written only AFTER API call)
        time.sleep(2)
        payload, api_status, api_code, api_response = get_last_log_entry(before)

        if not payload:
            print(f"  ⚠️  NO LOG ENTRY — trying one more confirm ...")
            chat("yes confirm deploy", session_id)
            time.sleep(2)
            payload, api_status, api_code, api_response = get_last_log_entry(before)

        if not payload:
            print(f"  ❌ SKIPPED — deployment did not occur\n")
            result = TestResult(name)
            result.failed.append("  ❌ No payload logged — deployment did not trigger")
            all_results.append(result)
            overall_pass_deploy = False
            overall_fail += 1
            deploy_fail_count += 1
            continue

        # Step 4: Show real Market Maya API result
        if api_status == "success" and api_code == 200:
            print(f"  🟢 Market Maya: HTTP {api_code} — DEPLOYED SUCCESSFULLY")
            deploy_ok_count += 1
        else:
            print(f"  🔴 Market Maya: HTTP {api_code} — FAILED: {str(api_response)[:200]}")
            deploy_fail_count += 1

        # Step 5: Validate payload structure
        result = validator_fn(payload, ai_final)

        # Add deployment status as an explicit check
        if api_status == "success" and api_code == 200:
            result.passed.insert(0, f"  ✅ Market Maya deployment: HTTP {api_code} SUCCESS")
        else:
            result.failed.insert(0, f"  ❌ Market Maya deployment: HTTP {api_code} — {str(api_response)[:150]}")

        result.print_report()
        all_results.append(result)

        status, p, total = result.summary()
        if status == "PASS":
            overall_pass += 1
        else:
            overall_fail += 1

        time.sleep(3)

    # ── Final summary ────────────────────────────────────────────────────────
    print("\n" + "="*70)
    print(f"  FINAL RESULTS: {overall_pass} PASSED / {overall_fail} FAILED out of {len(TESTS)} tests")
    print(f"  Market Maya Deployments: {deploy_ok_count} SUCCESS / {deploy_fail_count} FAILED")
    print("="*70)

    total_checks_pass = sum(len(r.passed) for r in all_results)
    total_checks_fail = sum(len(r.failed) for r in all_results)
    total_checks = total_checks_pass + total_checks_fail
    print(f"  Individual checks: {total_checks_pass}/{total_checks} passed\n")

    if overall_fail > 0:
        print("  FAILED TESTS:")
        for r in all_results:
            if r.failed:
                print(f"\n  ► {r.name}")
                for f in r.failed:
                    print(f)

    # Save report
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, "w") as f:
        f.write(f"Test Run: {datetime.now().isoformat()}\n")
        f.write(f"Results: {overall_pass}/{len(TESTS)} tests passed, {total_checks_pass}/{total_checks} checks passed\n\n")
        for r in all_results:
            status, p, total = r.summary()
            f.write(f"\n{'='*60}\n{r.name}  [{status}] [{p}/{total}]\n")
            for line in r.passed:
                f.write(line + "\n")
            for line in r.failed:
                f.write(line + "\n")
    print(f"\n  Full report saved to: {report_file}")


if __name__ == "__main__":
    run_all()
