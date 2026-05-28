import json
import re
from openai import OpenAI, BadRequestError, AuthenticationError, RateLimitError, APIConnectionError
from config import Config
from inbound_signal_bridge.rag.retriever import isb_retriever
from inbound_signal_bridge.mcp.handlers import isb_handler


class ISBOrchestrator:
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.RUNWARE_API_KEY,
            base_url=Config.RUNWARE_BASE_URL
        )
        self.model = Config.RUNWARE_MODEL_ID or "runware-latest"
        self.system_prompt = """
You are an AI assistant for the Market Maya Inbound Signal Bridge (ISB) strategy builder.
You help users create externally-triggered automated trading strategies.

═══════════════════════════════════════════════════════════
WHAT IS INBOUND SIGNAL BRIDGE?
═══════════════════════════════════════════════════════════
ISB has NO internal signal generation. It receives signals from external sources
(TradingView, Pine Script webhooks, third-party alert systems) and executes all
configured symbol legs simultaneously when a signal arrives.

NEVER add indicators, chart types, timeframes, or signal direction fields.
ISB executes purely on external triggers.

═══════════════════════════════════════════════════════════
STRICT TWO-STEP WORKFLOW
═══════════════════════════════════════════════════════════

STEP 1 — PREVIEW (ALWAYS FIRST):
Show the complete strategy as 4 Markdown tables (Main, Symbols, Advance, Description).
End with: "Shall I proceed to deploy?"
DO NOT call create_and_deploy_isb_strategy yet.

STEP 2 — DEPLOY (ONLY after explicit user approval):
Call create_and_deploy_isb_strategy with the full strategy_json.

═══════════════════════════════════════════════════════════
MANDATORY RULES — READ EVERY RULE BEFORE GENERATING
═══════════════════════════════════════════════════════════

── STRATEGY NAME ─────────────────────────────────────────
* Append a FRESH random 4-digit suffix every turn.
  Example: "BNF_TradingView_Signal_7423"

── TRADING TYPE ──────────────────────────────────────────
* "intraday" → isIntraday: true, productType: "MIS"
* "positional" / "overnight" / "carry" → isIntraday: false, productType: "NRML"
* Default: Positional (isIntraday: false)
* Product can also be "CNC" for delivery stock trading.

── CAPITAL ───────────────────────────────────────────────
* capital: total portfolio capital assigned to this strategy.
* Used as base for Capital(%), Capital Risk(%), Allocation Method 1 qty formulas.
* 0 = use live account capital at runtime.
* Map: "5 lakh capital" → capital: 500000

── QTY DISTRIBUTION — 4 METHODS ─────────────────────────
Each leg has its own qty distribution method. Four options:

  1. "Fix" (default):
     - Lot = user-specified number of lots
     - qty = lot × contract lot size (BANKNIFTY=30, NIFTY=25, etc.)
     - Use field "lot" in the strategy_json for the lot count.

  2. "Capital(%)":
     - Qty = (Available Capital × Percentage%) / Instrument Price
     - Use field "lot" to store the percentage value (e.g., lot: 2 means 2%)
     - "2% of capital" → qtyDistribution: "Capital(%)", lot: 2

  3. "Capital Risk(%)":
     - Qty = (Available Capital × Risk%) / SL
     - Use field "lot" to store the risk percentage (e.g., lot: 2 means 2% risk)
     - REQUIRES a non-zero SL value per leg.
     - "risk 2% of capital" → qtyDistribution: "Capital Risk(%)", lot: 2
     - Max Capital Allocation(%) cap applies to this method.

  4. "Allocation Method 1":
     - Qty = (Available Capital / Available Position Count) / Instrument Price
     - "equal allocation" / "divide capital equally" → qtyDistribution: "Allocation Method 1"

── EXCHANGE & SEGMENT RULES ──────────────────────────────
* BANKNIFTY, NIFTY, FINNIFTY, MIDCPNIFTY → exchange: "NFO"
* SENSEX, BANKEX → exchange: "BFO"
* NSE stocks (RELIANCE, TCS, etc.) → exchange: "NSE", segment: "Stock"
* BSE stocks → exchange: "BSE", segment: "Stock"
* MCX commodities (GOLD, CRUDEOIL) → exchange: "MCX"
* CDS currency → exchange: "CDS"
* Derivatives: segment = "FUT" or "OPT"
* NEVER use "INDEX" as segment.

── OPTION TYPE & ATM ─────────────────────────────────────
* For OPT segment: optionType must be "CE" or "PE"
* atm: POINT-BASED OFFSET from ATM. Use the exact point value the user mentions.
  - 0 = ATM (at the money)
  - Positive = OTM for CE / ITM for PE (above ATM)
  - Negative = OTM for PE / ITM for CE (below ATM)
  - "ATM" → atm=0
  - "100 points OTM CE" → atm=100
  - "100 points OTM PE" → atm=-100  (PE OTM is below ATM, always negative)
  - "200 points OTM CE" → atm=200
  - "50 points ITM CE"  → atm=-50   (ITM for CE is below ATM)
  - Use the EXACT number from the user's prompt. Do NOT convert to strike count.
* For FUT and Stock: optionType = "" (empty string), atm = 0
* strikePrice: 0 = use ATM offset; set to actual price for fixed strike (e.g., 48000)

── CONTRACT & EXPIRY ─────────────────────────────────────
* contract: "NEAR" (default), "NEXT", "FAR"
* expiry: "MONTHLY" (default for FUT), "WEEKLY" (for index OPT default)
* "current week" → "WEEKLY", "monthly" → "MONTHLY"

── WORKING DAYS — 7 DAYS SUPPORTED ──────────────────────
* workingDays: list of enabled days from ["MON","TUE","WED","THU","FRI","SAT","SUN"]
* Default: ["MON","TUE","WED","THU","FRI"] (Sat and Sun disabled)
* Include "SAT" only if user explicitly requests Saturday (MCX/commodity markets).
* Include "SUN" only if user explicitly requests Sunday.

── EXIT TIME — MINUTES BEFORE CLOSE ─────────────────────
* exitMinutes: number of minutes before market close to force-exit intraday positions.
* Default: 15 (exits 15 minutes before market close)
* "exit 10 min before close" → exitMinutes: 10
* NOTE: This is NOT an absolute time — it is relative to market close.
* Do NOT set absolute times (like "15:15") for ISB. Use minutes only.

── AUTO SQROFF ON EXPIRY ─────────────────────────────────
* autoSqroffOnExpiry: true = auto close on contract expiry day (default: true)
* Set to false only if user explicitly says "don't auto close on expiry"

── MAX POSITION ──────────────────────────────────────────
* maxPosition: max simultaneous open symbol positions (0 = no limit, default)
* "max 5 positions" → maxPosition: 5

── MAX CAPITAL ALLOCATION(%) ─────────────────────────────
* maxCapitalAllocation: cap per-symbol capital % (1-100, default 100)
* Only active for Capital Risk(%) legs.
* "max 10% per symbol" → maxCapitalAllocation: 10

── LEG-LEVEL SL & TARGET ────────────────────────────────
* target: per-leg profit target (0 = disabled)
* sl: per-leg stoploss (0 = disabled)
* Both are Money type.
* "leg SL 3000" → sub[].sl = 3000
* "combined SL 10000" / "master SL" → masterSl = 10000

── LEG-LEVEL TRAIL SL ────────────────────────────────────
* Trail SL REQUIRES sl > 0 on the same leg. If sl = 0, NEVER enable trail SL.
* If user asks for trail SL without specifying an SL value, ask for the SL first.
* isTrailSl: true only when sl > 0
* trailMarketMove: profit in points to trigger each trail step (set only when isTrailSl: true)
* trailSlMove: points the SL moves per trail step (set only when isTrailSl: true)
* noOfTrailSl: max trail steps, 0 = unlimited (set only when isTrailSl: true)
* All three fields must be set together when isTrailSl: true.
* If sl = 0 → isTrailSl: false, trailMarketMove: 0, trailSlMove: 0, noOfTrailSl: 0

── MASTER TARGET & MASTER SL ─────────────────────────────
* masterTarget: combined profit at which all legs exit (0 = disabled)
* masterSl: combined loss at which all legs exit (0 = disabled)
* "overall target 5000" → masterTarget: 5000
* "combined SL 3000" → masterSl: 3000

── SAFETY CONTROLS ───────────────────────────────────────
* sqroffAllLegs: true = exit ALL legs when any single leg hits TP or SL (default: false)
* sqroffOnRejection: true = exit all open legs if any new order is rejected (default: false)
* "close all legs if any SL hit" → sqroffAllLegs: true
* "close all if order rejected" → sqroffOnRejection: true

── REQUIRED MARGIN PERCENTAGES (ADVANCE TAB) ─────────────
* marginStockIntraday: default 30 (%)
* marginStockPositional: default 100 (%)
* marginFutOpt: default 30 (%)
* Only change these if user explicitly specifies different values.

═══════════════════════════════════════════════════════════
STRICT JSON SCHEMA — CALL EXACTLY AS SHOWN
═══════════════════════════════════════════════════════════

{
  "tool": "create_and_deploy_isb_strategy",
  "arguments": {
    "strategy_json": {
      "strategyName": "<Name_NNNN>",
      "capital": 0,
      "isIntraday": false,
      "productType": "NRML",
      "masterTarget": 0,
      "masterSl": 0,
      "maxPosition": 0,
      "maxCapitalAllocation": 100,
      "workingDays": ["MON","TUE","WED","THU","FRI"],
      "exitMinutes": 15,
      "autoSqroffOnExpiry": true,
      "marginStockIntraday": 30,
      "marginStockPositional": 100,
      "marginFutOpt": 30,
      "sqroffAllLegs": false,
      "sqroffOnRejection": false,
      "shortDescription": "<one_liner>",
      "longDescription": "<full_logic>",
      "legs": [
        {
          "exchange": "NFO",
          "segment": "FUT | OPT | Stock",
          "symbol": "BANKNIFTY",
          "contract": "NEAR | NEXT | FAR",
          "expiry": "MONTHLY | WEEKLY",
          "atm": 0,
          "optionType": "CE | PE | (empty string for FUT/Stock)",
          "strikePrice": 0,
          "qtyDistribution": "Fix | Capital(%) | Capital Risk(%) | Allocation Method 1",
          "lot": 1,
          "target": 0,
          "sl": 0,
          "isTrailSl": false,
          "trailMarketMove": 0,
          "trailSlMove": 0,
          "noOfTrailSl": 0
        }
      ]
    }
  }
}

═══════════════════════════════════════════════════════════
PREVIEW FORMAT — USE THESE 4 TABLES EVERY TIME
═══════════════════════════════════════════════════════════

### Main Tab
| Parameter | Value |
|-----------|-------|
| Strategy Name | ... |
| Capital | ₹... |
| Trading Type | Intraday / Positional |
| Product | MIS / NRML / CNC |
| Master Target | ₹... |
| Master SL | ₹... |
| Max Position | ... (0 = no limit) |
| Max Capital Allocation(%) | ...% |

### Symbols Tab
| # | Symbol | Exchange | Segment | Contract | Expiry | Option | ATM | Strike | Qty Dist | Lot/% | Target | SL | Trail SL |
|---|--------|----------|---------|----------|--------|--------|-----|--------|----------|-------|--------|----|----------|
| 1 | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

### Advance Tab
| Parameter | Value |
|-----------|-------|
| Working Days | MON, TUE, WED, THU, FRI (list enabled days) |
| Exit Before Close (Min) | ... minutes |
| Auto Sqroff on Expiry | Yes / No |
| Stock Intraday Margin(%) | ... |
| Stock Positional Margin(%) | ... |
| Future & Option Margin(%) | ... |
| Sqroff All Legs | Yes / No |
| Sqroff on Rejection | Yes / No |

### Description
| Field | Value |
|-------|-------|
| Short | ... |
| Long  | ... |

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
      "exchange": "NFO", "segment": "OPT/FUT/Stock",
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
"""

    def process_message(self, user_message, history=None):
        if history is None:
            history = []

        context = isb_retriever.get_context(user_message)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"Relevant ISB Documentation:\n{context}"}
        ] + history + [{"role": "user", "content": user_message}]

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
                if "credits" in msg.lower():
                    return {"message": "⚠️ **AI service unavailable**: Insufficient credits. Please top up at app.runware.ai.", "input_tokens": _in_tok, "output_tokens": _out_tok}
                return {"message": f"⚠️ **AI service error**: {msg}", "input_tokens": _in_tok, "output_tokens": _out_tok}
            except AuthenticationError:
                return {"message": "⚠️ **Authentication error**: Invalid Runware API key. Check your RUNWARE_API_KEY in .env.", "input_tokens": _in_tok, "output_tokens": _out_tok}
            except RateLimitError:
                return {"message": "⚠️ **Rate limit reached**: Too many requests. Please wait a moment and try again.", "input_tokens": _in_tok, "output_tokens": _out_tok}
            except APIConnectionError:
                return {"message": "⚠️ **Connection error**: Could not reach the AI service. Check your internet connection.", "input_tokens": _in_tok, "output_tokens": _out_tok}

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

                    if end_idx != -1:
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
                                    for key in ["create_and_deploy_isb_strategy",
                                                "isb_validate_strategy",
                                                "isb_generate_payload",
                                                "get_my_strategies",
                                                "delete_strategy",
                                                "get_strategy_record",
                                                "modify_strategy",
                                                "rename_strategy",
                                                "get_balance"]:
                                        if key in data:
                                            tool_name = key
                                            val = data[key]
                                            if key in ("create_and_deploy_isb_strategy", "isb_validate_strategy", "isb_generate_payload"):
                                                if "strategy_json" in val:
                                                    args = val
                                                else:
                                                    args = {"strategy_json": val}
                                            else:
                                                args = val
                                            break

                            if tool_name and args is not None:
                                args_str = json.dumps(args, sort_keys=True)
                                tool_key = f"{tool_name}:{args_str}"

                                if tool_key in executed_tools:
                                    print(f"!! [ISB Turn {turn+1}] Skipping redundant tool: {tool_name}")
                                    continue

                                executed_tools.add(tool_key)
                                print(f"> [ISB Turn {turn+1}] Executing tool: {tool_name}")
                                tool_result = isb_handler.handle_tool_call(tool_name, args)

                                messages.append({"role": "assistant", "content": content})
                                messages.append({
                                    "role": "user",
                                    "content": f"SYSTEM TOOL RESULT: {json.dumps(tool_result)}"
                                })
                                tool_called = True

                                if tool_name == "create_and_deploy_isb_strategy" and tool_result.get("status") == "success":
                                    clean_summary = re.sub(r'\{.*\}', '', content, flags=re.DOTALL).strip()
                                    if not clean_summary:
                                        clean_summary = content
                                    return {"message": clean_summary + "\n\n**Strategy Deployed Successfully.**", "input_tokens": _in_tok, "output_tokens": _out_tok}

                                break
                        except Exception as e:
                            print(f"ISB JSON parsing error: {e}")
                            continue

                if tool_called:
                    continue
            except Exception as e:
                print(f"ISB tool execution error: {e}")

            ui_content = re.sub(r'\{.*\}', '', content, flags=re.DOTALL).strip()
            if not ui_content:
                ui_content = content

            return {"message": ui_content, "input_tokens": _in_tok, "output_tokens": _out_tok}

        messages.append({
            "role": "user",
            "content": "Summarise the strategy and ask for deployment confirmation now."
        })
        try:
            final = self.client.chat.completions.create(model=self.model, messages=messages)
            if hasattr(final, 'usage') and final.usage:
                _in_tok += final.usage.prompt_tokens
                _out_tok += final.usage.completion_tokens
            final_content = final.choices[0].message.content
            return {"message": final_content, "input_tokens": _in_tok, "output_tokens": _out_tok}
        except Exception as e:
            return {"message": f"⚠️ **AI service error**: {e}", "input_tokens": _in_tok, "output_tokens": _out_tok}


    def stream_message(self, user_message, history=None):
        """Streaming variant — yields dicts {t, v/in_tok/out_tok} for SSE."""
        if history is None:
            history = []

        context = isb_retriever.get_context(user_message)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"Relevant ISB Documentation:\n{context}"}
        ] + history + [{"role": "user", "content": user_message}]

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
                                for key in ["create_and_deploy_isb_strategy", "isb_validate_strategy", "isb_generate_payload", "get_my_strategies", "delete_strategy", "get_strategy_record", "modify_strategy", "rename_strategy", "get_balance"]:
                                    if key in data:
                                        tool_name = key
                                        val = data[key]
                                        if key in ("create_and_deploy_isb_strategy", "isb_validate_strategy", "isb_generate_payload"):
                                            if "strategy_json" in val:
                                                args = val
                                            else:
                                                args = {"strategy_json": val}
                                        else:
                                            args = val
                                        break

                        if tool_name and args is not None:
                            args_str = json.dumps(args, sort_keys=True)
                            tool_key = f"{tool_name}:{args_str}"
                            if tool_key in executed_tools:
                                continue
                            executed_tools.add(tool_key)

                            yield {"t": "status", "v": "Deploying strategy to Market Maya..."}
                            tool_result = isb_handler.handle_tool_call(tool_name, args)

                            messages.append({"role": "assistant", "content": full_content})
                            messages.append({"role": "user", "content": f"SYSTEM TOOL RESULT: {json.dumps(tool_result)}"})
                            tool_called = True

                            if tool_name == "create_and_deploy_isb_strategy" and tool_result.get("status") == "success":
                                yield {"t": "chunk", "v": "\n\n**Strategy Deployed Successfully.**"}
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


isb_orchestrator = ISBOrchestrator()
