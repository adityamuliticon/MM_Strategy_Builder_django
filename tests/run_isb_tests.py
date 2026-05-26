"""
Inbound Signal Bridge – Automated Test Runner
Runs all 20 test prompts, captures deployed payloads, validates against expected values.
Run with Django server active on port 8000:  python manage.py runserver 0.0.0.0:8000
"""
import requests
import json
import time
import os
from datetime import datetime

BASE_URL = "http://localhost:8000/bridge/api/chat"
LOG_FILE = "logs/deployed_strategies.log"

# ─────────────────────────────────────────────────────────────────────────────
# Helper: send one chat turn to ISB endpoint
# ─────────────────────────────────────────────────────────────────────────────
def chat(message, session_id):
    try:
        r = requests.post(BASE_URL, json={"message": message, "session_id": session_id}, timeout=180)
        r.raise_for_status()
        return r.json().get("message", "")
    except Exception as e:
        return f"ERROR: {e}"

# ─────────────────────────────────────────────────────────────────────────────
# Helpers: log file access — filter only ISB entries
# ─────────────────────────────────────────────────────────────────────────────
def isb_log_count():
    if not os.path.exists(LOG_FILE):
        return 0
    count = 0
    with open(LOG_FILE) as f:
        for line in f:
            if line.strip():
                try:
                    entry = json.loads(line)
                    if entry.get("strategy_type") == "inbound_signal_bridge":
                        count += 1
                except Exception:
                    pass
    return count


def get_last_isb_log_entry(before_count):
    """Returns (payload, api_status, api_code, api_response) from the last new ISB log line."""
    if not os.path.exists(LOG_FILE):
        return None, None, None, None
    isb_lines = []
    with open(LOG_FILE) as f:
        for line in f:
            if line.strip():
                try:
                    entry = json.loads(line)
                    if entry.get("strategy_type") == "inbound_signal_bridge":
                        isb_lines.append(entry)
                except Exception:
                    pass
    if len(isb_lines) <= before_count:
        return None, None, None, None
    try:
        entry = isb_lines[-1]
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

    def check_contains(self, label, actual, substring):
        if substring.lower() in str(actual).lower():
            self.passed.append(f"  ✅ {label} contains '{substring}'")
        else:
            self.failed.append(f"  ❌ {label}: expected to contain '{substring}', got={actual!r}")

    def check_in(self, label, item, container):
        if item in container:
            self.passed.append(f"  ✅ {label}: '{item}' present")
        else:
            self.failed.append(f"  ❌ {label}: '{item}' NOT found in {container!r}")

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
    """Return sub leg n (1-indexed) from payload or empty dict."""
    subs = p.get("sub", [])
    return subs[n - 1] if len(subs) >= n else {}


# ─────────────────────────────────────────────────────────────────────────────
# 20 Test Case definitions
# ─────────────────────────────────────────────────────────────────────────────
TESTS = []

def add_test(name, prompt, validator_fn):
    TESTS.append((name, prompt, validator_fn))


# ── PROMPT 1 ──────────────────────────────────────────────────────────────────
def validate_1(p, r):
    t = TestResult("PROMPT 1 – BankNifty FUT Intraday MIS Fix Qty (Core Basics)")
    t.check("is_intraday", p.get("is_intraday"), True)
    t.check("product_type", p.get("product_type"), "MIS")
    t.check("intraday_exit_time_min", p.get("intraday_exit_time_min"), 15)
    t.check("run_mon", p.get("run_mon"), True)
    t.check("run_tue", p.get("run_tue"), True)
    t.check("run_wed", p.get("run_wed"), True)
    t.check("run_thu", p.get("run_thu"), True)
    t.check("run_fri", p.get("run_fri"), True)
    t.check("run_sat", p.get("run_sat"), False)
    t.check("run_sun", p.get("run_sun"), False)
    s1 = sub(p, 1)
    t.check("sub1.exchange", s1.get("exchange"), "NFO")
    t.check("sub1.segment", s1.get("segment"), "FUT")
    t.check("sub1.symbol", s1.get("symbol"), "BANKNIFTY")
    t.check("sub1.contract", s1.get("contract"), "NEAR")
    t.check("sub1.expiry", s1.get("expiry"), "MONTHLY")
    t.check("sub1.atm", s1.get("atm"), 0)
    t.check("sub1.option_type", s1.get("option_type"), "")
    t.check("sub1.qty_distribution", s1.get("qty_distribution"), "Fix")
    t.check("sub1.lot", s1.get("lot"), 1)
    t.check("sub1.qty", s1.get("qty"), 30)
    t.check("sub1.is_trail_sl", s1.get("is_trail_sl"), False)
    return t

add_test("PROMPT 1",
    "Create an intraday TradingView signal strategy for BankNifty futures. Use MIS product, 1 fixed lot, near contract monthly expiry on NFO. Exit 15 minutes before market close. Trade Monday to Friday only.",
    validate_1)


