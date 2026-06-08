"""
Multi-Leg Hedger – Automated End-to-End Test Runner
20 prompts covering every parameter and every meaningful combination.
Sends natural-language prompts → LLM → deployed payload → validates against expected values.
No mocks. Reads the real deployed payload from logs/saved_strategies.log.
"""
import requests
import json
import time
import os
from datetime import datetime

BASE_URL = "http://localhost:8000/hedger/api/chat"
LOG_FILE = "logs/saved_strategies.log"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def chat(message, session_id):
    try:
        r = requests.post(BASE_URL, json={"message": message, "session_id": session_id}, timeout=180)
        r.raise_for_status()
        return r.json().get("message", "")
    except Exception as e:
        return f"ERROR: {e}"


def last_mlh_log_count():
    if not os.path.exists(LOG_FILE):
        return 0
    count = 0
    with open(LOG_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("strategy_type") == "multi_leg_hedger":
                    count += 1
            except Exception:
                pass
    return count


def get_last_mlh_log_entry(before_count):
    if not os.path.exists(LOG_FILE):
        return None, None, None, None
    mlh_entries = []
    with open(LOG_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("strategy_type") == "multi_leg_hedger":
                    mlh_entries.append(entry)
            except Exception:
                pass
    if len(mlh_entries) <= before_count:
        return None, None, None, None
    entry = mlh_entries[-1]
    return (
        entry.get("payload"),
        entry.get("api_status"),
        entry.get("api_code"),
        entry.get("api_response"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Validation framework
# ─────────────────────────────────────────────────────────────────────────────
class TestResult:
    def __init__(self, name):
        self.name = name
        self.passed = []
        self.failed = []

    def check(self, label, actual, expected):
        if actual == expected:
            self.passed.append(f"  ✅ {label}: {actual!r}")
        else:
            self.failed.append(f"  ❌ {label}: expected={expected!r}, got={actual!r}")

    def check_in(self, label, actual, expected_set):
        if actual in expected_set:
            self.passed.append(f"  ✅ {label}: {actual!r}")
        else:
            self.failed.append(f"  ❌ {label}: expected one of {expected_set}, got={actual!r}")

    def check_gt(self, label, actual, min_val):
        try:
            if float(actual) > float(min_val):
                self.passed.append(f"  ✅ {label}: {actual} > {min_val}")
            else:
                self.failed.append(f"  ❌ {label}: expected > {min_val}, got={actual!r}")
        except Exception:
            self.failed.append(f"  ❌ {label}: cannot compare {actual!r} > {min_val}")

    def check_gte(self, label, actual, min_val):
        try:
            if float(actual) >= float(min_val):
                self.passed.append(f"  ✅ {label}: {actual} >= {min_val}")
            else:
                self.failed.append(f"  ❌ {label}: expected >= {min_val}, got={actual!r}")
        except Exception:
            self.failed.append(f"  ❌ {label}: cannot compare {actual!r} >= {min_val}")

    def check_none(self, label, actual):
        if actual is None:
            self.passed.append(f"  ✅ {label}: None")
        else:
            self.failed.append(f"  ❌ {label}: expected None, got={actual!r}")

    def check_contains(self, label, actual, substring):
        if substring.lower() in str(actual).lower():
            self.passed.append(f"  ✅ {label} contains '{substring}'")
        else:
            self.failed.append(f"  ❌ {label}: expected to contain '{substring}', got={actual!r}")

    def check_nonempty(self, label, actual):
        if actual and str(actual).strip():
            self.passed.append(f"  ✅ {label} non-empty: {str(actual)[:60]!r}")
        else:
            self.failed.append(f"  ❌ {label}: expected non-empty, got={actual!r}")

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


def sleg(p, n):
    """Return nth leg (1-indexed) from payload's sub array."""
    legs = p.get("sub", [])
    return legs[n - 1] if len(legs) >= n else {}


# ─────────────────────────────────────────────────────────────────────────────
# 20 Test cases
# ─────────────────────────────────────────────────────────────────────────────
TESTS = []

def add_test(name, prompt, validator_fn):
    TESTS.append((name, prompt, validator_fn))


# ── PROMPT 1 ──────────────────────────────────────────────────────────────────
# Covers: Normal mode, BankNifty, Intraday MIS, SELL CE+PE ATM, weekly,
#         master target + master SL by Money, fixed invariants
# ─────────────────────────────────────────────────────────────────────────────
def validate_1(p, r):
    t = TestResult("PROMPT 1 — BankNifty Short Straddle, Intraday MIS, Master Target+SL")
    t.check("symbol",       p.get("symbol"),       "BANKNIFTY")
    t.check("exchange",     p.get("exchange"),      "NFO")
    t.check("isIntraday",   p.get("isIntraday"),    True)
    t.check("productType",  p.get("productType"),   "MIS")
    t.check("underlying",   p.get("underlying"),    "BANKNIFTY FUT NFO")
    t.check("target",       float(p.get("target", 0)), 5000.0)
    t.check("sl",           float(p.get("sl", 0)),    3000.0)
    t.check("is_btst_stbt",      p.get("is_btst_stbt"),      False)
    t.check("is_range_break_out",p.get("is_range_break_out"),False)
    l1, l2 = sleg(p, 1), sleg(p, 2)
    t.check("l1.tradeSide",  l1.get("tradeSide"),  "SELL")
    t.check("l1.optionType", l1.get("optionType"), "CE")
    t.check("l1.segment",    l1.get("segment"),    "OPT")
    t.check("l1.atm",        l1.get("atm"),        0)
    t.check("l1.lot",        l1.get("lot"),        1)
    t.check("l1.qty",        l1.get("qty"),        30)   # BANKNIFTY=30
    t.check("l1.expiry",     l1.get("expiry"),     "WEEKLY")
    t.check("l2.tradeSide",  l2.get("tradeSide"),  "SELL")
    t.check("l2.optionType", l2.get("optionType"), "PE")
    t.check("l2.atm",        l2.get("atm"),        0)
    t.check("l2.qty",        l2.get("qty"),        30)
    # Fixed invariants
    t.check_none("l1.product",       l1.get("product"))
    t.check("l1.workingDay",         l1.get("workingDay"),        "ALL")
    t.check("l1.qty_distribution",   l1.get("qty_distribution"),  "Fix")
    return t

add_test("PROMPT 1",
    "Create a BankNifty intraday short straddle. Sell ATM CE and ATM PE, current week expiry, 1 lot each. Master target 5000, master SL 3000. Both by Money. Start at 9:20, exit at 15:15.",
    validate_1)


# ── PROMPT 2 ──────────────────────────────────────────────────────────────────
# Covers: Nifty, ATM offset (strangle), per-leg target/SL, 2 lots, no master TP/SL
# ─────────────────────────────────────────────────────────────────────────────
def validate_2(p, r):
    t = TestResult("PROMPT 2 — Nifty Strangle, Per-Leg Target/SL, ATM Offset, 2 Lots")
    t.check("symbol",    p.get("symbol"),   "NIFTY")
    t.check("exchange",  p.get("exchange"), "NFO")
    l1, l2 = sleg(p, 1), sleg(p, 2)
    t.check("l1.optionType", l1.get("optionType"), "CE")
    t.check("l1.tradeSide",  l1.get("tradeSide"),  "SELL")
    t.check("l1.lot",        l1.get("lot"),        2)
    t.check("l1.qty",        l1.get("qty"),        130)   # NIFTY=65 * 2
    t.check_gte("l1.atm OTM (CE)", l1.get("atm", 0), 100)   # some positive offset
    t.check("l1.target", float(l1.get("target", 0)), 2000.0)
    t.check("l1.sl",     float(l1.get("sl", 0)),     1500.0)
    t.check("l2.optionType", l2.get("optionType"), "PE")
    t.check("l2.tradeSide",  l2.get("tradeSide"),  "SELL")
    t.check("l2.lot",        l2.get("lot"),        2)
    t.check("l2.qty",        l2.get("qty"),        130)
    t.check_gte("l2.atm OTM (PE)", -(l2.get("atm", 0) or 0), 100)  # some negative atm
    t.check("l2.target", float(l2.get("target", 0)), 2000.0)
    t.check("l2.sl",     float(l2.get("sl", 0)),     1500.0)
    # No master target/SL (both 0)
    t.check("master target disabled", float(p.get("target", 0)), 0.0)
    t.check("master sl disabled",     float(p.get("sl", 0)),     0.0)
    return t

add_test("PROMPT 2",
    "Create a Nifty strangle. Sell CE at ATM+200 (OTM) and Sell PE at ATM-200 (OTM), 2 lots each, current week expiry, intraday MIS. Per-leg target 2000 and per-leg SL 1500 (both by Money). No master target or master SL.",
    validate_2)


# ── PROMPT 3 ──────────────────────────────────────────────────────────────────
# Covers: 4-leg Iron Condor, BUY+SELL mix, correct ATM offsets per leg
# ─────────────────────────────────────────────────────────────────────────────
def validate_3(p, r):
    t = TestResult("PROMPT 3 — BankNifty Iron Condor, 4 Legs, Master Target")
    t.check("symbol",     p.get("symbol"),      "BANKNIFTY")
    t.check("leg_count",  len(p.get("sub", [])), 4)
    l1, l2, l3, l4 = sleg(p,1), sleg(p,2), sleg(p,3), sleg(p,4)
    t.check("l1 SELL CE",     (l1.get("tradeSide"), l1.get("optionType")), ("SELL","CE"))
    t.check("l1.atm OTM CE",  l1.get("atm"),  300)
    t.check("l2 SELL PE",     (l2.get("tradeSide"), l2.get("optionType")), ("SELL","PE"))
    t.check("l2.atm OTM PE",  l2.get("atm"),  -300)
    t.check("l3 BUY CE",      (l3.get("tradeSide"), l3.get("optionType")), ("BUY","CE"))
    t.check("l3.atm",         l3.get("atm"),   500)
    t.check("l4 BUY PE",      (l4.get("tradeSide"), l4.get("optionType")), ("BUY","PE"))
    t.check("l4.atm",         l4.get("atm"),  -500)
    for i, l in enumerate([l1,l2,l3,l4], 1):
        t.check(f"l{i}.lot=1",    l.get("lot"),    1)
        t.check(f"l{i}.qty=30",   l.get("qty"),    30)
        t.check(f"l{i}.expiry",   l.get("expiry"), "WEEKLY")
    t.check("master target", float(p.get("target", 0)), 4000.0)
    t.check("master sl=0",   float(p.get("sl", 0)),     0.0)
    return t

add_test("PROMPT 3",
    "Build a BankNifty iron condor, weekly expiry, intraday, 1 lot each. Sell CE at ATM+300 and Sell PE at ATM-300. Buy CE at ATM+500 and Buy PE at ATM-500. Set master target 4000 by Money. No master SL.",
    validate_3)


# ── PROMPT 4 ──────────────────────────────────────────────────────────────────
# Covers: Range Breakout mode, range_time, per-leg range_breakout_direction High+Low
# ─────────────────────────────────────────────────────────────────────────────
def validate_4(p, r):
    t = TestResult("PROMPT 4 — Range Breakout Mode, Direction High+Low per Leg")
    t.check("is_range_break_out", p.get("is_range_break_out"), True)
    t.check("is_btst_stbt",       p.get("is_btst_stbt"),       False)
    t.check("isIntraday",         p.get("isIntraday"),          True)
    t.check("range_time",         p.get("range_time"),         "09:30")
    l1, l2 = sleg(p, 1), sleg(p, 2)
    t.check("l1.optionType CE",             l1.get("optionType"),             "CE")
    t.check("l1.range_breakout_direction",  l1.get("range_breakout_direction"),"High")
    t.check("l1.tradeSide BUY",             l1.get("tradeSide"),              "BUY")
    t.check("l2.optionType PE",             l2.get("optionType"),             "PE")
    t.check("l2.range_breakout_direction",  l2.get("range_breakout_direction"),"Low")
    t.check("l2.tradeSide BUY",             l2.get("tradeSide"),              "BUY")
    return t

add_test("PROMPT 4",
    "Create a BankNifty Range Breakout strategy. Range formation candle starts at 9:15 and ends at 9:30. Leg 1: Buy CE ATM, execute on High breakout. Leg 2: Buy PE ATM, execute on Low breakout. 1 lot each, weekly expiry. Master target 3000.",
    validate_4)


# ── PROMPT 5 ──────────────────────────────────────────────────────────────────
# Covers: BTST/STBT mode forces isIntraday=False, productType=NRML
# ─────────────────────────────────────────────────────────────────────────────
def validate_5(p, r):
    t = TestResult("PROMPT 5 — BTST/STBT Mode Forces NRML and Not Intraday")
    t.check("is_btst_stbt",       p.get("is_btst_stbt"),       True)
    t.check("is_range_break_out", p.get("is_range_break_out"), False)
    t.check("isIntraday",         p.get("isIntraday"),          False)
    t.check("productType",        p.get("productType"),         "NRML")
    t.check("symbol",             p.get("symbol"),              "NIFTY")
    l1, l2 = sleg(p, 1), sleg(p, 2)
    t.check("l1.optionType CE", l1.get("optionType"), "CE")
    t.check("l1.tradeSide",     l1.get("tradeSide"),  "SELL")
    t.check("l2.optionType PE", l2.get("optionType"), "PE")
    t.check("l2.tradeSide",     l2.get("tradeSide"),  "SELL")
    t.check("master target", float(p.get("target", 0)), 8000.0)
    t.check("master sl",     float(p.get("sl", 0)),     5000.0)
    return t

add_test("PROMPT 5",
    "Create a Nifty BTST/STBT strategy. Sell ATM CE and ATM PE, monthly expiry, 1 lot each. Master target 8000 and master SL 5000 by Money. Exit next day at 15:15.",
    validate_5)


# ── PROMPT 6 ──────────────────────────────────────────────────────────────────
# Covers: FINNIFTY and MIDCPNIFTY lot sizes, multiple lots
# ─────────────────────────────────────────────────────────────────────────────
def validate_6(p, r):
    t = TestResult("PROMPT 6 — FINNIFTY lot size verification (lot=2 → qty=80)")
    t.check("symbol",   p.get("symbol"),   "FINNIFTY")
    t.check("exchange", p.get("exchange"), "NFO")
    l1, l2 = sleg(p, 1), sleg(p, 2)
    t.check("l1.lot",  l1.get("lot"),  2)
    t.check("l1.qty",  l1.get("qty"),  80)   # FINNIFTY=40 * 2
    t.check("l2.lot",  l2.get("lot"),  2)
    t.check("l2.qty",  l2.get("qty"),  80)
    t.check("l1.optionType CE", l1.get("optionType"), "CE")
    t.check("l2.optionType PE", l2.get("optionType"), "PE")
    return t

add_test("PROMPT 6",
    "Create a FINNIFTY intraday short straddle. Sell ATM CE and ATM PE, weekly expiry, 2 lots each. Master target 3000, master SL 2000. Start at 9:20.",
    validate_6)


# ── PROMPT 7 ──────────────────────────────────────────────────────────────────
# Covers: Wait-and-Trade — Up% and Down Pts on separate legs, disabled on third leg
# ─────────────────────────────────────────────────────────────────────────────
def validate_7(p, r):
    t = TestResult("PROMPT 7 — Wait-and-Trade: Up% active, Down Pts active, none disabled")
    t.check("symbol", p.get("symbol"), "BANKNIFTY")
    l1, l2, l3 = sleg(p, 1), sleg(p, 2), sleg(p, 3)
    # Leg 1: wait Up 0.5%
    t.check("l1.is_wait_and_trade",  l1.get("is_wait_and_trade"), True)
    t.check("l1.wait_for UP%",       l1.get("wait_for"),          "UP %")
    t.check("l1.wait_value",  float(l1.get("wait_value", 0)),     0.5)
    # Leg 2: wait Down 100 pts
    t.check("l2.is_wait_and_trade",  l2.get("is_wait_and_trade"), True)
    t.check("l2.wait_for Down Pts",  l2.get("wait_for"),          "Down Pts.")
    t.check("l2.wait_value",  float(l2.get("wait_value", 0)),     100.0)
    # Leg 3: no wait
    t.check("l3.is_wait_and_trade",  l3.get("is_wait_and_trade"), False)
    return t

add_test("PROMPT 7",
    "BankNifty intraday strategy with 3 legs: Leg 1 Sell CE ATM weekly 1 lot — wait for underlying to move UP 0.5% before entering. Leg 2 Sell PE ATM weekly 1 lot — wait for underlying to move Down 100 points before entering. Leg 3 Buy CE ATM+500 weekly 1 lot — enter immediately, no wait. Master target 4000, master SL 2500.",
    validate_7)


# ── PROMPT 8 ──────────────────────────────────────────────────────────────────
# Covers: Working days Mon/Wed/Fri only + VIX filter
# ─────────────────────────────────────────────────────────────────────────────
def validate_8(p, r):
    t = TestResult("PROMPT 8 — VIX Filter + Working Days Mon/Wed/Fri")
    t.check("enableVixFilter",  p.get("enableVixFilter"),  True)
    t.check("vixStartValue",    float(p.get("vixStartValue", 0)),   12.0)
    t.check("vixEndValue",      float(p.get("vixEndValue", 0)),     22.0)
    t.check("mon", p.get("mon"), True)
    t.check("tue", p.get("tue"), False)
    t.check("wed", p.get("wed"), True)
    t.check("thu", p.get("thu"), False)
    t.check("fri", p.get("fri"), True)
    t.check("sat", p.get("sat"), False)
    t.check("sun", p.get("sun"), False)
    t.check("isIntraday", p.get("isIntraday"), True)
    return t

add_test("PROMPT 8",
    "Nifty short straddle, sell ATM CE and PE, weekly, 1 lot, intraday MIS, start 9:20. Only trade on Monday, Wednesday, Friday. Enable VIX filter: trade only when VIX is between 12 and 22. Master target 2500, master SL 1500.",
    validate_8)


# ── PROMPT 9 ──────────────────────────────────────────────────────────────────
# Covers: Master Trail SL — isTrailSl, profitMove, slMove, noOfTrailSL, trail_sl_by
# ─────────────────────────────────────────────────────────────────────────────
def validate_9(p, r):
    t = TestResult("PROMPT 9 — Master Trail SL (Dynamic): profitMove, slMove, noOfTrailSL")
    t.check("isTrailSl",              p.get("isTrailSl"),             True)
    t.check("profitMove",      float( p.get("profitMove",  0)),       1000.0)
    t.check("slMove",          float( p.get("slMove",      0)),        500.0)
    t.check("noOfTrailSL",     int(   p.get("noOfTrailSL", 0)),        5)
    t.check("startTrailAfterProfit", float(p.get("startTrailAfterProfit", 0)), 2000.0)
    t.check("master target",   float( p.get("target",  0)),            6000.0)
    t.check("master sl",       float( p.get("sl",      0)),            3000.0)
    t.check("symbol",  p.get("symbol"),   "BANKNIFTY")
    return t

add_test("PROMPT 9",
    "BankNifty short straddle, sell ATM CE and PE, weekly, 1 lot, intraday. Master target 6000, master SL 3000. Enable master trail SL: start trailing after profit reaches 2000. For every 1000 profit increase, trail SL by 500, max 5 times.",
    validate_9)


# ── PROMPT 10 ─────────────────────────────────────────────────────────────────
# Covers: sqroff_all_legs → squareoffLegs + sqroffAllLegs both True,
#         squareoffRejection, cosider_closed_pnl, requiredMargin
# ─────────────────────────────────────────────────────────────────────────────
def validate_10(p, r):
    t = TestResult("PROMPT 10 — sqroffAllLegs, cosider_closed_pnl, requiredMargin")
    t.check("squareoffLegs",      p.get("squareoffLegs"),      False)
    t.check("sqroffAllLegs",      p.get("sqroffAllLegs"),      True)
    t.check("squareoffRejection", p.get("squareoffRejection"), True)
    t.check("cosider_closed_pnl", p.get("cosider_closed_pnl"), True)
    t.check("requiredMargin",  float(p.get("requiredMargin", 0)), 150000.0)
    t.check("leg_count",  len(p.get("sub", [])), 4)
    return t

add_test("PROMPT 10",
    "BankNifty iron condor, weekly, intraday. Sell CE ATM+300, Sell PE ATM-300, Buy CE ATM+500, Buy PE ATM-500, 1 lot each. Enable: square off all legs when any leg hits TP/SL. Enable square off on order rejection. Enable consider closed PnL in master TP/SL. Required margin 150000. Master target 3000.",
    validate_10)


# ── PROMPT 11 ─────────────────────────────────────────────────────────────────
# Covers: Positional NRML, is_intraday=False, sqroff_before_expiry_days, sqroffTime, monthly expiry
# ─────────────────────────────────────────────────────────────────────────────
def validate_11(p, r):
    t = TestResult("PROMPT 11 — Positional NRML, Pre-Expiry Sqroff, Monthly Expiry")
    t.check("isIntraday",    p.get("isIntraday"),    False)
    t.check("productType",   p.get("productType"),   "NRML")
    t.check("is_btst_stbt",  p.get("is_btst_stbt"),  False)
    t.check("sqroff_before_expiry_days", int(p.get("sqroff_before_expiry_days", 0)), 2)
    t.check("sqroffTime",    p.get("sqroffTime"),    "15:00")
    l1, l2 = sleg(p, 1), sleg(p, 2)
    t.check("l1.expiry MONTHLY", l1.get("expiry"), "MONTHLY")
    t.check("l2.expiry MONTHLY", l2.get("expiry"), "MONTHLY")
    t.check("master target", float(p.get("target", 0)), 10000.0)
    t.check("master sl",     float(p.get("sl", 0)),      6000.0)
    return t

add_test("PROMPT 11",
    "Create a positional BankNifty strategy with NRML product. Sell ATM CE and ATM PE, monthly expiry, 1 lot each. Square off 2 days before expiry at 15:00. Master target 10000, master SL 6000. Not intraday.",
    validate_11)


# ── PROMPT 12 ─────────────────────────────────────────────────────────────────
# Covers: Per-leg Trail SL — is_trail_sl, trail_sl_market_move, trail_sl_move,
#         no_of_time_trail_sl, trail_sl_by, trail_sl_cost
# ─────────────────────────────────────────────────────────────────────────────
def validate_12(p, r):
    t = TestResult("PROMPT 12 — Per-Leg Trail SL (market_move, sl_move, count, by)")
    l1, l2 = sleg(p, 1), sleg(p, 2)
    # CE leg: trail SL enabled
    t.check("l1.is_trail_sl",          l1.get("is_trail_sl"),          True)
    t.check("l1.trail_sl_market_move", float(l1.get("trail_sl_market_move", 0)), 500.0)
    t.check("l1.trail_sl_move",        float(l1.get("trail_sl_move", 0)),        200.0)
    t.check("l1.no_of_time_trail_sl",  int(l1.get("no_of_time_trail_sl", 0)),    3)
    t.check_in("l1.trail_sl_by",       l1.get("trail_sl_by"), {"Point", "Money", "Percentage(%)"})
    # PE leg: trail SL disabled
    t.check("l2.is_trail_sl False",    l2.get("is_trail_sl"),          False)
    return t

add_test("PROMPT 12",
    "Nifty short straddle intraday, sell ATM CE and PE, weekly, 1 lot each. For the CE leg: enable per-leg trail SL — for every 500 profit, trail SL by 200, max 3 times. For the PE leg: no trail SL. Master target 3000, master SL 2000.",
    validate_12)


# ── PROMPT 13 ─────────────────────────────────────────────────────────────────
# Covers: Per-leg Re-entry (reentry_on, no_of_reentry) +
#         Per-leg Re-execute (reexecute_on, no_of_reexecute, reexecute_delay)
# ─────────────────────────────────────────────────────────────────────────────
def validate_13(p, r):
    t = TestResult("PROMPT 13 — Per-Leg Re-entry + Re-execute")
    l1, l2 = sleg(p, 1), sleg(p, 2)
    # CE leg: re-entry on SL
    t.check("l1.reentry_on",    l1.get("reentry_on"),    "SL Only")
    t.check("l1.no_of_reentry", int(l1.get("no_of_reentry", 0)), 2)
    # PE leg: re-execute on Target, with delay
    t.check("l2.reexecute_on",    l2.get("reexecute_on"),    "TP Only")
    t.check("l2.no_of_reexecute", int(l2.get("no_of_reexecute", 0)), 3)
    t.check("l2.reexecute_delay", int(l2.get("reexecute_delay", 0)), 5)
    return t

add_test("PROMPT 13",
    "BankNifty intraday straddle, sell ATM CE and ATM PE, weekly, 1 lot each. For CE leg: re-enter 2 times when SL is hit (wait for price to return to entry). For PE leg: re-execute 3 times when target is hit, with 5 minute delay. Per-leg SL 1000 and target 800 by Money. No master TP/SL.",
    validate_13)


# ── PROMPT 14 ─────────────────────────────────────────────────────────────────
# Covers: Dynamic ATM type → atmType="Dynamic", premiumStartRange, premiumEndRange
# ─────────────────────────────────────────────────────────────────────────────
def validate_14(p, r):
    t = TestResult("PROMPT 14 — Dynamic ATM Type (Premium Range Selection)")
    l1, l2 = sleg(p, 1), sleg(p, 2)
    t.check("l1.atmType",           l1.get("atmType"),           "Dynamic")
    t.check("l1.premiumStartRange", float(l1.get("premiumStartRange", 0)), 100.0)
    t.check("l1.premiumEndRange",   float(l1.get("premiumEndRange",   0)), 180.0)
    t.check("l1.optionType CE",     l1.get("optionType"),         "CE")
    t.check("l2.atmType",           l2.get("atmType"),           "Dynamic")
    t.check("l2.premiumStartRange", float(l2.get("premiumStartRange", 0)), 100.0)
    t.check("l2.premiumEndRange",   float(l2.get("premiumEndRange",   0)), 180.0)
    t.check("l2.optionType PE",     l2.get("optionType"),         "PE")
    return t

add_test("PROMPT 14",
    "BankNifty intraday straddle using Dynamic ATM selection. Sell CE where premium is between 100 and 180. Sell PE where premium is between 100 and 180. Weekly expiry, 1 lot each. Master target 4000, master SL 2500.",
    validate_14)


# ── PROMPT 15 ─────────────────────────────────────────────────────────────────
# Covers: SENSEX on BFO exchange, underlying string, lot size=20
# ─────────────────────────────────────────────────────────────────────────────
def validate_15(p, r):
    t = TestResult("PROMPT 15 — SENSEX on BFO Exchange, Lot Size=20")
    t.check("symbol",     p.get("symbol"),     "SENSEX")
    t.check("exchange",   p.get("exchange"),   "BFO")
    t.check("underlying", p.get("underlying"), "SENSEX FUT BFO")
    t.check("isIntraday", p.get("isIntraday"), True)
    l1, l2 = sleg(p, 1), sleg(p, 2)
    t.check("l1.symbol",  l1.get("symbol"),     "SENSEX")
    t.check("l1.lot",     l1.get("lot"),        1)
    t.check("l1.qty",     l1.get("qty"),        20)   # SENSEX=20 * 1
    t.check("l2.lot",     l2.get("lot"),        2)
    t.check("l2.qty",     l2.get("qty"),        40)   # SENSEX=20 * 2
    t.check("l1.optionType CE", l1.get("optionType"), "CE")
    t.check("l2.optionType PE", l2.get("optionType"), "PE")
    return t

add_test("PROMPT 15",
    "Create a SENSEX intraday straddle on BSE (BFO exchange). Sell ATM CE 1 lot and Sell ATM PE 2 lots. Weekly expiry. Master target 3000, master SL 2000. Start at 9:20.",
    validate_15)


# ── PROMPT 16 ─────────────────────────────────────────────────────────────────
# Covers: is_live_mtm_profit_move → True, noOfIntradayCycle, intraday_cycle_delay
# ─────────────────────────────────────────────────────────────────────────────
def validate_16(p, r):
    t = TestResult("PROMPT 16 — is_live_mtm_profit_move (True) + Trading Cycle")
    t.check("is_live_mtm_profit_move", p.get("is_live_mtm_profit_move"), True)
    t.check("isTrailSl",   p.get("isTrailSl"),   True)
    t.check("noOfIntradayCycle",   int(p.get("noOfIntradayCycle",   0)), 3)
    t.check("intraday_cycle_delay",int(p.get("intraday_cycle_delay",0)), 10)
    t.check("symbol",  p.get("symbol"),   "NIFTY")
    return t

add_test("PROMPT 16",
    "Nifty short straddle, sell ATM CE and PE, weekly, 1 lot, intraday. Enable master trail SL using live MTM peak as reference — for every 1000 profit, trail SL by 500, max 3 times. Run 3 cycles per day with 10 minute delay between cycles. Master target 4000, master SL 2000.",
    validate_16)


# ── PROMPT 17 ─────────────────────────────────────────────────────────────────
# Covers: FUT + OPT mixed legs (Covered Call pattern), different expiries per leg
# ─────────────────────────────────────────────────────────────────────────────
def validate_17(p, r):
    t = TestResult("PROMPT 17 — FUT + OPT Mixed Legs (Covered Call), Different Expiries")
    t.check("symbol",      p.get("symbol"),      "BANKNIFTY")
    t.check("leg_count",   len(p.get("sub", [])), 3)
    # Find FUT leg and OPT legs
    legs = p.get("sub", [])
    fut_legs = [l for l in legs if l.get("segment") == "FUT"]
    opt_legs = [l for l in legs if l.get("segment") == "OPT"]
    t.check("FUT leg count",  len(fut_legs), 1)
    t.check("OPT leg count",  len(opt_legs), 2)
    if fut_legs:
        fl = fut_legs[0]
        t.check("FUT leg tradeSide", fl.get("tradeSide"), "BUY")
        t.check("FUT leg optionType empty", fl.get("optionType"), "")
        t.check("FUT leg qty", fl.get("qty"), 30)   # BANKNIFTY=30 * 1
    sell_ce = [l for l in opt_legs if l.get("optionType") == "CE" and l.get("tradeSide") == "SELL"]
    buy_pe  = [l for l in opt_legs if l.get("optionType") == "PE" and l.get("tradeSide") == "BUY"]
    t.check("SELL CE OPT exists",  len(sell_ce) > 0, True)
    t.check("BUY PE OPT exists",   len(buy_pe)  > 0, True)
    return t

add_test("PROMPT 17",
    "Create a BankNifty collar strategy. Leg 1: Buy 1 lot BankNifty Futures, monthly expiry. Leg 2: Sell 1 lot ATM+300 CE options, weekly expiry, 1 lot. Leg 3: Buy 1 lot ATM-300 PE options, weekly expiry, 1 lot. Intraday MIS. Master target 5000, master SL 3000.",
    validate_17)


# ── PROMPT 18 ─────────────────────────────────────────────────────────────────
# Covers: Ratio spread — different lot sizes per leg (2 lots SELL, 1 lot BUY)
# ─────────────────────────────────────────────────────────────────────────────
def validate_18(p, r):
    t = TestResult("PROMPT 18 — Ratio Spread, Different Lots per Leg")
    t.check("symbol",    p.get("symbol"),    "BANKNIFTY")
    t.check("leg_count", len(p.get("sub", [])), 4)
    l1, l2, l3, l4 = sleg(p,1), sleg(p,2), sleg(p,3), sleg(p,4)
    t.check("l1 SELL CE",  (l1.get("tradeSide"), l1.get("optionType")), ("SELL","CE"))
    t.check("l1.lot=2",     l1.get("lot"), 2)
    t.check("l1.qty=60",    l1.get("qty"), 60)   # 30*2
    t.check("l2 BUY CE",   (l2.get("tradeSide"), l2.get("optionType")), ("BUY","CE"))
    t.check("l2.lot=1",     l2.get("lot"), 1)
    t.check("l2.qty=30",    l2.get("qty"), 30)
    t.check("l3 SELL PE",  (l3.get("tradeSide"), l3.get("optionType")), ("SELL","PE"))
    t.check("l3.lot=2",     l3.get("lot"), 2)
    t.check("l3.qty=60",    l3.get("qty"), 60)
    t.check("l4 BUY PE",   (l4.get("tradeSide"), l4.get("optionType")), ("BUY","PE"))
    t.check("l4.lot=1",     l4.get("lot"), 1)
    t.check("l4.qty=30",    l4.get("qty"), 30)
    return t

add_test("PROMPT 18",
    "BankNifty ratio spread, weekly, intraday. Sell 2 lots CE ATM, Buy 1 lot CE ATM+300 as hedge. Sell 2 lots PE ATM, Buy 1 lot PE ATM-300 as hedge. Master target 5000, master SL 3000. Start 9:20.",
    validate_18)


# ── PROMPT 19 ─────────────────────────────────────────────────────────────────
# Covers: Required margin, short_description, long_description, all working days,
#         MIDCPNIFTY lot size=75
# ─────────────────────────────────────────────────────────────────────────────
def validate_19(p, r):
    t = TestResult("PROMPT 19 — Required Margin, Descriptions, MIDCPNIFTY lot size")
    t.check("symbol",   p.get("symbol"),   "MIDCPNIFTY")
    t.check("requiredMargin", float(p.get("requiredMargin", 0)), 200000.0)
    # All weekdays on
    t.check("mon", p.get("mon"), True)
    t.check("tue", p.get("tue"), True)
    t.check("wed", p.get("wed"), True)
    t.check("thu", p.get("thu"), True)
    t.check("fri", p.get("fri"), True)
    t.check("sat", p.get("sat"), False)
    # Descriptions
    t.check_nonempty("shortDescription",  p.get("shortDescription", ""))
    t.check_nonempty("longDescription",   p.get("longDescription", ""))
    t.check_contains("shortDescription contains MIDCPNIFTY", p.get("shortDescription",""), "MIDCP")
    # Lot size check
    l1 = sleg(p, 1)
    t.check("l1.lot=1",  l1.get("lot"), 1)
    t.check("l1.qty=75", l1.get("qty"), 75)   # MIDCPNIFTY=75
    return t

add_test("PROMPT 19",
    "Create a MIDCPNIFTY intraday short straddle. Sell ATM CE and PE, weekly expiry, 1 lot each. Trade all weekdays Mon to Fri. Set required margin to 200000. Master target 5000, master SL 3000. Short description: 'MIDCPNIFTY short straddle weekly'. Long description: 'Automated MIDCPNIFTY short straddle strategy with weekly expiry and daily entry.'",
    validate_19)


# ── PROMPT 20 ─────────────────────────────────────────────────────────────────
# Covers: Maximum complexity — Normal mode, all advance controls combined:
#         4 legs, Dynamic ATM, per-leg trail SL, per-leg re-execute,
#         master trail SL, VIX filter, working days, cycle, cosider_closed_pnl,
#         sqroff_all_legs, required_margin, descriptions, wait-and-trade
# ─────────────────────────────────────────────────────────────────────────────
def validate_20(p, r):
    t = TestResult("PROMPT 20 — Maximum Complexity (ALL Parameters Combined)")
    # Main
    t.check("symbol",           p.get("symbol"),           "BANKNIFTY")
    t.check("exchange",         p.get("exchange"),         "NFO")
    t.check("isIntraday",       p.get("isIntraday"),       True)
    t.check("productType",      p.get("productType"),      "MIS")
    t.check("is_btst_stbt",     p.get("is_btst_stbt"),     False)
    t.check("is_range_break_out",p.get("is_range_break_out"),False)
    t.check("leg_count",        len(p.get("sub", [])),     4)
    # Legs
    l1, l2, l3, l4 = sleg(p,1), sleg(p,2), sleg(p,3), sleg(p,4)
    t.check("l1.tradeSide SELL", l1.get("tradeSide"),  "SELL")
    t.check("l1.optionType CE",  l1.get("optionType"), "CE")
    t.check("l1.atmType Dynamic",l1.get("atmType"),    "Dynamic")
    t.check_gt("l1.premiumStartRange", l1.get("premiumStartRange", 0), 0)
    t.check_gt("l1.premiumEndRange",   l1.get("premiumEndRange",   0), 0)
    t.check("l1.is_trail_sl",    l1.get("is_trail_sl"), True)
    t.check_gt("l1.trail_sl_market_move", l1.get("trail_sl_market_move", 0), 0)
    t.check_gt("l1.trail_sl_move",        l1.get("trail_sl_move",        0), 0)
    t.check("l2.tradeSide SELL", l2.get("tradeSide"),  "SELL")
    t.check("l2.optionType PE",  l2.get("optionType"), "PE")
    t.check("l2.atmType Dynamic",l2.get("atmType"),    "Dynamic")
    t.check_gt("l2.reexecute count", int(l2.get("no_of_reexecute", 0)), 0)
    t.check("l3 BUY CE",         (l3.get("tradeSide"), l3.get("optionType")), ("BUY","CE"))
    t.check("l4 BUY PE",         (l4.get("tradeSide"), l4.get("optionType")), ("BUY","PE"))
    # Advance
    t.check("isTrailSl",         p.get("isTrailSl"),         True)
    t.check_gt("profitMove",     float(p.get("profitMove",  0)), 0)
    t.check_gt("slMove",         float(p.get("slMove",      0)), 0)
    t.check_gt("noOfTrailSL",    int(  p.get("noOfTrailSL", 0)), 0)
    t.check("enableVixFilter",   p.get("enableVixFilter"),   True)
    t.check_gt("vixStartValue",  float(p.get("vixStartValue", 0)), 0)
    t.check_gt("vixEndValue",    float(p.get("vixEndValue",   0)), 0)
    t.check("mon", p.get("mon"), True)
    t.check("tue", p.get("tue"), True)
    t.check("wed", p.get("wed"), True)
    t.check("thu", p.get("thu"), True)
    t.check("fri", p.get("fri"), False)   # no Friday
    t.check_gt("noOfIntradayCycle", int(p.get("noOfIntradayCycle", 0)), 1)
    t.check("cosider_closed_pnl",   p.get("cosider_closed_pnl"), True)
    t.check("squareoffLegs",        p.get("squareoffLegs"),      False)
    t.check("sqroffAllLegs",        p.get("sqroffAllLegs"),      True)
    t.check_gt("requiredMargin",    float(p.get("requiredMargin", 0)), 0)
    t.check_nonempty("shortDescription", p.get("shortDescription", ""))
    t.check("master target", float(p.get("target", 0)), 8000.0)
    t.check("master sl",     float(p.get("sl",     0)), 5000.0)
    return t

add_test("PROMPT 20",
    """BankNifty intraday MIS, NFO, 4 legs. Weekly expiry.

Leg 1: Sell CE using Dynamic ATM (premium between 120 and 200), 1 lot. Enable per-leg trail SL: for every 600 profit, trail SL by 250, 3 times.

Leg 2: Sell PE using Dynamic ATM (premium between 120 and 200), 1 lot. Re-execute 2 times on target hit with 5 minute delay.

Leg 3: Buy CE at ATM+600, 1 lot, as hedge.

Leg 4: Buy PE at ATM-600, 1 lot, as hedge.

Master target 8000, master SL 5000 by Money. Enable master trail SL: for every 2000 profit, trail SL by 1000, max 4 times.

VIX filter: trade only when VIX is between 13 and 21. Trade Mon, Tue, Wed, Thu only (not Friday). Run 2 cycles per day with 15 minute delay.

Enable consider closed PnL. Enable square off all legs on any exit. Required margin 175000.

Short description: 'BNF dynamic premium hedge with trail SL and cycle'. Start 9:20, exit 15:15.""",
    validate_20)


# ─────────────────────────────────────────────────────────────────────────────
# Main runner
# ─────────────────────────────────────────────────────────────────────────────
def run_all():
    overall_pass = 0
    overall_fail = 0
    all_results = []
    deploy_ok = 0
    deploy_fail = 0

    print("\n" + "=" * 70)
    print("  MULTI-LEG HEDGER — AUTOMATED END-TO-END TEST SUITE")
    print("  20 Prompts × Full Payload Validation")
    print("=" * 70)

    # Pre-flight: confirm server is reachable
    try:
        import requests as _req
        _req.get("http://localhost:8000/hedger/", timeout=5)
    except Exception as e:
        print(f"\n  ❌ ABORT — Django server not reachable at http://localhost:8000")
        print(f"     Start it first:  venv/bin/python manage.py runserver 0.0.0.0:8000")
        print(f"     Error: {e}")
        return

    for idx, (name, prompt, validator_fn) in enumerate(TESTS, 1):
        print(f"\n{'─' * 70}")
        print(f"▶  Running {name} ...")

        session_id = f"mlh_autotest_{idx}_{int(time.time())}"
        before = last_mlh_log_count()

        # Step 1: Send strategy prompt
        print("  → Sending strategy prompt ...")
        chat(prompt, session_id)

        # Step 2: Confirm deployment
        print("  → Confirming deployment ...")
        chat("yes proceed deploy it", session_id)

        # Step 3: Wait and grab log entry
        time.sleep(2)
        payload, api_status, api_code, api_response = get_last_mlh_log_entry(before)

        if not payload:
            print("  ⚠️  No log entry — trying one more confirm ...")
            chat("yes confirm deploy now", session_id)
            time.sleep(3)
            payload, api_status, api_code, api_response = get_last_mlh_log_entry(before)

        if not payload:
            print(f"  ❌ SKIPPED — deployment did not occur\n")
            result = TestResult(name)
            result.failed.append("  ❌ No payload logged — deployment did not trigger")
            all_results.append(result)
            overall_fail += 1
            deploy_fail += 1
            continue

        # Step 4: Show real API result
        if api_status == "success" and api_code == 200:
            print(f"  🟢 Market Maya: HTTP {api_code} — DEPLOYED SUCCESSFULLY")
            deploy_ok += 1
        else:
            print(f"  🔴 Market Maya: HTTP {api_code} — FAILED: {str(api_response)[:200]}")
            deploy_fail += 1

        # Step 5: Validate payload
        result = validator_fn(payload, "")
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

    # Final summary
    print("\n" + "=" * 70)
    print(f"  FINAL RESULTS: {overall_pass} PASSED / {overall_fail} FAILED out of {len(TESTS)} tests")
    print(f"  Market Maya Deployments: {deploy_ok} SUCCESS / {deploy_fail} FAILED")
    print("=" * 70)

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

    report_file = f"tests/reports/mlh_e2e_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    os.makedirs("tests/reports", exist_ok=True)
    with open(report_file, "w") as f:
        f.write(f"MLH E2E Test Run: {datetime.now().isoformat()}\n")
        f.write(f"Results: {overall_pass}/{len(TESTS)} tests passed, {total_checks_pass}/{total_checks} checks passed\n\n")
        for r in all_results:
            status, p, total = r.summary()
            f.write(f"\n{'=' * 60}\n{r.name}  [{status}] [{p}/{total}]\n")
            for line in r.passed:
                f.write(line + "\n")
            for line in r.failed:
                f.write(line + "\n")
    print(f"\n  Full report saved to: {report_file}")


if __name__ == "__main__":
    run_all()
