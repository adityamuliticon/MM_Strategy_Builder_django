from indicator_engine.mcp.tools import (
    ise_get_validation_rules,
    ise_validate_strategy,
    ise_generate_payload,
    ise_deploy,
    create_and_deploy_ise_strategy,
    get_my_strategies,
    delete_strategy,
    get_strategy_record,
    modify_strategy,
    rename_strategy,
    get_balance,
    get_backtest_options,
    run_backtest,
    get_backtest_result,
)


class ISEToolHandler:
    def handle_tool_call(self, tool_name, arguments):
        if tool_name == "ise_get_validation_rules":
            return ise_get_validation_rules(arguments.get("parameter_name"))
        elif tool_name == "ise_validate_strategy":
            return ise_validate_strategy(arguments.get("strategy_json"))
        elif tool_name == "ise_generate_payload":
            return ise_generate_payload(arguments.get("strategy_json"))
        elif tool_name == "ise_deploy":
            return ise_deploy(arguments.get("payload"))
        elif tool_name == "create_and_deploy_ise_strategy":
            return create_and_deploy_ise_strategy(arguments.get("strategy_json"))
        elif tool_name == "get_my_strategies":
            return get_my_strategies(
                search=arguments.get("search", ""),
                take=arguments.get("take", 50),
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
        return f"Error: Unknown tool '{tool_name}'."


# Singleton instance
ise_handler = ISEToolHandler()