# ── PROMPT 2 ──────────────────────────────────────────────────────────────────
def validate_2(p, r):
    t = TestResult("PROMPT 2 – Positional NRML with Leg Target and Leg SL (No Trail)")
    t.check("is_intraday", p.get("is_intraday"), False)
    t.check("product_type", p.get("product_type"), "NRML")
    t.check("intraday_exit_time_min", p.get("intraday_exit_time_min"), 15)
    s1 = sub(p, 1)
    t.check("sub1.segment", s1.get("segment"), "FUT")
    t.check("sub1.symbol", s1.get("symbol"), "NIFTY")
    t.check("sub1.qty_distribution", s1.get("qty_distribution"), "Fix")
    t.check("sub1.lot", s1.get("lot"), 1)
    t.check("sub1.qty", s1.get("qty"), 25)
    t.check("sub1.target", s1.get("target"), 5000)
    t.check("sub1.target_by", s1.get("target_by"), "Money")
    t.check("sub1.sl", s1.get("sl"), 3000)
    t.check("sub1.sl_by", s1.get("sl_by"), "Money")
    t.check("sub1.is_trail_sl", s1.get("is_trail_sl"), False)
    return t

add_test("PROMPT 2",
    "Create a positional NRML signal strategy for Nifty futures. Fixed 1 lot, near monthly. Set leg target 5000 rupees and leg stoploss 3000 rupees. No trail SL. Exit 15 minutes before close.",
    validate_2)


# ── PROMPT 3 ──────────────────────────────────────────────────────────────────
def validate_3(p, r):
    t = TestResult("PROMPT 3 – Capital(%) Qty Distribution with Required Margin")
    t.check("required_margin", p.get("required_margin"), 500000)
    t.check("is_intraday", p.get("is_intraday"), False)
    t.check("product_type", p.get("product_type"), "NRML")
    s1 = sub(p, 1)
    t.check("sub1.segment", s1.get("segment"), "FUT")
    t.check("sub1.symbol", s1.get("symbol"), "BANKNIFTY")
    t.check("sub1.qty_distribution", s1.get("qty_distribution"), "Capital(%)")
    t.check("sub1.qty", s1.get("qty"), 3)
    t.check("sub1.lot", s1.get("lot"), 1)
    return t

add_test("PROMPT 3",
    "Create a positional signal strategy for BankNifty futures on NFO. Capital is 5 lakh rupees. Use Capital(%) distribution, allocate 3% of capital per trade. Fixed near monthly contract. NRML product.",
    validate_3)


# ── PROMPT 4 ──────────────────────────────────────────────────────────────────
def validate_4(p, r):
    t = TestResult("PROMPT 4 – Capital Risk(%) Qty Distribution with SL Required")
    t.check("required_margin", p.get("required_margin"), 1000000)
    t.check("is_intraday", p.get("is_intraday"), False)
    t.check("product_type", p.get("product_type"), "NRML")
    s1 = sub(p, 1)
    t.check("sub1.segment", s1.get("segment"), "FUT")
    t.check("sub1.symbol", s1.get("symbol"), "BANKNIFTY")
    t.check("sub1.qty_distribution", s1.get("qty_distribution"), "Capital Risk(%)")
    t.check("sub1.qty", s1.get("qty"), 2)
    t.check("sub1.lot", s1.get("lot"), 1)
    t.check("sub1.sl", s1.get("sl"), 1500)
    t.check("sub1.sl_by", s1.get("sl_by"), "Money")
    return t

add_test("PROMPT 4",
    "Create a signal strategy for BankNifty futures. Capital 10 lakh. Risk 2% of capital per trade. Use Capital Risk(%) distribution. Leg stoploss 1500 rupees. Positional NRML, near monthly NFO.",
    validate_4)


# ── PROMPT 5 ──────────────────────────────────────────────────────────────────
def validate_5(p, r):
    t = TestResult("PROMPT 5 – Allocation Method 1 Qty Distribution")
    t.check("is_intraday", p.get("is_intraday"), False)
    t.check("product_type", p.get("product_type"), "NRML")
    s1 = sub(p, 1)
    t.check("sub1.segment", s1.get("segment"), "OPT")
    t.check("sub1.symbol", s1.get("symbol"), "NIFTY")
    t.check("sub1.option_type", s1.get("option_type"), "CE")
    t.check("sub1.atm", s1.get("atm"), 0)
    t.check("sub1.expiry", s1.get("expiry"), "WEEKLY")
    t.check("sub1.contract", s1.get("contract"), "NEAR")
    t.check("sub1.qty_distribution", s1.get("qty_distribution"), "Allocation Method 1")
    t.check("sub1.lot", s1.get("lot"), 1)
    return t

add_test("PROMPT 5",
    "Create a positional NRML signal strategy for Nifty weekly CE ATM options. Use Allocation Method 1 for quantity distribution — equally split capital across all open positions. Near contract.",
    validate_5)


