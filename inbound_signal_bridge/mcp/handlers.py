from inbound_signal_bridge.mcp.tools import (
    isb_get_validation_rules,
    isb_validate_strategy,
    isb_generate_payload,
    isb_deploy,
    create_and_save_isb_strategy,
    get_my_strategies,
    delete_strategy,
    get_strategy_record,
    modify_strategy,
    rename_strategy,
    get_balance,
)


class ISBToolHandler:
    def handle_tool_call(self, tool_name, arguments):
        try:
            if tool_name == "isb_get_validation_rules":
                return isb_get_validation_rules(arguments.get("parameter_name", ""))
            elif tool_name in ("isb_validate_strategy", "isb_generate_payload",
                               "create_and_save_isb_strategy"):
                fn = {
                    "isb_validate_strategy": isb_validate_strategy,
                    "isb_generate_payload": isb_generate_payload,
                    "create_and_save_isb_strategy": create_and_save_isb_strategy,
                }[tool_name]
                return fn(arguments.get("strategy_json", arguments))
            elif tool_name == "isb_deploy":
                return isb_deploy(arguments.get("payload", arguments))
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
            else:
                return {"status": "error", "message": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


isb_handler = ISBToolHandler()
