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
* atm: INTEGER COUNT OF STRIKES (not points). 0=ATM, 1=one strike OTM for CE, -1=one strike OTM for PE
* Direction: positive → OTM for CE / ITM for PE; negative → ITM for CE / OTM for PE
* CRITICAL: atm is always a small integer (typically -5 to +5). NEVER use point values like 100 or 200.
  - "ATM" or "at the money" → atm=0
  - "1 strike OTM" / "100 points OTM" / "one strike above ATM" → atm=1 (CE) or atm=-1 (PE)
  - "2 strikes OTM" / "200 points OTM" → atm=2 (CE) or atm=-2 (PE)
  - When user says "N points OTM", interpret as approximately 1 strike unless they explicitly say "N strikes"
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
* isTrailSl: true when trail SL is active for this leg
* trailMarketMove: profit in points to trigger each trail step
* trailSlMove: points the SL moves per trail step
* noOfTrailSl: max trail steps (0 = unlimited)
* All three fields required when isTrailSl is true.

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

        for turn in range(max_turns):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
            except BadRequestError as e:
                msg = str(e)
                if "credits" in msg.lower():
                    return "⚠️ **AI service unavailable**: Insufficient credits. Please top up at app.runware.ai."
                return f"⚠️ **AI service error**: {msg}"
            except AuthenticationError:
                return "⚠️ **Authentication error**: Invalid Runware API key. Check your RUNWARE_API_KEY in .env."
            except RateLimitError:
                return "⚠️ **Rate limit reached**: Too many requests. Please wait a moment and try again."
            except APIConnectionError:
                return "⚠️ **Connection error**: Could not reach the AI service. Check your internet connection."

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
                                                "isb_generate_payload"]:
                                        if key in data:
                                            tool_name = key
                                            val = data[key]
                                            if "strategy_json" in val:
                                                args = val
                                            else:
                                                args = {"strategy_json": val}
                                            break

                            if tool_name and args:
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
                                    return clean_summary + "\n\n**Strategy Deployed Successfully.**"

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

            return ui_content

        messages.append({
            "role": "user",
            "content": "Summarise the strategy and ask for deployment confirmation now."
        })
        try:
            final = self.client.chat.completions.create(model=self.model, messages=messages)
            return final.choices[0].message.content
        except Exception as e:
            return f"⚠️ **AI service error**: {e}"


isb_orchestrator = ISBOrchestrator()
