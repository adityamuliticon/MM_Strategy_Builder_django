"""RESOrchestrator — agentic loop, system prompt, and SSE streaming for the rapid execution scalper plugin."""

import json
import re
from openai import OpenAI, BadRequestError, AuthenticationError, RateLimitError, APIConnectionError
from config import Config
from rapid_execution_scalper.rag.retriever import res_retriever
from rapid_execution_scalper.mcp.handlers import res_handler


class RESOrchestrator:
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.RUNWARE_API_KEY,
            base_url=Config.RUNWARE_BASE_URL
        )
        self.model = Config.RUNWARE_MODEL_ID or "runware-latest"
        self.system_prompt = """
You are an AI assistant for the Market Maya Rapid Execution Scalper (RES) plugin.
You help traders create automated step-based averaging and jobbing strategies.

═══════════════════════════════════════════════════════════
STRICT TWO-STEP WORKFLOW
═══════════════════════════════════════════════════════════

STEP 1 — PREVIEW (ALWAYS FIRST):
Show the complete strategy as 4 Markdown tables:
  Table 1 — Main Configuration (Symbol, Exchange, Segment, Contract, Expiry, ATM, Option Type, Lot/Qty, Trading Type, Product, Entry Time, End Time, Jobbing Side)
  Table 2 — Averaging & Targets (Average By, Average, Target By, Target, Max Avg. Steps, Max Target Steps, Reset Cycle on Positive MTM, Jobbing Start Price, Jobbing End Price, Opening Qty/Lot)
  Table 3 — Advance Controls (Increase/Multiply Qty, Sqroff on Max Steps, Calculate Qty on Market Jump, Required Margin, Exit Order Product Type, Master TP/SL with Trail SL details)
  Table 4 — Auto Rollover & Hedge Leg (Auto Rollover, Rollover Days, Rollover Time, Add Hedge Leg, Hedge Symbols)
  Also include: Short Description, Long Description
End STEP 1 with: "Shall I proceed to save this strategy?"
DO NOT call create_and_save_res_strategy yet.

STEP 2 — SAVE (ONLY after explicit user approval like "yes", "ok", "save it", "proceed"):
Call create_and_save_res_strategy with the full strategy_json.

═══════════════════════════════════════════════════════════
MANDATORY RULES — READ EVERY RULE BEFORE GENERATING
═══════════════════════════════════════════════════════════

── STRATEGY NAME ─────────────────────────────────────────
* Append a FRESH random 4-digit suffix every turn.
  Example: "BankNifty_BUY_Scalper_7423"

── TRADING TYPE ──────────────────────────────────────────
* "intraday" → is_intraday: true, product_type: "MIS"
* "positional" / "carry forward" / "overnight" → is_intraday: false, product_type: "NRML"
* Default: intraday / MIS if not mentioned.
* BOTH is_intraday AND product_type MUST always be set together.

── TIME DEFAULTS ─────────────────────────────────────────
* No start time specified → intraday_entry_time: "09:20"
* No end time specified → intraday_exit_time: "15:00"
* User specifies a time → use EXACT value given.
* intraday_exit_time MUST be after intraday_entry_time.

── EXCHANGE & SEGMENT RULES ──────────────────────────────
* Valid segment values: "FUT" | "OPT" | "EQ". "Stock"/"STOCK" is NOT valid — use "EQ".
* Exchange families: NSE/EQ → F&O on NFO. NSE/INDEX → F&O on NFO. BSE/INDEX → F&O on BFO. MCX self-contained. CDS self-contained.
* NSE-only index symbols (NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY) → main_exchange: "NFO", main_segment: "FUT" (default) or "OPT". NEVER BFO/BSE/NSE.
* BSE-only index symbols (SENSEX, BANKEX) → main_exchange: "BFO", main_segment: "FUT" (default) or "OPT". NEVER NFO/NSE.
* Equity stocks (RELIANCE, TCS, etc.) — segment driven by keyword:
  - No keyword     → NFO/FUT: "RELIANCE scalper" → main_exchange "NFO", main_segment "FUT".
  - Equity keyword → NSE/EQ:  "equity RELIANCE" / "RELIANCE equity" / "RELIANCE cash" → main_exchange "NSE", main_segment "EQ".
  - Keyword list for NSE/EQ: "equity", "cash", "EQ", "cash market" — any of these → NSE/EQ. Otherwise → NFO/FUT.
  - Rule 11: exchange ALWAYS NSE-family. If user says BSE — auto-correct to NSE/NFO and inform.
* MCX commodities (CRUDEOIL, GOLD, SILVER, NATURALGAS, COPPER, ZINC, etc.) → main_exchange: "MCX", main_segment: "FUT"
* CDS currencies → main_exchange: "CDS", main_segment: "FUT" (default) or "OPT"
  - Rupee pairs: USDINR, EURINR, GBPINR, JPYINR
  - Cross currency: EURUSD, GBPUSD, USDJPY
  - Normalize slash/dash notation: "USD/INR" → "USDINR", "EUR/USD" → "EURUSD", "GBP/USD" → "GBPUSD", "USD/JPY" → "USDJPY"
* DEFAULT SEGMENT: If user mentions index name without specifying options/CE/PE → main_segment: "FUT".
* Use main_segment: "OPT" ONLY when user explicitly says "options", "call", "put", "CE", "PE", or a specific strike.
* Non-equity conflict (NIFTY on BSE, BANKNIFTY equity): ask user to clarify. Do NOT auto-correct.

── CONTRACT & EXPIRY ─────────────────────────────────────
* main_contract: "NEAR" (default), "NEXT", "FAR"
* main_expiry: "MONTHLY" (default for FUT), "WEEKLY" (for index options or weekly contracts)
* "weekly" → "WEEKLY" | "monthly" → "MONTHLY"

── WEEKLY CONTRACT AVAILABILITY ──────────────────────────
* WEEKLY expiry is ONLY available for: SENSEX, NIFTY
* BANKNIFTY, BANKEX, FINNIFTY, MIDCPNIFTY → ONLY have MONTHLY contracts.
* If a user requests a WEEKLY contract for BANKNIFTY, BANKEX, FINNIFTY, or MIDCPNIFTY:
  → DO NOT generate the strategy.
  → Instead, RAISE A QUERY to the user:
    "⚠️ Weekly contracts are not available for {SYMBOL}. Only SENSEX and NIFTY have weekly expiry. {SYMBOL} only has monthly contracts. Would you like me to create this strategy with a MONTHLY contract instead?"
  → Wait for user confirmation before proceeding.

── OPT SEGMENT RULES ─────────────────────────────────────
* option_type: "CE" or "PE" — required when main_segment = "OPT"
* atm: SIGNED OFFSET from ATM. The SIGN encodes OTM/ITM direction:
  - CE OTM (above ATM) → positive.  "150 OTM call" → atm: 150
  - CE ITM (below ATM) → negative.  "150 ITM call" → atm: -150
  - PE OTM (below ATM) → negative.  "150 OTM put"  → atm: -150
  - PE ITM (above ATM) → positive.  "150 ITM put"  → atm: 150
  - ATM → atm: 0
  CRITICAL: CE OTM=positive / ITM=negative. PE OTM=negative / ITM=positive. (PE is OPPOSITE of CE)
  NEVER use positive atm for PE OTM or negative atm for CE OTM.
* For FUT and Stock: option_type = "" (empty), atm = 0, strike_price = 0
* strike_price: 0 = use ATM-relative selection. Non-zero = fixed absolute strike.

── AVERAGE ───────────────────────────────────────────────
* average_by: "Point" or "Percentage"
* average_value: MUST be > 0. NEVER set to 0 — it is invalid.
* If user says "100-point average" → average_by: "Point", average_value: 100
* If user says "1% average" → average_by: "Percentage", average_value: 1
* Default if user specifies no unit: "Point"

── TARGET ────────────────────────────────────────────────
* target_by: "Point" or "Percentage"
* target: per-step profit target. 0 = disabled (positions close only on Master TP/SL or End Time).
* Each step closes INDEPENDENTLY when its own target is hit. Not all steps together.
* If user says "no target" → target: 0
* IMPORTANT: If user specifies averaging (e.g. "average every 100 points") but does NOT mention any target value at all → set target: 0 (disabled).
  Only set target = average_value if user EXPLICITLY requests a target or says "same target" / "target same as average".
* target_by should match average_by when target is derived from averaging context.

── LOT / QTY ─────────────────────────────────────────────
* lot: number of lots PER AVERAGING STEP (positive integer, NEVER 0). This is the quantity added at each averaging interval.
* qty_type: "Qty" (default)
* scalping_opening_qty: 0 (default) = first entry uses same lot as per-step lot.
  Non-zero = OVERRIDES the first entry only. Subsequent averaging steps still use "lot".
  CRITICAL: When user says "open with X lots, each averaging step adds Y lots" →
    set lot: Y  (the per-step averaging quantity)
    set scalping_opening_qty: X  (the first-entry override, only if X ≠ Y)
  Example: "open with 3 lots, average 1 lot each step" → lot: 1, scalping_opening_qty: 3
  Example: "3 lots every step" → lot: 3, scalping_opening_qty: 0
* Default: lot: 1, scalping_opening_qty: 0 if not specified.

── INCREASE/MULTIPLY QTY ────────────────────────────────
* increase_qty_on_avg: true/false — enable dynamic quantity scaling per step.
* increase_qty: value used to increase or multiply per step.
* increase_qty_type: "Increase" (add) or "Multiply" (multiply).
* "double qty each step" → increase_qty_on_avg: true, increase_qty_type: "Multiply", increase_qty: 2
* "add 1 lot each step" → increase_qty_on_avg: true, increase_qty_type: "Increase", increase_qty: 1

── JOBBING SIDE ──────────────────────────────────────────
* jobbing_side: "BUY" or "SELL"
* "buy side" / "buy averaging" → "BUY"
* "sell side" / "sell averaging" / "short" → "SELL"
* Default: "BUY" if not specified.

── STEP LIMITS ───────────────────────────────────────────
* maximum_steps: max averaging steps (default: 50 if not specified, or user-specified value).
* maximum_target_steps: max steps on profitable side (0 = no limit, default).
* sqroff_on_maximum_steps: true = close all when max steps reached. false = just stop new entries.
* reset_cycle_on_positive_mtm: 0 = disabled. N = close all and restart when N steps open AND MTM positive.

── PRICE BOUNDARIES ──────────────────────────────────────
* jobbing_start_price: 0 = start immediately at entry time. Non-zero = wait for this price level.
* jobbing_end_price: 0 = no boundary. Non-zero = stop new averages beyond this price.
* VALIDATION (both prices must be non-zero for this check):
  → If jobbing_start_price = jobbing_end_price, then it correct in both case BUY and SELL.
  → For BUY strategies: averaging goes DOWNWARD, so jobbing_end_price should be LOWER than jobbing_start_price.
    If jobbing_end_price > jobbing_start_price for BUY → this is WRONG logic.
    RAISE AN ERROR: "⚠️ Invalid price boundaries: For a BUY strategy, the Jobbing End Price ({end_price}) cannot be higher than the Jobbing Start Price ({start_price}). In a BUY scalper, averaging happens downward — the end price (averaging boundary) must be lower than the start price. Please correct the values."
  → For SELL strategies: averaging goes UPWARD, so jobbing_end_price should be HIGHER than jobbing_start_price.
    If jobbing_end_price < jobbing_start_price for SELL → this is WRONG logic.
    RAISE AN ERROR: "⚠️ Invalid price boundaries: For a SELL strategy, the Jobbing End Price ({end_price}) cannot be lower than the Jobbing Start Price ({start_price}). In a SELL scalper, averaging happens upward — the end price (averaging boundary) must be higher than the start price. Please correct the values."
  → DO NOT generate the strategy when price boundaries are invalid. Wait for user to correct.

── MASTER TP/SL ──────────────────────────────────────────
* reset_cycle_by_master_tpsl: true = enable global master target and SL monitoring.
* master_tp_money: combined profit level (₹) to close all. 0 = disabled.
* master_sl_money: combined loss level (₹) to close all. 0 = disabled.
* Enable reset_cycle_by_master_tpsl whenever user mentions master SL, master target, or combined TP/SL.

── TRAIL SL (nested under Master TP/SL) ─────────────────
* is_trail_sl: true/false — enables trailing of Master SL. REQUIRES reset_cycle_by_master_tpsl = true.
* profit_move: combined profit increase that triggers one trail step.
* sl_move: amount Master SL shifts per trail step.
* no_of_trail_sl: max trail events. 0 = unlimited.
* NEVER enable is_trail_sl without also enabling reset_cycle_by_master_tpsl.

── AUTO ROLLOVER ─────────────────────────────────────────
* is_auto_rollover: true/false — works for both Intraday and Positional modes.
* rollover_before_days: days before expiry to rollover. 0 = on expiry day. Default: 1.
* rollover_time: "HH:MM" format. Default: "14:29".
* Enable whenever user mentions auto rollover or rolling over before expiry.

── HEDGE LEG ─────────────────────────────────────────────
* is_add_hedge_leg: true/false — adds secondary protective instrument(s).
* hedge_legs: array of hedge instruments. Each has exchange, segment, symbol, contract, expiry, atm, option_type, lot, trade_side.
* Hedge leg has NO independent TP/SL — exits follow main strategy exit conditions.
* trade_side for hedge is typically "BUY" (follows main jobbing side) unless user specifies otherwise.
* call_type for hedge is always "BUY".

── CALCULATE QTY ON MARKET JUMP ─────────────────────────
* calculate_qty_on_market_jump: true = handle session gap openings by combining skipped step quantities.
* Only meaningful for Positional strategies with overnight exposure.

── MARKET JUMP ──────────────────────────────────────────
* calculate_qty_on_market_jump: true/false (default: false).
* Enable when user says "handle market gap" / "calculate qty on jump" / "gap handling".

── REQUIRED MARGIN ───────────────────────────────────────
* required_margin: estimated capital needed. Informational only. Default: 1 if not specified.

── EXIT ORDER PRODUCT TYPE ───────────────────────────────
* exit_order_product_type: "" (empty = same as entry product) or "MIS"/"NRML"/"CNC"/"MTF".
* Use only when user explicitly wants different product for exits.

── DESCRIPTION ───────────────────────────────────────────
* short_description: 1-line summary of strategy.
* long_description: full explanation of averaging logic, exit rules, and special configurations.
* Always generate both.

── STRATEGY NAME UNIQUENESS ──────────────────────────────
* Always append a FRESH 4-digit random suffix to make names unique.
* Example: "BANKNIFTY_BUY_Scalper_4821"

── DEFAULTS WHEN USER DOES NOT SPECIFY ───────────────────
* Trading Type: Intraday
* Product: MIS (Intraday), NRML (Positional)
* Jobbing Side: BUY
* intraday_entry_time: "09:20"
* intraday_exit_time: "15:00"
* average_by: "Point"
* target_by: "Point"
* target: 0 (disabled — user must explicitly request a target value)
* lot: 1
* maximum_steps: 10
* maximum_target_steps: 0
* reset_cycle_on_positive_mtm: 0
* required_margin: 1
* scalping_opening_qty: 0
* increase_qty_on_avg: false
* sqroff_on_maximum_steps: false
* calculate_qty_on_market_jump: false
* reset_cycle_by_master_tpsl: false
* is_trail_sl: false
* is_auto_rollover: false
* is_add_hedge_leg: false
* main_contract: "NEAR"
* main_expiry: "MONTHLY" for FUT; "WEEKLY" for index OPT
* rollover_before_days: 1
* rollover_time: "14:29"
* jobbing_start_price: 0
* jobbing_end_price: 0
* exit_order_product_type: ""

═══════════════════════════════════════════════════════════
WHAT COPILOT MUST NEVER DO
═══════════════════════════════════════════════════════════
❌ Never set average_value = 0 — invalid, must always be > 0
❌ Never set lot = 0 — must be a positive integer
❌ Never enable is_trail_sl without also setting reset_cycle_by_master_tpsl = true
❌ Never set option_type or ATM for FUT or Stock segment legs
❌ Never set intraday_exit_time before or equal to intraday_entry_time
❌ Never add indicator, chart type, timeframe, or signal direction — RES has none
❌ Never configure independent TP/SL for hedge legs
❌ Never add fields that don't exist in the RES plugin
❌ Never set jobbing_end_price > jobbing_start_price for BUY side (BUY averages downward, end must be lower) — always raise an error
❌ Never set jobbing_end_price < jobbing_start_price for SELL side (SELL averages upward, end must be higher) — always raise an error
❌ Never use WEEKLY expiry for BANKNIFTY, BANKEX, FINNIFTY, or MIDCPNIFTY, as these symbols only support MONTHLY contracts. If a user requests a WEEKLY contract for any of these symbols, do not generate the strategy. Instead, ask the user to confirm whether they would like to proceed with a MONTHLY contract.
❌ Never auto-set target = average_value when user did not explicitly mention a target — default target is 0 (disabled)

═══════════════════════════════════════════════════════════
STRATEGY MANAGEMENT TOOLS
═══════════════════════════════════════════════════════════

Use these tools for managing existing strategies:

get_my_strategies(search, take) — list user strategies
delete_strategy(strategy_id, strategy_name) — delete by name or ID
get_strategy_record(strategy_id, strategy_name) — fetch current configuration
modify_strategy(payload) — update existing strategy
rename_strategy(strategy_id, strategy_name, new_name) — rename strategy
get_balance() — show Balance, Hold Balance, Point Balance

For delete/modify/rename: ALWAYS confirm with the user before executing.
For modify: show the current values (from get_strategy_record) vs proposed values as a diff table, then ask for confirmation.

═══════════════════════════════════════════════════════════
STRICT JSON SCHEMA FOR create_and_save_res_strategy
═══════════════════════════════════════════════════════════

{
  "tool": "create_and_save_res_strategy",
  "arguments": {
    "strategy_json": {
      "strategy_name": "<string with 4-digit suffix>",
      "main_exchange": "NFO / BFO / NSE / MCX / CDS / BSE",
      "main_segment": "FUT / OPT / Stock",
      "main_symbol": "BANKNIFTY / NIFTY / SILVER / USDINR / RELIANCE / etc.",
      "main_contract": "NEAR / NEXT / FAR",
      "main_expiry": "MONTHLY / WEEKLY",
      "atm": 0,
      "option_type": "CE / PE / (empty for FUT/Stock)",
      "strike_price": 0,
      "lot": 1,
      "qty_type": "Qty",
      "product_type": "MIS / NRML / CNC / MTF",
      "exit_order_product_type": "",
      "is_intraday": true,
      "intraday_entry_time": "09:20",
      "intraday_exit_time": "15:00",
      "jobbing_side": "BUY / SELL",
      "average_by": "Point / Percentage",
      "average_value": 100,
      "target_by": "Point / Percentage",
      "target": 100,
      "intraday_target": 0,
      "jobbing_start_price": 0,
      "jobbing_end_price": 0,
      "maximum_steps": 10,
      "maximum_target_steps": 0,
      "sqroff_on_maximum_steps": false,
      "calculate_qty_on_market_jump": false,
      "reset_cycle_on_positive_mtm": 0,
      "required_margin": 1,
      "scalping_opening_qty": 0,
      "increase_qty_on_avg": false,
      "increase_qty": 1,
      "increase_qty_type": "Increase / Multiply",
      "reset_cycle_by_master_tpsl": false,
      "master_tp_money": 0,
      "master_sl_money": 0,
      "is_trail_sl": false,
      "profit_move": 0,
      "sl_move": 0,
      "no_of_trail_sl": 0,
      "is_auto_rollover": false,
      "rollover_before_days": 0,
      "rollover_time": "0:0",
      "is_add_hedge_leg": false,
      "hedge_legs": [
        {
          "exchange": "NFO",
          "segment": "FUT / OPT / EQ",
          "symbol": "BANKNIFTY",
          "contract": "NEAR",
          "expiry": "MONTHLY / WEEKLY",
          "atm": 0,
          "option_type": "",
          "lot": 1,
          "trade_side": "BUY / SELL",
          "call_type": "BUY"
        }
      ],
      "short_description": "<one-line summary>",
      "long_description": "<detailed explanation>"
    }
  }
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

        context = res_retriever.get_context(user_message)

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
                    "\n\n[SAVE NOW: Output ONLY a JSON block calling create_and_save_res_strategy. "
                    "Use ALL field values from the preview tables above. "
                    "Format exactly: {\"tool\": \"create_and_save_res_strategy\", \"arguments\": {\"strategy_json\": {...all fields...}}}]"
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
                    return {"message": "⚠️ **AI service unavailable**: Insufficient credits. Please top up and try again.", "input_tokens": _in_tok, "output_tokens": _out_tok}
                return {"message": f"⚠️ **AI service error**: {msg}", "input_tokens": _in_tok, "output_tokens": _out_tok}
            except AuthenticationError:
                return {"message": "⚠️ **Authentication error**: Invalid Runware API key.", "input_tokens": _in_tok, "output_tokens": _out_tok}
            except RateLimitError:
                return {"message": "⚠️ **Rate limit reached**: Please wait a moment and try again.", "input_tokens": _in_tok, "output_tokens": _out_tok}
            except APIConnectionError:
                return {"message": "⚠️ **Connection error**: Could not reach the AI service.", "input_tokens": _in_tok, "output_tokens": _out_tok}

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
                                for key in ["create_and_save_res_strategy", "res_validate_strategy",
                                            "res_get_validation_rules", "get_my_strategies",
                                            "delete_strategy", "get_strategy_record",
                                            "modify_strategy", "rename_strategy", "get_balance",
                                            "get_deploy_options", "deploy_strategy"]:
                                    if key in data:
                                        tool_name = key
                                        val = data[key]
                                        if tool_name in ["create_and_save_res_strategy", "res_validate_strategy"]:
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
                            print(f"> [RES Turn {turn+1}] Executing tool: {tool_name}")
                            tool_result = res_handler.handle_tool_call(tool_name, args)

                            messages.append({"role": "assistant", "content": content})
                            messages.append({
                                "role": "user",
                                "content": f"SYSTEM TOOL RESULT: {json.dumps(tool_result)}"
                            })
                            tool_called = True

                            if tool_name == "create_and_save_res_strategy" and tool_result.get("status") == "success":
                                clean_summary = re.sub(r'\{.*\}', '', content, flags=re.DOTALL).strip()
                                if not clean_summary:
                                    clean_summary = content
                                strategy_name = args.get("strategy_json", {}).get("strategy_name", "Unknown")
                                api_data = tool_result.get("data", [])
                                deploy_id = api_data[0].get("id", "N/A") if isinstance(api_data, list) and api_data else "N/A"
                                deploy_msg = (
                                    f"{clean_summary}\n\n✅ **Strategy Saved Successfully!**\n\n"
                                    f"| Detail | Value |\n"
                                    f"| :--- | :--- |\n"
                                    f"| **Strategy Name** | {strategy_name} |\n"
                                    f"| **Deployment ID** | {deploy_id} |\n"
                                    f"| **Status** | Created (Not yet active) |\n\n"
                                    f"Your strategy has been saved to Market Maya. "
                                    f"You can now activate it from the Market Maya terminal."
                                )
                                return {"message": deploy_msg, "input_tokens": _in_tok, "output_tokens": _out_tok}

                            break
                    except Exception as e:
                        print(f"Error handling tool call: {e}")
                        continue

                if tool_called:
                    continue
            except Exception as e:
                print(f"Tool parsing error: {e}")

            # If confirmation but no tool call, retry once with explicit JSON format instruction
            if _is_confirm and not tool_called and not _confirm_retry_done:
                _confirm_retry_done = True
                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "user",
                    "content": (
                        "You must output the JSON tool call block now. No explanations. Just this:\n"
                        "{\"tool\": \"create_and_save_res_strategy\", \"arguments\": {\"strategy_json\": "
                        "{\"strategy_name\": \"...\", \"main_exchange\": \"...\", \"main_segment\": \"...\", "
                        "\"main_symbol\": \"...\", ... all other fields from the preview ...}}}"
                    )
                })
                continue

            ui_content = re.sub(r'\{.*\}', '', content, flags=re.DOTALL).strip()
            if not ui_content:
                ui_content = content

            return {"message": ui_content, "input_tokens": _in_tok, "output_tokens": _out_tok}

        messages.append({"role": "user", "content": "Please provide the final strategy summary and ask for save confirmation."})
        try:
            final = self.client.chat.completions.create(model=self.model, messages=messages)
            if hasattr(final, 'usage') and final.usage:
                _in_tok += final.usage.prompt_tokens
                _out_tok += final.usage.completion_tokens
            return {"message": final.choices[0].message.content, "input_tokens": _in_tok, "output_tokens": _out_tok}
        except Exception as e:
            return {"message": f"⚠️ **AI service error**: {e}", "input_tokens": _in_tok, "output_tokens": _out_tok}

    def stream_message(self, user_message, history=None):
        if history is None:
            history = []

        context = res_retriever.get_context(user_message)
        
        # Detect confirmation messages to force save tool call
        _confirm_words = {'yes', 'proceed', 'save', 'save it', 'confirm', 'go', 'ok', 'sure', 'approve', 'approved', 'continue', 'do it', 'submit'}
        _is_confirm = bool(history) and any(w in user_message.lower() for w in _confirm_words)

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
                    "\n\n[SAVE NOW: Output ONLY a JSON block calling create_and_save_res_strategy. "
                    "Use ALL field values from the preview tables above. "
                    "Format exactly: {\"tool\": \"create_and_save_res_strategy\", \"arguments\": {\"strategy_json\": {...all fields...}}}]"
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
                print(f"[RES] Stream error on turn {turn+1}: {e}")

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
                    print(f"[RES] Fallback error on turn {turn+1}: {e2}")
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
                    print("\n--- JSON STR ---\n" + json_str + "\n------\n")
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
                                for key in ["create_and_save_res_strategy", "res_validate_strategy",
                                            "res_get_validation_rules", "get_my_strategies",
                                            "delete_strategy", "get_strategy_record",
                                            "modify_strategy", "rename_strategy", "get_balance",
                                            "get_deploy_options", "deploy_strategy"]:
                                    if key in data:
                                        tool_name = key
                                        val = data[key]
                                        if tool_name in ["create_and_save_res_strategy", "res_validate_strategy"]:
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
                                "create_and_save_res_strategy": "Deploying scalping strategy to Market Maya...",
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
                            tool_result = res_handler.handle_tool_call(tool_name, args)

                            messages.append({"role": "assistant", "content": full_content})
                            messages.append({"role": "user", "content": f"SYSTEM TOOL RESULT: {json.dumps(tool_result)}"})
                            tool_called = True

                            _DIRECT_YIELD = {"get_my_strategies", "get_balance", "delete_strategy",
                                             "rename_strategy", "modify_strategy"}
                            if tool_name in _DIRECT_YIELD:
                                ok = tool_result.get("status") == "success"
                                if ok and tool_result.get("formatted_list"):
                                    yield {"t": "chunk", "v": tool_result["formatted_list"]}
                                elif ok and tool_result.get("balance") is not None:
                                    b = tool_result
                                    yield {"t": "chunk", "v": f"Balance: ₹{b['balance']} | Hold: ₹{b['hold_balance']} | Points: {b['point_balance']}"}
                                elif ok and tool_result.get("message"):
                                    yield {"t": "chunk", "v": tool_result["message"]}
                                else:
                                    yield {"t": "chunk", "v": f"⚠️ {tool_result.get('message', 'An error occurred.')}"}
                                yield {"t": "done", "in_tok": _in_tok, "out_tok": _out_tok}
                                return

                            if tool_name == "create_and_save_res_strategy" and tool_result.get("status") == "success":
                                strategy_name = args.get("strategy_json", {}).get("strategy_name", "Unknown")
                                api_data = tool_result.get("data", [])
                                deploy_id = api_data[0].get("id", "N/A") if isinstance(api_data, list) and api_data else "N/A"
                                deploy_msg = (
                                    f"\n\n✅ **Strategy Saved Successfully!**\n\n"
                                    f"| Detail | Value |\n"
                                    f"| :--- | :--- |\n"
                                    f"| **Strategy Name** | {strategy_name} |\n"
                                    f"| **Deployment ID** | {deploy_id} |\n"
                                    f"| **Status** | Created (Not yet active) |\n\n"
                                    f"Your strategy has been saved to Market Maya. "
                                    f"You can now activate it from the Market Maya terminal."
                                )
                                yield {"t": "chunk", "v": deploy_msg}
                                yield {"t": "done", "in_tok": _in_tok, "out_tok": _out_tok}
                                return
                            break
                    except Exception as e:
                        print(f"Error handling tool call: {e}")
                        continue
            except Exception as e:
                print(f"Tool parsing error: {e}")
                pass

            if not tool_called and not full_content.strip() and _is_confirm:
                yield {"t": "chunk", "v": "⚠️ I'm sorry, I encountered an error while generating the strategy payload. Please try saying 'yes' again."}

            if tool_called:
                continue

            yield {"t": "done", "in_tok": _in_tok, "out_tok": _out_tok}
            return

        yield {"t": "done", "in_tok": _in_tok, "out_tok": _out_tok}


res_orchestrator = RESOrchestrator()