# ── PROMPT 6 ──────────────────────────────────────────────────────────────────
def validate_6(p, r):
    t = TestResult("PROMPT 6 – OPT CE+PE Legs, ATM Offsets, Weekly Expiry")
    t.check("is_intraday", p.get("is_intraday"), True)
    t.check("product_type", p.get("product_type"), "MIS")
    t.check("sub_count", len(p.get("sub", [])), 2)
    s1, s2 = sub(p, 1), sub(p, 2)
    t.check("sub1.segment", s1.get("segment"), "OPT")
    t.check("sub1.symbol", s1.get("symbol"), "NIFTY")
    t.check("sub1.option_type", s1.get("option_type"), "CE")
    t.check("sub1.atm", s1.get("atm"), 1)
    t.check("sub1.expiry", s1.get("expiry"), "WEEKLY")
    t.check("sub1.contract", s1.get("contract"), "NEAR")
    t.check("sub1.qty_distribution", s1.get("qty_distribution"), "Fix")
    t.check("sub1.lot", s1.get("lot"), 1)
    t.check("sub2.segment", s2.get("segment"), "OPT")
    t.check("sub2.symbol", s2.get("symbol"), "NIFTY")
    t.check("sub2.option_type", s2.get("option_type"), "PE")
    t.check("sub2.atm", s2.get("atm"), -1)
    t.check("sub2.expiry", s2.get("expiry"), "WEEKLY")
    t.check("sub2.contract", s2.get("contract"), "NEAR")
    t.check("sub2.qty_distribution", s2.get("qty_distribution"), "Fix")
    t.check("sub2.lot", s2.get("lot"), 1)
    return t

add_test("PROMPT 6",
    "Create an intraday MIS signal strategy with two Nifty option legs on NFO. Leg 1: CE 100 points OTM weekly near 1 lot. Leg 2: PE 100 points OTM weekly near 1 lot. Exit 15 minutes before close.",
    validate_6)


# ── PROMPT 7 ──────────────────────────────────────────────────────────────────
def validate_7(p, r):
    t = TestResult("PROMPT 7 – Stock Segment, NSE Exchange, CNC Product")
    t.check("product_type", p.get("product_type"), "CNC")
    t.check("is_intraday", p.get("is_intraday"), False)
    s1 = sub(p, 1)
    t.check("sub1.exchange", s1.get("exchange"), "NSE")
    t.check("sub1.segment", s1.get("segment"), "Stock")
    t.check("sub1.symbol", s1.get("symbol"), "RELIANCE")
    t.check("sub1.qty_distribution", s1.get("qty_distribution"), "Fix")
    t.check("sub1.lot", s1.get("lot"), 5)
    t.check("sub1.qty", s1.get("qty"), 5)
    t.check("sub1.option_type", s1.get("option_type"), "")
    t.check("sub1.atm", s1.get("atm"), 0)
    return t

add_test("PROMPT 7",
    "Create a signal strategy to trade Reliance stock on NSE. Use CNC product for delivery. Fixed 5 shares (5 lots) per signal. Positional. Exit 15 minutes before close.",
    validate_7)


# ── PROMPT 8 ──────────────────────────────────────────────────────────────────
def validate_8(p, r):
    t = TestResult("PROMPT 8 – Fixed Strike Price (Non-Zero strike_price)")
    t.check("is_intraday", p.get("is_intraday"), False)
    t.check("product_type", p.get("product_type"), "NRML")
    s1 = sub(p, 1)
    t.check("sub1.exchange", s1.get("exchange"), "NFO")
    t.check("sub1.segment", s1.get("segment"), "OPT")
    t.check("sub1.symbol", s1.get("symbol"), "BANKNIFTY")
    t.check("sub1.option_type", s1.get("option_type"), "CE")
    t.check("sub1.expiry", s1.get("expiry"), "WEEKLY")
    t.check("sub1.contract", s1.get("contract"), "NEAR")
    t.check("sub1.strike_price", s1.get("strike_price"), 52000)
    t.check("sub1.qty_distribution", s1.get("qty_distribution"), "Fix")
    t.check("sub1.lot", s1.get("lot"), 1)
    return t

add_test("PROMPT 8",
    "Create a positional NRML signal strategy for BankNifty weekly CE options on NFO. Use a fixed strike price of 52000 instead of ATM-relative selection. 1 lot near contract. Exit 15 min before close.",
    validate_8)


# ── PROMPT 9 ──────────────────────────────────────────────────────────────────
def validate_9(p, r):
    t = TestResult("PROMPT 9 – Leg Trail SL with Max Times (no_of_time_trail_sl=3)")
    t.check("is_intraday", p.get("is_intraday"), False)
    s1 = sub(p, 1)
    t.check("sub1.segment", s1.get("segment"), "FUT")
    t.check("sub1.symbol", s1.get("symbol"), "NIFTY")
    t.check("sub1.qty_distribution", s1.get("qty_distribution"), "Fix")
    t.check("sub1.lot", s1.get("lot"), 1)
    t.check("sub1.qty", s1.get("qty"), 25)
    t.check("sub1.is_trail_sl", s1.get("is_trail_sl"), True)
    t.check("sub1.trail_sl_market_move", s1.get("trail_sl_market_move"), 1000)
    t.check("sub1.trail_sl_move", s1.get("trail_sl_move"), 500)
    t.check("sub1.no_of_time_trail_sl", s1.get("no_of_time_trail_sl"), 3)
    return t

