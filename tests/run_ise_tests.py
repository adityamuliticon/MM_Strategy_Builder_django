"""
Indicator Signal Engine – Automated Test Runner
Runs all 20 test prompts, captures deployed payloads, validates against expected values.
Run with Django server active on port 8000:  python manage.py runserver 0.0.0.0:8000
"""
import requests
import json
import time
import os
from datetime import datetime

BASE_URL = "http://localhost:8000/indicator/api/chat"
LOG_FILE = "logs/deployed_strategies.log"

# ─────────────────────────────────────────────────────────────────────────────
# Helper: send one chat turn to ISE endpoint
# ─────────────────────────────────────────────────────────────────────────────
def chat(message, session_id):
    try:
        r = requests.post(BASE_URL, json={"message": message, "session_id": session_id}, timeout=180)
        r.raise_for_status()
        return r.json().get("message", "")
    except Exception as e:
        return f"ERROR: {e}"

# ─────────────────────────────────────────────────────────────────────────────
# Helpers: log file access — filter only ISE entries
# ─────────────────────────────────────────────────────────────────────────────
def ise_log_count():
    if not os.path.exists(LOG_FILE):
        return 0
    count = 0
    with open(LOG_FILE) as f:
        for line in f:
            if line.strip():
                try:
                    entry = json.loads(line)
                    if entry.get("strategy_type") == "indicator_signal_engine":
                        count += 1
                except Exception:
                    pass
    return count


def get_last_ise_log_entry(before_count):
    """Returns (payload, api_status, api_code, api_response) from the last new ISE log line."""
    if not os.path.exists(LOG_FILE):
        return None, None, None, None
    ise_lines = []
    with open(LOG_FILE) as f:
        for line in f:
            if line.strip():
                try:
                    entry = json.loads(line)
                    if entry.get("strategy_type") == "indicator_signal_engine":
                        ise_lines.append(entry)
                except Exception:
                    pass
    if len(ise_lines) <= before_count:
        return None, None, None, None
    try:
        entry = ise_lines[-1]
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
        if expected_substring.lower() in str(actual).lower():
            self.passed.append(f"  ✅ {label} contains '{expected_substring}'")
        else:
            self.failed.append(f"  ❌ {label}: expected to contain '{expected_substring}', got={actual!r}")

    def check_in(self, label, expected_item, container):
        if expected_item in container:
            self.passed.append(f"  ✅ {label}: '{expected_item}' present")
        else:
            self.failed.append(f"  ❌ {label}: '{expected_item}' NOT found in {container!r}")

    def check_not_in(self, label, item, container):
        if item not in container:
            self.passed.append(f"  ✅ {label}: '{item}' correctly absent")
        else:
            self.failed.append(f"  ❌ {label}: '{item}' should NOT be in {container!r}")

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


def sub(p, n):
    """Return sub-leg n (1-indexed) from payload or empty dict."""
    subs = p.get("sub", [])
    return subs[n - 1] if len(subs) >= n else {}


def ind(p, n):
    """Return indicator n (1-indexed) from payload or empty dict."""
    indicators = p.get("indicators", [])
    return indicators[n - 1] if len(indicators) >= n else {}


def param_val(indicator_obj, code):
    """Return the string value of a parameter by param_code from an indicator."""
    for param in indicator_obj.get("parameter", []):
        if param.get("param_code") == code:
            return param.get("value")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 20 Test Case definitions
# ─────────────────────────────────────────────────────────────────────────────
TESTS = []

def add_test(name, prompt, validator_fn):
    TESTS.append((name, prompt, validator_fn))


# ── PROMPT 1 ──────────────────────────────────────────────────────────────────
def validate_1(p, r):
    t = TestResult("PROMPT 1 – Basic SuperTrend BankNifty FUT (Core Basics)")
    t.check("isIntraday", p.get("isIntraday"), True)
    t.check("entryOrderProduct", p.get("entryOrderProduct"), "MIS")
    t.check("exitOrderProduct", p.get("exitOrderProduct"), "MIS")
    t.check("chartType", p.get("chartType"), "Candlestick")
    t.check("timeFrame", p.get("timeFrame"), "5Min")
    t.check("signal", p.get("signal"), "Both")
    t.check("entryTime", p.get("entryTime"), "09:15")
    t.check("sqroffTime", p.get("sqroffTime"), "15:15")
    # Sub Leg 1
    s1 = sub(p, 1)
    t.check("sub1.exchange", s1.get("exchange"), "NFO")
    t.check("sub1.segment", s1.get("segment"), "FUT")
    t.check("sub1.symbol", s1.get("symbol"), "BANKNIFTY")
    t.check("sub1.contract", s1.get("contract"), "NEAR")
    t.check("sub1.expiry", s1.get("expiry"), "MONTHLY")
    t.check("sub1.atm", s1.get("atm"), 0)
    t.check("sub1.optionType", s1.get("optionType"), "")
    t.check("sub1.lot", s1.get("lot"), 1)
    t.check("sub1.qty", s1.get("qty"), 30)
    t.check("sub1.callType", s1.get("callType"), "BUY")
    t.check("sub1.isTrailSl", s1.get("isTrailSl"), False)
    t.check("sub1.isReverseSignal", s1.get("isReverseSignal"), False)
    # Indicator 1
    i1 = ind(p, 1)
    t.check("ind1.indicator_code", i1.get("indicator_code"), "supertrend")
    t.check("ind1.index", i1.get("index"), 1)
    t.check("ind1.length", param_val(i1, "length"), "10")
    t.check("ind1.factor", param_val(i1, "factor"), "3")
    return t

add_test("PROMPT 1",
    "Create a BankNifty intraday strategy using SuperTrend indicator on 5 minute chart. Use 1 lot of BankNifty futures, near contract, monthly expiry. Entry at 9:15, sqroff at 15:15. Trade both BUY and SELL signals.",
    validate_1)


