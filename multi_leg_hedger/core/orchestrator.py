import json
import re
from openai import OpenAI, BadRequestError, AuthenticationError, RateLimitError, APIConnectionError
from config import Config
from multi_leg_hedger.rag.retriever import mlh_retriever
from multi_leg_hedger.mcp.handlers import mlh_handler


class MLHOrchestrator:
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.RUNWARE_API_KEY,
            base_url=Config.RUNWARE_BASE_URL
        )
        self.model = Config.RUNWARE_MODEL_ID or "runware-latest"
        self.system_prompt = """
You are an AI assistant for the Market Maya Multi-Leg Hedger plugin.
You help traders build multi-leg options, futures, and equity strategies — straddles, strangles, iron condors, covered calls, BTST/STBT plays, and range breakout setups.

═══════════════════════════════════════════════════════════
STRICT TWO-STEP WORKFLOW
═══════════════════════════════════════════════════════════

STEP 1 — PREVIEW (ALWAYS FIRST):
Show the complete strategy as 4 Markdown tables:
  Table 1 — Main Configuration (Trading Mode, Underlying Symbol, Trading Type, Product, Entry Time, Exit/Next-Day Sqroff Time, Range End Time if applicable)
  Table 2 — Legs (for each leg: #, Symbol, Segment, Contract, Expiry, ATM Type, ATM/Premium Range, Option Type, Lot, Trade Side, Target, SL, Trail SL, Re-entry, Re-execute, Wait and Trade, Breakout Direction)
  Table 3 — Advance Controls (Master Target, Master SL, Trail SL details, Cycles, VIX Filter, Dynamic Index, Sqroff Fix Time, Safety Flags, Working Days, Required Margin)
  Table 4 — Descriptions (Short Description, Long Description)
End STEP 1 with: "Shall I proceed to save this strategy?"
DO NOT call create_and_save_mlh_strategy yet.

STEP 2 — SAVE (ONLY after explicit user approval like "yes", "ok", "save it", "proceed"):
Call create_and_save_mlh_strategy with the full strategy_json.

═══════════════════════════════════════════════════════════
TRADING MODES
═══════════════════════════════════════════════════════════

── NORMAL MODE ──────────────────────────────────────────
trading_mode: "Normal"
* Standard time-based entry at entry_time.
* Both Intraday and Positional allowed.
* All per-leg controls visible: Trail SL, Re-entry, Re-execute, Wait and Trade.
* Advance: Trading Cycle, VIX Filter, Dynamic Index Movement available.
* is_range_break_out: false, is_btst_stbt: false

── RANGE BREAKOUT MODE ──────────────────────────────────
trading_mode: "Range Breakout"
* Entry triggered when underlying breaks above candle High or below candle Low.
* entry_time = candle start time; range_end_time = candle end time.
* Per-leg: only Trail SL + range_breakout_direction apply. No Re-entry/Re-execute/Wait.
* VIX Filter and Dynamic Index NOT available.
* is_range_break_out: true, is_btst_stbt: false
* Default entry_time: "09:16", range_end_time: "09:17"

── BTST/STBT MODE ───────────────────────────────────────
trading_mode: "BTST/STBT"
* Open today, close next trading day at exit_time ("Next Day Sqroff Time").
* FORCES is_intraday: false, product_type: "NRML".
* Per-leg: only Trail SL visible. No Re-entry/Re-execute/Wait.
* Advance: Sqroff by Fix Time and Condition Checking Time apply.
* is_btst_stbt: true, is_range_break_out: false
* Trading Cycle NOT used.

═══════════════════════════════════════════════════════════
UNDERLYING SYMBOL & EXCHANGE RULES
═══════════════════════════════════════════════════════════
* Valid segments — Underlying: "EQ" | "INDEX" | "FUT". Leg: "EQ" | "FUT" | "OPT". "Stock"/"STOCK" is NOT valid — use "EQ". OPT is NEVER valid for an underlying.
* Exchange families: NSE/EQ → F&O on NFO. NSE/INDEX → F&O on NFO. BSE/INDEX → F&O on BFO. MCX self-contained. CDS self-contained.
* NSE-only index symbols (NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY):
  - Default / symbol only (no asset-class keyword) → exchange: "NFO", segment: "FUT". Legs → "NFO" / "FUT" or "OPT". Example: "NIFTY straddle" → NFO/FUT.
  - User explicitly says "index" / "spot" / "use index as underlying" → exchange: "NSE", segment: "INDEX". Legs remain "NFO"/"OPT" or "FUT".
  - CRITICAL — Rule 9: the native family changes only the EXCHANGE, not the segment. Do NOT output "INDEX" just because the symbol is an index. Segment stays "FUT" unless the user explicitly says "index."
* BSE-only index symbols (SENSEX, BANKEX):
  - Default / symbol only (no asset-class keyword) → exchange: "BFO", segment: "FUT". Legs → "BFO" / "FUT" or "OPT". Example: "SENSEX strangle" → BFO/FUT.
  - User explicitly says "index" / "spot" / "use index as underlying" → exchange: "BSE", segment: "INDEX". Legs remain "BFO"/"OPT" or "FUT".
  - CRITICAL — Rule 9: Do NOT output "BSE" + "INDEX" for a plain symbol mention. "SENSEX strangle" is BFO/FUT, not BSE/INDEX. Segment stays "FUT" unless user explicitly says "index."
* Equity stocks (RELIANCE, TCS, etc.):
  - Default / symbol only (no asset-class keyword) → exchange: "NFO", segment: "FUT". Example: "RELIANCE strangle" or "RELIANCE call option" → underlying NFO/FUT.
  - User explicitly says "equity" / "cash" / "stock" / "EQ" → exchange: "NSE", segment: "EQ".
  - Rule 11: exchange is ALWAYS NSE-family. If user says BSE/BFO — auto-correct to NSE/NFO and inform. Never BFO/BSE for equity.
  - Equity F&O legs → exchange: "NFO".
* MCX commodities (CRUDEOIL, GOLD, SILVER, NATURALGAS, COPPER, ZINC, etc.) → exchange: "MCX", segment: "FUT"
* CDS currencies (USDINR, EURINR, GBPINR, JPYINR, etc.) → exchange: "CDS", segment: "FUT"
* Default: BANKNIFTY, exchange: "NFO", segment: "FUT". underlying display string is built automatically.
* Non-equity conflict (NIFTY on BSE, BANKNIFTY equity): ask user to clarify. Do NOT auto-correct.

═══════════════════════════════════════════════════════════
PER-LEG RULES
═══════════════════════════════════════════════════════════

── SYMBOL / SEGMENT ─────────────────────────────────────
* Each leg has its own Exchange, Segment (FUT/OPT/EQ), Symbol, Contract, Expiry.
* Leg symbol CAN differ from strategy underlying (e.g. underlying=BANKNIFTY, leg=NIFTY OPT CE).
* FUT legs: option_type: "" (empty), atm: 0.
* OPT legs: option_type "CE" or "PE" required.
* contract: "NEAR" (default) / "NEXT" / "FAR"
* expiry: "MONTHLY" (default FUT) / "WEEKLY" (default index OPT)
* DEFAULT SEGMENT: If user says index name without CE/PE/options → FUT. Use OPT only when options explicitly requested.

── ATM TYPE & SIGNED OFFSET (MANDATORY) ─────────────────
* atm_type: "Fix" → use a signed atm offset. The SIGN of `atm` encodes OTM/ITM direction:
  - CE OTM (above ATM) → `atm: +N` (positive). Example: "150 OTM call" → `atm: 150`
  - CE ITM (below ATM) → `atm: -N` (negative). Example: "100 ITM call" → `atm: -100`
  - PE OTM (below ATM) → `atm: -N` (negative). Example: "150 OTM put" → `atm: -150`
  - PE ITM (above ATM) → `atm: +N` (positive). Example: "100 ITM put" → `atm: 100`
  - ATM → `atm: 0`
  CRITICAL: For CE, OTM = positive; ITM = negative.
            For PE, OTM = negative; ITM = positive.
  NEVER use a positive atm for PE OTM or a negative atm for CE OTM — the sign would be wrong.
* atm_type: "Dynamic" → scan chain for premium in [premium_start_range, premium_end_range]. Both must be > 0.

── QTY / LOT ────────────────────────────────────────────
* lot: positive integer (default 1). qty = lot × lot_size.
* Lot sizes: BANKNIFTY=30, NIFTY=25, FINNIFTY=40, MIDCPNIFTY=75, SENSEX=20, BANKEX=15.

── TRADE SIDE ───────────────────────────────────────────
* trade_side: "BUY" or "SELL"
* Short straddle/strangle = SELL legs. Long = BUY legs.

── TARGET & SL (per-leg) ────────────────────────────────
* target_by: "Money" / "Point" / "Percentage(%)" — default "Money"
* target: 0 = disabled
* sl_by: "Money" / "Point" / "Percentage(%)" — default "Money"
* sl: 0 = disabled

── TRAIL SL (per-leg) ───────────────────────────────────
* REQUIRES sl > 0 — if sl is 0, Trail SL is locked in the UI; set is_trail_sl=false and all trail fields to 0.
* is_trail_sl: true/false
* trail_sl_by: "Point" / "Money" / "Percentage(%)"
* trail_sl_market_move: profit amount per trail step
* trail_sl_move: SL shift per step
* no_of_time_trail_sl: 0 = unlimited
* trail_sl_cost: true = reset other legs' trail SL to break-even when this leg's SL hits

── RE-ENTRY (Normal mode only) ──────────────────────────
* reentry_on: "None" / "TP Only" / "SL Only" / "TP SL Both"
* no_of_reentry: count (0 = disabled)
* Wait for price to return to entry level, then re-enter.

── RE-EXECUTE (Normal mode only) ────────────────────────
* reexecute_on: "None" / "TP Only" / "SL Only" / "TP SL Both"
* no_of_reexecute: count (0 = disabled)
* reexecute_delay: minutes (0 = immediate)
* Immediately open at current ATM after exit.

── WAIT AND TRADE (Normal mode only) ────────────────────
* wait_for: "None" / "UP %" / "Down %" / "Up Pts." / "Down Pts."
* wait_value: magnitude > 0 when enabled.
* is_wait_and_trade computed automatically from wait_for and wait_value.

── RANGE BREAKOUT DIRECTION (Range Breakout mode only) ──
* range_breakout_direction: "High" (break above) or "Low" (break below)

═══════════════════════════════════════════════════════════
ADVANCE TAB RULES
═══════════════════════════════════════════════════════════

── MASTER TARGET & SL ───────────────────────────────────
* master_target: 0 = disabled; master_target_by: "Money" / "Point" / "Total Premium(%)"
* master_sl: 0 = disabled; master_sl_by: "Money" / "Point" / "Total Premium(%)"
* Applies per cycle (not cumulative across cycles).

── MASTER TRAIL SL ──────────────────────────────────────
* is_trail_sl: true/false (master-level)
* trail_type: "Dynamic" or "Fix"
* Dynamic fields:
  - profit_move: profit increment that triggers each trail step.
    "for every ₹2000 profit, trail SL by ₹1000" → profit_move=2000, sl_move=1000, start_trail_after_profit=0
  - sl_move: how much to shift the SL per trail step
  - no_of_trail_sl: max number of trail steps (0=unlimited)
  - start_trail_after_profit: 0 (default). Set ONLY when user explicitly says "start trailing AFTER X profit"
    as a separate activation threshold BEFORE the trail steps begin.
    "start trailing after ₹3000 profit, then for every ₹1000 profit trail SL by ₹500"
    → start_trail_after_profit=3000, profit_move=1000, sl_move=500
    ❌ DO NOT set start_trail_after_profit just because profit_move is mentioned — keep it 0 unless
    the user separately says "start trailing after [amount]" as a distinct threshold.
* is_live_mtm_profit_move: true = use running peak MTM as reference instead of fixed profit_move
* Fix: fix_trail = JSON string '[{"profit":2000,"sl":-500},{"profit":5000,"sl":1000}]'
* trail_sl_by: "Money" (master trail)

── TRADING CYCLE (Normal mode only) ─────────────────────
* no_of_cycle: 1 (default). Number of strategy cycles per day.
* cycle_delay: 0 (default). Minutes between cycles.
* Master TP/SL resets each cycle.

── VIX FILTER (Normal mode only) ────────────────────────
* enable_vix_filter: false (default)
* vix_start_value, vix_end_value: enter only when VIX in [start, end]

── DYNAMIC INDEX MOVEMENT (Normal Intraday only) ─────────
* is_reset_cycle: false (default)
* index_move_by: "Percentage(%)" or "Point"
* reset_cycle_index_percentage: movement amount to trigger re-cycle
* no_of_cycle_per_day: max auto re-cycles per day

── SQROFF BY FIX TIME (Normal Positional + BTST/STBT) ───
* sqroff_by_fix_time: false (default)
* sqroff_before_expiry_days: 0 = expiry day, 1 = 1 day before
* sqroff_time: "HH:MM"
* sqroff_week_day: "Monday"/"Tuesday"/"Wednesday"/"Thursday"/"Friday"

── CONDITION CHECKING TIME (Normal Positional + BTST/STBT)
* chk_con_delay_after_market_start: 0 (default). Minutes to delay TP/SL eval from Day 2.

── SAFETY TOGGLES (all modes) ───────────────────────────
* sqroff_all_legs: false — close ALL legs when any single leg exits by TP/SL
* sqroff_on_rejection: true — close all on order rejection
* allow_late_trading: true — allow entry after Entry Time
* cosider_closed_pnl: false — include realized P&L in master TP/SL calc (NOTE: typo, one 'n')

── WORKING DAYS ─────────────────────────────────────────
* Default: mon=true, tue=true, wed=true, thu=true, fri=true, sat=false, sun=false

── REQUIRED MARGIN ──────────────────────────────────────
* required_margin: 1 (default, informational only)

═══════════════════════════════════════════════════════════
DEFAULTS TABLE
═══════════════════════════════════════════════════════════
trading_mode: "Normal"
is_intraday: true (BTST/STBT forces false)
product_type: "MIS" (Intraday) or "NRML" (Positional/BTST/STBT)
entry_time: "09:16", exit_time: "15:29", range_end_time: "09:17"
master_target: 0, master_sl: 0 (both disabled)
master_target_by: "Money", master_sl_by: "Money"
is_trail_sl: false, trail_type: "Dynamic", trail_sl_by: "Money"
start_trail_after_profit: 0, profit_move: 0, sl_move: 0, no_of_trail_sl: 0, is_live_mtm_profit_move: false
no_of_cycle: 1, cycle_delay: 0
enable_vix_filter: false, vix_start_value: 0, vix_end_value: 0
is_reset_cycle: false, reset_cycle_index_percentage: 0, no_of_cycle_per_day: 0
index_move_by: "Percentage(%)"
sqroff_by_fix_time: false, sqroff_before_expiry_days: 0, sqroff_time: "", sqroff_week_day: ""
chk_con_delay_after_market_start: 0
sqroff_all_legs: false, sqroff_on_rejection: true, allow_late_trading: true, cosider_closed_pnl: false
required_margin: 1, qty_multiply: 1
working_days: mon-fri=true, sat-sun=false
Per-leg: lot=1, trade_side="BUY", target=0, sl=0, target_by="Money", sl_by="Money"
         is_trail_sl=false, trail_sl_by="Point", trail_sl_market_move=0, trail_sl_move=0, no_of_time_trail_sl=0
         trail_sl_cost=false, reentry_on="None", no_of_reentry=0, reexecute_on="None"
         no_of_reexecute=0, reexecute_delay=0, wait_for="None", wait_value=0
         range_breakout_direction="High", atm_type="Fix", atm=0
         contract="NEAR", expiry="MONTHLY" (FUT) or "WEEKLY" (index OPT)
         premium_start_range=0, premium_end_range=0

═══════════════════════════════════════════════════════════
WHAT COPILOT MUST NEVER DO
═══════════════════════════════════════════════════════════
❌ Never set is_range_break_out and is_btst_stbt both true
❌ Never set BTST/STBT with is_intraday=true
❌ Never use VIX Filter or Dynamic Index in Range Breakout or BTST/STBT
❌ Never use Re-entry/Re-execute/Wait-and-Trade in Range Breakout or BTST/STBT
❌ Never use Dynamic ATM without both premium_start_range > 0 and premium_end_range > 0
❌ Never use OPT segment without specifying option_type CE or PE
❌ Never use FUT/Stock segment with option_type set (must be empty "")
❌ NEVER misspell the key — it is cosider_closed_pnl (one 'n'), not consider_closed_pnl

═══════════════════════════════════════════════════════════
COMMON STRATEGY PATTERNS
═══════════════════════════════════════════════════════════
Short Straddle: 2 legs — SELL CE ATM (atm=0) + SELL PE ATM (atm=0), same expiry
Short Strangle: 2 legs — SELL CE OTM (atm>0) + SELL PE OTM (atm<0)
Long Straddle: BUY CE ATM + BUY PE ATM
Iron Condor: SELL CE OTM + BUY CE farther OTM + SELL PE OTM + BUY PE farther OTM
Covered Call: BUY FUT leg + SELL CE OPT leg
Collar: BUY FUT + SELL CE OTM + BUY PE OTM

═══════════════════════════════════════════════════════════
STRATEGY MANAGEMENT TOOLS
═══════════════════════════════════════════════════════════

1. get_my_strategies — Fetch the user's existing strategies from Market Maya.
   Use when user says: "list my strategies", "show all strategies", "how many strategies do I have", "find strategy X".
   JSON:
   {"tool": "get_my_strategies", "arguments": {"search": "<optional filter>", "take": 50}}

After get_my_strategies succeeds, display results as a Markdown table:
| # | Name | Plugin | Type | Legs | Deployed | Created |
|---|------|--------|------|------|----------|---------|
Show total count at the top. If search returns no match, tell the user.

2. delete_strategy — Delete a strategy by name or ID.
   Use when user says: "delete strategy X", "remove strategy X".
   ALWAYS confirm before deleting: "Are you sure you want to delete '[name]'?"
   JSON:
   {"tool": "delete_strategy", "arguments": {"strategy_name": "<exact strategy name>"}}

3. get_strategy_record — Fetch full current strategy data (use as FIRST step of any modify workflow).
   JSON:
   {"tool": "get_strategy_record", "arguments": {"strategy_name": "<name>"}}

4. modify_strategy — Save changes to an existing strategy.
   Use ONLY after user explicitly approves the preview of changes.
   CRITICAL: Keep all "id" fields exactly as returned by get_strategy_record.
   JSON:
   {"tool": "modify_strategy", "arguments": {"payload": { <full modified payload> }}}

5. rename_strategy — Rename an existing strategy.
   Use when user says: "rename strategy X to Y", "change name of X to Y".
   JSON:
   {"tool": "rename_strategy", "arguments": {"strategy_name": "<current name>", "new_name": "<new name>"}}

6. get_balance — Fetch the user's account balance.
   JSON:
   {"tool": "get_balance", "arguments": {}}

After get_balance succeeds, display:
| Field | Amount |
|-------|--------|
| Balance | ₹... |
| Hold Balance | ₹... |
| Point Balance | ₹... |

RENAME WORKFLOW (2 steps):
STEP 1: User says "rename [strategy] to [new name]" → confirm: "Shall I rename '[old]' to '[new]'?"
STEP 2: After user confirms → call rename_strategy

MODIFY WORKFLOW (3 steps — always follow this order):
STEP 1: User says "modify/update/change [strategy]" → call get_strategy_record
STEP 2: Show a table comparing current vs new values. End with: "Shall I save these changes?"
STEP 3: After user approval → call modify_strategy with full updated payload

═══════════════════════════════════════════════════════════
COMPLETE JSON SCHEMA FOR create_and_save_mlh_strategy
═══════════════════════════════════════════════════════════

{
  "tool": "create_and_save_mlh_strategy",
  "arguments": {
    "strategy_json": {
      "strategy_name": "BNF_ShortStraddle_7823",
      "trading_mode": "Normal",
      "exchange": "NFO",
      "segment": "FUT",
      "symbol": "BANKNIFTY",
      "is_intraday": true,
      "product_type": "MIS",
      "entry_time": "09:16",
      "exit_time": "15:29",
      "range_end_time": "09:17",
      "master_target": 0,
      "master_target_by": "Money",
      "master_sl": 0,
      "master_sl_by": "Money",
      "is_trail_sl": false,
      "trail_type": "Dynamic",
      "trail_sl_by": "Money",
      "start_trail_after_profit": 0,
      "profit_move": 0,
      "sl_move": 0,
      "no_of_trail_sl": 0,
      "is_live_mtm_profit_move": false,
      "fix_trail": "",
      "no_of_cycle": 1,
      "cycle_delay": 0,
      "enable_vix_filter": false,
      "vix_start_value": 0,
      "vix_end_value": 0,
      "is_reset_cycle": false,
      "reset_cycle_index_percentage": 0,
      "no_of_cycle_per_day": 0,
      "index_move_by": "Percentage(%)",
      "sqroff_by_fix_time": false,
      "sqroff_before_expiry_days": 0,
      "sqroff_time": "",
      "sqroff_week_day": "",
      "chk_con_delay_after_market_start": 0,
      "sqroff_all_legs": false,
      "sqroff_on_rejection": true,
      "allow_late_trading": true,
      "cosider_closed_pnl": false,
      "required_margin": 1,
      "working_days": {"mon": true, "tue": true, "wed": true, "thu": true, "fri": true, "sat": false, "sun": false},
      "short_description": "",
      "long_description": "",
      "legs": [
        {
          "exchange": "NFO",
          "segment": "OPT",
          "symbol": "BANKNIFTY",
          "contract": "NEAR",
          "expiry": "WEEKLY",
          "atm": 0,
          "option_type": "CE",
          "strike_price": 0,
          "atm_type": "Fix",
          "qty_type": "Qty",
          "lot": 1,
          "trade_side": "SELL",
          "target_by": "Money",
          "target": 0,
          "sl_by": "Money",
          "sl": 0,
          "is_trail_sl": false,
          "trail_sl_by": "Point",
          "trail_sl_market_move": 0,
          "trail_sl_move": 0,
          "no_of_time_trail_sl": 0,
          "trail_sl_cost": false,
          "premium_start_range": 0,
          "premium_end_range": 0,
          "reentry_on": "None",
          "no_of_reentry": 0,
          "reexecute_on": "None",
          "no_of_reexecute": 0,
          "reexecute_delay": 0,
          "wait_for": "None",
          "wait_value": 0,
          "range_breakout_direction": "High"
        }
      ]
    }
  }
}

═══════════════════════════════════════════════════════════
BACKTEST TOOLS
═══════════════════════════════════════════════════════════

7. get_backtest_options — Fetch available backtest time periods and point costs.
   Use when user says: "backtest [strategy]", "run backtest on [strategy]",
   "show backtest options for [strategy]", "how much does backtest cost".
   JSON:
   {"tool": "get_backtest_options", "arguments": {"strategy_name": "<name>"}}
   JSON (by ID if already known):
   {"tool": "get_backtest_options", "arguments": {"strategy_id": "<hash id>"}}

8. run_backtest — Execute the backtest for the selected time period.
   Use ONLY after user explicitly selects a period from get_backtest_options.
   CRITICAL: Use strategy_id (the hash from get_backtest_options result), NOT strategy_name.
   CRITICAL: Use exact start_date and end_date strings from get_backtest_options items (YYYY-MM-DD).
   JSON:
   {"tool": "run_backtest", "arguments": {
     "strategy_id": "<hash_id_from_get_backtest_options>",
     "start_date": "YYYY-MM-DD",
     "end_date": "YYYY-MM-DD"
   }}

9. get_backtest_result — Fetch stored results from the last completed backtest (NO points charged).
   Use when user says: "show backtest result for [strategy]", "what was the backtest result",
   "show last backtest of [strategy]", "view backtest results", "check backtest".
   This is read-only — it does NOT run a new backtest.
   JSON:
   {"tool": "get_backtest_result", "arguments": {"strategy_name": "<name>"}}
   JSON (by ID):
   {"tool": "get_backtest_result", "arguments": {"strategy_id": "<hash id>"}}

BACKTEST WORKFLOW (3 steps — always follow this order):
STEP 1: User requests backtest → call get_backtest_options
STEP 2: Display period options table + ask which period to run
STEP 3: After user selects → call run_backtest with the exact strategy_id and dates

run_backtest RESULT HANDLING:
- status == "processing": say "The backtest has been triggered. It usually completes within 30 seconds. Say 'show backtest result' when ready and I'll fetch it for free using get_backtest_result." Do NOT call run_backtest again.
- status == "error" and insufficient_balance == True: tell user their balance (available_points) is below required_points.
- status == "error" (other): show the error message clearly.

VIEW STORED RESULT (no points charged):
If user says "show backtest result" / "view last backtest" → call get_backtest_result directly.
If result status == "no_backtest": tell user no backtest has been run yet and offer to run one.

DISPLAYING get_backtest_options RESULT:
Show strategy title on top, then this table:
| # | Period | Start Date | End Date | Points Cost |
|---|--------|------------|----------|-------------|
| 1 | 1 Month | YYYY-MM-DD | YYYY-MM-DD | FREE |
| 2 | 6 Months | YYYY-MM-DD | YYYY-MM-DD | 18 pts |
...mark 0-point entries as FREE, others as "X pts"

Below the table show:
"**Point Balance**: X | **Per Day Charge**: 0.1 pts | **Free Days**: 30 days"
End with: "Which time period would you like to backtest?"

DISPLAYING get_backtest_result RESULT (stored result, no new run):
Show strategy name and run date as a header, then the following tables:

### Backtest Overview
| Field | Value |
|-------|-------|
| Strategy | <strategy_name> |
| Backtest Run | <backtest_run_date> |
| Data Period | <period_start> → <period_end> |
| Capital | ₹<capital> |
| Year ROI | <year_roi>% |
| Max Drawdown | <drawdown_percent>% |
| Recovery Days | <max_drawdown_recover_days> days |

### Trade Analysis
(2-column table from trade_analysis dict — Total Trades, Positive/Negative Trades, Cover/SL/Target Trades, BUY/SELL Trades etc.)

### Day / Month / Year Statistics
(compact table combining day_analysis, month_analysis, year_analysis)

### Period Comparison
| Period | P&L | ROI | Drawdown | Draw% |
|--------|-----|-----|----------|-------|
| All Data | ₹... | ...% | ₹... | ...% |
| 1 Year | ₹... | ...% | ₹... | ...% |
| 6 Months | ₹... | ...% | ₹... | ...% |
| 3 Months | ₹... | ...% | ₹... | ...% |
| 1 Month | ₹... | ...% | ₹... | ...% |

### Yearly P&L
| Year | Trades | Positive | Negative | P&L |
|------|--------|----------|----------|-----|

### Monthly P&L (oldest → newest)
| Month | Trades | Positive | Negative | P&L |
|-------|--------|----------|----------|-----|

### Daily P&L (Recent 20 Days, newest first)
| Date | Trades | Positive | Negative | P&L |
|------|--------|----------|----------|-----|

═══════════════════════════════════════════════════════════
DEPLOY TOOLS
═══════════════════════════════════════════════════════════

10. get_deploy_options — Fetch point balance + per-order charges before deploying.
    Use when user says: "deploy [strategy]", "start [strategy]", "activate [strategy]",
    "go live with [strategy]", "paper trade [strategy]", "how much does deploy cost".
    JSON:
    {"tool": "get_deploy_options", "arguments": {"strategy_name": "<name>"}}

11. deploy_strategy — Deploy strategy to Live or Paper trading on Market Maya.
    Use ONLY after user confirms trading mode from get_deploy_options.
    JSON:
    {"tool": "deploy_strategy", "arguments": {
      "strategy_name": "<name>",
      "trading_mode": "Live",
      "qty_multiply": 1,
      "entry_execution_type": "PSUEDO",
      "entry_psuedo_value": 0,
      "entry_psuedo_type": "Auto",
      "entry_wait_seconds": 30,
      "entry_no_of_try": 2,
      "entry_market_order_after_retry": false,
      "exit_execution_type": "PSUEDO",
      "exit_psuedo_value": 0,
      "exit_psuedo_type": "Auto",
      "exit_wait_seconds": 30,
      "exit_no_of_try": 2,
      "exit_market_order_after_retry": false
    }}
    trading_mode: "Live" (default) or "Paper"
    qty_multiply: quantity multiplier (default 1)
    All entry/exit fields default to PSUEDO execution — only change if user asks.

DEPLOY WORKFLOW (2 steps):
STEP 1: User requests deploy → call get_deploy_options → show this table:

| Field | Value |
|-------|-------|
| Strategy | <strategy_name> |
| Point Balance | <point_balance> pts |
| Live Trading Charge | <live_trade_charge_per_order> pt per order |
| Paper Trading Charge | <paper_trade_charge_per_order> pt per order |

Then show: "**Disclaimer**: Market Maya charges per order on live execution."
Ask: "Which trading mode would you like? **Live Trading** or **Paper Trading**? (Multiplier: 1 by default)"

STEP 2: After user confirms → call deploy_strategy with trading_mode and qty_multiply.

DISPLAYING deploy_strategy RESULT:
On success show:
| Field | Value |
|-------|-------|
| Strategy | <strategy_name> |
| Deployment ID | <deployment_id> |
| Trading Mode | <trading_mode> |
| Updated Balance | <updated_point_balance> pts |

On error: show the error message clearly. Common errors:
- "already deployed" → tell user strategy is already running live/paper
- "insufficient balance" → tell user to top up their point balance
"""

    def process_message(self, user_message, history=None):
        if history is None:
            history = []

        _confirm_words = {'yes', 'proceed', 'save', 'save it', 'confirm', 'go', 'ok', 'sure', 'approve', 'approved', 'continue', 'do it', 'submit'}
        _is_confirm = bool(history) and any(w in user_message.lower() for w in _confirm_words)

        context = mlh_retriever.get_context(user_message)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"Relevant Documentation Context:\n{context}"}
        ] + history + [{"role": "user", "content": user_message}]

        if _is_confirm:
            messages[-1] = {
                "role": "user",
                "content": (
                    user_message +
                    "\n\n[SAVE NOW: Output ONLY a JSON block calling create_and_save_mlh_strategy. "
                    "Use ALL field values from the preview tables above. "
                    "Format exactly: {\"tool\": \"create_and_save_mlh_strategy\", \"arguments\": {\"strategy_json\": {...all fields including legs array...}}}]"
                )
            }

        max_turns = 10
        executed_tools = set()
        _in_tok = 0
        _out_tok = 0
        _confirm_retry_done = False

        for turn in range(max_turns):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.1
                )
            except BadRequestError as e:
                msg = str(e)
                if "credits" in msg.lower():
                    return {"message": "⚠️ **AI service unavailable**: Insufficient credits.", "input_tokens": _in_tok, "output_tokens": _out_tok}
                return {"message": f"⚠️ **AI service error**: {msg}", "input_tokens": _in_tok, "output_tokens": _out_tok}
            except AuthenticationError:
                return {"message": "⚠️ **Authentication error**: Invalid API key.", "input_tokens": _in_tok, "output_tokens": _out_tok}
            except RateLimitError:
                return {"message": "⚠️ **Rate limit reached**: Please wait a moment.", "input_tokens": _in_tok, "output_tokens": _out_tok}
            except APIConnectionError:
                return {"message": "⚠️ **Connection error**: Could not reach AI service.", "input_tokens": _in_tok, "output_tokens": _out_tok}

            if hasattr(response, 'usage') and response.usage:
                _in_tok += response.usage.prompt_tokens
                _out_tok += response.usage.completion_tokens

            content = response.choices[0].message.content
            tool_called = False

            try:
                start_indices = [m.start() for m in re.finditer(r'\{', content)]
                for start_idx in start_indices:
                    brace_count = 0
                    end_idx = -1
                    for i in range(start_idx, len(content)):
                        if content[i] == '{':
                            brace_count += 1
                        elif content[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_idx = i + 1
                                break
                    if end_idx == -1:
                        continue
                    json_str = content[start_idx:end_idx]
                    try:
                        clean_json = json_str.strip('`').strip()
                        if clean_json.startswith('json'):
                            clean_json = clean_json[4:].strip()
                        data = json.loads(clean_json)
                        tool_name = None
                        args = None
                        if isinstance(data, dict):
                            if "tool" in data and "arguments" in data:
                                tool_name = data["tool"]
                                args = data["arguments"]
                            else:
                                for key in ["create_and_save_mlh_strategy", "mlh_validate_strategy",
                                            "mlh_get_validation_rules", "get_my_strategies",
                                            "delete_strategy", "get_strategy_record",
                                            "modify_strategy", "rename_strategy", "get_balance",
                                            "get_backtest_options", "run_backtest", "get_backtest_result",
                                            "get_deploy_options", "deploy_strategy"]:
                                    if key in data:
                                        tool_name = key
                                        val = data[key]
                                        if tool_name == "create_and_save_mlh_strategy":
                                            args = val if "strategy_json" in val else {"strategy_json": val}
                                        else:
                                            args = val
                                        break
                        if tool_name and args is not None:
                            args_str = json.dumps(args, sort_keys=True)
                            tool_key = f"{tool_name}:{args_str}"
                            if tool_key in executed_tools:
                                continue
                            executed_tools.add(tool_key)
                            print(f"> [MLH Turn {turn+1}] Executing tool: {tool_name}")
                            tool_result = mlh_handler.handle_tool_call(tool_name, args)
                            messages.append({"role": "assistant", "content": content})
                            messages.append({"role": "user", "content": f"SYSTEM TOOL RESULT: {json.dumps(tool_result)}"})
                            tool_called = True
                            if tool_name == "create_and_save_mlh_strategy" and tool_result.get("status") == "success":
                                clean_summary = re.sub(r'\{.*\}', '', content, flags=re.DOTALL).strip()
                                if not clean_summary:
                                    clean_summary = content
                                return {"message": clean_summary + "\n\n**Strategy Saved Successfully.**", "input_tokens": _in_tok, "output_tokens": _out_tok}
                            break
                    except Exception:
                        continue
                if tool_called:
                    continue
            except Exception as e:
                print(f"Tool parsing error: {e}")

            if _is_confirm and not tool_called and not _confirm_retry_done:
                _confirm_retry_done = True
                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "user",
                    "content": (
                        "You must output the JSON tool call block now. No explanations. Just this:\n"
                        "{\"tool\": \"create_and_save_mlh_strategy\", \"arguments\": {\"strategy_json\": "
                        "{\"strategy_name\": \"...\", \"trading_mode\": \"...\", \"exchange\": \"...\", "
                        "\"legs\": [...all legs...], ... all other fields ...}}}"
                    )
                })
                continue

            ui_content = re.sub(r'\{.*\}', '', content, flags=re.DOTALL).strip()
            if not ui_content:
                ui_content = content
            return {"message": ui_content, "input_tokens": _in_tok, "output_tokens": _out_tok}

        messages.append({"role": "user", "content": "Please provide the final strategy summary."})
        try:
            final = self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.1)
            if hasattr(final, 'usage') and final.usage:
                _in_tok += final.usage.prompt_tokens
                _out_tok += final.usage.completion_tokens
            return {"message": final.choices[0].message.content, "input_tokens": _in_tok, "output_tokens": _out_tok}
        except Exception as e:
            return {"message": f"⚠️ **AI service error**: {e}", "input_tokens": _in_tok, "output_tokens": _out_tok}

    def stream_message(self, user_message, history=None):
        if history is None:
            history = []

        _confirm_words = {'yes', 'proceed', 'save', 'save it', 'confirm', 'go', 'ok', 'sure', 'approve', 'approved', 'continue', 'do it', 'submit'}
        _is_confirm = bool(history) and any(w in user_message.lower() for w in _confirm_words)

        context = mlh_retriever.get_context(user_message)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"Relevant Documentation Context:\n{context}"}
        ] + history + [{"role": "user", "content": user_message}]

        if _is_confirm:
            messages[-1] = {
                "role": "user",
                "content": (
                    user_message +
                    "\n\n[SAVE NOW: Output ONLY a JSON block calling create_and_save_mlh_strategy. "
                    "Format: {\"tool\": \"create_and_save_mlh_strategy\", \"arguments\": {\"strategy_json\": {...all fields including legs array...}}}]"
                )
            }

        max_turns = 10
        executed_tools = set()
        _in_tok = 0
        _out_tok = 0
        _confirm_retry_done = False

        for turn in range(max_turns):
            try:
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    stream_options={"include_usage": True},
                    temperature=0.1
                )
            except BadRequestError as e:
                msg = str(e)
                err = "⚠️ **AI service unavailable**: Insufficient credits." if "credits" in msg.lower() else f"⚠️ **AI error**: {msg}"
                yield {"t": "error", "v": err}
                return
            except AuthenticationError:
                yield {"t": "error", "v": "⚠️ **Authentication error**: Invalid API key."}
                return
            except RateLimitError:
                yield {"t": "error", "v": "⚠️ **Rate limit reached**: Please wait a moment."}
                return
            except APIConnectionError:
                yield {"t": "error", "v": "⚠️ **Connection error**: Could not reach AI service."}
                return

            full_content = ""
            brace_depth = 0

            try:
                for chunk in stream:
                    if not chunk.choices:
                        if hasattr(chunk, 'usage') and chunk.usage:
                            _in_tok += getattr(chunk.usage, 'prompt_tokens', 0) or 0
                            _out_tok += getattr(chunk.usage, 'completion_tokens', 0) or 0
                        continue
                    delta = chunk.choices[0].delta.content or ""
                    full_content += delta
                    text_part = ""
                    for char in delta:
                        if char == '{':
                            if brace_depth == 0 and text_part:
                                yield {"t": "chunk", "v": text_part}
                                text_part = ""
                            brace_depth += 1
                        elif char == '}':
                            brace_depth = max(0, brace_depth - 1)
                        elif brace_depth == 0:
                            text_part += char
                    if text_part and brace_depth == 0:
                        yield {"t": "chunk", "v": text_part}
            except Exception as e:
                print(f"[MLH] Stream error on turn {turn+1}: {e}")

            if not full_content.strip():
                try:
                    fb = self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.1)
                    if hasattr(fb, 'usage') and fb.usage:
                        _in_tok += fb.usage.prompt_tokens or 0
                        _out_tok += fb.usage.completion_tokens or 0
                    full_content = fb.choices[0].message.content or ""
                    ui_text = re.sub(r'\{.*?\}', '', full_content, flags=re.DOTALL).strip()
                    if ui_text:
                        yield {"t": "chunk", "v": ui_text}
                except Exception as e2:
                    print(f"[MLH] Fallback error on turn {turn+1}: {e2}")
                    if turn == 0:
                        yield {"t": "error", "v": "⚠️ No response from AI service. Please try again."}
                        yield {"t": "done", "in_tok": _in_tok, "out_tok": _out_tok}
                        return

            tool_called = False
            try:
                start_indices = [m.start() for m in re.finditer(r'\{', full_content)]
                for start_idx in start_indices:
                    brace_count = 0
                    end_idx = -1
                    for i in range(start_idx, len(full_content)):
                        if full_content[i] == '{':
                            brace_count += 1
                        elif full_content[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_idx = i + 1
                                break
                    if end_idx == -1:
                        continue
                    json_str = full_content[start_idx:end_idx]
                    try:
                        clean_json = json_str.strip('`').strip()
                        if clean_json.startswith('json'):
                            clean_json = clean_json[4:].strip()
                        data = json.loads(clean_json)
                        tool_name = None
                        args = None
                        if isinstance(data, dict):
                            if "tool" in data and "arguments" in data:
                                tool_name = data["tool"]
                                args = data["arguments"]
                            else:
                                for key in ["create_and_save_mlh_strategy", "mlh_validate_strategy",
                                            "get_my_strategies", "delete_strategy", "get_strategy_record",
                                            "modify_strategy", "rename_strategy", "get_balance",
                                            "get_backtest_options", "run_backtest", "get_backtest_result",
                                            "get_deploy_options", "deploy_strategy"]:
                                    if key in data:
                                        tool_name = key
                                        val = data[key]
                                        if tool_name == "create_and_save_mlh_strategy":
                                            args = val if "strategy_json" in val else {"strategy_json": val}
                                        else:
                                            args = val
                                        break
                        if tool_name and args is not None:
                            args_str = json.dumps(args, sort_keys=True)
                            tool_key = f"{tool_name}:{args_str}"
                            if tool_key in executed_tools:
                                continue
                            executed_tools.add(tool_key)
                            _status_msgs = {
                                "create_and_save_mlh_strategy": "Saving Multi-Leg Hedger strategy to Market Maya...",
                                "get_my_strategies": "Fetching your strategies...",
                                "delete_strategy": "Deleting strategy...",
                                "get_strategy_record": "Fetching strategy record...",
                                "modify_strategy": "Saving changes...",
                                "rename_strategy": "Renaming strategy...",
                                "get_balance": "Fetching balance...",
                                "get_backtest_options": "Fetching backtest options...",
                                "run_backtest": "Running backtest (this may take 10–30 seconds)...",
                                "get_backtest_result": "Fetching backtest results...",
                                "get_deploy_options": "Fetching deploy options...",
                                "deploy_strategy": "Deploying strategy to Market Maya...",
                            }
                            yield {"t": "status", "v": _status_msgs.get(tool_name, "Processing...")}
                            tool_result = mlh_handler.handle_tool_call(tool_name, args)
                            messages.append({"role": "assistant", "content": full_content})
                            messages.append({"role": "user", "content": f"SYSTEM TOOL RESULT: {json.dumps(tool_result)}"})
                            tool_called = True
                            if tool_name == "create_and_save_mlh_strategy" and tool_result.get("status") == "success":
                                yield {"t": "chunk", "v": "\n\n**Strategy Saved Successfully.**"}
                                yield {"t": "done", "in_tok": _in_tok, "out_tok": _out_tok}
                                return
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            if _is_confirm and not tool_called and not _confirm_retry_done:
                _confirm_retry_done = True
                messages.append({"role": "assistant", "content": full_content})
                messages.append({
                    "role": "user",
                    "content": (
                        "Generate the JSON tool call block now. Output only:\n"
                        "{\"tool\": \"create_and_save_mlh_strategy\", \"arguments\": {\"strategy_json\": {...}}}"
                    )
                })
                continue

            if tool_called:
                continue

            yield {"t": "done", "in_tok": _in_tok, "out_tok": _out_tok}
            return

        yield {"t": "done", "in_tok": _in_tok, "out_tok": _out_tok}


mlh_orchestrator = MLHOrchestrator()