add_test("PROMPT 9",
    "Create a positional NRML signal strategy for Nifty futures, 1 lot near monthly NFO. Enable trail SL on the leg: after every 1000 rupees profit increase, trail the SL by 500 rupees. Maximum 3 trail steps.",
    validate_9)


# ── PROMPT 10 ─────────────────────────────────────────────────────────────────
def validate_10(p, r):
    t = TestResult("PROMPT 10 – Leg Trail SL Unlimited (no_of_time_trail_sl=0)")
    t.check("is_intraday", p.get("is_intraday"), True)
    t.check("product_type", p.get("product_type"), "MIS")
    s1 = sub(p, 1)
    t.check("sub1.segment", s1.get("segment"), "FUT")
    t.check("sub1.symbol", s1.get("symbol"), "BANKNIFTY")
    t.check("sub1.qty_distribution", s1.get("qty_distribution"), "Fix")
    t.check("sub1.lot", s1.get("lot"), 1)
    t.check("sub1.qty", s1.get("qty"), 30)
    t.check("sub1.is_trail_sl", s1.get("is_trail_sl"), True)
    t.check("sub1.trail_sl_market_move", s1.get("trail_sl_market_move"), 500)
    t.check("sub1.trail_sl_move", s1.get("trail_sl_move"), 250)
    t.check("sub1.no_of_time_trail_sl", s1.get("no_of_time_trail_sl"), 0)  # 0 = unlimited
    return t

add_test("PROMPT 10",
    "Create an intraday MIS signal strategy for BankNifty futures on NFO, 1 lot near monthly. Enable leg trail SL: trail after every 500 rupees profit move, trail SL by 250 rupees. Allow unlimited trail steps.",
    validate_10)


# ── PROMPT 11 ─────────────────────────────────────────────────────────────────
def validate_11(p, r):
    t = TestResult("PROMPT 11 – Master Target + Master SL with 2 Legs")
    t.check("is_intraday", p.get("is_intraday"), False)
    t.check("product_type", p.get("product_type"), "NRML")
    t.check("intraday_target", p.get("intraday_target"), 8000)
    t.check("target_by", p.get("target_by"), "Money")
    t.check("intraday_sl", p.get("intraday_sl"), 5000)
    t.check("sl_by", p.get("sl_by"), "Money")
    t.check("sub_count", len(p.get("sub", [])), 2)
    s1, s2 = sub(p, 1), sub(p, 2)
    t.check("sub1.segment", s1.get("segment"), "FUT")
    t.check("sub1.symbol", s1.get("symbol"), "BANKNIFTY")
    t.check("sub1.qty_distribution", s1.get("qty_distribution"), "Fix")
    t.check("sub1.lot", s1.get("lot"), 1)
    t.check("sub1.qty", s1.get("qty"), 30)
    t.check("sub2.segment", s2.get("segment"), "OPT")
    t.check("sub2.symbol", s2.get("symbol"), "NIFTY")
    t.check("sub2.option_type", s2.get("option_type"), "CE")
    t.check("sub2.atm", s2.get("atm"), 0)
    t.check("sub2.expiry", s2.get("expiry"), "WEEKLY")
    return t

add_test("PROMPT 11",
    "Create a positional NRML signal strategy. Leg 1: BankNifty futures 1 lot near monthly NFO. Leg 2: Nifty CE ATM weekly near 1 lot NFO. Set master target 8000 rupees and master stoploss 5000 rupees for combined portfolio.",
    validate_11)


# ── PROMPT 12 ─────────────────────────────────────────────────────────────────
def validate_12(p, r):
    t = TestResult("PROMPT 12 – Working Days Mon-Wed-Fri Only")
    t.check("is_intraday", p.get("is_intraday"), True)
    t.check("product_type", p.get("product_type"), "MIS")
    t.check("run_mon", p.get("run_mon"), True)
    t.check("run_tue", p.get("run_tue"), False)
    t.check("run_wed", p.get("run_wed"), True)
    t.check("run_thu", p.get("run_thu"), False)
    t.check("run_fri", p.get("run_fri"), True)
    t.check("run_sat", p.get("run_sat"), False)
    t.check("run_sun", p.get("run_sun"), False)
    s1 = sub(p, 1)
    t.check("sub1.segment", s1.get("segment"), "FUT")
    t.check("sub1.symbol", s1.get("symbol"), "BANKNIFTY")
    t.check("sub1.qty_distribution", s1.get("qty_distribution"), "Fix")
    t.check("sub1.lot", s1.get("lot"), 1)
    t.check("sub1.qty", s1.get("qty"), 30)
    return t

add_test("PROMPT 12",
    "Create an intraday MIS signal strategy for BankNifty futures, 1 lot near monthly NFO. Trade only on Monday, Wednesday, and Friday — do not trade on Tuesday, Thursday, Saturday, or Sunday.",
    validate_12)


