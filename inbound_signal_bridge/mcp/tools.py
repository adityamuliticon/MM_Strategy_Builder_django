from inbound_signal_bridge.services.validator import isb_validator
from inbound_signal_bridge.services.generator import isb_generator
from inbound_signal_bridge.services.market_maya import isb_market_maya
from inbound_signal_bridge.rag.retriever import isb_retriever


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
