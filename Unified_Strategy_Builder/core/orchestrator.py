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
      * User says "OTM" / "out-of-the-money" → `"direction": "OTM"`
      * User says "ITM" / "in-the-money" → `"direction": "ITM"`
      * ATM strikes or unspecified → `"direction": "BOTH"`
      * This field MUST always be set explicitly. Never omit it.
   - **STRIKE CONDITION — MANDATORY** (for Nearest Premium / Delta / Theta only):
      * "above-equal" / "above equal" / ">=" → `"condition": "AboveEqual"`
      * "below-equal" / "below equal" / "<=" → `"condition": "BelowEqual"`
      * Not specified → `"condition": "Any"`
      * This field MUST always be set explicitly. Never omit it.
   - **TARGET BY / SL BY — MANDATORY**: Use EXACT strings for all types:
      * Money: `"Target by Money"` / `"SL by Money"`
      * Point: `"Target by Point"` / `"SL by Point"`
      * Point%: `"Target by Point (%)"` / `"SL by Point (%)"`
      * Delta: `"Target by Delta"` / `"SL by Delta"`
      * Delta%: `"Target by Delta (%)"` / `"SL by Delta (%)"`
      * Theta: `"Target by Theta"` / `"SL by Theta"`
      * Theta%: `"Target by Theta (%)"` / `"SL by Theta (%)"`
      * Range: `"Target by Range High/Low"` / `"SL by Range High/Low"`
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
   - **ACTION ON TARGET / SL — MANDATORY**: When user says "on target execute/reenter/sqroff leg N after X sec":
      * `"action_on_target"`: `"Execute Leg"` / `"Reenter Leg"` / `"Sqroff Leg"`
      * `"target_action_leg_no"`: the leg number (integer, 1-indexed)
      * `"target_action_delay"`: delay in seconds (integer)
      * All three fields MUST be set together. NEVER leave leg_no = 0 when a leg is referenced.
      * Same applies to `action_on_sl`, `sl_action_leg_no`, `sl_action_delay`.
      * **API CONSTRAINT — CRITICAL**: Only Leg 1 may use `"Execute Leg"` or `"Reenter Leg"` as action_on_target pointing to an idle leg. Legs 2, 3, 4+ can ONLY use `"Sqroff Leg"` as action on target or SL. NEVER assign `"Execute Leg"` or `"Reenter Leg"` action_on_target to any leg other than Leg 1.
      * `"Execute Leg"` and `"Reenter Leg"` MUST reference an IDLE leg (isIdle=true). Never reference an active leg.
      * `"optionType"` for a FUT segment leg MUST be `"CE"` or `"PE"` (default to `"CE"`). NEVER set it to `"NONE"`, `"NULL"`, or leave it empty.
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
   - **EXCHANGE RULES — MANDATORY**:
      * BANKNIFTY, NIFTY, FINNIFTY → exchange MUST be `"NFO"`, segment MUST be `"FUT"` (never BFO, never NSE, never INDEX)
      * SENSEX, BANKEX → exchange MUST be `"BFO"`, segment MUST be `"FUT"` (never INDEX — Market Maya rejects INDEX)
      * NSE stocks → exchange `"NSE"`, segment `"Stock"`
      * CRITICAL: The main strategy `segment` field MUST always be `"FUT"` for all index derivatives (NIFTY/BANKNIFTY/SENSEX/BANKEX/FINNIFTY). NEVER use `"INDEX"` — Market Maya API rejects it.
   - **PE LEG ATM OFFSETS — MANDATORY**: For PUT options, OTM is BELOW the ATM. ATM offset for a PE leg that is N points OTM MUST be negative (e.g., "PE ATM-300" → `"strike": -300`). NEVER send a positive ATM offset for a PE OTM leg.
   - **STRICT LEG ORDERING**: Output legs in the EXACT order the user listed them. Do NOT reorder or rearrange legs. Leg 1 is the first leg the user mentioned, Leg 2 is second, etc.
   - **STRICT RULE: NO DUPLICATE LEGS.** Give unique strike/wait offsets if legs share side+strike.
   - **MASTER SL TRAILING IS INDEPENDENT**: `master_sl_trailing` must ALWAYS be included when the user asks for master SL trailing, regardless of what other features (range breakout, combined premium, VIX, etc.) are also enabled. These are independent features — do NOT omit master_sl_trailing just because other advance features are set.
   - **RANGE BREAKOUT DIRECTION — MANDATORY**: When user enables range breakout and specifies a direction for a leg:
      * "execute on range high break" / "above range" / "breakout above" → `"execute_on_range_breakout": "Range High Break"`
      * "execute on range low break" / "below range" / "breakout below" → `"execute_on_range_breakout": "Range Low Break"`
      * Default when direction not stated → `"Range High Break"`
      * Both `"is_execute_on_range_breakout": true` and `"execute_on_range_breakout"` MUST be set together on the leg.
   - **WORKING DAYS — MANDATORY**: Valid days are Mon, Tue, Wed, Thu, Fri, Sat. Saturday is a valid trading day for some exchanges. Include "Sat" in `trading_days` only when user explicitly requests Saturday.
      * **CRITICAL**: OMIT the `"trading_days"` field entirely when the user does NOT explicitly mention specific trading days. NEVER generate `"trading_days": ["Mon","Tue","Wed","Thu","Fri"]` as a default — omitting it is correct and means "trade every day". Only include it when the user says "only on Monday and Wednesday" or similar explicit day restrictions.
   - **MASTER TARGET / SL ACTION — MANDATORY**: The `action_on_master_target` and `action_on_master_sl` fields always use `"Reexecute"` (only allowed value). When user specifies reexecution on master target/SL, set both the count and delay fields along with the action field.
   - **BOOLEAN FLAGS ARE INDEPENDENT**: `sqroff_all_legs`, `sqroff_on_rejection`, `enable_tp_sl_on_pause` are each independent boolean flags. When the user explicitly enables any of these, you MUST set it to `true` in the JSON. NEVER drop a boolean flag just because the prompt is complex or many other fields are also being set.
   - DO NOT call `create_and_deploy_strategy` yet. Ask: "Shall I proceed?"