# ── PROMPT 2 ──────────────────────────────────────────────────────────────────
def validate_2(p, r):
    t = TestResult("PROMPT 2 – MA CrossOver Custom Params + CE Normal + PE Reverse")
    t.check("timeFrame", p.get("timeFrame"), "15Min")
    t.check("entryTime", p.get("entryTime"), "09:30")
    t.check("sqroffTime", p.get("sqroffTime"), "15:00")
    t.check("isIntraday", p.get("isIntraday"), True)
    s1, s2 = sub(p, 1), sub(p, 2)
    t.check("sub1.symbol", s1.get("symbol"), "NIFTY")
    t.check("sub1.segment", s1.get("segment"), "OPT")
    t.check("sub1.optionType", s1.get("optionType"), "CE")
    t.check("sub1.atm", s1.get("atm"), 0)
    t.check("sub1.expiry", s1.get("expiry"), "WEEKLY")
    t.check("sub1.lot", s1.get("lot"), 2)
    t.check("sub1.qty", s1.get("qty"), 50)
    t.check("sub1.isReverseSignal", s1.get("isReverseSignal"), False)
    t.check("sub2.optionType", s2.get("optionType"), "PE")
    t.check("sub2.lot", s2.get("lot"), 2)
    t.check("sub2.isReverseSignal", s2.get("isReverseSignal"), True)
    i1 = ind(p, 1)
    t.check("ind1.indicator_code", i1.get("indicator_code"), "ma-cross-over")
    t.check("ind1.short", param_val(i1, "short"), "5")
    t.check("ind1.long", param_val(i1, "long"), "20")
    t.check("ind1.type", param_val(i1, "type"), "EMA")
    return t

add_test("PROMPT 2",
    "Nifty options strategy on 15 minute chart using MA CrossOver. Short=5, Long=20, type EMA. Leg 1: Buy CE ATM weekly near 2 lots normal signal. Leg 2: Buy PE ATM weekly near 2 lots with reverse signal. Entry at 9:30, sqroff 15:00. Intraday, signal=Both.",
    validate_2)


# ── PROMPT 3 ──────────────────────────────────────────────────────────────────
def validate_3(p, r):
    t = TestResult("PROMPT 3 – RSI Custom Bands + Leg SL + Signal=BUY")
    t.check("signal", p.get("signal"), "BUY")
    t.check("timeFrame", p.get("timeFrame"), "5Min")
    t.check("entryTime", p.get("entryTime"), "09:20")
    s1 = sub(p, 1)
    t.check("sub1.segment", s1.get("segment"), "FUT")
    t.check("sub1.symbol", s1.get("symbol"), "BANKNIFTY")
    t.check("sub1.expiry", s1.get("expiry"), "WEEKLY")
    t.check("sub1.lot", s1.get("lot"), 1)
    t.check("sub1.qty", s1.get("qty"), 30)
    t.check("sub1.sl", s1.get("sl"), 3000)
    t.check("sub1.slBy", s1.get("slBy"), "Money")
    t.check("sub1.target", s1.get("target"), 0)
    t.check("sub1.isTrailSl", s1.get("isTrailSl"), False)
    i1 = ind(p, 1)
    t.check("ind1.indicator_code", i1.get("indicator_code"), "rsi")
    t.check("ind1.length", param_val(i1, "length"), "21")
    t.check("ind1.lower-band", param_val(i1, "lower-band"), "25")
    t.check("ind1.upper-band", param_val(i1, "upper-band"), "75")
    return t

add_test("PROMPT 3",
    "BankNifty RSI strategy on 5 minute chart. RSI length 21, lower band 25, upper band 75. Trade only BUY signals. Use 1 lot BankNifty futures weekly near contract. Set leg stoploss 3000 rupees. Entry at 9:20, sqroff 15:15. Intraday.",
    validate_3)


# ── PROMPT 4 ──────────────────────────────────────────────────────────────────
def validate_4(p, r):
    t = TestResult("PROMPT 4 – MACD All 6 Params + Leg Target+SL + Signal=SELL")
    t.check("signal", p.get("signal"), "SELL")
    t.check("timeFrame", p.get("timeFrame"), "10Min")
    t.check("entryTime", p.get("entryTime"), "09:20")
    s1, s2 = sub(p, 1), sub(p, 2)
    t.check("sub1.optionType", s1.get("optionType"), "CE")
    t.check("sub1.atm", s1.get("atm"), 100)
    t.check("sub1.target", s1.get("target"), 2000)
    t.check("sub1.targetBy", s1.get("targetBy"), "Money")
    t.check("sub1.sl", s1.get("sl"), 1500)
    t.check("sub1.slBy", s1.get("slBy"), "Money")
    t.check("sub2.optionType", s2.get("optionType"), "PE")
    t.check("sub2.atm", s2.get("atm"), -100)
    t.check("sub2.target", s2.get("target"), 2000)
    t.check("sub2.sl", s2.get("sl"), 1500)
    i1 = ind(p, 1)
    t.check("ind1.indicator_code", i1.get("indicator_code"), "macd")
    t.check("ind1.fast-length", param_val(i1, "fast-length"), "8")
    t.check("ind1.slow-length", param_val(i1, "slow-length"), "21")
    t.check("ind1.source", param_val(i1, "source"), "High")
    t.check("ind1.signal-length", param_val(i1, "signal-length"), "5")
    t.check("ind1.oscillator-ma-type", param_val(i1, "oscillator-ma-type"), "SMA")
    t.check("ind1.signal-line-ma-type", param_val(i1, "signal-line-ma-type"), "SMA")
    return t

add_test("PROMPT 4",
    "Nifty MACD strategy on 10 minute chart. MACD fast=8, slow=21, source=High, signal length=5, oscillator type=SMA, signal line type=SMA. Trade only SELL signals. Leg 1: CE ATM+100 weekly near 1 lot, target 2000 rupees SL 1500 rupees. Leg 2: PE ATM-100 weekly near 1 lot, target 2000 rupees SL 1500 rupees. Entry 9:20. Intraday.",
    validate_4)


