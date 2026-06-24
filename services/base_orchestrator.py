"""Shared base for all module orchestrators — Template Method for process_message and stream_message."""

import json
import re
from openai import OpenAI, BadRequestError, AuthenticationError, RateLimitError, APIConnectionError
from config import Config

_CONFIRM_WORDS = frozenset({
    'yes', 'proceed', 'save', 'save it', 'confirm', 'go', 'ok',
    'sure', 'approve', 'approved', 'continue', 'do it', 'submit',
})
# Phrases that indicate the last assistant message was about deployment (not strategy creation).
# Used to suppress _confirm_save_instruction injection in that context.
_DEPLOY_CONTEXT_SIGNALS = frozenset({
    "which trading mode", "live trading charge", "paper trading charge", "per order",
})
_DIRECT_YIELD_TOOLS = frozenset({
    "get_my_strategies", "get_balance", "delete_strategy",
    "rename_strategy", "modify_strategy", "undeploy_strategy",
})
# Signals that the last assistant message showed the execution-settings confirmation table.
_DEPLOY_SETTINGS_SIGNALS = frozenset({
    "execution settings", "qty multiplier", "type **proceed**", "proceed** to deploy",
})
# Signals that the last assistant message is awaiting tool confirmation (undeploy, delete, rename, modify).
# Suppresses _confirm_save_instruction injection so "yes" routes to the pending tool, not the save tool.
_TOOL_CONFIRM_SIGNALS = frozenset({
    "undeploy",                   # undeploy_strategy confirmation
    "stop live/paper",            # "stop live/paper trading for this strategy"
    "undeploy_strategy again",    # literal from mcp/tools.py
    "permanently delete",         # delete_strategy confirmation
    "cannot be undone",           # delete_strategy confirmation
    "delete_strategy again",      # literal from mcp/tools.py
    "rename_strategy again",      # rename_strategy confirmation
    "modify_strategy again",      # modify_strategy confirmation
    "confirmed=true to proceed",  # present in ALL requires_confirmation tool messages
    "requires_confirmation",      # raw JSON (direct-yield path in RES/MLH)
})

_SETTINGS_TABLE = (
    "**Execution Settings (defaults):**\n\n"
    "| Setting | Entry | Exit |\n"
    "|---------|-------|------|\n"
    "| Type | PSUEDO | PSUEDO |\n"
    "| Pseudo Type | Auto | Auto |\n"
    "| Pseudo Value | 0 | 0 |\n"
    "| Wait Seconds | 30 | 30 |\n"
    "| No. of Tries | 2 | 2 |\n"
    "| Market Order on Retry | No | No |\n\n"
    "**Qty Multiplier:** 1\n\n"
    "**Types:** PSUEDO (Pseudo Type: Auto / Ticks / Points / %) · LIMIT (Wait only)\n\n"
    "Type **proceed** to deploy with defaults, or specify changes — e.g.:\n"
    "- `entry LIMIT 20 ticks` · `exit PSUEDO auto` · `qty 2` · `wait 60`"
)


