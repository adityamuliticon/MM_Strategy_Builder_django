"""
Common MCP handlers — all 5 strategy module handler classes in one file.

Each class is an exact copy of its original module mcp/handlers.py, with
imports redirected to utils.mcp.tools.  Logic is unchanged.

Handler classes:
  dispatch_usb_tool  — USB (function, not class — matches original design)
  BaseToolHandler    — shared common + backtest tool dispatch for MLH/RES/ISB/ISE
  MLHToolHandler     — Multi-Leg Hedger  → singleton: mlh_handler
  RESToolHandler     — Rapid Execution Scalper  → singleton: res_handler
  ISBToolHandler     — Inbound Signal Bridge  → singleton: isb_handler
  ISEToolHandler     — Indicator Signal Engine  → singleton: ise_handler
"""

from utils.mcp.tools import (
    # USB
    get_validation_rules,
    validate_strategy,
    generate_payload,
    deploy,
    create_and_save_strategy,
    # MLH
    mlh_get_validation_rules,
    mlh_validate_strategy,
    mlh_generate_payload,
    mlh_save,
    create_and_save_mlh_strategy,
    mlh_get_backtest_options,
    mlh_run_backtest,
    mlh_get_backtest_result,
    # RES
    res_get_validation_rules,
    res_validate_strategy,
    res_generate_payload,
    res_deploy,
    create_and_save_res_strategy,
    res_get_backtest_options,
    res_run_backtest,
    res_get_backtest_result,
    # ISB
    isb_get_validation_rules,
    isb_validate_strategy,
    isb_generate_payload,
    isb_save,
    create_and_save_isb_strategy,
    # ISE
    ise_get_validation_rules,
    ise_validate_strategy,
    ise_generate_payload,
    ise_save,
    create_and_save_ise_strategy,
    ise_get_backtest_options,
    ise_run_backtest,
    ise_get_backtest_result,
    # COMMON
    get_my_strategies,
    delete_strategy,
    get_strategy_record,
    modify_strategy,
    rename_strategy,
    get_balance,
    get_deploy_options,
    deploy_strategy,
    undeploy_strategy,
)


# ══════════════════════════════════════════════════════════════════════════════
# USB — Unified Strategy Builder
# Kept as a function (not a class) to match the original architecture.
# Called from StrategiesOrchestrator._dispatch_module_tool().
# ══════════════════════════════════════════════════════════════════════════════

def dispatch_usb_tool(tool_name, arguments):
    """USB-specific tool dispatch called from Orchestrator._dispatch_module_tool()."""
    if tool_name == "get_validation_rules":
        return get_validation_rules(arguments.get("parameter_name"))
    elif tool_name == "validate_strategy":
        return validate_strategy(arguments.get("strategy_json"))
    elif tool_name == "generate_payload":
        return generate_payload(arguments.get("strategy_json"))
    elif tool_name == "create_and_save_strategy":
        return create_and_save_strategy(arguments.get("strategy_json"))
    return f"Error: Unknown USB tool '{tool_name}'."


# ══════════════════════════════════════════════════════════════════════════════
# BaseToolHandler — shared common + backtest tool dispatch for all 4 handlers
# ══════════════════════════════════════════════════════════════════════════════

class BaseToolHandler:
    """Handles the 9 common tools (and optional backtest tools) shared by all 4 module handlers."""

    _backtest_fns = None  # set to {"options": fn, "run": fn, "result": fn} in subclasses

    def _dispatch_common(self, tool_name, arguments):
        """
        Handle tools that are identical across all four module handlers.
        Returns the tool result, or None if tool_name is module-specific.
        """
        if tool_name == "get_my_strategies":
            return get_my_strategies(
                search=arguments.get("search", ""),
                take=arguments.get("take", 500),
            )
        if tool_name == "delete_strategy":
            return delete_strategy(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
                confirmed=arguments.get("confirmed", False),
            )
        if tool_name == "get_strategy_record":
            return get_strategy_record(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
            )
        if tool_name == "modify_strategy":
            return modify_strategy(arguments.get("payload", arguments))
        if tool_name == "rename_strategy":
            return rename_strategy(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
                new_name=arguments.get("new_name", ""),
            )
        if tool_name == "get_balance":
            return get_balance()
        if tool_name == "get_deploy_options":
            return get_deploy_options(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
            )
        if tool_name == "deploy_strategy":
            return deploy_strategy(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
                trading_mode=arguments.get("trading_mode", "Live"),
                charges_acknowledged=arguments.get("charges_acknowledged", False),
                qty_multiply=arguments.get("qty_multiply", 1),
                entry_execution_type=arguments.get("entry_execution_type", "PSUEDO"),
                entry_psuedo_value=arguments.get("entry_psuedo_value", 0),
                entry_psuedo_type=arguments.get("entry_psuedo_type", "Auto"),
                entry_wait_seconds=arguments.get("entry_wait_seconds", 30),
                entry_no_of_try=arguments.get("entry_no_of_try", 2),
                entry_market_order_after_retry=arguments.get("entry_market_order_after_retry", False),
                exit_execution_type=arguments.get("exit_execution_type", "PSUEDO"),
                exit_psuedo_value=arguments.get("exit_psuedo_value", 0),
                exit_psuedo_type=arguments.get("exit_psuedo_type", "Auto"),
                exit_wait_seconds=arguments.get("exit_wait_seconds", 30),
                exit_no_of_try=arguments.get("exit_no_of_try", 2),
                exit_market_order_after_retry=arguments.get("exit_market_order_after_retry", False),
            )
        if tool_name == "undeploy_strategy":
            return undeploy_strategy(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
                confirmed=arguments.get("confirmed", False),
            )
        if self._backtest_fns:
            if tool_name == "get_backtest_options":
                return self._backtest_fns["options"](
                    strategy_id=arguments.get("strategy_id", ""),
                    strategy_name=arguments.get("strategy_name", ""),
                )
            if tool_name == "run_backtest":
                return self._backtest_fns["run"](
                    strategy_id=arguments.get("strategy_id", ""),
                    strategy_name=arguments.get("strategy_name", ""),
                    start_date=arguments.get("start_date", ""),
                    end_date=arguments.get("end_date", ""),
                )
            if tool_name == "get_backtest_result":
                return self._backtest_fns["result"](
                    strategy_id=arguments.get("strategy_id", ""),
                    strategy_name=arguments.get("strategy_name", ""),
                )
        return None


