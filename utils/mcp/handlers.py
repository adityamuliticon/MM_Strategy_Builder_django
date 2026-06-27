"""
Common MCP handlers — all 5 strategy module handler classes in one file.

Each class is an exact copy of its original module mcp/handlers.py, with
imports redirected to utils.mcp.tools.  Logic is unchanged.

Handler classes:
  dispatch_usb_tool  — USB (function, not class — matches original design)
  MLHToolHandler     — Multi-Leg Hedger  → singleton: mlh_handler
  RESToolHandler     — Rapid Execution Scalper  → singleton: res_handler
  ISBToolHandler     — Inbound Signal Bridge  → singleton: isb_handler
  ISEToolHandler     — Indicator Signal Engine  → singleton: ise_handler
"""

from marketmaya.Operations import Operations as shared

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
# MLH — Multi-Leg Hedger
# ══════════════════════════════════════════════════════════════════════════════

class MLHToolHandler:
    def handle_tool_call(self, tool_name, arguments):
        try:
            if tool_name == "mlh_get_validation_rules":
                return mlh_get_validation_rules(arguments.get("parameter_name", ""))
            elif tool_name == "create_and_save_mlh_strategy":
                return create_and_save_mlh_strategy(arguments.get("strategy_json", arguments))
            elif tool_name == "mlh_validate_strategy":
                return mlh_validate_strategy(arguments.get("strategy_json", arguments))
            elif tool_name == "mlh_generate_payload":
                return mlh_generate_payload(arguments.get("strategy_json", arguments))
            elif tool_name == "mlh_save":
                return mlh_save(arguments.get("payload", arguments))
            elif tool_name == "get_my_strategies":
                return shared.get_my_strategies(**arguments)
            elif tool_name == "delete_strategy":
                return delete_strategy(**arguments)
            elif tool_name == "get_strategy_record":
                return shared.get_strategy_record(**arguments)
            elif tool_name == "modify_strategy":
                return shared.modify_strategy(**arguments)
            elif tool_name == "rename_strategy":
                return shared.rename_strategy(**arguments)
            elif tool_name == "get_balance":
                return shared.get_balance()
            elif tool_name == "get_backtest_options":
                return mlh_get_backtest_options(
                    strategy_id=arguments.get("strategy_id", ""),
                    strategy_name=arguments.get("strategy_name", ""),
                )
            elif tool_name == "run_backtest":
                return mlh_run_backtest(
                    strategy_id=arguments.get("strategy_id", ""),
                    strategy_name=arguments.get("strategy_name", ""),
                    start_date=arguments.get("start_date", ""),
                    end_date=arguments.get("end_date", ""),
                )
            elif tool_name == "get_backtest_result":
                return mlh_get_backtest_result(
                    strategy_id=arguments.get("strategy_id", ""),
                    strategy_name=arguments.get("strategy_name", ""),
                )
            elif tool_name == "get_deploy_options":
                return get_deploy_options(
                    strategy_id=arguments.get("strategy_id", ""),
                    strategy_name=arguments.get("strategy_name", ""),
                )
            elif tool_name == "deploy_strategy":
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
            elif tool_name == "undeploy_strategy":
                return undeploy_strategy(
                    strategy_id=arguments.get("strategy_id", ""),
                    strategy_name=arguments.get("strategy_name", ""),
                    confirmed=arguments.get("confirmed", False),
                )
            else:
                return {"status": "error", "message": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


mlh_handler = MLHToolHandler()


# ══════════════════════════════════════════════════════════════════════════════
# RES — Rapid Execution Scalper
# ══════════════════════════════════════════════════════════════════════════════

class RESToolHandler:
    def handle_tool_call(self, tool_name, arguments):
        try:
            return self._dispatch(tool_name, arguments)
        except ValueError as e:
            return {"error": str(e), "resolution": "Please clarify the exchange or symbol before I proceed."}

    def _dispatch(self, tool_name, arguments):
        if tool_name == "res_get_validation_rules":
            return res_get_validation_rules(arguments.get("parameter_name"))
        elif tool_name == "res_validate_strategy":
            return res_validate_strategy(arguments.get("strategy_json"))
        elif tool_name == "res_generate_payload":
            return res_generate_payload(arguments.get("strategy_json"))
        elif tool_name == "res_deploy":
            return res_deploy(arguments.get("payload"))
        elif tool_name == "create_and_save_res_strategy":
            return create_and_save_res_strategy(arguments.get("strategy_json"))
        elif tool_name == "get_my_strategies":
            return get_my_strategies(
                search=arguments.get("search", ""),
                take=arguments.get("take", 500),
            )
        elif tool_name == "delete_strategy":
            return delete_strategy(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
                confirmed=arguments.get("confirmed", False),
            )
        elif tool_name == "get_strategy_record":
            return get_strategy_record(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
            )
        elif tool_name == "modify_strategy":
            return modify_strategy(arguments.get("payload", arguments))
        elif tool_name == "rename_strategy":
            return rename_strategy(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
                new_name=arguments.get("new_name", ""),
            )
        elif tool_name == "get_balance":
            return get_balance()
        elif tool_name == "get_backtest_options":
            return res_get_backtest_options(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
            )
        elif tool_name == "run_backtest":
            return res_run_backtest(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
                start_date=arguments.get("start_date", ""),
                end_date=arguments.get("end_date", ""),
            )
        elif tool_name == "get_backtest_result":
            return res_get_backtest_result(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
            )
        elif tool_name == "get_deploy_options":
            return get_deploy_options(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
            )
        elif tool_name == "deploy_strategy":
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
        elif tool_name == "undeploy_strategy":
            return undeploy_strategy(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
                confirmed=arguments.get("confirmed", False),
            )
        return f"Error: Unknown tool '{tool_name}'."


res_handler = RESToolHandler()


# ══════════════════════════════════════════════════════════════════════════════
# ISB — Inbound Signal Bridge
# ══════════════════════════════════════════════════════════════════════════════

class ISBToolHandler:
    def handle_tool_call(self, tool_name, arguments):
        try:
            if tool_name == "isb_get_validation_rules":
                return isb_get_validation_rules(arguments.get("parameter_name", ""))
            elif tool_name in ("isb_validate_strategy", "isb_generate_payload",
                               "create_and_save_isb_strategy"):
                fn = {
                    "isb_validate_strategy":      isb_validate_strategy,
                    "isb_generate_payload":        isb_generate_payload,
                    "create_and_save_isb_strategy": create_and_save_isb_strategy,
                }[tool_name]
                return fn(arguments.get("strategy_json", arguments))
            elif tool_name == "isb_save":
                return isb_save(arguments.get("payload", arguments))
            elif tool_name == "get_my_strategies":
                return get_my_strategies(
                    search=arguments.get("search", ""),
                    take=arguments.get("take", 500),
                )
            elif tool_name == "delete_strategy":
                return delete_strategy(
                    strategy_id=arguments.get("strategy_id", ""),
                    strategy_name=arguments.get("strategy_name", ""),
                    confirmed=arguments.get("confirmed", False),
                )
            elif tool_name == "get_strategy_record":
                return get_strategy_record(
                    strategy_id=arguments.get("strategy_id", ""),
                    strategy_name=arguments.get("strategy_name", ""),
                )
            elif tool_name == "modify_strategy":
                return modify_strategy(arguments.get("payload", arguments))
            elif tool_name == "rename_strategy":
                return rename_strategy(
                    strategy_id=arguments.get("strategy_id", ""),
                    strategy_name=arguments.get("strategy_name", ""),
                    new_name=arguments.get("new_name", ""),
                )
            elif tool_name == "get_balance":
                return get_balance()
            elif tool_name == "get_deploy_options":
                return get_deploy_options(
                    strategy_id=arguments.get("strategy_id", ""),
                    strategy_name=arguments.get("strategy_name", ""),
                )
            elif tool_name == "deploy_strategy":
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
            elif tool_name == "undeploy_strategy":
                return undeploy_strategy(
                    strategy_id=arguments.get("strategy_id", ""),
                    strategy_name=arguments.get("strategy_name", ""),
                    confirmed=arguments.get("confirmed", False),
                )
            else:
                return {"status": "error", "message": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


isb_handler = ISBToolHandler()


# ══════════════════════════════════════════════════════════════════════════════
# ISE — Indicator Signal Engine
# ══════════════════════════════════════════════════════════════════════════════

class ISEToolHandler:
    def handle_tool_call(self, tool_name, arguments):
        try:
            return self._dispatch(tool_name, arguments)
        except ValueError as e:
            return {"error": str(e), "resolution": "Please clarify the exchange or symbol before I proceed."}

    def _dispatch(self, tool_name, arguments):
        if tool_name == "ise_get_validation_rules":
            return ise_get_validation_rules(arguments.get("parameter_name"))
        elif tool_name == "ise_validate_strategy":
            return ise_validate_strategy(arguments.get("strategy_json"))
        elif tool_name == "ise_generate_payload":
            return ise_generate_payload(arguments.get("strategy_json"))
        elif tool_name == "ise_save":
            return ise_save(arguments.get("payload"))
        elif tool_name == "create_and_save_ise_strategy":
            return create_and_save_ise_strategy(arguments.get("strategy_json"))
        elif tool_name == "get_my_strategies":
            return get_my_strategies(
                search=arguments.get("search", ""),
                take=arguments.get("take", 500),
            )
        elif tool_name == "delete_strategy":
            return delete_strategy(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
                confirmed=arguments.get("confirmed", False),
            )
        elif tool_name == "get_strategy_record":
            return get_strategy_record(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
            )
        elif tool_name == "modify_strategy":
            return modify_strategy(arguments.get("payload", arguments))
        elif tool_name == "rename_strategy":
            return rename_strategy(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
                new_name=arguments.get("new_name", ""),
            )
        elif tool_name == "get_balance":
            return get_balance()
        elif tool_name == "get_backtest_options":
            return ise_get_backtest_options(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
            )
        elif tool_name == "run_backtest":
            return ise_run_backtest(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
                start_date=arguments.get("start_date", ""),
                end_date=arguments.get("end_date", ""),
            )
        elif tool_name == "get_backtest_result":
            return ise_get_backtest_result(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
            )
        elif tool_name == "get_deploy_options":
            return get_deploy_options(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
            )
        elif tool_name == "deploy_strategy":
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
        elif tool_name == "undeploy_strategy":
            return undeploy_strategy(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
                confirmed=arguments.get("confirmed", False),
            )
        return f"Error: Unknown tool '{tool_name}'."


ise_handler = ISEToolHandler()
