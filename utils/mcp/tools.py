"""
Common MCP tool functions — all 5 strategy modules consolidated.

Function names match the original module mcp/tools.py files exactly so that
handler dispatch logic is a drop-in replacement.

Sections:
  COMMON  — shared tools (strategies list, deploy, balance, etc.)
  USB     — Unified Strategy Builder  (no module prefix — original design)
  MLH     — Multi-Leg Hedger
  RES     — Rapid Execution Scalper
  ISB     — Inbound Signal Bridge
  ISE     — Indicator Signal Engine

For backtest tools, MLH and ISE both expose handler tool_names like
"get_backtest_options" / "run_backtest" / "get_backtest_result".  In this
file those are namespaced as mlh_* and ise_* so they can coexist; the
handler classes map the unqualified LLM tool_name to the right function.
"""

# ── Shared service imports ─────────────────────────────────────────────────────
from utils.rag.retriever import common_retriever
from marketmaya.Operations import Operations as _Ops
_get_strategies      = _Ops.get_strategies
_delete_strategy     = _Ops.delete_strategy
_get_strategy_record = _Ops.get_strategy_record
_modify_strategy     = _Ops.modify_strategy
_rename_strategy     = _Ops.rename_strategy
_get_balance         = _Ops.get_balance
from services.deploy import (
    get_deploy_options  as _get_deploy_options,
    deploy_strategy     as _deploy_strategy,
    undeploy_strategy   as _undeploy_strategy,
)

# ── Module-specific service imports ───────────────────────────────────────────
from utils.validation.USBValidator  import validator       as _usb_validator
from utils.generators.USBGenerator  import generator       as _usb_generator
from strategys.market_maya.market_maya import market_maya      as _usb_market_maya

from utils.validation.MLHValidator  import mlh_validator
from utils.generators.MLHGenerator  import mlh_generator
from strategys.market_maya.market_maya import mlh_market_maya
from services.backtest import (
    get_backtest_options as _mlh_get_backtest_options,
    run_backtest         as _mlh_run_backtest,
    get_backtest_result  as _mlh_get_backtest_result,
)

from utils.validation.RESValidator  import res_validator
from utils.generators.RESGenerator  import res_generator
from strategys.market_maya.market_maya import res_market_maya
from services.backtest import (
    get_backtest_options as _res_get_backtest_options,
    run_backtest         as _res_run_backtest,
    get_backtest_result  as _res_get_backtest_result,
)

from utils.validation.ISBValidator  import isb_validator
from utils.generators.ISBGenerator  import isb_generator
from strategys.market_maya.market_maya import isb_market_maya

from utils.validation.ISEValidator  import ise_validator
from utils.generators.ISEGenerator  import ise_generator
from strategys.market_maya.market_maya import ise_market_maya
from services.backtest import (
    get_backtest_options as _ise_get_backtest_options,
    run_backtest         as _ise_run_backtest,
    get_backtest_result  as _ise_get_backtest_result,
)


# ══════════════════════════════════════════════════════════════════════════════
# COMMON — shared across all modules
# ══════════════════════════════════════════════════════════════════════════════

def get_my_strategies(search="", take=500):
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