# ── PROMPT 5 ──────────────────────────────────────────────────────────────────
def validate_5(p, r):
    t = TestResult("PROMPT 5 – Stochastic AND Bollinger Bands (Same Index=1)")
    t.check("timeFrame", p.get("timeFrame"), "30Min")
    s1 = sub(p, 1)
    t.check("sub1.segment", s1.get("segment"), "FUT")
    t.check("sub1.symbol", s1.get("symbol"), "BANKNIFTY")
    t.check("sub1.expiry", s1.get("expiry"), "MONTHLY")
    t.check("sub1.lot", s1.get("lot"), 1)
    # Both indicators must share index=1 (AND logic)
    i1, i2 = ind(p, 1), ind(p, 2)
    t.check("ind1.indicator_code", i1.get("indicator_code"), "stochastic")
    t.check("ind1.index", i1.get("index"), 1)
    t.check("ind1.k-length", param_val(i1, "k-length"), "9")
    t.check("ind1.d-length", param_val(i1, "d-length"), "3")
    t.check("ind1.lower-band", param_val(i1, "lower-band"), "25")
    t.check("ind1.upper-band", param_val(i1, "upper-band"), "75")
    t.check("ind2.indicator_code", i2.get("indicator_code"), "bollinger-bands")
    t.check("ind2.index", i2.get("index"), 1)  # SAME index → AND logic
    t.check("ind2.length", param_val(i2, "length"), "15")
    t.check("ind2.multiplier", param_val(i2, "multiplier"), "3")
    t.check("indicator_count", len(p.get("indicators", [])), 2)
    return t

add_test("PROMPT 5",
    "BankNifty futures strategy: Entry only when Stochastic AND Bollinger Bands both signal together. Stochastic K=9, D=3, lower=25, upper=75. Bollinger Bands length=15, multiplier=3, source=Close. 30 minute chart, signal=Both, 1 lot near monthly. Entry 9:15. Intraday.",
    validate_5)


# ── PROMPT 6 ──────────────────────────────────────────────────────────────────
def validate_6(p, r):
    t = TestResult("PROMPT 6 – SuperTrend OR RSI (Different Indexes) + Leg Trail SL")
    t.check("timeFrame", p.get("timeFrame"), "1Hour")
    i1, i2 = ind(p, 1), ind(p, 2)
    t.check("ind1.indicator_code", i1.get("indicator_code"), "supertrend")
    t.check("ind1.index", i1.get("index"), 1)
    t.check("ind2.indicator_code", i2.get("indicator_code"), "rsi")
    t.check("ind2.index", i2.get("index"), 2)  # DIFFERENT index → OR logic
    s1 = sub(p, 1)
    t.check("sub1.isTrailSl", s1.get("isTrailSl"), True)
    t.check("sub1.trailSlMarketMove", s1.get("trailSlMarketMove"), 500)
    t.check("sub1.trailSlMove", s1.get("trailSlMove"), 200)
    t.check("sub1.noOfTimeTrailSl", s1.get("noOfTimeTrailSl"), 3)
    return t

add_test("PROMPT 6",
    "Nifty futures strategy: Entry when SuperTrend signals OR RSI signals — either one triggers entry. SuperTrend default params. RSI default params. 1 hour chart, signal=Both. Leg-level trail SL: after every 500 profit move trail SL by 200, max 3 times. 1 lot near weekly. Entry 9:15. Intraday.",
    validate_6)


# ── PROMPT 7 ──────────────────────────────────────────────────────────────────
def validate_7(p, r):
    t = TestResult("PROMPT 7 – CE Normal + PE Reverse Signal Hedge + Master Target")
    s1, s2 = sub(p, 1), sub(p, 2)
    t.check("sub1.optionType", s1.get("optionType"), "CE")
    t.check("sub1.atm", s1.get("atm"), 0)
    t.check("sub1.isReverseSignal", s1.get("isReverseSignal"), False)
    t.check("sub1.callType", s1.get("callType"), "BUY")
    t.check("sub2.optionType", s2.get("optionType"), "PE")
    t.check("sub2.atm", s2.get("atm"), 0)
    t.check("sub2.isReverseSignal", s2.get("isReverseSignal"), True)
    t.check("sub2.callType", s2.get("callType"), "BUY")
    t.check("masterTarget", p.get("masterTarget"), 4000)
    t.check("masterSl", p.get("masterSl"), 0)
    t.check("signal", p.get("signal"), "Both")
    i1 = ind(p, 1)
    t.check("ind1.indicator_code", i1.get("indicator_code"), "supertrend")
    return t

add_test("PROMPT 7",
    "BankNifty hedge strategy using SuperTrend 5 min chart. Leg 1: CE ATM weekly near 1 lot, normal signal (follows indicator direction). Leg 2: PE ATM weekly near 1 lot, reverse signal (takes opposite of indicator direction). Signal=Both. Master target 4000 rupees. Entry 9:15, sqroff 15:15. Intraday.",
    validate_7)


# ── PROMPT 8 ──────────────────────────────────────────────────────────────────
def validate_8(p, r):
    t = TestResult("PROMPT 8 – Master Target + Master SL + Master Trail SL")
    t.check("masterTarget", p.get("masterTarget"), 5000)
    t.check("masterTargetType", p.get("masterTargetType"), "Money")
    t.check("masterSl", p.get("masterSl"), 3000)
    t.check("masterSlType", p.get("masterSlType"), "Money")
    t.check("isTrailSl", p.get("isTrailSl"), True)
    t.check("profitMove", p.get("profitMove"), 2000)
    t.check("slMove", p.get("slMove"), 1000)
    t.check("noOfTrailSl", p.get("noOfTrailSl"), 5)
    t.check("entryTime", p.get("entryTime"), "09:20")
    return t

