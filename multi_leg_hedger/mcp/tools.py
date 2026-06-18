"""MLH MCP tool functions — thin wrappers that expose MLH capabilities (including backtest and deploy) to the LLM via tool calls."""

from multi_leg_hedger.services.generator import mlh_generator
from multi_leg_hedger.services.validator import mlh_validator
from multi_leg_hedger.services.market_maya import mlh_market_maya
from multi_leg_hedger.services.backtest import (
    get_backtest_options as _get_backtest_options,
    run_backtest as _run_backtest,
    get_backtest_result as _get_backtest_result,
)
import services.market_maya_shared as shared
from services.market_maya_shared import delete_strategy as _delete_strategy
from services.deploy import (
    get_deploy_options as _get_deploy_options,
    deploy_strategy as _deploy_strategy,
)


def create_and_save_mlh_strategy(strategy_json):
    errors = mlh_validator.validate(strategy_json)
    if errors:
        return {"status": "error", "message": "Validation failed", "errors": errors}
    payload = mlh_generator.generate_payload(strategy_json)
    result = mlh_market_maya.deploy(payload)
    if result["status"] == "success":
        return {"status": "success", "message": f"Strategy '{strategy_json.get('strategy_name')}' deployed successfully.", "api_response": result["response"]}
    return {"status": "error", "message": f"Deployment failed: {result.get('response')}", "code": result.get("code")}


def mlh_validate_strategy(strategy_json):
    errors = mlh_validator.validate(strategy_json)
    return {"status": "valid" if not errors else "invalid", "errors": errors}


def mlh_generate_payload(strategy_json):
    return {"status": "success", "payload": mlh_generator.generate_payload(strategy_json)}


def mlh_save(payload):
    return mlh_market_maya.deploy(payload)


def delete_strategy(strategy_id="", strategy_name="", confirmed=False):
    if not confirmed:
        search = strategy_name or strategy_id
        return {
            "status": "requires_confirmation",
            "message": f"Are you sure you want to permanently delete '{search}'? "
                       "This cannot be undone. Call delete_strategy again with confirmed=True to proceed."
        }
    return _delete_strategy(strategy_id=strategy_id, strategy_name=strategy_name)


def get_backtest_options(strategy_id="", strategy_name=""):
    return _get_backtest_options(strategy_id=strategy_id, strategy_name=strategy_name)


def run_backtest(strategy_id="", strategy_name="", start_date="", end_date=""):
    return _run_backtest(strategy_id=strategy_id, strategy_name=strategy_name,
                         start_date=start_date, end_date=end_date)


def get_backtest_result(strategy_id="", strategy_name=""):
    return _get_backtest_result(strategy_id=strategy_id, strategy_name=strategy_name)


def get_deploy_options(strategy_id="", strategy_name=""):
    return _get_deploy_options(strategy_id=strategy_id, strategy_name=strategy_name)


def deploy_strategy(strategy_id="", strategy_name="", trading_mode="Live", qty_multiply=1,
                    charges_acknowledged=False,
                    entry_execution_type="PSUEDO", entry_psuedo_value=0, entry_psuedo_type="Auto",
                    entry_wait_seconds=30, entry_no_of_try=2, entry_market_order_after_retry=False,
                    exit_execution_type="PSUEDO", exit_psuedo_value=0, exit_psuedo_type="Auto",
                    exit_wait_seconds=30, exit_no_of_try=2, exit_market_order_after_retry=False):
    return _deploy_strategy(
        strategy_id=strategy_id, strategy_name=strategy_name, trading_mode=trading_mode,
        charges_acknowledged=charges_acknowledged,
        qty_multiply=qty_multiply,
        entry_execution_type=entry_execution_type, entry_psuedo_value=entry_psuedo_value,
        entry_psuedo_type=entry_psuedo_type, entry_wait_seconds=entry_wait_seconds,
        entry_no_of_try=entry_no_of_try, entry_market_order_after_retry=entry_market_order_after_retry,
        exit_execution_type=exit_execution_type, exit_psuedo_value=exit_psuedo_value,
        exit_psuedo_type=exit_psuedo_type, exit_wait_seconds=exit_wait_seconds,
        exit_no_of_try=exit_no_of_try, exit_market_order_after_retry=exit_market_order_after_retry,
    )
