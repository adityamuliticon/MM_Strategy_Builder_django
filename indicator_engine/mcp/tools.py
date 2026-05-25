from indicator_engine.services.validator import ise_validator
from indicator_engine.services.generator import ise_generator
from indicator_engine.services.market_maya import ise_market_maya
from indicator_engine.rag.retriever import ise_retriever


def ise_get_validation_rules(parameter_name):
    context = ise_retriever.get_context(f"validation rules for {parameter_name}")
    return context


def ise_validate_strategy(strategy_json):
    errors = ise_validator.validate_strategy(strategy_json)
    if errors:
        return {"status": "error", "errors": errors}
    return {"status": "success"}


def ise_generate_payload(strategy_json):
    return ise_generator.generate_payload(strategy_json)


def ise_deploy(payload):
    return ise_market_maya.deploy_strategy(payload)


def create_and_deploy_ise_strategy(strategy_json):
    payload = ise_generate_payload(strategy_json)
    return ise_deploy(payload)
