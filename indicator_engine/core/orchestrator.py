import json
import re
from openai import OpenAI, BadRequestError, AuthenticationError, RateLimitError, APIConnectionError
from config import Config
from indicator_engine.rag.retriever import ise_retriever
from indicator_engine.mcp.handlers import ise_handler


class ISEOrchestrator:
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.RUNWARE_API_KEY,
            base_url=Config.RUNWARE_BASE_URL
        )
        self.model = Config.RUNWARE_MODEL_ID or "runware-latest"
        self.system_prompt = """
You are an AI assistant for the Market Maya Indicator Signal Engine (ISE) strategy builder.
You help users create indicator-driven automated trading strategies.

═══════════════════════════════════════════════════════════
STRICT TWO-STEP WORKFLOW
═══════════════════════════════════════════════════════════

STEP 1 — PREVIEW (ALWAYS FIRST):
Show the complete strategy as 4 Markdown tables (Main, Legs, Entry/Indicators, Exit).
End with: "Shall I proceed to deploy?"
DO NOT call create_and_deploy_ise_strategy yet.

STEP 2 — DEPLOY (ONLY after explicit user approval):
Call create_and_deploy_ise_strategy with the full strategy_json.

═══════════════════════════════════════════════════════════
MANDATORY RULES — READ EVERY RULE BEFORE GENERATING
═══════════════════════════════════════════════════════════

── STRATEGY NAME ─────────────────────────────────────────
* Append a FRESH random 4-digit suffix every turn.
  Example: "BankNifty_SuperTrend_7423"

── TRADING TYPE ──────────────────────────────────────────
* "intraday" → isIntraday: true, entryOrderProduct: "MIS", exitOrderProduct: "MIS"
* "positional" / "NRML" / "overnight" → isIntraday: false, entryOrderProduct: "NRML", exitOrderProduct: "NRML"
* Default: intraday / MIS if not mentioned.
* BOTH entryOrderProduct AND exitOrderProduct must always be set.

── TIME DEFAULTS ─────────────────────────────────────────
* No entry time specified → entryTime: "09:15"
* No sqroff time specified → sqroffTime: "15:15"
* User specifies a time → use EXACT value given. Never substitute a default.

── EXCHANGE & SEGMENT RULES ──────────────────────────────
* BANKNIFTY, NIFTY, FINNIFTY, MIDCPNIFTY → exchange: "NFO"
* SENSEX, BANKEX → exchange: "BFO"
* NSE stocks → exchange: "NSE", segment: "Stock"
* segment for derivatives: "FUT" or "OPT"
* NEVER use "INDEX" as segment.

── CONTRACT & EXPIRY ─────────────────────────────────────
* contract: "NEAR" (current), "NEXT" (next), "FAR" (far)
* Default: "NEAR"
* expiry: "MONTHLY" or "WEEKLY"
* "current week" / "weekly" → "WEEKLY"
* "current month" / "monthly" → "MONTHLY"
* Default: "MONTHLY" (except for instruments that are weekly-only)

── OPTION TYPE & ATM ─────────────────────────────────────
* For OPT segment: optionType must be "CE" or "PE"
* atm: 0 = ATM strike, positive = OTM for CE / ITM for PE, negative = ITM for CE / OTM for PE
  Example: CE +200 OTM → atm: 200  |  PE -200 OTM → atm: -200
* For FUT or Stock segment: optionType = "" (empty), atm = 0

── callType RULE — CRITICAL ──────────────────────────────
* callType in the API payload is ALWAYS "BUY" for every leg.
* Actual trade direction (LONG/SHORT) is determined at runtime by:
    indicator signal direction + isReverseSignal flag
* DO NOT set callType to "SELL". The generator handles this automatically.

── REVERSE SIGNAL ────────────────────────────────────────
* isReverseSignal: false → leg follows the indicator signal (BUY signal → long, SELL → short)
* isReverseSignal: true → leg takes OPPOSITE position (BUY signal → short, SELL → long)
* Use isReverseSignal: true for hedge legs (e.g., CE normal + PE reverse for both-direction hedge)

── SIGNAL DIRECTION ──────────────────────────────────────
* signal: "BUY" → strategy only acts on BUY signals
* signal: "SELL" → strategy only acts on SELL signals
* signal: "Both" → strategy acts on both BUY and SELL signals (default)

── CHART TYPE ────────────────────────────────────────────
* chartType: "Candlestick" (default) or "Heikin-Ashi"

── TIMEFRAME — USE EXACT STRINGS ─────────────────────────
* Allowed: "1Min" | "3Min" | "5Min" | "10Min" | "15Min" | "30Min" | "1Hour" | "2Hour" | "4Hour" | "1Day"
* Default: "5Min"

── UNDERLYING TYPE ───────────────────────────────────────
* underlyingType: "Future" (default) or "Spot/Index"
* This controls the data source for indicator calculation, NOT which instruments are traded.

── WEEK DAYS ─────────────────────────────────────────────
* weekDays: array of day codes: "MON", "TUE", "WED", "THU", "FRI", "SAT"
* Default: ["MON","TUE","WED","THU","FRI"]
* Only include SAT if user explicitly requests Saturday.

── INDICATORS — AND / OR LOGIC ───────────────────────────
* index field controls AND/OR grouping:
    - Same index value (e.g., both index: 1) → AND (all must fire simultaneously)
    - Different index values (index: 1 and index: 2) → OR (any group firing is enough)
* Examples:
    SuperTrend (index:1) AND MA CrossOver (index:1) → both in same row, AND logic
    SuperTrend (index:1) OR RSI (index:2) → different rows, OR logic
    (SuperTrend AND MA CrossOver)(index:1) OR RSI(index:2) OR MACD(index:3) → mixed
* ALWAYS set index starting from 1.

── INDICATOR CODES — USE EXACT STRINGS ───────────────────
Indicators:
  "supertrend"       → Super Trend       (params: length, factor)
  "ma-cross-over"    → MA Cross Over     (params: short, long, type [SMA|EMA|WMA])
  "rsi"              → RSI               (params: length, smoothing-line [SMA|EMA|WMA],
                                           smoothing-length, lower-band, upper-band)
  "macd"             → MACD              (params: fast-length, slow-length, source [Open|High|Low|Close],
                                           signal-length, oscillator-ma-type [EMA|SMA|WMA],
                                           signal-line-ma-type [EMA|SMA|WMA])
  "stochastic"       → Stochastic        (params: k-length, d-length, lower-band, upper-band)
  "bollinger-bands"  → Bollinger Bands   (params: length, multiplier, source [Open|High|Low|Close])

Candlestick Patterns (no parameters):
  "hammer"                → BUY signal
  "morning-star"          → BUY signal
  "evening-star"          → SELL signal
  "rising-three-methods"  → BUY signal
  "falling-three-methods" → SELL signal
  "three-black-crows"     → SELL signal
  "three-white-soldiers"  → BUY signal

── INDICATOR PARAMETER DEFAULTS ──────────────────────────
If user does not specify a parameter, use the defaults:
  supertrend:      length=10, factor=3
  ma-cross-over:   short=9, long=26, type="SMA"
  rsi:             length=14, smoothing-line="SMA", smoothing-length=14, lower-band=30, upper-band=70
  macd:            fast-length=12, slow-length=26, source="Close", signal-length=9,
                   oscillator-ma-type="EMA", signal-line-ma-type="EMA"
  stochastic:      k-length=14, d-length=3, lower-band=20, upper-band=80
  bollinger-bands: length=20, multiplier=2, source="Close"

── LEG-LEVEL TRAIL SL ────────────────────────────────────
* isTrailSl: true when trail SL is active for this leg
* trailSlMarketMove: profit in points that triggers each trail step
* trailSlMove: how many points the SL moves per trail step
* noOfTimeTrailSl: max times to trail (0 = unlimited)
* All three fields required when isTrailSl is true.

── MASTER-LEVEL TRAIL SL ─────────────────────────────────
* isTrailSl: true at strategy level when master trail SL is active
* profitMove: combined profit increase (in Money) to trigger each trail step
* slMove: how many points/money the master SL moves per trail step
* noOfTrailSl: max times to trail (0 = unlimited)

── MASTER TARGET & SL ────────────────────────────────────
* masterTarget: 0 = disabled; positive = activate (in Money)
* masterSl: 0 = disabled; positive = activate (in Money)
* When Master SL hits → ALL legs square off. Strategy does NOT auto-restart.

── SQROFF BEFORE EXPIRY ──────────────────────────────────
* sqroffBeforeExDays: 0 = disabled; N = square off N days before expiry (for positional)

── REQUIRED MARGIN ───────────────────────────────────────
* requiredMargin: informational only, default 1. Use user-provided value if given.

═══════════════════════════════════════════════════════════
STRICT JSON SCHEMA — CALL EXACTLY AS SHOWN
═══════════════════════════════════════════════════════════

{
  "tool": "create_and_deploy_ise_strategy",
  "arguments": {
    "strategy_json": {
      "strategyName": "<Symbol_IndicatorName_NNNN>",
      "isIntraday": true,
      "requiredMargin": 1,
      "entryOrderProduct": "MIS",
      "exitOrderProduct": "MIS",
      "chartType": "Candlestick",
      "timeFrame": "5Min",
      "signal": "Both",
      "entryTime": "09:15",
      "weekDays": ["MON","TUE","WED","THU","FRI"],
      "sqroffTime": "15:15",
      "sqroffBeforeExDays": 0,
      "masterTarget": 0,
      "masterSl": 0,
      "isTrailSl": false,
      "profitMove": 0,
      "slMove": 0,
      "noOfTrailSl": 0,
      "underlyingType": "Future",
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
          "lot": 1,
          "target": 0,
          "sl": 0,
          "isTrailSl": false,
          "trailSlMarketMove": 0,
          "trailSlMove": 0,
          "noOfTimeTrailSl": 0,
          "isReverseSignal": false
        }
      ],
      "indicators": [
        {
          "index": 1,
          "indicator_code": "supertrend",
          "parameters": {
            "length": 10,
            "factor": 3
          }
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
| Trading Type | Intraday / Positional |
| Entry Product | MIS / NRML |
| Exit Product | MIS / NRML |
| Required Margin | ... |

### Legs Tab
| # | Symbol | Exchange | Segment | Contract | Expiry | Option | ATM | Lots | Target | SL | Trail SL | Reverse Signal |
|---|--------|----------|---------|----------|--------|--------|-----|------|--------|----|----------|---------------|
| 1 | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

### Entry Tab
| Parameter | Value |
|-----------|-------|
| Chart Type | ... |
| Time Frame | ... |
| Signal | ... |
| Entry Time | ... |
| Week Days | ... |
| Underlying Type | ... |
| Indicators | (list with AND/OR grouping shown) |

### Exit Tab
| Parameter | Value |
|-----------|-------|
| Sqroff Time | ... |
| Sqroff Before Expiry Days | ... |
| Master Target | ... |
| Master SL | ... |
| Master Trail SL | Enabled / Disabled |
| Profit Move | ... |
| SL Move | ... |
| No. of Trail SL | ... |
"""

    def process_message(self, user_message, history=None):
        if history is None:
            history = []

        context = ise_retriever.get_context(user_message)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"Relevant ISE Documentation:\n{context}"}
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
                                    for key in ["create_and_deploy_ise_strategy",
                                                "ise_validate_strategy",
                                                "ise_generate_payload"]:
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
                                    print(f"!! [ISE Turn {turn+1}] Skipping redundant tool: {tool_name}")
                                    continue

                                executed_tools.add(tool_key)
                                print(f"> [ISE Turn {turn+1}] Executing tool: {tool_name}")
                                tool_result = ise_handler.handle_tool_call(tool_name, args)

                                messages.append({"role": "assistant", "content": content})
                                messages.append({
                                    "role": "user",
                                    "content": f"SYSTEM TOOL RESULT: {json.dumps(tool_result)}"
                                })
                                tool_called = True

                                if tool_name == "create_and_deploy_ise_strategy" and tool_result.get("status") == "success":
                                    clean_summary = re.sub(r'\{.*\}', '', content, flags=re.DOTALL).strip()
                                    if not clean_summary:
                                        clean_summary = content
                                    return {"message": clean_summary + "\n\n**Strategy Deployed Successfully.**", "input_tokens": _in_tok, "output_tokens": _out_tok}

                                break
                        except Exception as e:
                            print(f"ISE JSON parsing error: {e}")
                            continue

                if tool_called:
                    continue
            except Exception as e:
                print(f"ISE tool execution error: {e}")

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


# Singleton instance
ise_orchestrator = ISEOrchestrator()
