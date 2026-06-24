"""ISE MCP ToolHandler — routes LLM tool-call names to the correct ISE tool function."""

from indicator_engine.mcp.tools import (
    ise_get_validation_rules,
    ise_validate_strategy,
    ise_generate_payload,
    ise_save,
    create_and_save_ise_strategy,
    get_my_strategies,
    delete_strategy,
    get_strategy_record,
    modify_strategy,
    rename_strategy,
    get_balance,
    get_backtest_options,
    run_backtest,
    get_backtest_result,
    get_deploy_options,
    deploy_strategy,
    undeploy_strategy,
)


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
            return get_backtest_options(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
            )
        elif tool_name == "run_backtest":
            return run_backtest(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
                start_date=arguments.get("start_date", ""),
                end_date=arguments.get("end_date", ""),
            )
        elif tool_name == "get_backtest_result":
            return get_backtest_result(
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


# Singleton instance
ise_handler = ISEToolHandler()