add_test("PROMPT 8",
    "BankNifty futures SuperTrend 5 min strategy, 1 lot near weekly. Set master target 5000 rupees and master SL 3000 rupees. Enable master trail SL: every time combined profit increases by 2000 rupees, trail the master SL by 1000 rupees, max 5 times. Entry 9:20, sqroff 15:15. Intraday.",
    validate_8)


# ── PROMPT 9 ──────────────────────────────────────────────────────────────────
def validate_9(p, r):
    t = TestResult("PROMPT 9 – (SuperTrend AND MA CrossOver) OR RSI — 3 Indicator Mix")
    t.check("indicator_count", len(p.get("indicators", [])), 3)
    i1, i2, i3 = ind(p, 1), ind(p, 2), ind(p, 3)
    t.check("ind1.code", i1.get("indicator_code"), "supertrend")
    t.check("ind1.index", i1.get("index"), 1)
    t.check("ind1.length", param_val(i1, "length"), "7")
    t.check("ind1.factor", param_val(i1, "factor"), "2")
    t.check("ind2.code", i2.get("indicator_code"), "ma-cross-over")
    t.check("ind2.index", i2.get("index"), 1)  # SAME index=1 → AND with supertrend
    t.check("ind2.short", param_val(i2, "short"), "5")
    t.check("ind2.long", param_val(i2, "long"), "13")
    t.check("ind2.type", param_val(i2, "type"), "EMA")
    t.check("ind3.code", i3.get("indicator_code"), "rsi")
    t.check("ind3.index", i3.get("index"), 2)  # DIFFERENT index=2 → OR
    t.check("timeFrame", p.get("timeFrame"), "5Min")
    return t

add_test("PROMPT 9",
    "Nifty futures strategy. Entry condition: SuperTrend AND MA CrossOver must both agree on same row, OR RSI alone on a different row. SuperTrend length=7, factor=2. MA CrossOver short=5, long=13, type=EMA. RSI default params. 5 min Candlestick, signal=Both, 1 lot near monthly. Entry 9:15. Intraday.",
    validate_9)


# ── PROMPT 10 ─────────────────────────────────────────────────────────────────
def validate_10(p, r):
    t = TestResult("PROMPT 10 – Heikin-Ashi + 2Hour Chart + Restricted WeekDays")
    t.check("chartType", p.get("chartType"), "Heikin-Ashi")
    t.check("timeFrame", p.get("timeFrame"), "2Hour")
    t.check("underlyingType", p.get("underlyingType"), "Future")
    week_days = p.get("weekDays", [])
    t.check_in("weekDays has TUE", "TUE", week_days)
    t.check_in("weekDays has THU", "THU", week_days)
    t.check_in("weekDays has FRI", "FRI", week_days)
    t.check_not_in("weekDays no MON", "MON", week_days)
    t.check_not_in("weekDays no WED", "WED", week_days)
    i1 = ind(p, 1)
    t.check("ind1.indicator_code", i1.get("indicator_code"), "supertrend")
    return t

add_test("PROMPT 10",
    "BankNifty futures strategy using Heikin-Ashi 2 hour chart. Use default SuperTrend. Only trade on Tuesday, Thursday and Friday. 1 lot near monthly. Entry 9:15, sqroff 15:15. Signal Both. Intraday. Underlying type Future.",
    validate_10)


# ── PROMPT 11 ─────────────────────────────────────────────────────────────────
def validate_11(p, r):
    t = TestResult("PROMPT 11 – Positional + NRML + Sqroff Before Expiry + 1Day Chart")
    t.check("isIntraday", p.get("isIntraday"), False)
    t.check("entryOrderProduct", p.get("entryOrderProduct"), "NRML")
    t.check("exitOrderProduct", p.get("exitOrderProduct"), "NRML")
    t.check("timeFrame", p.get("timeFrame"), "1Day")
    t.check("sqroffBeforeExDays", p.get("sqroffBeforeExDays"), 2)
    s1 = sub(p, 1)
    t.check("sub1.segment", s1.get("segment"), "FUT")
    t.check("sub1.symbol", s1.get("symbol"), "NIFTY")
    t.check("sub1.expiry", s1.get("expiry"), "MONTHLY")
    i1 = ind(p, 1)
    t.check("ind1.indicator_code", i1.get("indicator_code"), "ma-cross-over")
    t.check("ind1.short (default)", param_val(i1, "short"), "9")
    t.check("ind1.long (default)", param_val(i1, "long"), "26")
    t.check("ind1.type (default)", param_val(i1, "type"), "SMA")
    return t

add_test("PROMPT 11",
    "Create a positional Nifty strategy with NRML product. 1 lot Nifty futures near monthly expiry. Use MA CrossOver default settings on daily chart. Entry 9:15, sqroff 15:15. Square off 2 days before expiry. Signal Both. Underlying type Future.",
    validate_11)


# ── PROMPT 12 ─────────────────────────────────────────────────────────────────
def validate_12(p, r):
    t = TestResult("PROMPT 12 – BFO Exchange SENSEX + ATM Offsets + Reverse Signal + Master SL")
    s1, s2 = sub(p, 1), sub(p, 2)
    t.check("sub1.exchange", s1.get("exchange"), "BFO")
    t.check("sub1.symbol", s1.get("symbol"), "SENSEX")
    t.check("sub1.segment", s1.get("segment"), "OPT")
    t.check("sub1.optionType", s1.get("optionType"), "CE")
    t.check("sub1.atm", s1.get("atm"), 200)
    t.check("sub1.isReverseSignal", s1.get("isReverseSignal"), False)
    t.check("sub2.exchange", s2.get("exchange"), "BFO")
    t.check("sub2.symbol", s2.get("symbol"), "SENSEX")
    t.check("sub2.segment", s2.get("segment"), "OPT")
    t.check("sub2.optionType", s2.get("optionType"), "PE")
    t.check("sub2.atm", s2.get("atm"), -200)
    t.check("sub2.isReverseSignal", s2.get("isReverseSignal"), True)
    t.check("masterSl", p.get("masterSl"), 5000)
    t.check("masterTarget", p.get("masterTarget"), 0)
    return t

