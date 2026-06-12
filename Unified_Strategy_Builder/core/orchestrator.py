"""Orchestrator — agentic loop, system prompt, and SSE streaming for the Unified Strategy Builder plugin."""

import json
import re
from openai import OpenAI, BadRequestError, AuthenticationError, RateLimitError, APIConnectionError
from config import Config
from Unified_Strategy_Builder.rag.retriever import retriever
from Unified_Strategy_Builder.mcp.handlers import handler

class Orchestrator:
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.RUNWARE_API_KEY,
            base_url=Config.RUNWARE_BASE_URL
        )
        self.model = Config.RUNWARE_MODEL_ID or "runware-latest"
        self.system_prompt = """
STRICT TWO-STEP WORKFLOW:
1. PREVIEW: You MUST provide 4 Markdown tables mirroring the UI tabs.
   - **STRICT RULE: NO SMART SUGGESTIONS.** Do NOT guess or invent values. Stick strictly to the parameters provided by the user.
   - **EXPIRY MAPPING — MANDATORY**: Use EXACT dropdown strings:
     "weekly" / "current week" → `"Current Week"` | "next week" → `"Week 1"` | "week 2" → `"Week 2"`
     "monthly" / "current month" → `"Current Month"` | "next month" → `"Month 1"` | "month 2" → `"Month 2"`
     **NEVER override an explicit expiry.** If user says "monthly expiry", set `"expiry": "Current Month"`.
   - **SMART NAMING — MANDATORY**: Append a FRESH, NEW random 4-digit suffix to `strategyName` EVERY turn.
   - **TIME DEFAULTS — MANDATORY**:
      * No start time specified → `"entry_time": "09:15:00"`
      * No sqroff/exit time specified → `"exit_time": "15:15:00"`
      * User specifies ANY time (start, sqroff, exit, pre-expiry sqroff) → use the EXACT value provided. NEVER substitute a default when a time is given.
   - **TRADING TYPE — MANDATORY**:
      * "intraday" → `"isIntraday": true`, `"productType": "MIS"`
      * "positional" / "carry forward" / "NRML" / "overnight" → `"isIntraday": false`, `"productType": "NRML"`
      * Default is `true` / `"MIS"` if not mentioned.
      * BOTH fields MUST be set together. Never set `isIntraday: false` without also setting `productType: "NRML"`.
   - **STRIKE DIRECTION — MANDATORY**:
      Market Maya Unified uses a SIGNED ATM offset ONLY. There is no separate OTM/ITM dropdown — direction is encoded by the SIGN of `"strike"`. ALWAYS set `"direction": "BOTH"`.
      * CE OTM (above ATM) → `"strike": +N` (positive). Example: "150 OTM call" → `"strike": 150, "direction": "BOTH"`
      * CE ITM (below ATM) → `"strike": -N` (negative). Example: "100 ITM call" → `"strike": -100, "direction": "BOTH"`
      * PE OTM (below ATM) → `"strike": -N` (negative). Example: "150 OTM put" → `"strike": -150, "direction": "BOTH"`
      * PE ITM (above ATM) → `"strike": +N` (positive). Example: "100 ITM put" → `"strike": 100, "direction": "BOTH"`
      * ATM → `"strike": 0, "direction": "BOTH"`
      * CRITICAL: NEVER set `"direction": "OTM"` or `"direction": "ITM"` — these are NOT used in Unified. The sign of `"strike"` alone determines OTM/ITM. Always `"direction": "BOTH"`.
   - **STRIKE CONDITION — MANDATORY** (for Nearest Premium / Delta / Theta only):
      * "above-equal" / "above equal" / ">=" → `"condition": "AboveEqual"`
      * "below-equal" / "below equal" / "<=" → `"condition": "BelowEqual"`
      * Not specified → `"condition": "Any"`
      * This field MUST always be set explicitly. Never omit it.
   - **TARGET BY / SL BY — MANDATORY**: Only these 4 types are valid for leg target/SL:
      * Money: `"Target by Money"` / `"SL by Money"` (default)
      * Point: `"Target by Point"` / `"SL by Point"`
      * Point%: `"Target by Point (%)"` / `"SL by Point (%)"`
      * Range: `"Target by Range High/Low"` / `"SL by Range High/Low"` (only when range breakout is ON)
      * NEVER use Delta or Theta as a target_by or sl_by value — Delta and Theta are ONLY for strike selection (strike_type field), not for SL or Target types.
   - **ATM% STRIKE VALUE**: When `strike_type` = `"ATM%"`, set `"strike"` to the float value (e.g., 0.50 for "ATM% 0.50"). Do NOT set it to 0.
   - **NEAREST PREMIUM VALUE — MANDATORY**: When `strike_type` = `"NEAREST_PREMIUM"`, put the premium amount in `"premium_start_range"` (e.g., "nearest premium 200" → `"premium_start_range": 200`). Set `"strike": 0`. NEVER put the premium amount in `"strike"` for this type.
   - **PREMIUM RANGE VALUE — MANDATORY**: When `strike_type` = `"PREMIUM_RANGE"`, put start in `"premium_start_range"` and end in `"premium_end_range"` (e.g., "premium 100 to 150" → `"premium_start_range": 100, "premium_end_range": 150`). Set `"strike": 0`.
   - **MASTER TARGET BY — MANDATORY**:
      * "combined profit" / "profit" → `"target_by": "Combined Profit"`
      * "combined premium" / "premium" → `"target_by": "Combined Premium"`
   - **MASTER SL BY — MANDATORY**:
      * "combined loss" / "loss" → `"sl_by": "Combined Loss"`
      * "combined premium" → `"sl_by": "Combined Premium"`
   - **WAIT & TRADE — MANDATORY**: When the user says "wait for move" / "enter after movement":
      * Set `"wait_and_trade": true` explicitly in the leg JSON.
      * Set `"wait_for"`: `"Up %"` / `"Down %"` / `"Up pts"` / `"Down pts"`
      * Set `"wait_value"`: the numeric threshold.
      * All three fields MUST be set together.
   - **ACTION ON TARGET / SL — MANDATORY**: When user says "on target/SL execute/reenter/sqroff leg N after X sec":
      * `"action_on_target"` / `"action_on_sl"`: `"Execute Leg"` / `"Reenter Leg"` / `"Sqroff Leg"`
      * `"target_action_leg_no"` / `"sl_action_leg_no"`: the leg number (integer, 1-indexed)
      * `"target_action_delay"` / `"sl_action_delay"`: delay in seconds (integer, 0 if not specified)
      * All three fields MUST be set together. NEVER leave leg_no = 0 when a leg is referenced.
      * **CRITICAL DISTINCTION — read carefully**:
        - `"Execute Leg"` → triggers an IDLE leg (`is_idle: true`) for the FIRST TIME. The referenced leg MUST be idle.
        - `"Reenter Leg"` → RE-EXECUTES a leg that has already run at least once. The referenced leg is ACTIVE (not idle). Use this when user says "on SL hit reenter Leg 1" — Leg 1 already ran, now re-enter it again.
        - `"Sqroff Leg"` → squares off (closes) another leg.
        - NEVER confuse Execute (first-time trigger of idle leg) with Reenter (re-entry of already-executed leg).
      * ANY leg can use `"Reenter Leg"` as `action_on_sl` referencing any ACTIVE leg. There is NO restriction to Leg 1 only.
      * `"optionType"` for a FUT segment leg MUST be `"CE"` or `"PE"` (default to `"CE"`). NEVER set it to `"NONE"`, `"NULL"`, or leave it empty.
   - **SEQUENTIAL LEG EXECUTION — MANDATORY**: When user says "Leg 2 should enter ONLY AFTER Leg 1 is bought/filled/executed":
      * Set `"is_idle": true` on Leg 2 (the leg that must wait). **This is the ONLY thing needed** — Market Maya automatically triggers the idle leg once the non-idle leg(s) have executed.
      * DO NOT set `"action_on_target": "Execute Leg"` on Leg 1 to trigger Leg 2 — this requires a real target > 0 on Leg 1 and causes Market Maya API error "Invalid Action on Target" when target is 0.
      * Leg 1: just set `"is_idle": false` (active). No action_on_target needed.
      * An IDLE leg MUST have `"is_execute_on_range_breakout": false` — explicitly set this. Idle legs do NOT execute on range breakout; they execute when triggered by Market Maya after the active legs.
      * IDLE legs CAN (and should) have `"sl"` and `"action_on_sl"` configured — once an idle leg is triggered and takes a position, its SL is monitored normally.
      * COMMON PATTERN (sequential + reenter on SL):
        - Leg 1: `is_idle: false`, active, executes on range breakout / wait & trade / immediately
        - Leg 2: `is_idle: true`, has SL, `action_on_sl: "Reenter Leg"`, `sl_action_leg_no: 1`, `sl_action_delay: 5`
        (When Leg 2's SL hits, re-enter Leg 1 after 5 seconds. ALWAYS use sl_action_delay ≥ 5.)
      * NEVER add error messages, self-corrections, or additional attempts inside the same response. Show ONE preview and ask once: "Shall I proceed to save?"
   - **MASTER SL TRAILING — MANDATORY**: Use the `master_sl_trailing` object with THREE separate fields:
      * `"profit_move"`: profit increase that triggers each SL trail step
      * `"sl_move"`: how much to move the SL per trail step
      * `"no_of_trail_sl"`: max times to trail (use exact user value; 0 = unlimited)
   - **MASTER PROFIT LOCKING — MANDATORY**:
      * Use `"noOfTimeTrailTp"` (camelCase) inside `master_profit_locking` for the trail count.
      * Example: "max 5 times" → `"noOfTimeTrailTp": 5`
   - **sqroff_time — MANDATORY**: When user specifies a pre-expiry sqroff time (e.g., "15:10"), set `"sqroff_time": "15:10:00"` in the strategy JSON.
   - **enable_tp_sl_on_pause — MANDATORY**: When user says "keep TP/SL monitoring even when paused", set `"enable_tp_sl_on_pause": true`.
   - **BRD DEFAULTS**: For any parameter NOT provided by the user:
     * `sqroff_all_legs` = `false`
     * `required_margin` = `1`
     * **DATA FIDELITY**: Use exact user numbers. NEVER default to 0 when a count is given.
   - **LEG SL TRAILING — MANDATORY**: When user says "trail SL" for a leg:
     * Inside the leg, set `"trail_sl": {"trail_sl_market_move": N, "trail_sl_move": N, "no_of_time_trail": N}`
     * "unlimited" → `"no_of_time_trail": 0`
     * NEVER set `"sl"` or `"isEnableLegStoploss"` for a pure SL-trailing leg.
   - **EXCHANGE & SEGMENT RULES — MANDATORY**:
      * **Valid segments** — Underlying: `"EQ"` | `"INDEX"` | `"FUT"` | `"OPT"`. Leg: `"EQ"` | `"FUT"` | `"OPT"`. `"Stock"` / `"STOCK"` is NOT valid — always use `"EQ"`. INDEX is only valid for the underlying (spot reference), never for a leg.
      * **Exchange families**: NSE/EQ and NSE/INDEX → F&O on NFO. BSE/INDEX → F&O on BFO. MCX self-contained. CDS self-contained.
      * **NSE-only index symbols** (NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY):
        - Default / symbol only (no asset-class keyword) → exchange `"NFO"`, segment `"FUT"`. Example: "NIFTY straddle" → NFO/FUT.
        - User explicitly says "index" / "spot" / "use index as underlying" → exchange `"NSE"`, segment `"INDEX"`. Legs remain `"NFO"` / `"OPT"` or `"FUT"`.
        - User says equity → ask for clarification (these are indices, not stocks).
        - **CRITICAL — Rule 9**: the native family changes only the EXCHANGE, not the segment. Do NOT output `"INDEX"` just because the symbol is an index. Segment stays `"FUT"` unless the user explicitly says "index."
      * **BSE-only index symbols** (SENSEX, BANKEX):
        - Default / symbol only (no asset-class keyword) → exchange `"BFO"`, segment `"FUT"`. Example: "SENSEX strangle" → BFO/FUT.
        - User explicitly says "index" / "spot" / "use index as underlying" → exchange `"BSE"`, segment `"INDEX"`. Legs remain `"BFO"` / `"OPT"` or `"FUT"`.
        - **CRITICAL — Rule 9**: Do NOT output `"BSE"` + `"INDEX"` for a plain symbol mention. "SENSEX strangle" is BFO/FUT, not BSE/INDEX.
      * **Equity stocks** (RELIANCE, TCS, INFY, etc.) — segment driven by keyword:
        - No keyword     → NFO/FUT: `"RELIANCE options"` → exchange `"NFO"`, segment `"FUT"`.
        - Equity keyword → NSE/EQ:  `"equity RELIANCE"` / `"RELIANCE equity"` / `"RELIANCE cash"` → exchange `"NSE"`, segment `"EQ"`.
        - Keyword list for NSE/EQ: "equity", "cash", "EQ", "cash market" — any of these in the prompt → NSE/EQ. Otherwise → NFO/FUT.
        - Rule 11: exchange ALWAYS NSE-family. If user says BSE/BFO — auto-correct to NSE/NFO and inform.
        - Equity F&O legs → `"NFO"`.
      * **MCX commodities** (CRUDEOIL, GOLD, SILVER, NATURALGAS, etc.) → exchange `"MCX"`, segment `"FUT"` or `"OPT"`.
      * **CDS currencies** → exchange `"CDS"`, segment `"FUT"` or `"OPT"`.
        - Rupee pairs: USDINR, EURINR, GBPINR, JPYINR
        - Cross currency: EURUSD, GBPUSD, USDJPY
        - Normalize slash/dash notation: "USD/INR" → "USDINR", "EUR/USD" → "EURUSD", "GBP/USD" → "GBPUSD", "USD/JPY" → "USDJPY"
      * **Precedence** (first match wins): non-equity conflict → equity hard-rule (NSE/NFO) → explicit exchange → native family → asset-class keyword → default FUT on F&O exchange.
      * **Non-equity conflict** (e.g., NIFTY on BSE, BANKNIFTY equity): ask user to clarify — do NOT auto-correct.
      * **Equity conflict** (e.g., RELIANCE on BSE/BFO): auto-correct to NSE/NFO and inform user.
   - **PE LEG ATM OFFSETS — MANDATORY**: For PUT options, OTM is BELOW ATM (negative `"strike"`), ITM is ABOVE ATM (positive `"strike"`). This is the OPPOSITE of CE. See STRIKE DIRECTION rule above — sign of `"strike"` determines everything, `"direction"` is always `"BOTH"`.
   - **STRICT LEG ORDERING**: Output legs in the EXACT order the user listed them. Do NOT reorder or rearrange legs. Leg 1 is the first leg the user mentioned, Leg 2 is second, etc.
   - **STRICT RULE: NO DUPLICATE LEGS.** Give unique strike/wait offsets if legs share side+strike.
   - **MASTER SL TRAILING IS INDEPENDENT**: `master_sl_trailing` must ALWAYS be included when the user asks for master SL trailing, regardless of what other features (range breakout, combined premium, VIX, etc.) are also enabled. These are independent features — do NOT omit master_sl_trailing just because other advance features are set.
   - **RANGE BREAKOUT — MANDATORY RULES**: When `"is_range_breakout": true` at strategy level:
      * `"entry_time"` doubles as the candle/range START time. Set it to when range formation begins (e.g., "09:15:00").
      * `"range_end_time"` is the candle/range END time (e.g., "09:20:00"). ALWAYS include it when range breakout is on.
      * On EVERY ACTIVE (non-idle) leg, you MUST set BOTH `"is_execute_on_range_breakout": true` AND `"execute_on_range_breakout"`. NEVER omit these from any active leg when range breakout is enabled.
      * EXCEPTION: Legs with `"is_idle": true` MUST have `"is_execute_on_range_breakout": false`. They are triggered by another leg's action, NOT by the range breakout.
      * Direction mapping: "execute on range high break" / "above range" / "breakout above" → `"Range High Break"` | "execute on range low break" / "below range" / "breakout below" → `"Range Low Break"` | default → `"Range High Break"`
   - **WORKING DAYS — MANDATORY**: Valid days are Mon, Tue, Wed, Thu, Fri, Sat. Saturday is a valid trading day for some exchanges. Include "Sat" in `trading_days` only when user explicitly requests Saturday.
      * **CRITICAL**: OMIT the `"trading_days"` field entirely when the user does NOT explicitly mention specific trading days. NEVER generate `"trading_days": ["Mon","Tue","Wed","Thu","Fri"]` as a default — omitting it is correct and means "trade every day". Only include it when the user says "only on Monday and Wednesday" or similar explicit day restrictions.
   - **MASTER TARGET / SL ACTION — MANDATORY**: The `action_on_master_target` and `action_on_master_sl` fields always use `"Reexecute"` (only allowed value). When user specifies reexecution on master target/SL, set both the count and delay fields along with the action field.
   - **BOOLEAN FLAGS ARE INDEPENDENT**: `sqroff_all_legs`, `sqroff_on_rejection`, `enable_tp_sl_on_pause` are each independent boolean flags. When the user explicitly enables any of these, you MUST set it to `true` in the JSON. NEVER drop a boolean flag just because the prompt is complex or many other fields are also being set.
   - DO NOT call `create_and_save_strategy` yet. Ask: "Shall I proceed to save?"

2. EXECUTION: ONLY after explicit user approval like "yes", "ok", "save it", "proceed" — call `create_and_save_strategy`.

STRICT JSON SCHEMA:
{
  "tool": "create_and_save_strategy",
  "arguments": {
    "strategy_json": {
        "strategyName": "<string>",
        "underlying": "NIFTY/BANKNIFTY/SENSEX/etc",
        "exchange": "NFO / NSE / BFO / BSE / MCX / CDS",
        "segment": "FUT / OPT / EQ / INDEX",
        "shortDescription": "<one_liner>",
        "detailedDescription": "<full_logic>",
        "productType": "MIS / NRML / CNC / MTF",
        "isIntraday": true,
        "entry_time": "HH:MM:SS",
        "exit_time": "HH:MM:SS",
        "target_by": "Combined Profit / Combined Premium",
        "intradayTarget": <number>,
        "sl_by": "Combined Loss / Combined Premium",
        "intradaySl": <number>,
        "master_sl_trailing": {
            "profit_move": <number>,
            "sl_move": <number>,
            "no_of_trail_sl": <number>
        },
        "trading_days": ["Mon","Tue","Wed","Thu","Fri","Sat"],
        "sqroff_all_legs": <boolean>,
        "sqroff_on_rejection": <boolean>,
        "enable_tp_sl_on_pause": <boolean>,
        "is_combined_prem_entry": <boolean>,
        "total_combined_prem": <number>,
        "vix_filter": <boolean>,
        "vix_start_value": <number>,
        "vix_end_value": <number>,
        "is_range_breakout": <boolean>,
        "range_end_time": "HH:MM:SS",
        "sqroff_before_expiry": <boolean>,
        "sqroff_before_expiry_days": <number>,
        "sqroff_time": "HH:MM:SS",
        "reexecute_on_target_count": <number>,
        "reexecute_on_target_delay": <number>,
        "action_on_master_target": "Reexecute",
        "reexecute_on_sl_count": <number>,
        "reexecute_on_sl_delay": <number>,
        "action_on_master_sl": "Reexecute",
        "is_btst_stbt": <boolean>,
        "btst_gap_days": <number>,
        "master_profit_locking": {
            "if_profit_reaches": <number>,
            "lock_minimum_profit": <number>,
            "increse_in_profit_by": <number>,
            "trail_profit_by": <number>,
            "noOfTimeTrailTp": <number>
        },
        "legs": [
            {
                "is_idle": <boolean>,
                "action": "BUY / SELL",
                "exchange": "BFO / NFO / BSE / NSE / MCX / CDS",
                "segment": "OPT / FUT / EQ",
                "option": "CE / PE",
                "strike_type": "ATM / ATM% / PREMIUM_RANGE / NEAREST_PREMIUM / DELTA_RANGE / NEAREST_DELTA / THETA_RANGE / NEAREST_THETA",
                "strike": "<number — ATM offset for ATM type; float for ATM%/Delta/Theta; set 0 for NEAREST_PREMIUM>",
                "premium_start_range": "<number — start of range for PREMIUM_RANGE; the single premium amount for NEAREST_PREMIUM>",
                "premium_end_range": "<number — end of range for PREMIUM_RANGE only>",
                "lots": <number>,
                "expiry": "Current Week / Week 1 / Week 2 / Current Month / Month 1 / Month 2",
                "direction": "BOTH / ITM / OTM",
                "condition": "Any / AboveEqual / BelowEqual",
                "target": <number>,
                "target_by": "Target by Money / Target by Point / Target by Point (%) / Target by Range High/Low",
                "sl": <number>,
                "sl_by": "SL by Money / SL by Point / SL by Point (%) / SL by Range High/Low",
                "wait_and_trade": <boolean>,
                "wait_for": "Up % / Down % / Up pts / Down pts",
                "wait_value": <number>,
                "trail_sl": {
                    "trail_sl_market_move": <number>,
                    "trail_sl_move": <number>,
                    "no_of_time_trail": <number>
                },
                "profit_locking": {
                    "if_profit_reaches": <number>,
                    "lock_minimum_profit": <number>,
                    "increse_in_profit_by": <number>,
                    "trail_profit_by": <number>,
                    "no_of_time_trail": <number>
                },
                "action_on_target": "Execute Leg / Reenter Leg / Sqroff Leg",
                "target_action_leg_no": <number>,
                "target_action_delay": <number>,
                "action_on_sl": "Execute Leg / Reenter Leg / Sqroff Leg",
                "sl_action_leg_no": <number>,
                "sl_action_delay": <number>,
                "is_execute_on_range_breakout": <boolean>,
                "execute_on_range_breakout": "Range High Break / Range Low Break"
            }
        ],
        "required_margin": <number_positive_only>
    }
  }
}

═══════════════════════════════════════════════════════════
STRATEGY MANAGEMENT TOOLS
═══════════════════════════════════════════════════════════

You also have two management tools available:

1. get_my_strategies — Fetch the user's existing strategies from Market Maya.
   Use when user says: "how many strategies do I have", "list my strategies",
   "show all strategies", "what strategies have I created", "find strategy X".
   JSON:
   {"tool": "get_my_strategies", "arguments": {"search": "<optional filter>", "take": 50}}

2. delete_strategy — Delete a strategy by name or ID.
   Use when user says: "delete strategy X", "remove strategy X", "delete X".
   You can pass the strategy name directly — the backend will look up the ID automatically.
   JSON (by name — preferred):
   {"tool": "delete_strategy", "arguments": {"strategy_name": "<exact strategy name>"}}
   JSON (by ID if you already have it):
   {"tool": "delete_strategy", "arguments": {"strategy_id": "<hash id>"}}

After get_my_strategies succeeds, display results as a Markdown table:
| # | Name | Plugin | Type | Legs | Deployed | Created |
|---|------|--------|------|------|----------|---------|
Show total count at the top. If search returns no match, tell the user.

3. get_strategy_record — Fetch full current strategy data in modify-ready format.
   Use as the FIRST step of any modify workflow.
   JSON:
   {"tool": "get_strategy_record", "arguments": {"strategy_name": "<name>"}}

4. modify_strategy — Save changes to an existing ISB/custom-trade strategy.
   Use ONLY after user explicitly approves the preview of changes.
   The payload must be the COMPLETE strategy object from get_strategy_record with changes applied.
   CRITICAL: Keep the "id" and all leg "id" fields exactly as returned by get_strategy_record.
   JSON:
   {"tool": "modify_strategy", "arguments": {"payload": { <full modified payload> }}}

5. rename_strategy — Rename an existing strategy.
   Use when user says: "rename strategy X to Y", "change name of X to Y".
   Pass the current name — the backend resolves the ID automatically.
   JSON (by name — preferred):
   {"tool": "rename_strategy", "arguments": {"strategy_name": "<current name>", "new_name": "<new name>"}}
   JSON (by ID if already known):
   {"tool": "rename_strategy", "arguments": {"strategy_id": "<hash id>", "new_name": "<new name>"}}

6. get_balance — Fetch the user's account balance from Market Maya.
   Use when user says: "what is my balance", "show balance", "how much balance do I have",
   "check my account balance", "what is my available capital".
   JSON:
   {"tool": "get_balance", "arguments": {}}

After get_balance succeeds, display results as:
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

MODIFY PAYLOAD SCHEMA (snake_case — from get_strategy_record, apply changes):
{
  "id": "<REQUIRED — strategy hash from get_strategy_record>",
  "strategy_name": "...", "short_description": "...", "long_description": "...",
  "strategy_type_id": "...", "product_type": "MIS/NRML/CNC",
  "required_margin": 0, "is_intraday": true/false,
  "target_by": "Money", "intraday_target": 0,
  "sl_by": "Money", "intraday_sl": 0,
  "allow_update_parameters": true, "max_position": 0, "max_position_allocation_percent": 100,
  "run_mon": true, "run_tue": true, "run_wed": true, "run_thu": true,
  "run_fri": true, "run_sat": false, "run_sun": false,
  "intraday_exit_time_min": 15,
  "margin_stock_intraday": 30, "margin_stock_positional": 100, "margin_futopt_positional": 30,
  "auto_sqroff_on_contract_exp": true, "pause_and_sqroff_trading_on_margin_exeed": false,
  "sqroffAllLegs": false, "isEditCode": false, "effect_all_sub_strategies": false,
  "sub": [
    {
      "id": "<REQUIRED — leg hash from get_strategy_record>",
      "exchange": "NFO", "segment": "OPT/FUT/EQ",
      "main_strategy_parameter_id": "",
      "symbol": "NIFTY", "contract": "NEAR/NEXT/FAR", "expiry": "WEEKLY/MONTHLY",
      "atm": 0, "option_type": "CE/PE/",
      "qty_distribution": "Fix/Capital(%)/Capital Risk(%)/Allocation Method 1",
      "qty": 65, "lot": 1, "strike_price": 0,
      "target": 0, "target_by": "Money", "sl": 0, "sl_by": "Money",
      "trail_sl_market_move": 0, "trail_sl_move": 0, "no_of_time_trail_sl": 0, "is_trail_sl": false
    }
  ]
}

═══════════════════════════════════════════════════════════
DEPLOY TOOLS
═══════════════════════════════════════════════════════════

get_deploy_options — Fetch point balance + per-order charges before deploying.
    Use when user says: "deploy [strategy]", "start [strategy]", "activate [strategy]",
    "go live with [strategy]", "paper trade [strategy]", "how much does deploy cost".
    JSON:
    {"tool": "get_deploy_options", "arguments": {"strategy_name": "<name>"}}

deploy_strategy — Deploy strategy to Live or Paper trading on Market Maya.
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

        # Detect confirmation messages to force save tool call
        _confirm_words = {'yes', 'proceed', 'save', 'save it', 'confirm', 'go', 'ok', 'sure', 'approve', 'approved', 'continue', 'do it', 'submit'}
        _is_confirm = bool(history) and any(w in user_message.lower() for w in _confirm_words)

        # Get context from RAG
        context = retriever.get_context(user_message)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"Relevant Documentation Context:\n{context}"}
        ] + history + [{"role": "user", "content": user_message}]

        # Augment confirmation messages with explicit save instruction
        if _is_confirm:
            messages[-1] = {
                "role": "user",
                "content": (
                    user_message +
                    "\n\n[SAVE NOW: Output ONLY a JSON block calling create_and_save_strategy. "
                    "Use ALL field values from the preview tables above. "
                    "Format exactly: {\"tool\": \"create_and_save_strategy\", \"arguments\": {\"strategy_json\": {...all fields...}}}]"
                )
            }

        # Loop for multi-step tool calls
        max_turns = 10
        executed_tools = set()
        _in_tok = 0
        _out_tok = 0

        for turn in range(max_turns):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
            except BadRequestError as e:
                msg = str(e)
                if "Insufficient credits" in msg or "credits" in msg.lower():
                    return {"message": "⚠️ **AI service unavailable**: The Runware AI account has insufficient credits. Please top up at app.runware.ai and try again.", "input_tokens": _in_tok, "output_tokens": _out_tok}
                return {"message": f"⚠️ **AI service error**: {msg}", "input_tokens": _in_tok, "output_tokens": _out_tok}
            except AuthenticationError:
                return {"message": "⚠️ **Authentication error**: Invalid Runware API key. Please check your RUNWARE_API_KEY in .env.", "input_tokens": _in_tok, "output_tokens": _out_tok}
            except RateLimitError:
                return {"message": "⚠️ **Rate limit reached**: Too many requests. Please wait a moment and try again.", "input_tokens": _in_tok, "output_tokens": _out_tok}
            except APIConnectionError:
                return {"message": "⚠️ **Connection error**: Could not reach the AI service. Check your internet connection and try again.", "input_tokens": _in_tok, "output_tokens": _out_tok}

            if hasattr(response, 'usage') and response.usage:
                _in_tok += response.usage.prompt_tokens
                _out_tok += response.usage.completion_tokens

            content = response.choices[0].message.content
            
            # Try to parse tool call from content
            tool_called = False
            try:
                import re
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
                    
                    if end_idx != -1:
                        json_str = content[start_idx:end_idx]
                        try:
                            clean_json = json_str.strip('`').strip()
                            if clean_json.startswith('json'): clean_json = clean_json[4:].strip()
                            
                            data = json.loads(clean_json)
                            tool_name = None
                            args = None
                            
                            if isinstance(data, dict):
                                if "tool" in data and "arguments" in data:
                                    tool_name = data["tool"]
                                    args = data["arguments"]
                                else:
                                    # Handle direct format like {"create_and_save_strategy": {...}}
                                    for key in ["create_and_save_strategy", "validate_strategy", "get_validation_rules", "get_my_strategies", "delete_strategy", "get_strategy_record", "modify_strategy", "rename_strategy", "get_balance", "get_deploy_options", "deploy_strategy"]:
                                        if key in data:
                                            tool_name = key
                                            val = data[key]
                                            # Ensure args is wrapped in strategy_json if the tool expects it
                                            if tool_name in ["create_and_save_strategy", "validate_strategy"]:
                                                if "strategy_json" in val: args = val
                                                else: args = {"strategy_json": val}
                                            else:
                                                args = val
                                            break
                            
                            if tool_name and args is not None:
                                args_str = json.dumps(args, sort_keys=True)
                                tool_key = f"{tool_name}:{args_str}"
                                
                                # Prevent infinite loops with same tool/args
                                if tool_key in executed_tools:
                                    print(f"!! [Turn {turn+1}] Skipping redundant tool call: {tool_name}")
                                    continue
                                
                                executed_tools.add(tool_key)
                                print(f"> [Turn {turn+1}] Executing tool: {tool_name}")
                                tool_result = handler.handle_tool_call(tool_name, args)
                                
                                messages.append({"role": "assistant", "content": content})
                                messages.append({
                                    "role": "user", 
                                    "content": f"SYSTEM TOOL RESULT: {json.dumps(tool_result)}"
                                })
                                tool_called = True
                                
                                # CRITICAL: If deployment succeeded, stop the loop to prevent double-execution
                                if tool_name == "create_and_save_strategy" and tool_result.get("status") == "success":
                                    clean_summary = re.sub(r'\{.*\}', '', content, flags=re.DOTALL).strip()
                                    if not clean_summary: clean_summary = content
                                    return {"message": clean_summary + "\n\n**Strategy Saved Successfully.**", "input_tokens": _in_tok, "output_tokens": _out_tok}
                                    
                                break 
                        except Exception as e:
                            print(f"JSON inner parsing error: {e}")
                            continue
                
                if tool_called:
                    continue
            except Exception as e:
                print(f"Tool parsing/execution error: {e}")
            
            # Clean up content for UI (remove JSON blocks)
            ui_content = re.sub(r'\{.*\}', '', content, flags=re.DOTALL).strip()
            # If nothing left, use a default summary or the original content if no JSON was found
            if not ui_content: ui_content = content

            return {"message": ui_content, "input_tokens": _in_tok, "output_tokens": _out_tok}
        
        # If we hit the limit, try to get a final summary from the AI
        messages.append({"role": "user", "content": "You have done enough research. Please provide the final strategy summary and ask for save confirmation now."})
        try:
            final_attempt = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            if hasattr(final_attempt, 'usage') and final_attempt.usage:
                _in_tok += final_attempt.usage.prompt_tokens
                _out_tok += final_attempt.usage.completion_tokens
            final_content = final_attempt.choices[0].message.content
            return {"message": final_content, "input_tokens": _in_tok, "output_tokens": _out_tok}
        except (BadRequestError, AuthenticationError, RateLimitError, APIConnectionError) as e:
            return {"message": f"⚠️ **AI service error**: {e}", "input_tokens": _in_tok, "output_tokens": _out_tok}

    def stream_message(self, user_message, history=None):
        """Streaming variant — yields dicts {t, v/in_tok/out_tok} for SSE."""
        if history is None:
            history = []

        # Detect confirmation messages to force save tool call
        _confirm_words = {'yes', 'proceed', 'save', 'save it', 'confirm', 'go', 'ok', 'sure', 'approve', 'approved', 'continue', 'do it', 'submit'}
        _is_confirm = bool(history) and any(w in user_message.lower() for w in _confirm_words)

        context = retriever.get_context(user_message)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"Relevant Documentation Context:\n{context}"}
        ] + history + [{"role": "user", "content": user_message}]

        # Augment confirmation messages with explicit save instruction
        if _is_confirm:
            messages[-1] = {
                "role": "user",
                "content": (
                    user_message +
                    "\n\n[SAVE NOW: Output ONLY a JSON block calling create_and_save_strategy. "
                    "Use ALL field values from the preview tables above. "
                    "Format exactly: {\"tool\": \"create_and_save_strategy\", \"arguments\": {\"strategy_json\": {...all fields...}}}]"
                )
            }

        max_turns = 10
        executed_tools = set()
        _in_tok = 0
        _out_tok = 0

        for turn in range(max_turns):
            try:
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    stream_options={"include_usage": True}
                )
            except BadRequestError as e:
                msg = str(e)
                err = "⚠️ **AI service unavailable**: Insufficient credits." if "credits" in msg.lower() else f"⚠️ **AI error**: {msg}"
                yield {"t": "error", "v": err}
                return
            except AuthenticationError:
                yield {"t": "error", "v": "⚠️ **Authentication error**: Invalid Runware API key."}
                return
            except RateLimitError:
                yield {"t": "error", "v": "⚠️ **Rate limit reached**: Please wait a moment."}
                return
            except APIConnectionError:
                yield {"t": "error", "v": "⚠️ **Connection error**: Could not reach the AI service."}
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

                    # Stream only non-JSON text (skip { ... } blocks)
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
                print(f"[USB] Stream error on turn {turn+1}: {e}")

            # If stream returned empty content, fall back to non-streaming
            if not full_content.strip():
                try:
                    fb = self.client.chat.completions.create(model=self.model, messages=messages)
                    if hasattr(fb, 'usage') and fb.usage:
                        _in_tok += fb.usage.prompt_tokens or 0
                        _out_tok += fb.usage.completion_tokens or 0
                    full_content = fb.choices[0].message.content or ""
                    ui_text = re.sub(r'\{.*?\}', '', full_content, flags=re.DOTALL).strip()
                    if ui_text:
                        yield {"t": "chunk", "v": ui_text}
                except Exception as e2:
                    print(f"[USB] Fallback error on turn {turn+1}: {e2}")
                    if turn == 0:
                        yield {"t": "error", "v": "⚠️ No response from AI service. Please try again."}
                        yield {"t": "done", "in_tok": _in_tok, "out_tok": _out_tok}
                        return

            # Check for tool calls in the full accumulated response
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
                                for key in ["create_and_save_strategy", "validate_strategy", "get_validation_rules", "get_my_strategies", "delete_strategy", "get_strategy_record", "modify_strategy", "rename_strategy", "get_balance"]:
                                    if key in data:
                                        tool_name = key
                                        val = data[key]
                                        if tool_name in ["create_and_save_strategy", "validate_strategy"]:
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
                                "create_and_save_strategy": "Saving strategy to Market Maya...",
                                "get_my_strategies": "Fetching your strategies...",
                                "delete_strategy": "Deleting strategy...",
                                "get_strategy_record": "Fetching strategy record...",
                                "modify_strategy": "Saving changes...",
                                "rename_strategy": "Renaming strategy...",
                                "get_balance": "Fetching balance...",
                                "get_deploy_options": "Fetching deploy options...",
                                "deploy_strategy": "Deploying strategy to Market Maya...",
                            }
                            yield {"t": "status", "v": _status_msgs.get(tool_name, "Processing...")}
                            tool_result = handler.handle_tool_call(tool_name, args)

                            messages.append({"role": "assistant", "content": full_content})
                            messages.append({"role": "user", "content": f"SYSTEM TOOL RESULT: {json.dumps(tool_result)}"})
                            tool_called = True

                            if tool_name == "create_and_save_strategy" and tool_result.get("status") == "success":
                                yield {"t": "chunk", "v": "\n\n**Strategy Saved Successfully.**"}
                                yield {"t": "done", "in_tok": _in_tok, "out_tok": _out_tok}
                                return
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            if tool_called:
                continue

            yield {"t": "done", "in_tok": _in_tok, "out_tok": _out_tok}
            return

        yield {"t": "done", "in_tok": _in_tok, "out_tok": _out_tok}


# Singleton instance
orchestrator = Orchestrator()