# ── PROMPT 13 ─────────────────────────────────────────────────────────────────
def validate_13(p, r):
    t = TestResult("PROMPT 13 – Saturday Enabled (MCX Exchange, GOLD Futures)")
    t.check("is_intraday", p.get("is_intraday"), True)
    t.check("product_type", p.get("product_type"), "MIS")
    t.check("run_mon", p.get("run_mon"), True)
    t.check("run_tue", p.get("run_tue"), True)
    t.check("run_wed", p.get("run_wed"), True)
    t.check("run_thu", p.get("run_thu"), True)
    t.check("run_fri", p.get("run_fri"), True)
    t.check("run_sat", p.get("run_sat"), True)
    t.check("run_sun", p.get("run_sun"), False)
    s1 = sub(p, 1)
    t.check("sub1.exchange", s1.get("exchange"), "MCX")
    t.check("sub1.segment", s1.get("segment"), "FUT")
    t.check("sub1.symbol", s1.get("symbol"), "GOLD")
    t.check("sub1.contract", s1.get("contract"), "NEAR")
    t.check("sub1.expiry", s1.get("expiry"), "MONTHLY")
    t.check("sub1.qty_distribution", s1.get("qty_distribution"), "Fix")
    t.check("sub1.lot", s1.get("lot"), 1)
    return t

add_test("PROMPT 13",
    "Create an intraday MIS signal strategy for GOLD futures on MCX exchange. 1 lot fixed, near monthly contract. Trade Monday through Saturday — enable Saturday trading for MCX commodity market. Do not trade on Sunday.",
    validate_13)


# ── PROMPT 14 ─────────────────────────────────────────────────────────────────
def validate_14(p, r):
    t = TestResult("PROMPT 14 – Exit Minutes Non-Default (30 Minutes Before Close)")
    t.check("is_intraday", p.get("is_intraday"), True)
    t.check("product_type", p.get("product_type"), "MIS")
    t.check("intraday_exit_time_min", p.get("intraday_exit_time_min"), 30)
    t.check("run_mon", p.get("run_mon"), True)
    t.check("run_fri", p.get("run_fri"), True)
    s1 = sub(p, 1)
    t.check("sub1.segment", s1.get("segment"), "FUT")
    t.check("sub1.symbol", s1.get("symbol"), "BANKNIFTY")
    t.check("sub1.qty_distribution", s1.get("qty_distribution"), "Fix")
    t.check("sub1.lot", s1.get("lot"), 1)
    t.check("sub1.qty", s1.get("qty"), 30)
    return t

add_test("PROMPT 14",
    "Create an intraday MIS signal strategy for BankNifty futures, 1 lot near monthly NFO. Exit 30 minutes before market close (not the default 15 minutes). Trade all weekdays.",
    validate_14)


# ── PROMPT 15 ─────────────────────────────────────────────────────────────────
def validate_15(p, r):
    t = TestResult("PROMPT 15 – Auto Sqroff on Contract Expiry Disabled")
    t.check("is_intraday", p.get("is_intraday"), False)
    t.check("product_type", p.get("product_type"), "NRML")
    t.check("auto_sqroff_on_contract_exp", p.get("auto_sqroff_on_contract_exp"), False)
    s1 = sub(p, 1)
    t.check("sub1.segment", s1.get("segment"), "FUT")
    t.check("sub1.symbol", s1.get("symbol"), "NIFTY")
    t.check("sub1.expiry", s1.get("expiry"), "MONTHLY")
    t.check("sub1.qty_distribution", s1.get("qty_distribution"), "Fix")
    t.check("sub1.lot", s1.get("lot"), 1)
    t.check("sub1.qty", s1.get("qty"), 25)
    return t

add_test("PROMPT 15",
    "Create a positional NRML signal strategy for Nifty futures, 1 lot near monthly NFO. Disable auto square-off on contract expiry — I want to manage expiry manually.",
    validate_15)


# ── PROMPT 16 ─────────────────────────────────────────────────────────────────
def validate_16(p, r):
    t = TestResult("PROMPT 16 – Sqroff All Legs + Sqroff on Rejection (Safety Features)")
    t.check("is_intraday", p.get("is_intraday"), False)
    t.check("product_type", p.get("product_type"), "NRML")
    t.check("sqroffAllLegs", p.get("sqroffAllLegs"), True)
    t.check("pause_and_sqroff_trading_on_margin_exeed", p.get("pause_and_sqroff_trading_on_margin_exeed"), True)
    t.check("sub_count", len(p.get("sub", [])), 2)
    s1, s2 = sub(p, 1), sub(p, 2)
    t.check("sub1.segment", s1.get("segment"), "FUT")
    t.check("sub1.symbol", s1.get("symbol"), "BANKNIFTY")
    t.check("sub1.qty_distribution", s1.get("qty_distribution"), "Fix")
    t.check("sub1.lot", s1.get("lot"), 1)
    t.check("sub1.qty", s1.get("qty"), 30)
    t.check("sub2.segment", s2.get("segment"), "OPT")
    t.check("sub2.symbol", s2.get("symbol"), "BANKNIFTY")
    t.check("sub2.option_type", s2.get("option_type"), "CE")
    t.check("sub2.atm", s2.get("atm"), 0)
    t.check("sub2.expiry", s2.get("expiry"), "WEEKLY")
    return t