add_test("PROMPT 12",
    "SENSEX BFO options strategy using SuperTrend 5 min. Leg 1: CE ATM+200 weekly near 1 lot normal signal. Leg 2: PE ATM-200 weekly near 1 lot reverse signal. Master SL 5000 rupees, no master target. Entry 9:15. Intraday. Signal=Both.",
    validate_12)


# ── PROMPT 13 ─────────────────────────────────────────────────────────────────
def validate_13(p, r):
    t = TestResult("PROMPT 13 – 3 Legs Mixed OPT+FUT, NEAR vs NEXT Contract")
    t.check("sub_count", len(p.get("sub", [])), 3)
    s1, s2, s3 = sub(p, 1), sub(p, 2), sub(p, 3)
    t.check("sub1.segment", s1.get("segment"), "OPT")
    t.check("sub1.optionType", s1.get("optionType"), "CE")
    t.check("sub1.contract", s1.get("contract"), "NEAR")
    t.check("sub1.expiry", s1.get("expiry"), "WEEKLY")
    t.check("sub1.lot", s1.get("lot"), 1)
    t.check("sub1.isReverseSignal", s1.get("isReverseSignal"), False)
    t.check("sub2.optionType", s2.get("optionType"), "PE")
    t.check("sub2.contract", s2.get("contract"), "NEAR")
    t.check("sub2.expiry", s2.get("expiry"), "WEEKLY")
    t.check("sub2.isReverseSignal", s2.get("isReverseSignal"), True)
    t.check("sub3.segment", s3.get("segment"), "FUT")
    t.check("sub3.contract", s3.get("contract"), "NEXT")
    t.check("sub3.expiry", s3.get("expiry"), "MONTHLY")
    t.check("sub3.lot", s3.get("lot"), 2)
    i1 = ind(p, 1)
    t.check("ind1.indicator_code", i1.get("indicator_code"), "rsi")
    return t

add_test("PROMPT 13",
    "Nifty 3-leg strategy: Leg 1 — Buy CE ATM OPT near weekly 1 lot normal signal. Leg 2 — Buy PE ATM OPT near weekly 1 lot reverse signal. Leg 3 — Buy 2 lots Nifty futures NEXT contract monthly as hedge. RSI default on 5 min chart. Signal Both. Entry 9:15. Intraday.",
    validate_13)


# ── PROMPT 14 ─────────────────────────────────────────────────────────────────
def validate_14(p, r):
    t = TestResult("PROMPT 14 – Underlying Type=Spot/Index + Signal=SELL + Custom SuperTrend 15Min")
    t.check("underlyingType", p.get("underlyingType"), "Spot/Index")
    t.check("signal", p.get("signal"), "SELL")
    t.check("timeFrame", p.get("timeFrame"), "15Min")
    t.check("entryTime", p.get("entryTime"), "09:20")
    i1 = ind(p, 1)
    t.check("ind1.indicator_code", i1.get("indicator_code"), "supertrend")
    t.check("ind1.length", param_val(i1, "length"), "12")
    t.check("ind1.factor", param_val(i1, "factor"), "2")
    return t

add_test("PROMPT 14",
    "BankNifty futures strategy. Compute indicators on Spot/Index data not futures. Trade only SELL signals. SuperTrend length=12, factor=2 on 15 minute chart. 1 lot near weekly. Entry 9:20, sqroff 15:15. Intraday.",
    validate_14)


# ── PROMPT 15 ─────────────────────────────────────────────────────────────────
def validate_15(p, r):
    t = TestResult("PROMPT 15 – Candlestick Patterns Hammer OR Evening Star")
    i1, i2 = ind(p, 1), ind(p, 2)
    t.check("ind1.indicator_code", i1.get("indicator_code"), "hammer")
    t.check("ind1.index", i1.get("index"), 1)
    t.check("ind1.parameter_empty", i1.get("parameter"), [])   # no parameters for patterns
    t.check("ind2.indicator_code", i2.get("indicator_code"), "evening-star")
    t.check("ind2.index", i2.get("index"), 2)  # DIFFERENT index → OR logic
    t.check("ind2.parameter_empty", i2.get("parameter"), [])
    s1, s2 = sub(p, 1), sub(p, 2)
    t.check("sub1.optionType", s1.get("optionType"), "CE")
    t.check("sub1.isReverseSignal", s1.get("isReverseSignal"), False)
    t.check("sub2.optionType", s2.get("optionType"), "PE")
    t.check("sub2.isReverseSignal", s2.get("isReverseSignal"), True)
    return t

add_test("PROMPT 15",
    "BankNifty options strategy using candlestick patterns. Entry when Hammer pattern fires on row 1 OR Evening Star pattern fires on row 2. Leg 1: CE ATM weekly near 1 lot normal signal. Leg 2: PE ATM weekly near 1 lot reverse signal. 5 min Candlestick, signal=Both. Entry 9:15, sqroff 15:15. Intraday.",
    validate_15)


# ── PROMPT 16 ─────────────────────────────────────────────────────────────────
def validate_16(p, r):
    t = TestResult("PROMPT 16 – Leg Trail SL Unlimited (noOfTimeTrailSl=0) + Master SL Only")
    t.check("masterTarget", p.get("masterTarget"), 0)
    t.check("masterSl", p.get("masterSl"), 4000)
    t.check("isTrailSl (master)", p.get("isTrailSl"), False)
    s1 = sub(p, 1)
    t.check("sub1.isTrailSl", s1.get("isTrailSl"), True)
    t.check("sub1.trailSlMarketMove", s1.get("trailSlMarketMove"), 300)
    t.check("sub1.trailSlMove", s1.get("trailSlMove"), 150)
    t.check("sub1.noOfTimeTrailSl", s1.get("noOfTimeTrailSl"), 0)  # 0 = unlimited in ISE
    i1 = ind(p, 1)
    t.check("ind1.indicator_code", i1.get("indicator_code"), "macd")
    return t

