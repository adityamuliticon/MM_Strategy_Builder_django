"""USB MCP tool functions — USB-specific capabilities exposed to the LLM.

Common tools (get_my_strategies, delete_strategy, get_strategy_record,
modify_strategy, rename_strategy, get_balance, get_deploy_options,
deploy_strategy, undeploy_strategy) are handled centrally by
utils.Orchestrator.StrategiesOrchestrator.SharedToolHandler.
"""

from Unified_Strategy_Builder.services.validator import validator
from Unified_Strategy_Builder.services.generator import generator
from Unified_Strategy_Builder.services.market_maya import market_maya
from Unified_Strategy_Builder.rag.retriever import retriever


def get_validation_rules(parameter_name):
    return retriever.get_context(f"validation rules for {parameter_name}")


def validate_strategy(strategy_json):
    main_errors = validator.validate_main_parameters(strategy_json)
    leg_errors = []
    for leg in strategy_json.get("legs", []):
        leg_errors.extend(validator.validate_leg_parameters(leg))
    all_errors = main_errors + leg_errors
    if all_errors:
        return {"status": "error", "errors": all_errors}
    return {"status": "success"}


def generate_payload(strategy_json):
    return generator.generate_v3_payload(strategy_json, strategy_json.get("legs", []))


def deploy(payload):
    return market_maya.save_strategy(payload)


def create_and_save_strategy(strategy_json):
    """Validate → generate payload → save in one step."""
    validation = validate_strategy(strategy_json)
    if validation.get("status") == "error":
        return validation
    payload = generate_payload(strategy_json)
    return deploy(payload)
