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
* Allowed: "5Min" | "10Min" | "15Min" | "30Min" | "1Hr" | "4Hr" | "1Day"
* Default: "5Min"
* If user requests any other timeframe (e.g. 1Min, 3Min, 2Min, 1Hour, 2Hour, etc.),
  reply: "⚠️ That timeframe is not available. Please choose from: 5Min, 10Min, 15Min, 30Min, 1Hr, 4Hr, 1Day."
* DO NOT substitute or guess — always reject unsupported values.

── UNDERLYING TYPE ───────────────────────────────────────
* underlyingType: "Future" (default) or "Spot/Index"
* This controls the data source for indicator calculation, NOT which instruments are traded.

── WEEK DAYS ─────────────────────────────────────────────
* weekDays: array of day codes: "MON", "TUE", "WED", "THU", "FRI", "SAT"
* Default: ["MON","TUE","WED","THU","FRI"]
* Only include SAT if user explicitly requests Saturday.

── INDICATORS — AND / OR LOGIC ───────────────────────────
* You can add UNLIMITED indicators (there is NO limit of 10 indicators; users can add as many indicators as they want).
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
  "stochastic"       → Stochastic        (params: k-length, k-smoothing, d-smoothing)
  "bollinger-bands"  → Bollinger Bands   (params: length, mult)

Candlestick Patterns (use "candlestick-" prefix — MANDATORY):
  "candlestick-hammer"                → BUY signal
  "candlestick-morning-star"          → BUY signal
  "candlestick-evening-star"          → SELL signal
  "candlestick-rising-three-methods"  → BUY signal
  "candlestick-falling-three-methods" → SELL signal
  "candlestick-three-black-crows"     → SELL signal
  "candlestick-three-white-soldiers"  → BUY signal

── INDICATOR PARAMETER DEFAULTS ──────────────────────────
If user does not specify a parameter, use the defaults:
  supertrend:      length=10, factor=3
  ma-cross-over:   short=9, long=26, type="SMA"
  rsi:             length=14, smoothing-line="SMA", smoothing-length=14, lower-band=30, upper-band=70
  macd:            fast-length=12, slow-length=26, source="Close", signal-length=9,
                   oscillator-ma-type="EMA", signal-line-ma-type="EMA"
  stochastic:      k-length=14, k-smoothing=1, d-smoothing=3
  bollinger-bands: length=20, mult=2

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

═══════════════════════════════════════════════════════════
BACKTEST TOOLS (ISE EXCLUSIVE — only available in this module)
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
   Use when user says: "show backtest result for [strategy]", "what was the backtest result of [strategy]",
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
- status == "success": display the 4 tables below
- status == "error" and insufficient_balance == True: tell user their balance (available_points) is below required_points
- status == "error" (other): show the error message clearly
- status == "processing": say "The backtest has been triggered. It usually completes within 30 seconds. Say 'show backtest result' when ready and I'll fetch it for free using get_backtest_result." Do NOT call run_backtest again.
- status == "timeout": say "The backtest is running on Market Maya's servers and will complete shortly. Use get_backtest_result in about a minute to fetch the results." Do NOT call run_backtest again.

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

DISPLAYING run_backtest RESULT:
Note: run_backtest polls the server and may take ~10–15 seconds. Show results as 4 tables:

### Backtest Summary
| Metric | Value |
|--------|-------|
| Period | <period_start> → <period_end> (<duration_days> days, <trading_days> trading days) |
| Capital | ₹<capital> |
| Total P&L | ₹<profit> |
| ROI | <roi_percent>% |
| Max Drawdown | ₹<drawdown> (<drawdown_percent>%) |
| Recovery Days | <max_drawdown_recover_days> days |

### Trade Statistics
| Metric | Value |
|--------|-------|
| Total Trades | <total> |
| Positive Trades | <positive> |
| Negative Trades | <negative> |
| SL Trades | <sl> |
| Target Trades | <target> |
| Positive Days | <positive_days> |
| Negative Days | <negative_days> |
| Max Consecutive Pos Days | <consecutive_pos_days> |
| Max Consecutive Neg Days | <consecutive_neg_days> |

### Profit / ROI Metrics
| Metric | Daily | Monthly | Yearly |
|--------|-------|---------|--------|
| Average Profit | ₹<day_avg> | ₹<month_avg> | ₹<year_avg> |
| Max Profit | ₹<day_max> | ₹<month_max> | ₹<year_max> |
| Max Loss | ₹<day_max_loss> | ₹<month_max_loss> | ₹<year_max_loss> |
| ROI | <day_roi_pct>% | <month_roi_pct>% | <year_roi_pct>% |