2. EXECUTION: ONLY after user approval, call `create_and_deploy_strategy`.

STRICT JSON SCHEMA:
{
  "tool": "create_and_deploy_strategy",
  "arguments": {
    "strategy_json": {
        "strategyName": "<string>",
        "underlying": "NIFTY/BANKNIFTY/SENSEX/etc",
        "exchange": "NFO / NSE / BFO / BSE / MCX / CDS",
        "segment": "FUT / Stock",
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
                "segment": "OPT / FUT / Stock",
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
                "target_by": "Target by Money / Target by Point / Target by Point (%) / Target by Delta / Target by Delta (%) / Target by Theta / Target by Theta (%) / Target by Range High/Low",
                "sl": <number>,
                "sl_by": "SL by Money / SL by Point / SL by Point (%) / SL by Delta / SL by Delta (%) / SL by Theta / SL by Theta (%) / SL by Range High/Low",
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
"""

    def process_message(self, user_message, history=None):
        if history is None:
            history = []
            
        # Get context from RAG
        context = retriever.get_context(user_message)
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"Relevant Documentation Context:\n{context}"}
        ] + history + [{"role": "user", "content": user_message}]
        
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
                                    # Handle direct format like {"create_and_deploy_strategy": {...}}
                                    for key in ["create_and_deploy_strategy", "validate_strategy", "get_validation_rules"]:
                                        if key in data:
                                            tool_name = key
                                            val = data[key]
                                            # Ensure args is wrapped in strategy_json if the tool expects it
                                            if tool_name in ["create_and_deploy_strategy", "validate_strategy"]:
                                                if "strategy_json" in val: args = val
                                                else: args = {"strategy_json": val}
                                            else:
                                                args = val
                                            break
                            
                            if tool_name and args:
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
                                if tool_name == "create_and_deploy_strategy" and tool_result.get("status") == "success":
                                    clean_summary = re.sub(r'\{.*\}', '', content, flags=re.DOTALL).strip()
                                    if not clean_summary: clean_summary = content
                                    return {"message": clean_summary + "\n\n**Strategy Deployed Successfully.**", "input_tokens": _in_tok, "output_tokens": _out_tok}
                                    
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
        messages.append({"role": "user", "content": "You have done enough research. Please provide the final strategy summary and ask for deployment confirmation now."})
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

# Singleton instance
orchestrator = Orchestrator()
