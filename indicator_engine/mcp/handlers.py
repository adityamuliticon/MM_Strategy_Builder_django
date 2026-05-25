from indicator_engine.mcp.tools import (
    ise_get_validation_rules,
    ise_validate_strategy,
    ise_generate_payload,
    ise_deploy,
    create_and_deploy_ise_strategy,
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

        return f"Error: Unknown tool '{tool_name}'. Use 'create_and_deploy_ise_strategy' to deploy."


# Singleton instance
ise_handler = ISEToolHandler()