def delete_strategy(strategy_id="", strategy_name="", confirmed=False):
    if not confirmed:
        search = strategy_name or strategy_id
        return {
            "status": "requires_confirmation",
            "message": f"Are you sure you want to permanently delete '{search}'? "
                       "This cannot be undone. Call delete_strategy again with confirmed=True to proceed."
        }
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
                    charges_acknowledged=False,
                    entry_execution_type="PSUEDO", entry_psuedo_value=0, entry_psuedo_type="Auto",
                    entry_wait_seconds=30, entry_no_of_try=2, entry_market_order_after_retry=False,
                    exit_execution_type="PSUEDO", exit_psuedo_value=0, exit_psuedo_type="Auto",
                    exit_wait_seconds=30, exit_no_of_try=2, exit_market_order_after_retry=False):
    return _deploy_strategy(
        strategy_id=strategy_id, strategy_name=strategy_name, trading_mode=trading_mode,
        charges_acknowledged=charges_acknowledged, qty_multiply=qty_multiply,
        entry_execution_type=entry_execution_type, entry_psuedo_value=entry_psuedo_value,
        entry_psuedo_type=entry_psuedo_type, entry_wait_seconds=entry_wait_seconds,
        entry_no_of_try=entry_no_of_try, entry_market_order_after_retry=entry_market_order_after_retry,
        exit_execution_type=exit_execution_type, exit_psuedo_value=exit_psuedo_value,
        exit_psuedo_type=exit_psuedo_type, exit_wait_seconds=exit_wait_seconds,
        exit_no_of_try=exit_no_of_try, exit_market_order_after_retry=exit_market_order_after_retry,
    )


def undeploy_strategy(strategy_id="", strategy_name="", confirmed=False):
    if not confirmed:
        search = strategy_name or strategy_id
        return {
            "status": "requires_confirmation",
            "message": (
                f"Are you sure you want to undeploy '{search}'? "
                "This will stop live/paper trading for this strategy. "
                "Call undeploy_strategy again with confirmed=True to proceed."
            ),
        }
    return _undeploy_strategy(strategy_id=strategy_id, strategy_name=strategy_name)


# ══════════════════════════════════════════════════════════════════════════════
# USB — Unified Strategy Builder
# Function names have NO module prefix — matches original USB mcp/tools.py
# ══════════════════════════════════════════════════════════════════════════════

def get_validation_rules(parameter_name):
    return common_retriever.get_context(f"validation rules for {parameter_name}")


def validate_strategy(strategy_json):
    main_errors = _usb_validator.validate_main_parameters(strategy_json)
    leg_errors = []
    for leg in strategy_json.get("legs", []):
        leg_errors.extend(_usb_validator.validate_leg_parameters(leg))
    all_errors = main_errors + leg_errors
    if all_errors:
        return {"status": "error", "errors": all_errors}
    return {"status": "success"}


def generate_payload(strategy_json):
    return _usb_generator.generate_v3_payload(strategy_json, strategy_json.get("legs", []))


def deploy(payload):
    return _usb_market_maya.save_strategy(payload)


def create_and_save_strategy(strategy_json):
    validation = validate_strategy(strategy_json)
    if validation.get("status") == "error":
        return validation
    payload = generate_payload(strategy_json)
    return deploy(payload)


# ══════════════════════════════════════════════════════════════════════════════
# MLH — Multi-Leg Hedger
# ══════════════════════════════════════════════════════════════════════════════

def mlh_get_validation_rules(parameter_name):
    return common_retriever.get_context(f"validation rules for {parameter_name}")


def mlh_validate_strategy(strategy_json):
    errors = mlh_validator.validate(strategy_json)
    return {"status": "valid" if not errors else "invalid", "errors": errors}


def mlh_generate_payload(strategy_json):
    return {"status": "success", "payload": mlh_generator.generate_payload(strategy_json)}


def mlh_save(payload):
    return mlh_market_maya.deploy(payload)


def create_and_save_mlh_strategy(strategy_json):
    errors = mlh_validator.validate(strategy_json)
    if errors:
        return {"status": "error", "message": "Validation failed", "errors": errors}
    payload = mlh_generator.generate_payload(strategy_json)
    result = mlh_market_maya.deploy(payload)
    if result["status"] == "success":
        return {"status": "success", "message": f"Strategy '{strategy_json.get('strategy_name')}' deployed successfully.", "api_response": result["response"]}
    return {"status": "error", "message": f"Deployment failed: {result.get('response')}", "code": result.get("code")}


def mlh_get_backtest_options(strategy_id="", strategy_name=""):
    return _mlh_get_backtest_options(strategy_id=strategy_id, strategy_name=strategy_name)