add_test("PROMPT 16",
    "Nifty futures weekly 5 min chart using MACD default settings. 1 lot near. Leg-level trail SL: for every 300 point profit move, trail SL by 150 points, unlimited trails. Master SL 4000 rupees, no master target. Entry 9:20, sqroff 15:15. Intraday.",
    validate_16)


# ── PROMPT 17 ─────────────────────────────────────────────────────────────────
def validate_17(p, r):
    t = TestResult("PROMPT 17 – 4 Legs Different Lots + Trail SL Leg1 + WeekDays + Master Target")
    t.check("sub_count", len(p.get("sub", [])), 4)
    s1, s2, s3, s4 = sub(p,1), sub(p,2), sub(p,3), sub(p,4)
    t.check("sub1.optionType", s1.get("optionType"), "CE")
    t.check("sub1.atm", s1.get("atm"), 0)
    t.check("sub1.lot", s1.get("lot"), 2)
    t.check("sub1.qty", s1.get("qty"), 60)
    t.check("sub1.sl", s1.get("sl"), 2500)
    t.check("sub1.isTrailSl", s1.get("isTrailSl"), True)
    t.check("sub1.trailSlMarketMove", s1.get("trailSlMarketMove"), 1000)
    t.check("sub1.trailSlMove", s1.get("trailSlMove"), 500)
    t.check("sub1.noOfTimeTrailSl", s1.get("noOfTimeTrailSl"), 3)
    t.check("sub1.isReverseSignal", s1.get("isReverseSignal"), False)
    t.check("sub2.optionType", s2.get("optionType"), "PE")
    t.check("sub2.lot", s2.get("lot"), 2)
    t.check("sub2.sl", s2.get("sl"), 2500)
    t.check("sub2.isReverseSignal", s2.get("isReverseSignal"), True)
    t.check("sub3.optionType", s3.get("optionType"), "CE")
    t.check("sub3.atm", s3.get("atm"), 300)
    t.check("sub3.lot", s3.get("lot"), 1)
    t.check("sub4.optionType", s4.get("optionType"), "PE")
    t.check("sub4.atm", s4.get("atm"), -300)
    t.check("sub4.lot", s4.get("lot"), 1)
    t.check("sub4.isReverseSignal", s4.get("isReverseSignal"), True)
    week_days = p.get("weekDays", [])
    t.check_in("weekDays has MON", "MON", week_days)
    t.check_in("weekDays has WED", "WED", week_days)
    t.check_in("weekDays has FRI", "FRI", week_days)
    t.check_not_in("weekDays no TUE", "TUE", week_days)
    t.check_not_in("weekDays no THU", "THU", week_days)
    t.check("masterTarget", p.get("masterTarget"), 6000)
    t.check("entryTime", p.get("entryTime"), "09:20")
    t.check("sqroffTime", p.get("sqroffTime"), "15:10")
    return t

add_test("PROMPT 17",
    "BankNifty 4-leg OPT strategy using SuperTrend 5 min. Leg 1: CE ATM weekly 2 lots, SL 2500, trail SL every 1000 profit trail by 500 max 3 times. Leg 2: PE ATM weekly 2 lots reverse signal, SL 2500. Leg 3: CE ATM+300 weekly 1 lot. Leg 4: PE ATM-300 weekly 1 lot reverse signal. Trade only Monday, Wednesday, Friday. Master target 6000 rupees. Entry 9:20, sqroff 15:10. Intraday.",
    validate_17)


# ── PROMPT 18 ─────────────────────────────────────────────────────────────────
def validate_18(p, r):
    t = TestResult("PROMPT 18 – NEXT Contract + 4Hour Chart + Positional + Stochastic Custom + SqroffBeforeEx")
    t.check("isIntraday", p.get("isIntraday"), False)
    t.check("entryOrderProduct", p.get("entryOrderProduct"), "NRML")
    t.check("exitOrderProduct", p.get("exitOrderProduct"), "NRML")
    t.check("timeFrame", p.get("timeFrame"), "4Hour")
    t.check("sqroffBeforeExDays", p.get("sqroffBeforeExDays"), 1)
    s1, s2 = sub(p, 1), sub(p, 2)
    t.check("sub1.contract", s1.get("contract"), "NEXT")
    t.check("sub1.expiry", s1.get("expiry"), "WEEKLY")
    t.check("sub1.optionType", s1.get("optionType"), "CE")
    t.check("sub1.isReverseSignal", s1.get("isReverseSignal"), False)
    t.check("sub2.contract", s2.get("contract"), "NEXT")
    t.check("sub2.expiry", s2.get("expiry"), "WEEKLY")
    t.check("sub2.optionType", s2.get("optionType"), "PE")
    t.check("sub2.isReverseSignal", s2.get("isReverseSignal"), True)
    i1 = ind(p, 1)
    t.check("ind1.indicator_code", i1.get("indicator_code"), "stochastic")
    t.check("ind1.k-length", param_val(i1, "k-length"), "12")
    t.check("ind1.d-length", param_val(i1, "d-length"), "4")
    t.check("ind1.lower-band", param_val(i1, "lower-band"), "25")
    t.check("ind1.upper-band", param_val(i1, "upper-band"), "75")
    return t

add_test("PROMPT 18",
    "Nifty positional NRML strategy using Stochastic on 4 hour chart. K=12, D=4, lower=25, upper=75. Leg 1: CE ATM NEXT weekly 1 lot normal signal. Leg 2: PE ATM NEXT weekly 1 lot reverse signal. Sqroff 1 day before expiry. Signal=Both. Entry 9:15.",
    validate_18)


