import json
from Unified_Strategy_Builder.mcp.tools import (
    get_validation_rules, validate_strategy, generate_payload, deploy,
    create_and_save_strategy, get_my_strategies, delete_strategy,
    get_strategy_record, modify_strategy, rename_strategy, get_balance,
    get_deploy_options, deploy_strategy,
)

class ToolHandler:
    def handle_tool_call(self, tool_name, arguments):
        if tool_name == "get_validation_rules":
            return get_validation_rules(arguments.get("parameter_name"))
        elif tool_name == "validate_strategy":
            return validate_strategy(arguments.get("strategy_json"))
        elif tool_name == "generate_payload":
            return generate_payload(arguments.get("strategy_json"))
        elif tool_name == "deploy":
            return deploy(arguments.get("payload"))
        elif tool_name == "create_and_save_strategy":
            return create_and_save_strategy(arguments.get("strategy_json"))
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
        return f"Error: Unknown tool '{tool_name}'."

# Singleton instance
handler = ToolHandler()
