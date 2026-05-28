from inbound_signal_bridge.services.validator import isb_validator
from inbound_signal_bridge.services.generator import isb_generator
from inbound_signal_bridge.services.market_maya import isb_market_maya
from inbound_signal_bridge.rag.retriever import isb_retriever
from services.market_maya_shared import (
    get_strategies as _get_strategies,
    delete_strategy as _delete_strategy,
    get_strategy_record as _get_strategy_record,
    modify_strategy as _modify_strategy,
    rename_strategy as _rename_strategy,
    get_balance as _get_balance,
)


def isb_get_validation_rules(parameter_name):
    context = isb_retriever.get_context(f"validation rules for {parameter_name}")
    return context


def isb_validate_strategy(strategy_json):
    errors = isb_validator.validate_strategy(strategy_json)
    if errors:
        return {"status": "error", "errors": errors}
    return {"status": "success"}


def isb_generate_payload(strategy_json):
    return isb_generator.generate_payload(strategy_json)


def isb_deploy(payload):
    return isb_market_maya.deploy_strategy(payload)


def create_and_deploy_isb_strategy(strategy_json):
    payload = isb_generate_payload(strategy_json)
    return isb_deploy(payload)


def get_my_strategies(search="", take=50):
    return _get_strategies(search=search, take=take)


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