# ══════════════════════════════════════════════════════════════════════════════
# MLH — Multi-Leg Hedger
# ══════════════════════════════════════════════════════════════════════════════

class MLHToolHandler(BaseToolHandler):
    _backtest_fns = {
        "options": mlh_get_backtest_options,
        "run":     mlh_run_backtest,
        "result":  mlh_get_backtest_result,
    }

    def handle_tool_call(self, tool_name, arguments):
        try:
            result = self._dispatch_common(tool_name, arguments)
            if result is not None:
                return result
            if tool_name == "mlh_get_validation_rules":
                return mlh_get_validation_rules(arguments.get("parameter_name", ""))
            if tool_name == "create_and_save_mlh_strategy":
                return create_and_save_mlh_strategy(arguments.get("strategy_json", arguments))
            if tool_name == "mlh_validate_strategy":
                return mlh_validate_strategy(arguments.get("strategy_json", arguments))
            if tool_name == "mlh_generate_payload":
                return mlh_generate_payload(arguments.get("strategy_json", arguments))
            if tool_name == "mlh_save":
                return mlh_save(arguments.get("payload", arguments))
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


mlh_handler = MLHToolHandler()


# ══════════════════════════════════════════════════════════════════════════════
# RES — Rapid Execution Scalper
# ══════════════════════════════════════════════════════════════════════════════

class RESToolHandler(BaseToolHandler):
    _backtest_fns = {
        "options": res_get_backtest_options,
        "run":     res_run_backtest,
        "result":  res_get_backtest_result,
    }

    def handle_tool_call(self, tool_name, arguments):
        try:
            return self._dispatch(tool_name, arguments)
        except ValueError as e:
            return {"error": str(e), "resolution": "Please clarify the exchange or symbol before I proceed."}

    def _dispatch(self, tool_name, arguments):
        result = self._dispatch_common(tool_name, arguments)
        if result is not None:
            return result
        if tool_name == "res_get_validation_rules":
            return res_get_validation_rules(arguments.get("parameter_name"))
        if tool_name == "res_validate_strategy":
            return res_validate_strategy(arguments.get("strategy_json"))
        if tool_name == "res_generate_payload":
            return res_generate_payload(arguments.get("strategy_json"))
        if tool_name == "res_deploy":
            return res_deploy(arguments.get("payload"))
        if tool_name == "create_and_save_res_strategy":
            return create_and_save_res_strategy(arguments.get("strategy_json"))
        return f"Error: Unknown tool '{tool_name}'."


res_handler = RESToolHandler()


# ══════════════════════════════════════════════════════════════════════════════
# ISB — Inbound Signal Bridge
# ══════════════════════════════════════════════════════════════════════════════

class ISBToolHandler(BaseToolHandler):
    def handle_tool_call(self, tool_name, arguments):
        try:
            result = self._dispatch_common(tool_name, arguments)
            if result is not None:
                return result
            if tool_name == "isb_get_validation_rules":
                return isb_get_validation_rules(arguments.get("parameter_name", ""))
            if tool_name in ("isb_validate_strategy", "isb_generate_payload",
                             "create_and_save_isb_strategy"):
                fn = {
                    "isb_validate_strategy":       isb_validate_strategy,
                    "isb_generate_payload":         isb_generate_payload,
                    "create_and_save_isb_strategy": create_and_save_isb_strategy,
                }[tool_name]
                return fn(arguments.get("strategy_json", arguments))
            if tool_name == "isb_save":
                return isb_save(arguments.get("payload", arguments))
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


isb_handler = ISBToolHandler()


# ══════════════════════════════════════════════════════════════════════════════
# ISE — Indicator Signal Engine
# ══════════════════════════════════════════════════════════════════════════════

class ISEToolHandler(BaseToolHandler):
    _backtest_fns = {
        "options": ise_get_backtest_options,
        "run":     ise_run_backtest,
        "result":  ise_get_backtest_result,
    }

    def handle_tool_call(self, tool_name, arguments):
        try:
            return self._dispatch(tool_name, arguments)
        except ValueError as e:
            return {"error": str(e), "resolution": "Please clarify the exchange or symbol before I proceed."}

    def _dispatch(self, tool_name, arguments):
        result = self._dispatch_common(tool_name, arguments)
        if result is not None:
            return result
        if tool_name == "ise_get_validation_rules":
            return ise_get_validation_rules(arguments.get("parameter_name"))
        if tool_name == "ise_validate_strategy":
            return ise_validate_strategy(arguments.get("strategy_json"))
        if tool_name == "ise_generate_payload":
            return ise_generate_payload(arguments.get("strategy_json"))
        if tool_name == "ise_save":
            return ise_save(arguments.get("payload"))
        if tool_name == "create_and_save_ise_strategy":
            return create_and_save_ise_strategy(arguments.get("strategy_json"))
        return f"Error: Unknown tool '{tool_name}'."


ise_handler = ISEToolHandler()
