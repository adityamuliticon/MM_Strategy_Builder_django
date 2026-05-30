from indicator_engine.services.validator import ise_validator
from indicator_engine.services.generator import ise_generator
from indicator_engine.services.market_maya import ise_market_maya
from indicator_engine.rag.retriever import ise_retriever
from indicator_engine.services.backtest import (
    get_backtest_options as _get_backtest_options,
    run_backtest as _run_backtest,
    get_backtest_result as _get_backtest_result,
)
from services.market_maya_shared import (
    get_strategies as _get_strategies,
    delete_strategy as _delete_strategy,
    get_strategy_record as _get_strategy_record,
    modify_strategy as _modify_strategy,
    rename_strategy as _rename_strategy,
    get_balance as _get_balance,
)


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


def get_backtest_options(strategy_id="", strategy_name=""):
    return _get_backtest_options(strategy_id=strategy_id, strategy_name=strategy_name)


def run_backtest(strategy_id="", strategy_name="", start_date="", end_date=""):
    return _run_backtest(strategy_id=strategy_id, strategy_name=strategy_name,
                         start_date=start_date, end_date=end_date)


def get_backtest_result(strategy_id="", strategy_name=""):
    return _get_backtest_result(strategy_id=strategy_id, strategy_name=strategy_name)