def _parse_deploy_settings(msg):
    """
    Parse execution-setting overrides from a natural language message.
    Returns a dict of deploy_strategy kwargs that differ from defaults.
    """
    o = {}
    m = msg.lower()

    # Qty multiplier: "qty 2", "multiplier 2"
    qm = re.search(r'\bqty\s+(\d+)|\bmultipl\w*\s+(\d+)', m)
    if qm:
        o['qty_multiply'] = int(qm.group(1) or qm.group(2))

    for side in ('entry', 'exit'):
        # Execution type
        if re.search(rf'\b{side}\b[^.]*\blimit\b', m):
            o[f'{side}_execution_type'] = 'LIMIT'
        elif re.search(rf'\b{side}\b[^.]*\bpsuedo\b', m):
            o[f'{side}_execution_type'] = 'PSUEDO'

        # Pseudo type + value (only meaningful for PSUEDO, but harmless for LIMIT)
        if re.search(rf'\b{side}\b[^.]*\bauto\b', m):
            o[f'{side}_psuedo_type'] = 'Auto'
            o[f'{side}_psuedo_value'] = 0
        elif re.search(rf'\b{side}\b[^.]*tick', m):
            o[f'{side}_psuedo_type'] = 'Ticks'
            v = re.search(rf'\b{side}\b[^.]*?(\d+)\s*tick', m) or re.search(r'(\d+)\s*tick', m)
            if v:
                o[f'{side}_psuedo_value'] = int(v.group(1))
        elif re.search(rf'\b{side}\b[^.]*point', m):
            o[f'{side}_psuedo_type'] = 'Points'
            v = re.search(rf'\b{side}\b[^.]*?(\d+)\s*point', m) or re.search(r'(\d+)\s*point', m)
            if v:
                o[f'{side}_psuedo_value'] = int(v.group(1))
        elif re.search(rf'\b{side}\b[^.]*percent|\b{side}\b[^.]*\b%', m):
            o[f'{side}_psuedo_type'] = '%'
            v = re.search(rf'\b{side}\b[^.]*?(\d+(?:\.\d+)?)\s*%', m)
            if v:
                o[f'{side}_psuedo_value'] = float(v.group(1))

        # Wait seconds (side-specific): "wait 40", "for 40 sec", "40 seconds", "40s"
        w = (
            re.search(rf'\b{side}\b[^.]*wait\s+(\d+)', m)
            or re.search(rf'\b{side}\b[^.]*for\s+(\d+)\s*sec', m)
            or re.search(rf'\b{side}\b[^.]*\b(\d+)\s*sec(?:ond)?s?\b', m)
        )
        if w:
            o[f'{side}_wait_seconds'] = int(w.group(1))

        # No. of tries
        n = re.search(rf'\b{side}\b[^.]*(?:tr(?:y|ies)|attempt)\s+(\d+)', m)
        if n:
            o[f'{side}_no_of_try'] = int(n.group(1))

    # Global wait (no side specified) — applies to both
    if 'entry_wait_seconds' not in o and 'exit_wait_seconds' not in o:
        gw = (
            re.search(r'\bwait\s+(\d+)', m)
            or re.search(r'\bfor\s+(\d+)\s*sec', m)
            or re.search(r'\b(\d+)\s*sec(?:ond)?s?\b', m)
        )
        if gw:
            o['entry_wait_seconds'] = o['exit_wait_seconds'] = int(gw.group(1))

    return o


