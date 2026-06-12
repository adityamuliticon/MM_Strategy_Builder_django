"""RES MCP tool functions — thin wrappers that expose RES capabilities to the LLM via tool calls."""

from rapid_execution_scalper.services.validator import res_validator
from rapid_execution_scalper.services.generator import res_generator
from rapid_execution_scalper.services.market_maya import res_market_maya
from rapid_execution_scalper.rag.retriever import res_retriever
from services.market_maya_shared import (
    get_strategies as _get_strategies,
    delete_strategy as _delete_strategy,
    get_strategy_record as _get_strategy_record,
    modify_strategy as _modify_strategy,
    rename_strategy as _rename_strategy,
    get_balance as _get_balance,
)
from services.deploy import (
    get_deploy_options as _get_deploy_options,
    deploy_strategy as _deploy_strategy,
)


def res_get_validation_rules(parameter_name):
    context = res_retriever.get_context(f"validation rules for {parameter_name}")
    return context


def res_validate_strategy(strategy_json):
    errors = res_validator.validate_strategy(strategy_json)
    if errors:
        return {"status": "error", "errors": errors}
    return {"status": "success"}


def res_generate_payload(strategy_json):
    return res_generator.generate_payload(strategy_json)


def res_deploy(payload):
    return res_market_maya.save_strategy(payload)


def create_and_save_res_strategy(strategy_json):
    payload = res_generate_payload(strategy_json)
    return res_deploy(payload)


def get_my_strategies(search="", take=50):
    result = _get_strategies(search=search, take=take)
    if result.get("status") != "success":
        return result
    strategies = result.get("strategies", [])
    total = result.get("total", 0)
    lines = [f"Total: {total} strategies (showing {len(strategies)}):"]
    for i, s in enumerate(strategies, 1):
        deployed = "Deployed" if s.get("deployed") else "Not deployed"
        created = (s.get("created") or "")[:10] or "—"
        lines.append(f"{i}. {s['name']} | {s['plugin']} | {deployed} | Created: {created}")
    return {
        "status": "success",
        "total": total,
        "formatted_list": "\n".join(lines),
        "strategies": [{"name": s["name"], "id": s["id"]} for s in strategies],
    }


def delete_strategy(strategy_id="", strategy_name=""):
    return _delete_strategy(strategy_id=strategy_id, strategy_name=strategy_name)


def get_strategy_record(strategy_id="", strategy_name=""):
    return _get_strategy_record(strategy_id=strategy_id, strategy_name=strategy_name)


def modify_strategy(payload):
    return _modify_strategy(payload)


def rename_strategy(strategy_id="", strategy_name="", new_name=""):
    return _rename_strategy(strategy_id=strategy_id, strategy_name=strategy_name, new_name=new_name)


def get_balance():
    return _get_balance()


def get_deploy_options(strategy_id="", strategy_name=""):
    return _get_deploy_options(strategy_id=strategy_id, strategy_name=strategy_name)


def deploy_strategy(strategy_id="", strategy_name="", trading_mode="Live", qty_multiply=1,
                    entry_execution_type="PSUEDO", entry_psuedo_value=0, entry_psuedo_type="Auto",
                    entry_wait_seconds=30, entry_no_of_try=2, entry_market_order_after_retry=False,
                    exit_execution_type="PSUEDO", exit_psuedo_value=0, exit_psuedo_type="Auto",
                    exit_wait_seconds=30, exit_no_of_try=2, exit_market_order_after_retry=False):
    return _deploy_strategy(
        strategy_id=strategy_id, strategy_name=strategy_name, trading_mode=trading_mode,
        qty_multiply=qty_multiply,
        entry_execution_type=entry_execution_type, entry_psuedo_value=entry_psuedo_value,
        entry_psuedo_type=entry_psuedo_type, entry_wait_seconds=entry_wait_seconds,
        entry_no_of_try=entry_no_of_try, entry_market_order_after_retry=entry_market_order_after_retry,
        exit_execution_type=exit_execution_type, exit_psuedo_value=exit_psuedo_value,
        exit_psuedo_type=exit_psuedo_type, exit_wait_seconds=exit_wait_seconds,
        exit_no_of_try=exit_no_of_try, exit_market_order_after_retry=exit_market_order_after_retry,
    )