# ── PROMPT 19 ─────────────────────────────────────────────────────────────────
def validate_19(p, r):
    t = TestResult("PROMPT 19 – Candlestick Patterns AND+OR + Descriptions + Signal=BUY")
    t.check("indicator_count", len(p.get("indicators", [])), 3)
    i1, i2, i3 = ind(p, 1), ind(p, 2), ind(p, 3)
    t.check("ind1.code", i1.get("indicator_code"), "three-white-soldiers")
    t.check("ind1.index", i1.get("index"), 1)
    t.check("ind1.no_params", i1.get("parameter"), [])
    t.check("ind2.code", i2.get("indicator_code"), "hammer")
    t.check("ind2.index", i2.get("index"), 1)  # SAME index=1 → AND with three-white-soldiers
    t.check("ind2.no_params", i2.get("parameter"), [])
    t.check("ind3.code", i3.get("indicator_code"), "morning-star")
    t.check("ind3.index", i3.get("index"), 2)  # DIFFERENT index=2 → OR
    t.check("ind3.no_params", i3.get("parameter"), [])
    t.check("signal", p.get("signal"), "BUY")
    t.check("entryTime", p.get("entryTime"), "09:30")
    t.check_contains("shortDescription", p.get("shortDescription", ""), "BNF")
    t.check_contains("longDescription", p.get("longDescription", ""), "Three White Soldiers")
    return t

add_test("PROMPT 19",
    "BankNifty CE ATM weekly 1 lot strategy. Entry when Three White Soldiers AND Hammer both fire on same row, OR Morning Star fires alone on a separate row. 5 min Candlestick, signal=BUY. Entry 9:30, sqroff 15:15. Intraday. Short description: 'BNF bullish pattern combo strategy.' Long description: 'Uses Three White Soldiers and Hammer patterns in AND logic for strong bullish confirmation on BankNifty weekly CE options.'",
    validate_19)


# ── PROMPT 20 ─────────────────────────────────────────────────────────────────
def validate_20(p, r):
    t = TestResult("PROMPT 20 – Maximum Complexity (ALL Parameters)")
    # Main tab
    t.check("isIntraday", p.get("isIntraday"), False)
    t.check("entryOrderProduct", p.get("entryOrderProduct"), "NRML")
    t.check("exitOrderProduct", p.get("exitOrderProduct"), "NRML")
    t.check("chartType", p.get("chartType"), "Heikin-Ashi")
    t.check("timeFrame", p.get("timeFrame"), "30Min")
    t.check("signal", p.get("signal"), "Both")
    t.check("underlyingType", p.get("underlyingType"), "Spot/Index")
    t.check("entryTime", p.get("entryTime"), "09:20")
    t.check("sqroffTime", p.get("sqroffTime"), "15:15")
    # WeekDays
    week_days = p.get("weekDays", [])
    t.check_in("weekDays has MON", "MON", week_days)
    t.check_in("weekDays has TUE", "TUE", week_days)
    t.check_in("weekDays has WED", "WED", week_days)
    t.check_not_in("weekDays no THU", "THU", week_days)
    t.check_not_in("weekDays no FRI", "FRI", week_days)
    # Exit tab
    t.check("sqroffBeforeExDays", p.get("sqroffBeforeExDays"), 2)
    t.check("masterTarget", p.get("masterTarget"), 8000)
    t.check("masterTargetType", p.get("masterTargetType"), "Money")
    t.check("masterSl", p.get("masterSl"), 5000)
    t.check("masterSlType", p.get("masterSlType"), "Money")
    t.check("isTrailSl (master)", p.get("isTrailSl"), True)
    t.check("profitMove", p.get("profitMove"), 3000)
    t.check("slMove", p.get("slMove"), 1500)
    t.check("noOfTrailSl", p.get("noOfTrailSl"), 4)
    # Legs
    t.check("sub_count", len(p.get("sub", [])), 4)
    s1, s2, s3, s4 = sub(p,1), sub(p,2), sub(p,3), sub(p,4)
    t.check("sub1.segment", s1.get("segment"), "OPT")
    t.check("sub1.optionType", s1.get("optionType"), "CE")
    t.check("sub1.atm", s1.get("atm"), 0)
    t.check("sub1.lot", s1.get("lot"), 2)
    t.check("sub1.qty", s1.get("qty"), 60)
    t.check("sub1.sl", s1.get("sl"), 3000)
    t.check("sub1.isReverseSignal", s1.get("isReverseSignal"), False)
    t.check("sub1.isTrailSl", s1.get("isTrailSl"), True)
    t.check("sub1.trailSlMarketMove", s1.get("trailSlMarketMove"), 1500)
    t.check("sub1.trailSlMove", s1.get("trailSlMove"), 600)
    t.check("sub1.noOfTimeTrailSl", s1.get("noOfTimeTrailSl"), 4)
    t.check("sub2.optionType", s2.get("optionType"), "PE")
    t.check("sub2.atm", s2.get("atm"), 0)
    t.check("sub2.lot", s2.get("lot"), 2)
    t.check("sub2.sl", s2.get("sl"), 3000)
    t.check("sub2.isReverseSignal", s2.get("isReverseSignal"), True)
    t.check("sub3.segment", s3.get("segment"), "OPT")
    t.check("sub3.optionType", s3.get("optionType"), "CE")
    t.check("sub3.atm", s3.get("atm"), 200)
    t.check("sub3.lot", s3.get("lot"), 1)
    t.check("sub3.isReverseSignal", s3.get("isReverseSignal"), False)
    t.check("sub4.segment", s4.get("segment"), "FUT")
    t.check("sub4.optionType (empty)", s4.get("optionType"), "")
    t.check("sub4.lot", s4.get("lot"), 1)
    t.check("sub4.isReverseSignal", s4.get("isReverseSignal"), False)
    # Indicators
    t.check("indicator_count", len(p.get("indicators", [])), 4)
    i1, i2, i3, i4 = ind(p,1), ind(p,2), ind(p,3), ind(p,4)
    t.check("ind1.code", i1.get("indicator_code"), "supertrend")
    t.check("ind1.index", i1.get("index"), 1)
    t.check("ind1.length", param_val(i1, "length"), "10")
    t.check("ind1.factor", param_val(i1, "factor"), "3")
    t.check("ind2.code", i2.get("indicator_code"), "ma-cross-over")
    t.check("ind2.index", i2.get("index"), 1)  # AND with supertrend
    t.check("ind2.short", param_val(i2, "short"), "9")
    t.check("ind2.long", param_val(i2, "long"), "26")
    t.check("ind2.type", param_val(i2, "type"), "SMA")
    t.check("ind3.code", i3.get("indicator_code"), "rsi")
    t.check("ind3.index", i3.get("index"), 2)  # OR
    t.check("ind4.code", i4.get("indicator_code"), "macd")
    t.check("ind4.index", i4.get("index"), 3)  # OR
    # Descriptions
    t.check_contains("shortDescription", p.get("shortDescription", ""), "ISE")
    t.check_contains("longDescription", p.get("longDescription", ""), "SuperTrend")
    # Fixed fields
    t.check("strategyTypeId", p.get("strategyTypeId"), "QFwz7gYjmmabUT8SBvZQGgaC0$aC0$")
    t.check("rebacktest", p.get("rebacktest"), True)
    t.check("effectAllSubStrategies", p.get("effectAllSubStrategies"), False)
    return t

