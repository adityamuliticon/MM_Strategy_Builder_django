from Unified_Strategy_Builder.services.validator import validator
from Unified_Strategy_Builder.services.generator import generator
from Unified_Strategy_Builder.services.market_maya import market_maya
from Unified_Strategy_Builder.rag.retriever import retriever
from services.market_maya_shared import (
    get_strategies as _get_strategies,
    delete_strategy as _delete_strategy,
    get_strategy_record as _get_strategy_record,
    modify_strategy as _modify_strategy,
)

def get_validation_rules(parameter_name):
    """
    Retrieves validation rules for a specific parameter from the documentation.
    """
    context = retriever.get_context(f"validation rules for {parameter_name}")
    return context

def validate_strategy(strategy_json):
    """
    Validates a strategy JSON object.
    """
    main_errors = validator.validate_main_parameters(strategy_json)
    leg_errors = []
    for leg in strategy_json.get("legs", []):
        leg_errors.extend(validator.validate_leg_parameters(leg))
    
    all_errors = main_errors + leg_errors
    if all_errors:
        return {"status": "error", "errors": all_errors}
    return {"status": "success"}

def generate_payload(strategy_json):
    """
    Generates a V3 payload from strategy parameters.
    """
    main_params = strategy_json
    legs = strategy_json.get("legs", [])
    payload = generator.generate_v3_payload(main_params, legs)
    return payload

def deploy(payload):
    """
    Deploys the strategy to Market Maya.
    """
    return market_maya.deploy_strategy(payload)

def create_and_deploy_strategy(strategy_json):
    """
    Generates the correct V3 payload and deploys it in one step.
    """
    payload = generate_payload(strategy_json)
    return deploy(payload)


def get_my_strategies(search="", take=50):
    return _get_strategies(search=search, take=take)


def delete_strategy(strategy_id="", strategy_name=""):
    return _delete_strategy(strategy_id=strategy_id, strategy_name=strategy_name)


def get_strategy_record(strategy_id="", strategy_name=""):
    return _get_strategy_record(strategy_id=strategy_id, strategy_name=strategy_name)


def modify_strategy(payload):
    return _modify_strategy(payload)