def mlh_run_backtest(strategy_id="", strategy_name="", start_date="", end_date=""):
    return _mlh_run_backtest(strategy_id=strategy_id, strategy_name=strategy_name,
                             start_date=start_date, end_date=end_date)


def mlh_get_backtest_result(strategy_id="", strategy_name=""):
    return _mlh_get_backtest_result(strategy_id=strategy_id, strategy_name=strategy_name)


# ══════════════════════════════════════════════════════════════════════════════
# RES — Rapid Execution Scalper
# ══════════════════════════════════════════════════════════════════════════════

def res_get_validation_rules(parameter_name):
    return common_retriever.get_context(f"validation rules for {parameter_name}")


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
    errors = res_validator.validate_strategy(strategy_json)
    if errors:
        return {"status": "error", "message": "Validation failed", "errors": errors}
    payload = res_generate_payload(strategy_json)
    return res_deploy(payload)


def res_get_backtest_options(strategy_id="", strategy_name=""):
    return _res_get_backtest_options(strategy_id=strategy_id, strategy_name=strategy_name)


def res_run_backtest(strategy_id="", strategy_name="", start_date="", end_date=""):
    return _res_run_backtest(strategy_id=strategy_id, strategy_name=strategy_name,
                             start_date=start_date, end_date=end_date)


def res_get_backtest_result(strategy_id="", strategy_name=""):
    return _res_get_backtest_result(strategy_id=strategy_id, strategy_name=strategy_name)


# ══════════════════════════════════════════════════════════════════════════════
# ISB — Inbound Signal Bridge
# ══════════════════════════════════════════════════════════════════════════════

def isb_get_validation_rules(parameter_name):
    return common_retriever.get_context(f"validation rules for {parameter_name}")


def isb_validate_strategy(strategy_json):
    errors = isb_validator.validate_strategy(strategy_json)
    if errors:
        return {"status": "error", "errors": errors}
    return {"status": "success"}


def isb_generate_payload(strategy_json):
    return isb_generator.generate_payload(strategy_json)


def isb_save(payload):
    return isb_market_maya.save_strategy(payload)


def create_and_save_isb_strategy(strategy_json):
    # H-13: validate before every save
    validation = isb_validate_strategy(strategy_json)
    if validation.get("status") == "error":
        return validation
    payload = isb_generate_payload(strategy_json)
    return isb_save(payload)


# ══════════════════════════════════════════════════════════════════════════════
# ISE — Indicator Signal Engine
# ══════════════════════════════════════════════════════════════════════════════

def ise_get_validation_rules(parameter_name):
    return common_retriever.get_context(f"validation rules for {parameter_name}")


def ise_validate_strategy(strategy_json):
    errors = ise_validator.validate_strategy(strategy_json)
    if errors:
        return {"status": "error", "errors": errors}
    return {"status": "success"}


def ise_generate_payload(strategy_json):
    return ise_generator.generate_payload(strategy_json)


def ise_save(payload):
    return ise_market_maya.save_strategy(payload)


def create_and_save_ise_strategy(strategy_json):
    # H-13: validate before every save
    validation = ise_validate_strategy(strategy_json)
    if validation.get("status") == "error":
        return validation
    payload = ise_generate_payload(strategy_json)
    return ise_save(payload)


def ise_get_backtest_options(strategy_id="", strategy_name=""):
    return _ise_get_backtest_options(strategy_id=strategy_id, strategy_name=strategy_name)


def ise_run_backtest(strategy_id="", strategy_name="", start_date="", end_date=""):
    return _ise_run_backtest(strategy_id=strategy_id, strategy_name=strategy_name,
                             start_date=start_date, end_date=end_date)


def ise_get_backtest_result(strategy_id="", strategy_name=""):
    return _ise_get_backtest_result(strategy_id=strategy_id, strategy_name=strategy_name)
