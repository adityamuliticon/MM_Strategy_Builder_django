"""
Rapid Execution Scalper – Automated End-to-End Test Runner
20 prompts covering every parameter and every meaningful combination.
Sends natural-language prompts → LLM → deployed payload → validates against expected values.
No mocks. Reads the real deployed payload from logs/saved_strategies.log.
"""
import requests
import json
import time
import os
from datetime import datetime

BASE_URL = "http://localhost:8000/scalper/api/chat"
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


def last_res_log_count():
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
                if entry.get("strategy_type") == "rapid_execution_scalper":
                    count += 1
            except Exception:
                pass
    return count


def get_last_res_log_entry(before_count):
    if not os.path.exists(LOG_FILE):
        return None, None, None, None
    res_entries = []
    with open(LOG_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("strategy_type") == "rapid_execution_scalper":
                    res_entries.append(entry)
            except Exception:
                pass
    if len(res_entries) <= before_count:
        return None, None, None, None
    entry = res_entries[-1]
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


def hleg(p, n):
    """Return nth hedge leg (1-indexed) from payload's sub array."""
    legs = p.get("sub", [])
    return legs[n - 1] if len(legs) >= n else {}


# ─────────────────────────────────────────────────────────────────────────────
# 20 Test cases
# ─────────────────────────────────────────────────────────────────────────────
TESTS = []

def add_test(name, prompt, validator_fn):
    TESTS.append((name, prompt, validator_fn))


# ── PROMPT 1 ──────────────────────────────────────────────────────────────────
# Covers: BankNifty FUT intraday BUY, 100-point avg, default lot/qty, MIS,
#         intraday_target mirrors target, fixed constants (strategy_id, order_type)
# ─────────────────────────────────────────────────────────────────────────────
def validate_1(p, r):
    t = TestResult("PROMPT 1 — BankNifty FUT Intraday BUY, 100-pt avg, all defaults")
    t.check("main_exchange",       p.get("main_exchange"),       "NFO")
    t.check("main_segment",        p.get("main_segment"),        "FUT")
    t.check("main_symbol",         p.get("main_symbol"),         "BANKNIFTY")
    t.check("main_contract",       p.get("main_contract"),       "NEAR")
    t.check("main_expiry",         p.get("main_expiry"),         "MONTHLY")
    t.check("is_intraday",         p.get("is_intraday"),         True)
    t.check("product_type",        p.get("product_type"),        "MIS")
    t.check("jobbing_side",        p.get("jobbing_side"),        "BUY")
    t.check("lot",                 int(p.get("lot", 0)),         1)
    t.check("qty",                 int(p.get("qty", 0)),         30)   # BANKNIFTY=30 × 1
    t.check("qty_type",            p.get("qty_type"),            "Qty")
    t.check("average_by",          p.get("average_by"),          "Point")
    t.check("average_value",       float(p.get("average_value", 0)), 100.0)
    # LLM may strip leading zero: "09:20" → "9:20"; use contains to handle both
    t.check_contains("intraday_entry_time contains 9:20", p.get("intraday_entry_time", ""), "9:20")
    t.check("intraday_exit_time",  p.get("intraday_exit_time"),  "15:00")
    # For intraday: target=0 (LLM puts value in intraday_target, not target)
    t.check("target",              float(p.get("target", -1)),   0.0)
    t.check_gt("intraday_target > 0",  p.get("intraday_target", 0), 0)
    # FUT: OPT fields must be empty/zero
    t.check("option_type",         p.get("option_type"),         "")
    t.check("atm",                 int(p.get("atm", 0)),         0)
    t.check("strike_price",        int(p.get("strike_price", 0)), 0)
    # All off by default
    t.check("scalping_opening_qty",       int(p.get("scalping_opening_qty", 0)),  0)
    t.check("increase_qty_on_avg",        p.get("increase_qty_on_avg"),           False)
    t.check("sqroff_on_maximum_steps",    p.get("sqroff_on_maximum_steps"),       False)
    t.check("calculate_qty_on_market_jump", p.get("calculate_qty_on_market_jump"), False)
    t.check("reset_cycle_by_master_tpsl", p.get("reset_cycle_by_master_tpsl"),   False)
    t.check("is_trail_sl",                p.get("is_trail_sl"),                   False)
    t.check("is_auto_rollover",           p.get("is_auto_rollover"),              False)
    t.check("is_add_hedge_leg",           p.get("is_add_hedge_leg"),              False)
    # Fixed constants
    t.check("strategy_id",         p.get("strategy_id"),         "YioJhK5IqBULe8fPLMnXaAaC0$aC0$")
    t.check("order_type",          p.get("order_type"),          "Market Order")
    t.check("allow_update_parameters", p.get("allow_update_parameters"), True)
    t.check("rebacktest",          p.get("rebacktest"),          False)
    t.check("effect_all_sub_strategies", p.get("effect_all_sub_strategies"), False)
    t.check_nonempty("short_description", p.get("short_description"))
    t.check_nonempty("long_description",  p.get("long_description"))
    return t

add_test("PROMPT 1",
    "Create a BankNifty intraday buy-side scalping strategy. Average every 100 points. "
    "Start at 9:20, exit at 15:00. 1 lot per step.",
    validate_1)


# ── PROMPT 2 ──────────────────────────────────────────────────────────────────
# Covers: SELL side, percentage average AND target, 3 lots, custom exit time
# ─────────────────────────────────────────────────────────────────────────────
def validate_2(p, r):
    t = TestResult("PROMPT 2 — BankNifty SELL side, percentage avg+target, 3 lots, exit 15:15")
    t.check("main_symbol",    p.get("main_symbol"),   "BANKNIFTY")
    t.check("main_segment",   p.get("main_segment"),  "FUT")
    t.check("jobbing_side",   p.get("jobbing_side"),  "SELL")
    t.check("lot",            int(p.get("lot", 0)),   3)
    t.check("qty",            int(p.get("qty", 0)),   90)   # BANKNIFTY=30 × 3
    t.check("average_by",     p.get("average_by"),    "Percentage")
    t.check("average_value",  float(p.get("average_value", 0)), 0.5)
    t.check("target_by",      p.get("target_by"),     "Percentage")
    # Intraday: target=0, actual value in intraday_target
    t.check("target",         float(p.get("target", -1)), 0.0)
    t.check_gt("intraday_target > 0", p.get("intraday_target", 0), 0)
    t.check("intraday_exit_time", p.get("intraday_exit_time"), "15:15")
    t.check("is_intraday",    p.get("is_intraday"),   True)
    t.check("product_type",   p.get("product_type"),  "MIS")
    return t

add_test("PROMPT 2",
    "Create a BankNifty intraday sell-side scalping strategy. "
    "Average every 0.5% move. 3 lots per averaging step. Target 0.5% per step. "
    "Exit at 15:15.",
    validate_2)


# ── PROMPT 3 ──────────────────────────────────────────────────────────────────
# Covers: Nifty OPT CE, ATM+100 (OTM CE), 2 lots, weekly expiry,
#         qty = NIFTY(65) × 2 = 130
# ─────────────────────────────────────────────────────────────────────────────
def validate_3(p, r):
    t = TestResult("PROMPT 3 — Nifty OPT CE OTM+100, weekly, 2 lots (qty=130)")
    t.check("main_exchange",  p.get("main_exchange"), "NFO")
    t.check("main_segment",   p.get("main_segment"),  "OPT")
    t.check("main_symbol",    p.get("main_symbol"),   "NIFTY")
    t.check("main_expiry",    p.get("main_expiry"),   "WEEKLY")
    t.check("option_type",    p.get("option_type"),   "CE")
    t.check_gte("atm OTM CE >= 100", p.get("atm", 0), 100)
    t.check("lot",            int(p.get("lot", 0)),   2)
    t.check("qty",            int(p.get("qty", 0)),   130)   # NIFTY=65 × 2
    t.check("average_by",     p.get("average_by"),    "Point")
    t.check("average_value",  float(p.get("average_value", 0)), 50.0)
    t.check("is_intraday",    p.get("is_intraday"),   True)
    t.check("product_type",   p.get("product_type"),  "MIS")
    return t

add_test("PROMPT 3",
    "Create a Nifty intraday buy-side options scalping strategy. "
    "Trade CE options 100 points OTM (above ATM). 2 lots per step, weekly expiry. "
    "Average every 50 points.",
    validate_3)


# ── PROMPT 4 ──────────────────────────────────────────────────────────────────
# Covers: scalping_opening_qty (first entry override), custom max steps
# ─────────────────────────────────────────────────────────────────────────────
def validate_4(p, r):
    t = TestResult("PROMPT 4 — Opening qty=5 (first entry), per-step lot=2, max steps=8")
    t.check("main_symbol",          p.get("main_symbol"),             "BANKNIFTY")
    t.check("lot",                  int(p.get("lot", 0)),             2)
    t.check("qty",                  int(p.get("qty", 0)),             60)   # 2 × 30
    t.check("scalping_opening_qty", int(p.get("scalping_opening_qty", 0)), 5)
    t.check("maximum_steps",        int(p.get("maximum_steps", 0)),   8)
    t.check("is_intraday",          p.get("is_intraday"),             True)
    t.check("jobbing_side",         p.get("jobbing_side"),            "BUY")
    return t

add_test("PROMPT 4",
    "Create a BankNifty intraday buy scalping strategy. "
    "Open the first entry with 5 lots. Each subsequent averaging step adds 2 lots. "
    "Average every 100 points. Maximum 8 averaging steps.",
    validate_4)


# ── PROMPT 5 ──────────────────────────────────────────────────────────────────
# Covers: increase_qty_on_avg, increase_qty_type = "Multiply", increase_qty = 2
# ─────────────────────────────────────────────────────────────────────────────
def validate_5(p, r):
    t = TestResult("PROMPT 5 — Multiply qty ×2 at each averaging step")
    t.check("main_symbol",        p.get("main_symbol"),         "NIFTY")
    t.check("lot",                int(p.get("lot", 0)),         1)
    t.check("increase_qty_on_avg",  p.get("increase_qty_on_avg"),  True)
    t.check("increase_qty_type",    p.get("increase_qty_type"),    "Multiply")
    t.check("increase_qty",         float(p.get("increase_qty", 0)), 2.0)
    t.check("average_by",           p.get("average_by"),            "Point")
    t.check("average_value",        float(p.get("average_value", 0)), 100.0)
    t.check("is_intraday",          p.get("is_intraday"),            True)
    return t

add_test("PROMPT 5",
    "Create a Nifty intraday buy-side scalping strategy. 1 lot per step. "
    "Average every 100 points. Double the quantity at each averaging step (multiply by 2).",
    validate_5)


# ── PROMPT 6 ──────────────────────────────────────────────────────────────────
# Covers: increase_qty_on_avg, increase_qty_type = "Increase", increase_qty = 1
# ─────────────────────────────────────────────────────────────────────────────
def validate_6(p, r):
    t = TestResult("PROMPT 6 — Add 1 lot at each averaging step (Increase type)")
    t.check("main_symbol",       p.get("main_symbol"),         "BANKNIFTY")
    t.check("lot",               int(p.get("lot", 0)),         1)
    t.check("average_value",     float(p.get("average_value", 0)), 150.0)
    t.check("increase_qty_on_avg",  p.get("increase_qty_on_avg"),  True)
    t.check("increase_qty_type",    p.get("increase_qty_type"),    "Increase")
    t.check("increase_qty",         float(p.get("increase_qty", 0)), 1.0)
    t.check("is_intraday",          p.get("is_intraday"),            True)
    return t

add_test("PROMPT 6",
    "Create a BankNifty intraday buy scalping strategy. 1 lot per step. "
    "Average every 150 points. Add 1 extra lot at each averaging step.",
    validate_6)


# ── PROMPT 7 ──────────────────────────────────────────────────────────────────
# Covers: reset_cycle_by_master_tpsl, master_tp_money, master_sl_money
#         is_trail_sl must remain false
# ─────────────────────────────────────────────────────────────────────────────
def validate_7(p, r):
    t = TestResult("PROMPT 7 — Master TP 10000 + Master SL 5000, trail SL off")
    t.check("main_symbol",               p.get("main_symbol"),               "BANKNIFTY")
    t.check("reset_cycle_by_master_tpsl", p.get("reset_cycle_by_master_tpsl"), True)
    t.check("master_tp_money",           float(p.get("master_tp_money", 0)),  10000.0)
    t.check("master_sl_money",           float(p.get("master_sl_money", 0)),  5000.0)
    t.check("is_trail_sl",               p.get("is_trail_sl"),                False)
    t.check("profit_move",               float(p.get("profit_move", 0)),      0.0)
    t.check("sl_move",                   float(p.get("sl_move", 0)),          0.0)
    return t

add_test("PROMPT 7",
    "Create a BankNifty intraday buy scalping strategy. Average every 100 points. "
    "Master target 10000 rupees and master SL 5000 rupees. Close all positions on either limit. "
    "No trail SL.",
    validate_7)


# ── PROMPT 8 ──────────────────────────────────────────────────────────────────
# Covers: Master TP/SL + Trail SL (profit_move, sl_move, no_of_trail_sl)
# ─────────────────────────────────────────────────────────────────────────────
def validate_8(p, r):
    t = TestResult("PROMPT 8 — Master TP/SL + Trail SL every 3000/1500, max 5 steps")
    t.check("reset_cycle_by_master_tpsl", p.get("reset_cycle_by_master_tpsl"), True)
    t.check("master_tp_money",  float(p.get("master_tp_money", 0)),  15000.0)
    t.check("master_sl_money",  float(p.get("master_sl_money", 0)),  8000.0)
    t.check("is_trail_sl",      p.get("is_trail_sl"),                True)
    t.check("profit_move",      float(p.get("profit_move", 0)),      3000.0)
    t.check("sl_move",          float(p.get("sl_move", 0)),          1500.0)
    t.check("no_of_trail_sl",   int(p.get("no_of_trail_sl", 0)),     5)
    return t

add_test("PROMPT 8",
    "Create a BankNifty intraday buy scalping strategy. 1 lot, average every 100 points. "
    "Master target 15000 rupees and master SL 8000 rupees. "
    "Enable trail SL: for every 3000 rupees profit increase, trail the master SL by 1500 rupees. "
    "Maximum 5 trail steps.",
    validate_8)


# ── PROMPT 9 ──────────────────────────────────────────────────────────────────
# Covers: sqroff_on_maximum_steps, reset_cycle_on_positive_mtm, maximum_steps
# ─────────────────────────────────────────────────────────────────────────────
def validate_9(p, r):
    t = TestResult("PROMPT 9 — Sqroff on max steps + reset cycle on positive MTM at 5 steps")
    t.check("main_symbol",              p.get("main_symbol"),              "BANKNIFTY")
    t.check("maximum_steps",            int(p.get("maximum_steps", 0)),    10)
    t.check("sqroff_on_maximum_steps",  p.get("sqroff_on_maximum_steps"),  True)
    t.check("reset_cycle_on_positive_mtm", int(p.get("reset_cycle_on_positive_mtm", 0)), 5)
    t.check("is_intraday",              p.get("is_intraday"),              True)
    return t

add_test("PROMPT 9",
    "Create a BankNifty intraday buy scalping strategy. Average every 100 points. "
    "Maximum 10 averaging steps. When max steps is reached, close all positions immediately. "
    "Also reset the cycle automatically when 5 or more averaging steps are open and overall MTM is positive.",
    validate_9)


# ── PROMPT 10 ─────────────────────────────────────────────────────────────────
# Covers: SENSEX BFO FUT, positional NRML, required_margin, no target (0)
# ─────────────────────────────────────────────────────────────────────────────
def validate_10(p, r):
    t = TestResult("PROMPT 10 — SENSEX BFO FUT, Positional NRML, no target, margin 50000")
    t.check("main_exchange",   p.get("main_exchange"),  "BFO")
    t.check("main_segment",    p.get("main_segment"),   "FUT")
    t.check("main_symbol",     p.get("main_symbol"),    "SENSEX")
    t.check("is_intraday",     p.get("is_intraday"),    False)
    t.check("product_type",    p.get("product_type"),   "NRML")
    t.check("average_value",   float(p.get("average_value", 0)), 200.0)
    t.check("target",          float(p.get("target", 0)),        0.0)
    t.check("required_margin", float(p.get("required_margin", 0)), 50000.0)
    t.check("lot",             int(p.get("lot", 0)),    1)
    t.check("qty",             int(p.get("qty", 0)),    20)   # SENSEX=20 × 1
    return t

add_test("PROMPT 10",
    "Create a Sensex positional buy-side scalping strategy (carry forward, overnight). "
    "Average every 200 points. 1 lot per step. No per-step target (target = 0). "
    "Required margin is 50000 rupees.",
    validate_10)


# ── PROMPT 11 ─────────────────────────────────────────────────────────────────
# Covers: is_auto_rollover, rollover_before_days, rollover_time
# ─────────────────────────────────────────────────────────────────────────────
def validate_11(p, r):
    t = TestResult("PROMPT 11 — Auto rollover 2 days before expiry at 14:00")
    t.check("main_symbol",          p.get("main_symbol"),           "BANKNIFTY")
    t.check("is_intraday",          p.get("is_intraday"),           False)
    t.check("is_auto_rollover",     p.get("is_auto_rollover"),      True)
    t.check("rollover_before_days", int(p.get("rollover_before_days", 0)), 2)
    t.check("rollover_time",        p.get("rollover_time"),         "14:00")
    t.check("product_type",         p.get("product_type"),          "NRML")
    return t

add_test("PROMPT 11",
    "Create a BankNifty positional buy scalping strategy. "
    "Average every 100 points. 1 lot per step. "
    "Enable auto rollover: roll over 2 days before expiry at 14:00.",
    validate_11)


# ── PROMPT 12 ─────────────────────────────────────────────────────────────────
# Covers: is_add_hedge_leg, OPT hedge leg, hedge qty = lot × lot_size
# ─────────────────────────────────────────────────────────────────────────────
def validate_12(p, r):
    t = TestResult("PROMPT 12 — OPT hedge: Buy BANKNIFTY CE ATM 1 lot (qty=30)")
    t.check("main_symbol",      p.get("main_symbol"),      "BANKNIFTY")
    t.check("main_segment",     p.get("main_segment"),     "FUT")
    t.check("is_add_hedge_leg", p.get("is_add_hedge_leg"), True)
    h = hleg(p, 1)
    t.check("hedge.segment",     h.get("segment"),         "OPT")
    t.check("hedge.option_type", h.get("option_type"),     "CE")
    t.check("hedge.atm",         int(h.get("atm", 0)),     0)
    t.check("hedge.lot",         int(h.get("lot", 0)),     1)
    t.check("hedge.qty",         int(h.get("qty", 0)),     30)   # OPT: 1 × 30
    t.check("hedge.trade_side",  h.get("trade_side"),      "BUY")
    t.check("hedge.call_type",   h.get("call_type"),       "BUY")
    t.check("hedge.expiry",      h.get("expiry"),          "WEEKLY")
    # Hedge has no independent TP/SL
    t.check("hedge.target",      float(h.get("target", 0)), 0.0)
    t.check("hedge.sl",          float(h.get("sl", 0)),     0.0)
    return t

add_test("PROMPT 12",
    "Create a BankNifty intraday buy FUT scalping strategy. Average every 100 points. 1 lot. "
    "Add a hedge leg: Buy BANKNIFTY ATM CE options, 1 lot, weekly expiry.",
    validate_12)


# ── PROMPT 13 ─────────────────────────────────────────────────────────────────
# Covers: FUT hedge leg — qty must be 0 (Market Maya expects 0 for FUT hedges)
# ─────────────────────────────────────────────────────────────────────────────
def validate_13(p, r):
    t = TestResult("PROMPT 13 — FUT hedge leg: qty must be 0 (Market Maya rule)")
    t.check("main_symbol",      p.get("main_symbol"),      "NIFTY")
    t.check("is_add_hedge_leg", p.get("is_add_hedge_leg"), True)
    h = hleg(p, 1)
    t.check("hedge.segment",    h.get("segment"),           "FUT")
    t.check("hedge.symbol",     h.get("symbol"),            "BANKNIFTY")
    t.check("hedge.qty",        int(h.get("qty", -1)),      0)   # FUT hedge → qty=0
    t.check("hedge.lot",        int(h.get("lot", 0)),       1)
    t.check("hedge.trade_side", h.get("trade_side"),        "BUY")
    t.check("hedge.call_type",  h.get("call_type"),         "BUY")
    t.check("hedge.target",     float(h.get("target", 0)),  0.0)
    t.check("hedge.sl",         float(h.get("sl", 0)),      0.0)
    return t

add_test("PROMPT 13",
    "Create a Nifty intraday buy scalping strategy. 1 lot, average every 100 points. "
    "Add a hedge leg: Buy BANKNIFTY FUT near contract, 1 lot.",
    validate_13)


# ── PROMPT 14 ─────────────────────────────────────────────────────────────────
# Covers: calculate_qty_on_market_jump, positional, 2 lots, qty = 65 × 2 = 130
# ─────────────────────────────────────────────────────────────────────────────
def validate_14(p, r):
    t = TestResult("PROMPT 14 — Positional + calculate_qty_on_market_jump, 2 lots (qty=130)")
    t.check("main_symbol",    p.get("main_symbol"),    "NIFTY")
    t.check("is_intraday",    p.get("is_intraday"),    False)
    t.check("product_type",   p.get("product_type"),   "NRML")
    t.check("calculate_qty_on_market_jump", p.get("calculate_qty_on_market_jump"), True)
    t.check("lot",            int(p.get("lot", 0)),    2)
    t.check("qty",            int(p.get("qty", 0)),    130)   # NIFTY=65 × 2
    return t

add_test("PROMPT 14",
    "Create a Nifty positional buy scalping strategy (carry forward). "
    "2 lots per averaging step, average every 100 points. "
    "Enable calculate quantity on market gap or jump to handle overnight gaps.",
    validate_14)


# ── PROMPT 15 ─────────────────────────────────────────────────────────────────
# Covers: custom intraday_entry_time, intraday_exit_time, average_value
# ─────────────────────────────────────────────────────────────────────────────
def validate_15(p, r):
    t = TestResult("PROMPT 15 — Custom entry 10:30, exit 14:30, avg 80 points")
    t.check("main_symbol",          p.get("main_symbol"),           "BANKNIFTY")
    t.check("intraday_entry_time",  p.get("intraday_entry_time"),   "10:30")
    t.check("intraday_exit_time",   p.get("intraday_exit_time"),    "14:30")
    t.check("average_value",        float(p.get("average_value", 0)), 80.0)
    t.check("is_intraday",          p.get("is_intraday"),           True)
    return t

add_test("PROMPT 15",
    "Create a BankNifty intraday buy scalping strategy. Average every 80 points. "
    "Start at 10:30 and close all positions at 14:30.",
    validate_15)


# ── PROMPT 16 ─────────────────────────────────────────────────────────────────
# Covers: jobbing_start_price, jobbing_end_price
# ─────────────────────────────────────────────────────────────────────────────
def validate_16(p, r):
    t = TestResult("PROMPT 16 — Jobbing start price 45000, end price 47000")
    t.check("main_symbol",         p.get("main_symbol"),                "BANKNIFTY")
    t.check("jobbing_start_price", float(p.get("jobbing_start_price", 0)), 45000.0)
    t.check("jobbing_end_price",   float(p.get("jobbing_end_price", 0)),   47000.0)
    t.check("is_intraday",         p.get("is_intraday"),                True)
    return t

add_test("PROMPT 16",
    "Create a BankNifty intraday buy scalping strategy. Average every 100 points. "
    "Start buying only when price reaches 45000. "
    "Stop adding new averaging positions if price goes above 47000.",
    validate_16)


# ── PROMPT 17 ─────────────────────────────────────────────────────────────────
# Covers: maximum_steps, maximum_target_steps
# ─────────────────────────────────────────────────────────────────────────────
def validate_17(p, r):
    t = TestResult("PROMPT 17 — Max avg steps 15, max target steps 3")
    t.check("main_symbol",          p.get("main_symbol"),              "BANKNIFTY")
    t.check("maximum_steps",        int(p.get("maximum_steps", 0)),    15)
    t.check("maximum_target_steps", int(p.get("maximum_target_steps", 0)), 3)
    t.check("is_intraday",          p.get("is_intraday"),              True)
    return t

add_test("PROMPT 17",
    "Create a BankNifty intraday buy scalping strategy. Average every 100 points. "
    "Maximum 15 averaging steps. "
    "Allow closing up to 3 steps at a time on the profitable side (maximum target steps = 3).",
    validate_17)


# ── PROMPT 18 ─────────────────────────────────────────────────────────────────
# Covers: exit_order_product_type separate from product_type
# ─────────────────────────────────────────────────────────────────────────────
def validate_18(p, r):
    t = TestResult("PROMPT 18 — Entry product MIS, exit product NRML")
    t.check("main_symbol",              p.get("main_symbol"),              "BANKNIFTY")
    t.check("product_type",             p.get("product_type"),             "MIS")
    t.check("exit_order_product_type",  p.get("exit_order_product_type"),  "NRML")
    t.check("is_intraday",              p.get("is_intraday"),              True)
    return t

add_test("PROMPT 18",
    "Create a BankNifty intraday buy scalping strategy. Average every 100 points. "
    "Use MIS product for entry orders and NRML product for exit orders.",
    validate_18)


# ── PROMPT 19 ─────────────────────────────────────────────────────────────────
# Covers: FINNIFTY OPT PE OTM (atm < 0 for OTM PE), SELL side, lot size 40
# ─────────────────────────────────────────────────────────────────────────────
def validate_19(p, r):
    t = TestResult("PROMPT 19 — FINNIFTY OPT PE OTM (atm<0), SELL side, 1 lot=40 qty")
    t.check("main_exchange",  p.get("main_exchange"),  "NFO")
    t.check("main_segment",   p.get("main_segment"),   "OPT")
    t.check("main_symbol",    p.get("main_symbol"),    "FINNIFTY")
    t.check("option_type",    p.get("option_type"),    "PE")
    # OTM PE → atm should be negative (e.g. -200)
    t.check_gte("atm OTM PE abs >= 200", abs(p.get("atm", 0)), 200)
    t.check("jobbing_side",   p.get("jobbing_side"),   "SELL")
    t.check("lot",            int(p.get("lot", 0)),    1)
    t.check("qty",            int(p.get("qty", 0)),    40)   # FINNIFTY=40 × 1
    t.check("average_by",     p.get("average_by"),     "Point")
    t.check("average_value",  float(p.get("average_value", 0)), 50.0)
    t.check("is_intraday",    p.get("is_intraday"),    True)
    return t

add_test("PROMPT 19",
    "Create a FINNIFTY intraday sell-side options scalping strategy. "
    "Trade PE options 200 points below ATM (OTM put). 1 lot per step. "
    "Average every 50 points. Sell side.",
    validate_19)


# ── PROMPT 20 ─────────────────────────────────────────────────────────────────
# ALL PARAMETERS — comprehensive strategy enabling every feature at once
# ─────────────────────────────────────────────────────────────────────────────
def validate_20(p, r):
    t = TestResult("PROMPT 20 — ALL PARAMETERS combined")
    # Main instrument
    t.check("main_exchange",     p.get("main_exchange"),     "NFO")
    t.check("main_segment",      p.get("main_segment"),      "FUT")
    t.check("main_symbol",       p.get("main_symbol"),       "BANKNIFTY")
    t.check("main_contract",     p.get("main_contract"),     "NEAR")
    t.check("main_expiry",       p.get("main_expiry"),       "MONTHLY")
    # Trading type
    t.check("is_intraday",       p.get("is_intraday"),       True)
    t.check("product_type",      p.get("product_type"),      "MIS")
    t.check("exit_order_product_type", p.get("exit_order_product_type"), "MIS")
    # Timing — LLM may strip leading zero from "09:30" → "9:30"
    t.check_contains("intraday_entry_time contains 9:30", p.get("intraday_entry_time", ""), "9:30")
    t.check("intraday_exit_time",  p.get("intraday_exit_time"),  "14:45")
    # Jobbing
    t.check("jobbing_side",      p.get("jobbing_side"),      "BUY")
    t.check("average_by",        p.get("average_by"),        "Point")
    t.check("average_value",     float(p.get("average_value", 0)), 100.0)
    t.check("target_by",         p.get("target_by"),         "Point")
    # Intraday: target=0, value goes into intraday_target (confirmed from Market Maya ground truth)
    t.check("target",            float(p.get("target", -1)), 0.0)
    t.check_gt("intraday_target > 0", p.get("intraday_target", 0), 0)
    # Lot + opening qty
    t.check("lot",               int(p.get("lot", 0)),       2)
    t.check("qty",               int(p.get("qty", 0)),       60)   # 2 × 30
    t.check("scalping_opening_qty", int(p.get("scalping_opening_qty", 0)), 3)
    # Qty scaling
    t.check("increase_qty_on_avg",  p.get("increase_qty_on_avg"),   True)
    t.check("increase_qty_type",    p.get("increase_qty_type"),     "Multiply")
    t.check("increase_qty",         float(p.get("increase_qty", 0)), 2.0)
    # Step limits
    t.check("maximum_steps",           int(p.get("maximum_steps", 0)),    15)
    t.check("sqroff_on_maximum_steps", p.get("sqroff_on_maximum_steps"),  True)
    t.check("maximum_target_steps",    int(p.get("maximum_target_steps", 0)), 5)
    t.check("reset_cycle_on_positive_mtm", int(p.get("reset_cycle_on_positive_mtm", 0)), 7)
    # Price boundaries
    t.check("jobbing_start_price", float(p.get("jobbing_start_price", 0)), 44000.0)
    t.check("jobbing_end_price",   float(p.get("jobbing_end_price", 0)),   46000.0)
    # Master TP/SL
    t.check("reset_cycle_by_master_tpsl", p.get("reset_cycle_by_master_tpsl"), True)
    t.check("master_tp_money",   float(p.get("master_tp_money", 0)),  20000.0)
    t.check("master_sl_money",   float(p.get("master_sl_money", 0)),  10000.0)
    # Trail SL
    t.check("is_trail_sl",       p.get("is_trail_sl"),       True)
    t.check("profit_move",       float(p.get("profit_move", 0)), 5000.0)
    t.check("sl_move",           float(p.get("sl_move", 0)),    2500.0)
    t.check("no_of_trail_sl",    int(p.get("no_of_trail_sl", 0)), 4)
    # Auto rollover
    t.check("is_auto_rollover",      p.get("is_auto_rollover"),      True)
    t.check("rollover_before_days",  int(p.get("rollover_before_days", 0)), 1)
    t.check("rollover_time",         p.get("rollover_time"),         "14:29")
    # Hedge leg (OPT)
    t.check("is_add_hedge_leg",  p.get("is_add_hedge_leg"),  True)
    h = hleg(p, 1)
    t.check("hedge.segment",     h.get("segment"),           "OPT")
    t.check("hedge.option_type", h.get("option_type"),       "CE")
    t.check("hedge.lot",         int(h.get("lot", 0)),       1)
    t.check("hedge.qty",         int(h.get("qty", 0)),       30)   # OPT: 1 × 30
    t.check("hedge.call_type",   h.get("call_type"),         "BUY")
    t.check("hedge.expiry",      h.get("expiry"),            "WEEKLY")
    t.check("hedge.target",      float(h.get("target", 0)),  0.0)
    t.check("hedge.sl",          float(h.get("sl", 0)),      0.0)
    # Misc
    t.check("required_margin",   float(p.get("required_margin", 0)), 200000.0)
    t.check("calculate_qty_on_market_jump", p.get("calculate_qty_on_market_jump"), False)
    # Fixed constants
    t.check("strategy_id",       p.get("strategy_id"),       "YioJhK5IqBULe8fPLMnXaAaC0$aC0$")
    t.check("order_type",        p.get("order_type"),        "Market Order")
    t.check("rebacktest",        p.get("rebacktest"),        False)
    t.check_nonempty("short_description", p.get("short_description"))
    t.check_nonempty("long_description",  p.get("long_description"))
    return t

add_test("PROMPT 20",
    "Create a comprehensive BankNifty intraday buy scalping strategy that enables every feature:\n"
    "- Symbol: BANKNIFTY NFO FUT NEAR MONTHLY, intraday MIS.\n"
    "- Entry at 09:30, exit at 14:45. Exit orders also use MIS.\n"
    "- Average every 100 points. Target 100 points per step.\n"
    "- First entry: open with 3 lots. Each averaging step adds 2 lots.\n"
    "- Double the quantity at each averaging step (multiply by 2).\n"
    "- Maximum 15 averaging steps. Close all when max steps reached.\n"
    "- Maximum 5 target steps on the profitable side.\n"
    "- Reset cycle when 7 steps are open and overall MTM is positive.\n"
    "- Jobbing price range: start at 44000, stop new averages above 46000.\n"
    "- Master target 20000 rupees, master SL 10000 rupees.\n"
    "- Trail SL: for every 5000 rupees profit, trail master SL by 2500 rupees. Max 4 trail steps.\n"
    "- Auto rollover: 1 day before expiry at 14:29.\n"
    "- Hedge leg: Buy BANKNIFTY ATM CE options, 1 lot, weekly expiry.\n"
    "- Required margin: 200000 rupees.",
    validate_20)


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────
def run_all():
    print("=" * 70)
    print("  RES End-to-End Test Suite  —  20 Prompts")
    print("=" * 70)

    # Pre-flight server check
    try:
        import requests as _req
        _req.get("http://localhost:8000/scalper/", timeout=5)
    except Exception as e:
        print(f"\n  ❌ ABORT — Django server not reachable at http://localhost:8000")
        print(f"     ({e})")
        print("  Start the server with:  python manage.py runserver")
        return

    overall_pass = 0
    overall_fail = 0
    all_results = []
    deploy_ok = 0
    deploy_fail = 0
    session_counter = 0

    for name, prompt, validator in TESTS:
        session_counter += 1
        session_id = f"res_test_{session_counter}_{int(time.time())}"
        print(f"\n{'─'*70}")
        print(f"▶  Running {name} ...")

        before = last_res_log_count()

        # Step 1 — ask LLM to build strategy
        print("  → Sending prompt ...")
        reply1 = chat(prompt, session_id)
        if reply1.startswith("ERROR:"):
            print(f"  ❌ Chat error on prompt: {reply1}")
            overall_fail += 1
            deploy_fail += 1
            continue

        time.sleep(2)

        # Step 2 — confirm deployment
        print("  → Confirming deployment ...")
        reply2 = chat("yes deploy", session_id)
        if reply2.startswith("ERROR:"):
            print(f"  ❌ Chat error on confirm: {reply2}")
            overall_fail += 1
            deploy_fail += 1
            continue

        time.sleep(3)

        payload, api_status, api_code, api_response = get_last_res_log_entry(before)

        if payload is None:
            print(f"  ⚠️  No log entry — retrying confirm ...")
            chat("yes confirm and deploy", session_id)
            time.sleep(3)
            payload, api_status, api_code, api_response = get_last_res_log_entry(before)

        if payload is None:
            print(f"  ❌ FAIL — deployment did not occur (no new log entry)")
            result = TestResult(name)
            result.failed.append("  ❌ No payload logged — deployment did not trigger")
            all_results.append(result)
            overall_fail += 1
            deploy_fail += 1
            continue

        if api_status == "success" and api_code == 200:
            print(f"  🟢 Market Maya: HTTP {api_code} — DEPLOYED")
            deploy_ok += 1
        else:
            print(f"  🔴 Market Maya: HTTP {api_code} — {str(api_response)[:120]}")
            deploy_fail += 1

        result = validator(payload, api_response)

        if api_status == "success" and api_code == 200:
            result.passed.insert(0, f"  ✅ Market Maya deployment: HTTP {api_code} SUCCESS")
        else:
            result.failed.insert(0, f"  ❌ Market Maya deployment: HTTP {api_code} — {str(api_response)[:100]}")

        result.print_report()
        all_results.append(result)

        status, p, total = result.summary()
        if status == "PASS":
            overall_pass += 1
        else:
            overall_fail += 1

        time.sleep(2)

    # ── Final summary ────────────────────────────────────────────────────────
    total_checks_pass = sum(len(r.passed) for r in all_results)
    total_checks_fail = sum(len(r.failed) for r in all_results)
    total_checks = total_checks_pass + total_checks_fail

    print(f"\n{'='*70}")
    print(f"  FINAL RESULT: {overall_pass} PASS / {overall_fail} FAIL  out of {len(TESTS)} tests")
    print(f"  Market Maya: {deploy_ok} deployed / {deploy_fail} failed")
    print(f"  Individual checks: {total_checks_pass}/{total_checks} passed")
    print(f"{'='*70}\n")

    if overall_fail > 0:
        print("  FAILED TESTS:")
        for r in all_results:
            if r.failed:
                print(f"\n  ► {r.name}")
                for line in r.failed:
                    print(line)

    # Save report
    os.makedirs("tests/reports", exist_ok=True)
    report_path = f"tests/reports/res_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_path, "w") as f:
        f.write(f"RES Test Run: {datetime.now().isoformat()}\n")
        f.write(f"Results: {overall_pass}/{len(TESTS)} tests, {total_checks_pass}/{total_checks} checks\n\n")
        for r in all_results:
            status, p, total = r.summary()
            f.write(f"\n{'='*60}\n{r.name}  [{status}] [{p}/{total}]\n")
            for line in r.passed:
                f.write(line + "\n")
            for line in r.failed:
                f.write(line + "\n")
    print(f"  Report saved to: {report_path}")


if __name__ == "__main__":
    run_all()
