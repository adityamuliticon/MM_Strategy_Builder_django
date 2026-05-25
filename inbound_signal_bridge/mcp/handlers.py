from inbound_signal_bridge.mcp.tools import (
    isb_get_validation_rules,
    isb_validate_strategy,
    isb_generate_payload,
    isb_deploy,
    create_and_deploy_isb_strategy,
)


class ISBToolHandler:

    TOOL_MAP = {
        "isb_get_validation_rules": isb_get_validation_rules,
        "isb_validate_strategy":    isb_validate_strategy,
        "isb_generate_payload":     isb_generate_payload,
        "isb_deploy":               isb_deploy,
        "create_and_deploy_isb_strategy": create_and_deploy_isb_strategy,
    }

    def handle_tool_call(self, tool_name, arguments):
        fn = self.TOOL_MAP.get(tool_name)
        if not fn:
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}

        try:
            if tool_name == "isb_get_validation_rules":
                return fn(arguments.get("parameter_name", ""))
            elif tool_name in ("isb_validate_strategy", "isb_generate_payload",
                               "create_and_deploy_isb_strategy"):
                return fn(arguments.get("strategy_json", arguments))
            elif tool_name == "isb_deploy":
                return fn(arguments.get("payload", arguments))
            else:
                return fn(**arguments)
        except Exception as e:
            return {"status": "error", "message": str(e)}


isb_handler = ISBToolHandler()