add_test("PROMPT 16",
    "Create a positional NRML signal strategy. Leg 1: BankNifty futures 1 lot near monthly NFO. Leg 2: BankNifty CE ATM weekly near 1 lot NFO. Enable Sqroff All Legs — if any one leg exits on target or SL, close all other legs. Also enable Sqroff on Rejection — if any order is rejected by broker, close all open legs immediately.",
    validate_16)


# ── PROMPT 17 ─────────────────────────────────────────────────────────────────
def validate_17(p, r):
    t = TestResult("PROMPT 17 – Max Position + Max Capital Allocation Percent")
    t.check("required_margin", p.get("required_margin"), 2000000)
    t.check("is_intraday", p.get("is_intraday"), False)
    t.check("product_type", p.get("product_type"), "NRML")
    t.check("max_position", p.get("max_position"), 5)
    t.check("max_position_allocation_percent", p.get("max_position_allocation_percent"), 20)
    t.check("sub_count", len(p.get("sub", [])), 2)
    s1, s2 = sub(p, 1), sub(p, 2)
    t.check("sub1.exchange", s1.get("exchange"), "NSE")
    t.check("sub1.segment", s1.get("segment"), "Stock")
    t.check("sub1.symbol", s1.get("symbol"), "RELIANCE")
    t.check("sub1.qty_distribution", s1.get("qty_distribution"), "Capital Risk(%)")
    t.check("sub1.qty", s1.get("qty"), 5)
    t.check("sub1.lot", s1.get("lot"), 1)
    t.check("sub1.sl", s1.get("sl"), 2000)
    t.check("sub2.exchange", s2.get("exchange"), "NSE")
    t.check("sub2.segment", s2.get("segment"), "Stock")
    t.check("sub2.symbol", s2.get("symbol"), "INFY")
    t.check("sub2.qty_distribution", s2.get("qty_distribution"), "Capital Risk(%)")
    t.check("sub2.qty", s2.get("qty"), 5)
    t.check("sub2.lot", s2.get("lot"), 1)
    t.check("sub2.sl", s2.get("sl"), 1500)
    return t

add_test("PROMPT 17",
    "Create a positional NRML signal strategy for portfolio execution. Capital 20 lakh. Use Capital Risk(%) distribution, risk 5% per stock. Leg 1: RELIANCE stock on NSE, SL 2000. Leg 2: INFY stock on NSE, SL 1500. Set max 5 simultaneous positions. Cap each symbol allocation at 20% of total capital.",
    validate_17)


# ── PROMPT 18 ─────────────────────────────────────────────────────────────────
def validate_18(p, r):
    t = TestResult("PROMPT 18 – 3-Leg Strategy: FUT + CE OPT + PE OPT Multi-Symbol")
    t.check("is_intraday", p.get("is_intraday"), False)
    t.check("product_type", p.get("product_type"), "NRML")
    t.check("sub_count", len(p.get("sub", [])), 3)
    s1, s2, s3 = sub(p, 1), sub(p, 2), sub(p, 3)
    t.check("sub1.segment", s1.get("segment"), "FUT")
    t.check("sub1.symbol", s1.get("symbol"), "BANKNIFTY")
    t.check("sub1.expiry", s1.get("expiry"), "MONTHLY")
    t.check("sub1.qty_distribution", s1.get("qty_distribution"), "Fix")
    t.check("sub1.lot", s1.get("lot"), 1)
    t.check("sub1.qty", s1.get("qty"), 30)
    t.check("sub1.option_type", s1.get("option_type"), "")
    t.check("sub2.segment", s2.get("segment"), "OPT")
    t.check("sub2.symbol", s2.get("symbol"), "NIFTY")
    t.check("sub2.option_type", s2.get("option_type"), "CE")
    t.check("sub2.atm", s2.get("atm"), 0)
    t.check("sub2.expiry", s2.get("expiry"), "WEEKLY")
    t.check("sub2.qty_distribution", s2.get("qty_distribution"), "Fix")
    t.check("sub2.lot", s2.get("lot"), 1)
    t.check("sub3.segment", s3.get("segment"), "OPT")
    t.check("sub3.symbol", s3.get("symbol"), "NIFTY")
    t.check("sub3.option_type", s3.get("option_type"), "PE")
    t.check("sub3.atm", s3.get("atm"), 0)
    t.check("sub3.expiry", s3.get("expiry"), "WEEKLY")
    t.check("sub3.qty_distribution", s3.get("qty_distribution"), "Fix")
    t.check("sub3.lot", s3.get("lot"), 1)
    return t