add_test("PROMPT 20",
    """Create a positional BankNifty strategy called 'ISE Full Combo', NRML product.

Leg 1: CE ATM OPT weekly near 2 lots, reverse signal OFF. SL 3000 rupees. Trail SL: every 1500 profit trail by 600, max 4 times.
Leg 2: PE ATM OPT weekly near 2 lots, reverse signal ON. SL 3000 rupees.
Leg 3: CE ATM+200 OPT weekly near 1 lot, normal signal.
Leg 4: BankNifty futures near monthly 1 lot as hedge, normal signal.

Entry condition: SuperTrend length=10 factor=3 AND MA CrossOver short=9 long=26 type=SMA on same row, OR RSI length=14 default on separate row, OR MACD all defaults on another separate row.

Heikin-Ashi chart, 30 minute timeframe. Signal=Both. Only trade Monday, Tuesday, Wednesday. Underlying type=Spot/Index. Entry 9:20, sqroff 15:15.

Master target 8000 rupees, master SL 5000 rupees. Master trail SL: every 3000 profit trail master SL by 1500, max 4 times. Sqroff 2 days before expiry.

Short description: 'ISE max param BNF strategy.' Long description: 'Full-parameter ISE strategy with SuperTrend+MACross AND RSI OR MACD, Heikin-Ashi 30min, positional NRML, master trail SL.'""",
    validate_20)


# ─────────────────────────────────────────────────────────────────────────────
# Main runner
# ─────────────────────────────────────────────────────────────────────────────
def run_all():
    overall_pass = 0
    overall_fail = 0
    all_results = []

    print("\n" + "="*70)
    print("  INDICATOR SIGNAL ENGINE — AUTOMATED TEST SUITE")
    print("  20 Prompts × Full Payload Validation")
    print("  Server: http://localhost:8000/indicator/api/chat")
    print("="*70)

    deploy_ok_count = 0
    deploy_fail_count = 0

    for idx, (name, prompt, validator_fn) in enumerate(TESTS, 1):
        print(f"\n{'─'*70}")
        print(f"▶  Running {name} ...")

        session_id = f"ise_autotest_{idx}_{int(time.time())}"
        before = ise_log_count()

        # Step 1: Send strategy prompt
        print("  → Sending strategy prompt ...")
        ai_preview = chat(prompt, session_id)

        # Step 2: Confirm deployment
        print("  → Confirming deployment ...")
        ai_final = chat("yes proceed deploy it", session_id)

        # Step 3: Wait and grab ISE log entry
        time.sleep(2)
        payload, api_status, api_code, api_response = get_last_ise_log_entry(before)

        if not payload:
            print(f"  ⚠️  NO LOG ENTRY — trying one more confirm ...")
            chat("yes confirm deploy", session_id)
            time.sleep(2)
            payload, api_status, api_code, api_response = get_last_ise_log_entry(before)

        if not payload:
            print(f"  ❌ SKIPPED — ISE deployment did not occur\n")
            result = TestResult(name)
            result.failed.append("  ❌ No ISE payload logged — deployment did not trigger")
            all_results.append(result)
            overall_fail += 1
            deploy_fail_count += 1
            continue

        # Step 4: Show Market Maya API result
        if api_status == "success" and api_code == 200:
            print(f"  🟢 Market Maya: HTTP {api_code} — DEPLOYED SUCCESSFULLY")
            deploy_ok_count += 1
        else:
            print(f"  🔴 Market Maya: HTTP {api_code} — {str(api_response)[:200]}")
            deploy_fail_count += 1

        # Step 5: Validate payload structure
        result = validator_fn(payload, ai_final)

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
    print(f"  Market Maya ISE Deployments: {deploy_ok_count} SUCCESS / {deploy_fail_count} FAILED")
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

    report_file = f"tests/reports/ise_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, "w") as f:
        f.write(f"ISE Test Run: {datetime.now().isoformat()}\n")
        f.write(f"Results: {overall_pass}/{len(TESTS)} tests passed, {total_checks_pass}/{total_checks} checks passed\n\n")
        for r in all_results:
            status, p_count, total = r.summary()
            f.write(f"\n{'='*60}\n{r.name}  [{status}] [{p_count}/{total}]\n")
            for line in r.passed:
                f.write(line + "\n")
            for line in r.failed:
                f.write(line + "\n")
    print(f"\n  Full report saved to: {report_file}")


if __name__ == "__main__":
    run_all()