class BaseOrchestrator:
    def __init__(self):
        self.client = OpenAI(api_key=Config.RUNWARE_API_KEY, base_url=Config.RUNWARE_BASE_URL)
        self.model = Config.RUNWARE_MODEL_ID

    # ── Abstract hooks — implement in every subclass ───────────────────────
    def _retriever(self):                raise NotImplementedError
    def _handler(self):                  raise NotImplementedError
    def _context_label(self):            raise NotImplementedError
    def _save_tool_name(self):           raise NotImplementedError
    def _tool_whitelist(self):           raise NotImplementedError
    def _strategy_json_wrap_keys(self):  raise NotImplementedError
    def _module_prefix(self):            raise NotImplementedError
    def _status_messages(self):          raise NotImplementedError
    def _max_turns_msg(self):            raise NotImplementedError
    def _confirm_save_instruction(self): raise NotImplementedError

    # ── Hooks with defaults — override per module as needed ────────────────
    def _temperature(self):          return None   # None → omit; 0.1 → pass
    def _final_temperature(self):    return None   # for fallback/final calls; MLH returns 0.1
    def _confirm_in_stream(self):    return True   # ISE returns False
    def _null_content_check(self):   return True   # RES+MLH return False
    def _has_direct_yield(self):     return False  # RES+MLH return True
    def _debug_json_str(self):       return False  # RES returns True

    def _is_deploy_confirm_context(self, history):
        """True when the last assistant message is about deployment charges (trading mode selection)."""
        for msg in reversed(history or []):
            if msg.get("role") == "assistant" and msg.get("content"):
                content = msg["content"].lower()
                return any(kw in content for kw in _DEPLOY_CONTEXT_SIGNALS)
        return False

    def _is_deploy_settings_context(self, history):
        """True when the last assistant message showed the execution-settings confirmation table."""
        for msg in reversed(history or []):
            if msg.get("role") == "assistant" and msg.get("content"):
                content = msg["content"].lower()
                return any(kw in content for kw in _DEPLOY_SETTINGS_SIGNALS)
        return False

    def _is_tool_confirm_context(self, history):
        """True when the last assistant message is waiting for confirmation from any tool (undeploy, delete, rename, etc.)."""
        for msg in reversed(history or []):
            if msg.get("role") == "assistant" and msg.get("content"):
                content = msg["content"].lower()
                return any(kw in content for kw in _TOOL_CONFIRM_SIGNALS)
        return False

    def _credits_check(self, msg):   return "credits" in msg.lower()

    def _process_error_msgs(self):
        return {
            "credits": "⚠️ **AI service unavailable**: Insufficient credits.",
            "auth":    "⚠️ **Authentication error**: Invalid API key.",
            "rate":    "⚠️ **Rate limit reached**: Please wait a moment.",
            "conn":    "⚠️ **Connection error**: Could not reach AI service.",
        }

    def _stream_error_msgs(self):
        return {
            "credits": "⚠️ **AI service unavailable**: Insufficient credits.",
            "auth":    "⚠️ **Authentication error**: Invalid API key.",
            "rate":    "⚠️ **Rate limit reached**: Please wait a moment.",
            "conn":    "⚠️ **Connection error**: Could not reach AI service.",
        }

    def _save_success_process(self, content, json_str, args, tool_result):
        clean_summary = content.replace(json_str, '', 1).strip()
        if not clean_summary:
            clean_summary = content
        return clean_summary + "\n\n**Strategy Saved Successfully.**"

    def _save_success_stream(self, args, tool_result):
        return "\n\n**Strategy Saved Successfully.**"

    def _confirm_retry_msg_process(self):  return None  # RES+MLH override
    def _confirm_retry_msg_stream(self):   return None  # MLH overrides
    def _stream_empty_confirm_msg(self):   return None  # RES overrides

    # ── Template method: process_message ──────────────────────────────────
    def process_message(self, user_message, history=None):
        if history is None:
            history = []

        _is_confirm = bool(history) and any(w in user_message.lower() for w in _CONFIRM_WORDS)
        _in_deploy_ctx = self._is_deploy_confirm_context(history)
        context = self._retriever().get_context(user_message)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"{self._context_label()}:\n{context}"},
        ] + history + [{"role": "user", "content": user_message}]

        if _is_confirm and not _in_deploy_ctx and not self._is_tool_confirm_context(history):
            messages[-1] = {
                "role": "user",
                "content": user_message + "\n\n" + self._confirm_save_instruction(),
            }

        max_turns = 10
        executed_tools = set()
        _in_tok = _out_tok = 0
        _confirm_retry_done = False
        _errs = self._process_error_msgs()
        _temp = self._temperature()
        _prefix = self._module_prefix()
        _save_tool = self._save_tool_name()
        _whitelist = self._tool_whitelist()
        _wrap_keys = self._strategy_json_wrap_keys()
        _do_null_check = self._null_content_check()

        def _call(**extra):
            kw = {"model": self.model, "messages": messages}
            if _temp is not None:
                kw["temperature"] = _temp
            kw.update(extra)
            return self.client.chat.completions.create(**kw)

        for turn in range(max_turns):
            try:
                response = _call()
            except BadRequestError as e:
                msg = str(e)
                if self._credits_check(msg):
                    return {"message": _errs["credits"], "input_tokens": _in_tok, "output_tokens": _out_tok}
                return {"message": f"⚠️ **AI service error**: {msg}", "input_tokens": _in_tok, "output_tokens": _out_tok}
            except AuthenticationError:
                return {"message": _errs["auth"], "input_tokens": _in_tok, "output_tokens": _out_tok}
            except RateLimitError:
                return {"message": _errs["rate"], "input_tokens": _in_tok, "output_tokens": _out_tok}
            except APIConnectionError:
                return {"message": _errs["conn"], "input_tokens": _in_tok, "output_tokens": _out_tok}

            if hasattr(response, 'usage') and response.usage:
                _in_tok += response.usage.prompt_tokens
                _out_tok += response.usage.completion_tokens

            content = response.choices[0].message.content
            if _do_null_check and not content:
                return {"message": "Sorry, I received an empty response. Please try again.", "input_tokens": _in_tok, "output_tokens": _out_tok}

            tool_called = False
            json_str = ''
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
                                for key in _whitelist:
                                    if key in data:
                                        tool_name = key
                                        val = data[key]
                                        if key in _wrap_keys:
                                            args = val if isinstance(val, dict) and "strategy_json" in val else {"strategy_json": val}
                                        else:
                                            args = val
                                        break
                        if tool_name and args is not None:
                            args_str = json.dumps(args, sort_keys=True)
                            tool_key = f"{tool_name}:{args_str}"
                            if tool_key in executed_tools:
                                print(f"!! [{_prefix} Turn {turn+1}] Skipping redundant tool: {tool_name}")
                                tool_called = True
                                break
                            executed_tools.add(tool_key)
                            print(f"> [{_prefix} Turn {turn+1}] Executing tool: {tool_name}")
                            tool_result = self._handler().handle_tool_call(tool_name, args)
                            messages.append({"role": "assistant", "content": content})
                            messages.append({"role": "user", "content": f"SYSTEM TOOL RESULT: {json.dumps(tool_result)}"})
                            tool_called = True
                            if tool_name == _save_tool and tool_result.get("status") == "success":
                                return {"message": self._save_success_process(content, json_str, args, tool_result), "input_tokens": _in_tok, "output_tokens": _out_tok}
                            break
                    except Exception as e:
                        print(f"[{_prefix}] JSON parsing error: {e}")
                        continue
                if tool_called:
                    continue
            except Exception as e:
                print(f"[{_prefix}] Tool execution error: {e}")

            if _is_confirm and not _in_deploy_ctx and not self._is_tool_confirm_context(history) and not tool_called and not _confirm_retry_done:
                retry_msg = self._confirm_retry_msg_process()
                if retry_msg:
                    _confirm_retry_done = True
                    messages.append({"role": "assistant", "content": content})
                    messages.append({"role": "user", "content": retry_msg})
                    continue

            ui_content = content.replace(json_str, '', 1).strip() if json_str else content.strip()
            if not ui_content:
                ui_content = content
            return {"message": ui_content, "input_tokens": _in_tok, "output_tokens": _out_tok}

        messages.append({"role": "user", "content": self._max_turns_msg()})
        _ft = self._final_temperature()
        final_kw = {"model": self.model, "messages": messages}
        if _ft is not None:
            final_kw["temperature"] = _ft
        try:
            final = self.client.chat.completions.create(**final_kw)
            if hasattr(final, 'usage') and final.usage:
                _in_tok += final.usage.prompt_tokens
                _out_tok += final.usage.completion_tokens
            return {"message": final.choices[0].message.content, "input_tokens": _in_tok, "output_tokens": _out_tok}
        except Exception as e:
            return {"message": f"⚠️ **AI service error**: {e}", "input_tokens": _in_tok, "output_tokens": _out_tok}

    # ── Template method: stream_message ───────────────────────────────────
    def stream_message(self, user_message, history=None):
        if history is None:
            history = []

        # ── Shortcut: digit selection in a backtest-options context ────────
        # The LLM returns empty content when the user says "1"/"2"/... after
        # seeing a backtest options table, so we parse + call the tool directly.
        _digit_m = re.fullmatch(r'\s*(\d)\s*', user_message)
        if _digit_m and "run_backtest" in self._tool_whitelist():
            period_num = int(_digit_m.group(1))
            for _msg in reversed(history or []):
                if _msg.get("role") != "assistant":
                    continue
                _c = _msg.get("content", "")
                _name_m = re.search(r'Backtest Strategy\s*[-–]\s*(.+)', _c)
                _row_m = re.search(
                    rf'\|\s*{period_num}\s*\|[^|]+\|\s*(\d{{4}}-\d{{2}}-\d{{2}})\s*\|\s*(\d{{4}}-\d{{2}}-\d{{2}})\s*\|',
                    _c,
                )
                if _name_m and _row_m:
                    _strat = _name_m.group(1).split('\n')[0].strip()
                    _s_date = _row_m.group(1)
                    _e_date = _row_m.group(2)
                    yield {"t": "status", "v": "Running backtest (this may take 10–30 seconds)..."}
                    _bt = self._handler().handle_tool_call(
                        "run_backtest",
                        {"strategy_name": _strat, "start_date": _s_date, "end_date": _e_date},
                    )
                    yield {"t": "chunk", "v": _bt.get("message", "Backtest triggered. Use get_backtest_result to fetch results.")}
                    yield {"t": "done", "in_tok": 0, "out_tok": 0}
                    return
                break  # only inspect the last assistant message

        # ── Shortcut: "proceed" or settings change after seeing execution-settings table ──
        # Handles both "proceed" (use defaults) and inline changes ("entry LIMIT 20 ticks").
        _proceed_m = re.search(
            r'\b(proceed|no|yes|ok|sure|go|default|confirm|deploy|continue'
            r'|entry|exit|limit|psuedo|qty|wait|tick|auto|point|percent)\b',
            user_message, re.IGNORECASE,
        )
        if _proceed_m and "deploy_strategy" in self._tool_whitelist():
            if self._is_deploy_settings_context(history):
                for _msg in reversed(history or []):
                    if _msg.get("role") != "assistant":
                        continue
                    _c = _msg.get("content", "")
                    if not any(kw in _c.lower() for kw in _DEPLOY_SETTINGS_SIGNALS):
                        continue
                    # Format A: "Ready to deploy **X** to **Live Trading**"
                    _sm = re.search(
                        r"deploy\s+\*?\*?(.+?)\*?\*?\s+to\s+\*?\*?(Live|Paper)\s+Trading",
                        _c, re.IGNORECASE,
                    )
                    # Format B: "**Deploy: X** · Balance: ..." (new direct-yield format)
                    _sm2 = re.search(r"\*\*Deploy:\s*([^·*\n]+)", _c) if not _sm else None
                    if _sm:
                        _strat = _sm.group(1).strip().strip("'\"")
                        _mode = _sm.group(2).capitalize()
                    elif _sm2:
                        _strat = _sm2.group(1).strip().strip("'\"")
                        _mode = "Live"  # only live trading
                    if _sm or _sm2:
                        _overrides = _parse_deploy_settings(user_message)
                        yield {"t": "status", "v": f"Deploying '{_strat}' to {_mode} Trading (connecting to exchange)..."}
                        _dr = self._handler().handle_tool_call(
                            "deploy_strategy",
                            {"strategy_name": _strat, "trading_mode": _mode, "charges_acknowledged": True, **_overrides},
                        )
                        yield {"t": "chunk", "v": _dr.get("message", f"Strategy deployed to {_mode} Trading.")}
                        yield {"t": "done", "in_tok": 0, "out_tok": 0}
                        return
                    break

        # ── Shortcut: "Live Trading" / "Paper Trading" in deploy-charges context ──────
        # The LLM returns empty content for short mode selections.
        # Show execution settings table and ask for confirmation before deploying.
        _deploy_mode_m = re.search(r'\b(live|paper)\b', user_message, re.IGNORECASE)
        if _deploy_mode_m and "deploy_strategy" in self._tool_whitelist():
            if self._is_deploy_confirm_context(history):
                for _msg in reversed(history or []):
                    if _msg.get("role") != "assistant":
                        continue
                    _c = _msg.get("content", "")
                    if not any(kw in _c.lower() for kw in _DEPLOY_CONTEXT_SIGNALS):
                        continue
                    _strat_m = (
                        re.search(r'\|\s*Strategy\s*\|\s*(.+?)\s*\|', _c)
                        or re.search(r"Strategy\s*[|\s]+([^\|\n]+)", _c)
                    )
                    if _strat_m:
                        _strat = _strat_m.group(1).strip()
                        _mode = "Live" if _deploy_mode_m.group(1).lower() == "live" else "Paper"
                        _settings_msg = (
                            f"Ready to deploy **{_strat}** to **{_mode} Trading**.\n\n"
                            + _SETTINGS_TABLE
                        )
                        yield {"t": "chunk", "v": _settings_msg}
                        yield {"t": "done", "in_tok": 0, "out_tok": 0}
                        return
                    break
        # ─────────────────────────────────────────────────────────────────────────────

        _is_confirm = bool(history) and any(w in user_message.lower() for w in _CONFIRM_WORDS)
        _in_deploy_ctx = self._is_deploy_confirm_context(history)
        context = self._retriever().get_context(user_message)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"{self._context_label()}:\n{context}"},
        ] + history + [{"role": "user", "content": user_message}]

        if _is_confirm and not _in_deploy_ctx and not self._is_tool_confirm_context(history) and self._confirm_in_stream():
            messages[-1] = {
                "role": "user",
                "content": user_message + "\n\n" + self._confirm_save_instruction(),
            }

        max_turns = 10
        executed_tools = set()
        _in_tok = _out_tok = 0
        _confirm_retry_done = False
        _errs = self._stream_error_msgs()
        _temp = self._temperature()
        _ft = self._final_temperature()
        _prefix = self._module_prefix()
        _save_tool = self._save_tool_name()
        _whitelist = self._tool_whitelist()
        _wrap_keys = self._strategy_json_wrap_keys()
        _status_msgs = self._status_messages()
        _has_direct = self._has_direct_yield()
        _dbg = self._debug_json_str()

        for turn in range(max_turns):
            stream_kw = {"model": self.model, "messages": messages, "stream": True, "stream_options": {"include_usage": True}}
            if _temp is not None:
                stream_kw["temperature"] = _temp
            try:
                stream = self.client.chat.completions.create(**stream_kw)
            except BadRequestError as e:
                msg = str(e)
                yield {"t": "error", "v": _errs["credits"] if self._credits_check(msg) else f"⚠️ **AI error**: {msg}"}
                return
            except AuthenticationError:
                yield {"t": "error", "v": _errs["auth"]}
                return
            except RateLimitError:
                yield {"t": "error", "v": _errs["rate"]}
                return
            except APIConnectionError:
                yield {"t": "error", "v": _errs["conn"]}
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
                                clean = re.sub(r'```(?:json|js|JSON)?', '', text_part)
                                if clean:
                                    yield {"t": "chunk", "v": clean}
                                text_part = ""
                            brace_depth += 1
                        elif char == '}':
                            brace_depth = max(0, brace_depth - 1)
                        elif brace_depth == 0:
                            text_part += char
                    if text_part and brace_depth == 0:
                        clean = re.sub(r'```(?:json|js|JSON)?', '', text_part)
                        if clean:
                            yield {"t": "chunk", "v": clean}
            except Exception as e:
                print(f"[{_prefix}] Stream error on turn {turn+1}: {e}")

            if not full_content.strip():
                fb_kw = {"model": self.model, "messages": messages}
                if _ft is not None:
                    fb_kw["temperature"] = _ft
                try:
                    fb = self.client.chat.completions.create(**fb_kw)
                    if hasattr(fb, 'usage') and fb.usage:
                        _in_tok += fb.usage.prompt_tokens or 0
                        _out_tok += fb.usage.completion_tokens or 0
                    full_content = fb.choices[0].message.content or ""
                    ui_text = re.sub(r'```(?:json|js|JSON)?', '', re.sub(r'\{.*?\}', '', full_content, flags=re.DOTALL)).strip()
                    if ui_text:
                        yield {"t": "chunk", "v": ui_text}
                except Exception as e2:
                    print(f"[{_prefix}] Fallback error on turn {turn+1}: {e2}")
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
                    if _dbg:
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
                                for key in _whitelist:
                                    if key in data:
                                        tool_name = key
                                        val = data[key]
                                        if key in _wrap_keys:
                                            args = val if isinstance(val, dict) and "strategy_json" in val else {"strategy_json": val}
                                        else:
                                            args = val
                                        break
                        if tool_name and args is not None:
                            args_str = json.dumps(args, sort_keys=True)
                            tool_key = f"{tool_name}:{args_str}"
                            if tool_key in executed_tools:
                                tool_called = True
                                break
                            executed_tools.add(tool_key)
                            yield {"t": "status", "v": _status_msgs.get(tool_name, "Processing...")}
                            tool_result = self._handler().handle_tool_call(tool_name, args)
                            messages.append({"role": "assistant", "content": full_content})
                            messages.append({"role": "user", "content": f"SYSTEM TOOL RESULT: {json.dumps(tool_result)}"})
                            tool_called = True
                            if tool_name == _save_tool and tool_result.get("status") == "success":
                                yield {"t": "chunk", "v": self._save_success_stream(args, tool_result)}
                                yield {"t": "done", "in_tok": _in_tok, "out_tok": _out_tok}
                                return
                            if tool_name == "get_deploy_options" and tool_result.get("status") == "success":
                                _dn = tool_result.get("strategy_name") or args.get("strategy_name") or args.get("strategy_id", "")
                                _db = tool_result.get("point_balance")
                                _dc = tool_result.get("live_trade_charge_per_order", 1.0)
                                _dsm = (
                                    f"**Deploy: {_dn}** · Balance: {_db} pts · Live charge: {_dc} pt/order\n\n"
                                    + _SETTINGS_TABLE
                                )
                                yield {"t": "chunk", "v": _dsm}
                                yield {"t": "done", "in_tok": _in_tok, "out_tok": _out_tok}
                                return
                            if tool_name == "deploy_strategy" and tool_result.get("status") == "success" and not tool_result.get("requires_confirmation"):
                                yield {"t": "chunk", "v": tool_result.get("message", "Strategy deployed successfully.")}
                                yield {"t": "done", "in_tok": _in_tok, "out_tok": _out_tok}
                                return
                            if tool_name == "run_backtest":
                                yield {"t": "chunk", "v": tool_result.get("message", "Backtest triggered. Use get_backtest_result when ready.")}
                                yield {"t": "done", "in_tok": _in_tok, "out_tok": _out_tok}
                                return
                            if _has_direct and tool_name in _DIRECT_YIELD_TOOLS:
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
                            break
                    except Exception as e:
                        print(f"Error handling tool call: {e}")
                        continue
            except Exception as e:
                print(f"Tool parsing error: {e}")

            empty_confirm_msg = self._stream_empty_confirm_msg()
            if empty_confirm_msg and not tool_called and not full_content.strip() and _is_confirm:
                yield {"t": "chunk", "v": empty_confirm_msg}

            if _is_confirm and not _in_deploy_ctx and not self._is_tool_confirm_context(history) and not tool_called and not _confirm_retry_done:
                retry_msg = self._confirm_retry_msg_stream()
                if retry_msg:
                    _confirm_retry_done = True
                    messages.append({"role": "assistant", "content": full_content})
                    messages.append({"role": "user", "content": retry_msg})
                    continue

            if tool_called:
                continue

            yield {"t": "done", "in_tok": _in_tok, "out_tok": _out_tok}
            return

        yield {"t": "done", "in_tok": _in_tok, "out_tok": _out_tok}
