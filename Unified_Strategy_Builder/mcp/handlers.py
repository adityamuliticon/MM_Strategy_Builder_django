import json
from Unified_Strategy_Builder.mcp.tools import (
    get_validation_rules, validate_strategy, generate_payload, deploy,
    create_and_deploy_strategy, get_my_strategies, delete_strategy,
    get_strategy_record, modify_strategy,
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
        elif tool_name == "create_and_deploy_strategy":
            return create_and_deploy_strategy(arguments.get("strategy_json"))
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
        return f"Error: Unknown tool '{tool_name}'."

# Singleton instance
handler = ToolHandler()
