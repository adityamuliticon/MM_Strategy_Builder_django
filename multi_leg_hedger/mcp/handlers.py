"""MLH MCP ToolHandler — routes LLM tool-call names to the correct MLH tool function."""

from multi_leg_hedger.mcp.tools import (
    create_and_save_mlh_strategy, mlh_validate_strategy,
    mlh_generate_payload, mlh_save,
    delete_strategy,
    get_backtest_options, run_backtest, get_backtest_result,
    get_deploy_options, deploy_strategy,
)
import services.market_maya_shared as shared


class MLHToolHandler:
    def handle_tool_call(self, tool_name, arguments):
        try:
            if tool_name == "create_and_save_mlh_strategy":
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
            else:
                return {"status": "error", "message": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


mlh_handler = MLHToolHandler()