add_test("PROMPT 18",
    "Create a positional NRML signal strategy with 3 legs. Leg 1: BankNifty futures 1 lot near monthly NFO. Leg 2: Nifty CE ATM weekly near 1 lot NFO. Leg 3: Nifty PE ATM weekly near 1 lot NFO. All legs execute on a single inbound signal.",
    validate_18)


# ── PROMPT 19 ─────────────────────────────────────────────────────────────────
def validate_19(p, r):
    t = TestResult("PROMPT 19 – NEXT Contract + BFO Exchange SENSEX + Required Margin + Descriptions")
    t.check("required_margin", p.get("required_margin"), 300000)
    t.check("is_intraday", p.get("is_intraday"), False)
    t.check("product_type", p.get("product_type"), "NRML")
    s1 = sub(p, 1)
    t.check("sub1.exchange", s1.get("exchange"), "BFO")
    t.check("sub1.segment", s1.get("segment"), "OPT")
    t.check("sub1.symbol", s1.get("symbol"), "SENSEX")
    t.check("sub1.contract", s1.get("contract"), "NEXT")
    t.check("sub1.expiry", s1.get("expiry"), "WEEKLY")
    t.check("sub1.option_type", s1.get("option_type"), "CE")
    t.check("sub1.atm", s1.get("atm"), 0)
    t.check("sub1.qty_distribution", s1.get("qty_distribution"), "Fix")
    t.check("sub1.lot", s1.get("lot"), 1)
    t.check_contains("short_description", p.get("short_description", ""), "SENSEX")
    t.check_contains("long_description", p.get("long_description", ""), "SENSEX")
    return t

add_test("PROMPT 19",
    "Create a positional NRML signal strategy for SENSEX options on BFO exchange. Leg 1: SENSEX CE ATM NEXT weekly 1 lot. Capital base is 3 lakh rupees. Short description: 'SENSEX BFO next-week CE signal bridge.' Long description: 'Receives TradingView alerts on SENSEX weekly CE options, NEXT contract on BFO exchange. Capital 3L, NRML positional. Exit 15 min before close.'",
    validate_19)


# ── PROMPT 20 ─────────────────────────────────────────────────────────────────
def validate_20(p, r):
    t = TestResult("PROMPT 20 – Maximum Complexity (ALL Parameters)")
    # Main tab
    t.check("is_intraday", p.get("is_intraday"), False)
    t.check("product_type", p.get("product_type"), "NRML")
    t.check("required_margin", p.get("required_margin"), 1500000)
    t.check("intraday_target", p.get("intraday_target"), 10000)
    t.check("target_by", p.get("target_by"), "Money")
    t.check("intraday_sl", p.get("intraday_sl"), 6000)
    t.check("sl_by", p.get("sl_by"), "Money")
    t.check("max_position", p.get("max_position"), 8)
    t.check("max_position_allocation_percent", p.get("max_position_allocation_percent"), 25)
    # Safety features
    t.check("sqroffAllLegs", p.get("sqroffAllLegs"), True)
    t.check("pause_and_sqroff_trading_on_margin_exeed", p.get("pause_and_sqroff_trading_on_margin_exeed"), True)
    t.check("auto_sqroff_on_contract_exp", p.get("auto_sqroff_on_contract_exp"), False)
    # Working days
    t.check("run_mon", p.get("run_mon"), True)
    t.check("run_tue", p.get("run_tue"), True)
    t.check("run_wed", p.get("run_wed"), True)
    t.check("run_thu", p.get("run_thu"), True)
    t.check("run_fri", p.get("run_fri"), False)
    t.check("run_sat", p.get("run_sat"), False)
    t.check("run_sun", p.get("run_sun"), False)
    # Advance
    t.check("intraday_exit_time_min", p.get("intraday_exit_time_min"), 20)
    t.check("margin_stock_intraday", p.get("margin_stock_intraday"), 25)
    t.check("margin_stock_positional", p.get("margin_stock_positional"), 80)
    t.check("margin_futopt_positional", p.get("margin_futopt_positional"), 20)
    # Sub legs
    t.check("sub_count", len(p.get("sub", [])), 3)
    s1, s2, s3 = sub(p, 1), sub(p, 2), sub(p, 3)
    t.check("sub1.segment", s1.get("segment"), "FUT")
    t.check("sub1.symbol", s1.get("symbol"), "BANKNIFTY")
    t.check("sub1.qty_distribution", s1.get("qty_distribution"), "Fix")
    t.check("sub1.lot", s1.get("lot"), 1)
    t.check("sub1.qty", s1.get("qty"), 30)
    t.check("sub1.sl", s1.get("sl"), 4000)
    t.check("sub1.is_trail_sl", s1.get("is_trail_sl"), True)
    t.check("sub1.trail_sl_market_move", s1.get("trail_sl_market_move"), 2000)
    t.check("sub1.trail_sl_move", s1.get("trail_sl_move"), 1000)
    t.check("sub1.no_of_time_trail_sl", s1.get("no_of_time_trail_sl"), 5)
    t.check("sub2.segment", s2.get("segment"), "OPT")
    t.check("sub2.symbol", s2.get("symbol"), "NIFTY")
    t.check("sub2.option_type", s2.get("option_type"), "CE")
    t.check("sub2.atm", s2.get("atm"), 0)
    t.check("sub2.expiry", s2.get("expiry"), "WEEKLY")
    t.check("sub2.qty_distribution", s2.get("qty_distribution"), "Capital Risk(%)")
    t.check("sub2.qty", s2.get("qty"), 3)
    t.check("sub2.lot", s2.get("lot"), 1)
    t.check("sub2.sl", s2.get("sl"), 2500)
    t.check("sub3.segment", s3.get("segment"), "OPT")
    t.check("sub3.symbol", s3.get("symbol"), "NIFTY")
    t.check("sub3.option_type", s3.get("option_type"), "PE")
    t.check("sub3.atm", s3.get("atm"), 0)
    t.check("sub3.expiry", s3.get("expiry"), "WEEKLY")
    t.check("sub3.qty_distribution", s3.get("qty_distribution"), "Capital Risk(%)")
    t.check("sub3.qty", s3.get("qty"), 3)
    t.check("sub3.lot", s3.get("lot"), 1)
    t.check("sub3.sl", s3.get("sl"), 2500)
    # Descriptions
    t.check_contains("short_description", p.get("short_description", ""), "ISB")
    t.check_contains("long_description", p.get("long_description", ""), "BankNifty")
    # Fixed field
    t.check("strategy_type_id", p.get("strategy_type_id"), "XBZs7OE0aMivKaB0$aA0$Wej3PcwaC0$aC0$")
    return t