### Day-of-Week P&L
| Mon | Tue | Wed | Thu | Fri |
|-----|-----|-----|-----|-----|
| ₹<Mon> | ₹<Tue> | ₹<Wed> | ₹<Thu> | ₹<Fri> |

End the response with a one-line risk summary:
**Risk Profile**: <risk_profile> | **Recovery**: <recovery_ratio> | **Positive Months**: <positive_months> | **Negative Months**: <negative_months>

DISPLAYING get_backtest_result RESULT (stored result, no new run):
Show strategy name and run date as a header, then the following tables in order:

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
Build from period_analyses — show each period's profit, ROI, and drawdown:
| Period | P&L | ROI | Drawdown | Draw% |
|--------|-----|-----|----------|-------|
| All Data | ₹... | ...% | ₹... | ...% |
| 1 Year | ₹... | ...% | ₹... | ...% |
| 6 Months | ₹... | ...% | ₹... | ...% |
| 3 Months | ₹... | ...% | ₹... | ...% |
| 1 Month | ₹... | ...% | ₹... | ...% |

### Yearly P&L
Build from year_trade_history:
| Year | Trades | Positive | Negative | P&L |
|------|--------|----------|----------|-----|
| 2026 | ... | ... | ... | ₹... |

### Monthly P&L
Build from month_trade_history (oldest → newest):
| Month | Trades | Positive | Negative | P&L |
|-------|--------|----------|----------|-----|
| Dec 2025 | ... | ... | ... | ₹... |
...

### Daily P&L (Recent 20 Days)
Build from day_trade_history (most recent 20 days, newest first):
| Date | Trades | Positive | Negative | P&L |
|------|--------|----------|----------|-----|
| 2026-05-27 | ... | ... | ... | ₹... |
...
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
                                                "ise_generate_payload",
                                                "get_my_strategies",
                                                "delete_strategy",
                                                "get_strategy_record",
                                                "modify_strategy",
                                                "rename_strategy",
                                                "get_balance",
                                                "get_backtest_options",
                                                "run_backtest",
                                                "get_backtest_result"]:
                                        if key in data:
                                            tool_name = key
                                            val = data[key]
                                            if key in ("create_and_deploy_ise_strategy", "ise_validate_strategy", "ise_generate_payload"):
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


    def stream_message(self, user_message, history=None):
        """Streaming variant — yields dicts {t, v/in_tok/out_tok} for SSE."""
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
                print(f"[ISE] Stream error on turn {turn+1}: {e}")

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
                    print(f"[ISE] Fallback error on turn {turn+1}: {e2}")
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
                                for key in ["create_and_deploy_ise_strategy", "ise_validate_strategy", "ise_generate_payload", "get_my_strategies", "delete_strategy", "get_strategy_record", "modify_strategy", "rename_strategy", "get_balance", "get_backtest_options", "run_backtest", "get_backtest_result"]:
                                    if key in data:
                                        tool_name = key
                                        val = data[key]
                                        if key in ("create_and_deploy_ise_strategy", "ise_validate_strategy", "ise_generate_payload"):
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

                            _status_msgs = {
                                "create_and_deploy_ise_strategy": "Deploying strategy to Market Maya...",
                                "get_my_strategies": "Fetching your strategies...",
                                "delete_strategy": "Deleting strategy...",
                                "get_strategy_record": "Fetching strategy record...",
                                "modify_strategy": "Saving changes...",
                                "rename_strategy": "Renaming strategy...",
                                "get_balance": "Fetching balance...",
                                "get_backtest_options": "Fetching backtest options...",
                                "run_backtest": "Running backtest (this may take 10–30 seconds)...",
                                "get_backtest_result": "Fetching backtest results...",
                            }
                            yield {"t": "status", "v": _status_msgs.get(tool_name, "Processing...")}
                            tool_result = ise_handler.handle_tool_call(tool_name, args)

                            messages.append({"role": "assistant", "content": full_content})
                            messages.append({"role": "user", "content": f"SYSTEM TOOL RESULT: {json.dumps(tool_result)}"})
                            tool_called = True

                            if tool_name == "create_and_deploy_ise_strategy" and tool_result.get("status") == "success":
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


# Singleton instance
ise_orchestrator = ISEOrchestrator()
