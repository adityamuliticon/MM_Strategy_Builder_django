import json
from chat.mcp.tools import get_validation_rules, validate_strategy, generate_payload, deploy, create_and_deploy_strategy

class ToolHandler:
    def handle_tool_call(self, tool_name, arguments):
        """
        Routes tool calls from the LLM to the appropriate function.
        """
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
            
        return f"Error: Unknown tool '{tool_name}'. Please use 'create_and_deploy_strategy' for deployment."

# Singleton instance
handler = ToolHandler()