add_test("PROMPT 20",
    """Create a positional NRML signal strategy called 'ISB Full Param Test'. Capital 15 lakh.

Leg 1: BankNifty futures NFO, 1 lot fixed, near monthly. SL 4000 rupees. Trail SL: every 2000 rupees profit trail by 1000 rupees, max 5 trail steps.
Leg 2: Nifty CE ATM weekly near 1 lot NFO. Qty distribution Capital Risk(%), risk 3% of capital. SL 2500 rupees.
Leg 3: Nifty PE ATM weekly near 1 lot NFO. Qty distribution Capital Risk(%), risk 3% of capital. SL 2500 rupees.

Master target 10000 rupees. Master SL 6000 rupees. Max 8 simultaneous positions. Cap each symbol at 25% of capital. Enable Sqroff All Legs. Enable Sqroff on Rejection. Disable auto sqroff on contract expiry.

Trade only Monday, Tuesday, Wednesday, Thursday — disable Friday, Saturday, Sunday. Exit 20 minutes before market close.

Stock intraday margin 25%. Stock positional margin 80%. Future & Option margin 20%.

Short description: 'ISB max complexity test — 3 legs, Capital Risk(%), all safety features.' Long description: 'Full-parameter ISB strategy with BankNifty FUT Fix SL trail, Nifty CE+PE Capital Risk(%), master target/SL, all safety switches, restricted working days, non-default margins and exit time.'""",
    validate_20)


# ─────────────────────────────────────────────────────────────────────────────
# Main runner
# ─────────────────────────────────────────────────────────────────────────────
def run_all():
    overall_pass = 0
    overall_fail = 0
    all_results = []

    print("\n" + "="*70)
    print("  INBOUND SIGNAL BRIDGE — AUTOMATED TEST SUITE")
    print("  20 Prompts × Full Payload Validation")
    print("  Server: http://localhost:8000/bridge/api/chat")
    print("="*70)

    deploy_ok_count = 0
    deploy_fail_count = 0

    for idx, (name, prompt, validator_fn) in enumerate(TESTS, 1):
        print(f"\n{'─'*70}")
        print(f"▶  Running {name} ...")

        session_id = f"isb_autotest_{idx}_{int(time.time())}"
        before = isb_log_count()

        # Step 1: Send strategy prompt
        print("  → Sending strategy prompt ...")
        ai_preview = chat(prompt, session_id)

        # Step 2: Confirm deployment
        print("  → Confirming deployment ...")
        ai_final = chat("yes proceed deploy it", session_id)

        # Step 3: Wait and grab ISB log entry
        time.sleep(2)
        payload, api_status, api_code, api_response = get_last_isb_log_entry(before)

        if not payload:
            print(f"  ⚠️  NO LOG ENTRY — trying one more confirm ...")
            chat("yes confirm deploy", session_id)
            time.sleep(2)
            payload, api_status, api_code, api_response = get_last_isb_log_entry(before)

        if not payload:
            print(f"  ❌ SKIPPED — ISB deployment did not occur\n")
            result = TestResult(name)
            result.failed.append("  ❌ No ISB payload logged — deployment did not trigger")
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
    print(f"  Market Maya ISB Deployments: {deploy_ok_count} SUCCESS / {deploy_fail_count} FAILED")
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

    report_file = f"tests/reports/isb_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, "w") as f:
        f.write(f"ISB Test Run: {datetime.now().isoformat()}\n")
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
