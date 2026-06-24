"""USB MCP ToolHandler — routes USB-specific LLM tool calls to tool functions.

Common tools (get_my_strategies, delete_strategy, get_strategy_record,
modify_strategy, rename_strategy, get_balance, get_deploy_options,
deploy_strategy, undeploy_strategy) are handled by SharedToolHandler in
utils.Orchestrator.StrategiesOrchestrator and never reach this handler.
"""

from Unified_Strategy_Builder.mcp.tools import (
    get_validation_rules,
    validate_strategy,
    generate_payload,
    create_and_save_strategy,
)


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
