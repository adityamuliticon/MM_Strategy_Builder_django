"""
StrategiesOrchestrator — intermediate base class for all 5 strategy modules.

Implements the 9 tools that are identical across every module so each concrete
orchestrator only needs to handle its own module-specific tools.

Shared tools handled here:
  get_my_strategies, delete_strategy, get_strategy_record,
  modify_strategy, rename_strategy, get_balance,
  get_deploy_options, deploy_strategy, undeploy_strategy

Module-specific tools (validate, generate, save, backtest, …) are routed to
_dispatch_module_tool(), which each concrete orchestrator overrides.
"""

from utils.Orchestrator.BaseOrchestrator import BaseOrchestrator
from marketmaya.Operations import Operations as _Ops
_get_my_strategies   = _Ops.get_my_strategies
_delete_strategy     = _Ops.delete_strategy
_get_strategy_record = _Ops.get_strategy_record
_modify_strategy     = _Ops.modify_strategy
_rename_strategy     = _Ops.rename_strategy
_get_balance         = _Ops.get_balance
from services.deploy import (
    get_deploy_options as _get_deploy_options,
    deploy_strategy as _deploy_strategy,
    undeploy_strategy as _undeploy_strategy,
)


class SharedToolHandler:
    """
    Handles the 9 Market Maya tools that are common to all strategy modules.
    Unknown tools are forwarded to module_dispatch, which is the concrete
    orchestrator's _dispatch_module_tool() bound method.

    operations — optional marketmaya.Operations instance. When supplied, all
    shared API calls are routed through it (the marketmaya package). When None
    the handler falls back to the market_maya_shared module-level functions so
    every existing module keeps working without changes.
    """

    def __init__(self, module_dispatch, operations=None):
        self._module_dispatch = module_dispatch
        # Bind shared API callables from either marketmaya.Operations or the
        # legacy market_maya_shared functions — callers in _dispatch never care.
        if operations is not None:
            self._get_my_strategies  = operations.get_my_strategies
            self._delete_strategy    = operations.delete_strategy
            self._get_strategy_record= operations.get_strategy_record
            self._modify_strategy    = operations.modify_strategy
            self._rename_strategy    = operations.rename_strategy
            self._get_balance        = operations.get_balance
        else:
            self._get_my_strategies  = _get_my_strategies
            self._delete_strategy    = _delete_strategy
            self._get_strategy_record= _get_strategy_record
            self._modify_strategy    = _modify_strategy
            self._rename_strategy    = _rename_strategy
            self._get_balance        = _get_balance

    def handle_tool_call(self, tool_name, arguments):
        try:
            return self._dispatch(tool_name, arguments)
        except ValueError as e:
            return {
                "error": str(e),
                "resolution": "Please clarify the exchange or symbol before I proceed.",
            }

    def _dispatch(self, tool_name, arguments):
        if tool_name == "get_my_strategies":
            return self._get_my_strategies(
                search=arguments.get("search", ""),
                take=arguments.get("take", 500),
            )

        elif tool_name == "delete_strategy":
            if not arguments.get("confirmed", False):
                name = arguments.get("strategy_name") or arguments.get("strategy_id", "")
                return {
                    "status": "requires_confirmation",
                    "message": (
                        f"Are you sure you want to permanently delete '{name}'? "
                        "This cannot be undone. "
                        "Call delete_strategy again with confirmed=True to proceed."
                    ),
                }
            return self._delete_strategy(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
            )

        elif tool_name == "get_strategy_record":
            return self._get_strategy_record(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
            )

        elif tool_name == "modify_strategy":
            return self._modify_strategy(arguments.get("payload", arguments))

        elif tool_name == "rename_strategy":
            return self._rename_strategy(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
                new_name=arguments.get("new_name", ""),
            )

        elif tool_name == "get_balance":
            return self._get_balance()

        elif tool_name == "get_deploy_options":
            return _get_deploy_options(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
            )

        elif tool_name == "deploy_strategy":
            return _deploy_strategy(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
                trading_mode=arguments.get("trading_mode", "Live"),
                charges_acknowledged=arguments.get("charges_acknowledged", False),
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

        elif tool_name == "undeploy_strategy":
            if not arguments.get("confirmed", False):
                name = arguments.get("strategy_name") or arguments.get("strategy_id", "")
                return {
                    "status": "requires_confirmation",
                    "message": (
                        f"Are you sure you want to undeploy '{name}'? "
                        "This will stop live/paper trading for this strategy. "
                        "Call undeploy_strategy again with confirmed=True to proceed."
                    ),
                }
            return _undeploy_strategy(
                strategy_id=arguments.get("strategy_id", ""),
                strategy_name=arguments.get("strategy_name", ""),
            )

        # Not a shared tool — hand off to the concrete module's dispatch
        return self._module_dispatch(tool_name, arguments)


class StrategiesOrchestrator(BaseOrchestrator):
    """
    Abstract base for all 5 strategy orchestrators.

    Inheriting classes must still implement all hooks required by BaseOrchestrator
    (_retriever, _context_label, _save_tool_name, _tool_whitelist,
    _strategy_json_wrap_keys, _module_prefix, _status_messages,
    _max_turns_msg, _confirm_save_instruction) — but they no longer need to
    provide a _handler() or manage common tool routing.

    Each subclass overrides _dispatch_module_tool() with its own tools only.
    To supply a custom operations provider (e.g. marketmaya.Operations), override
    _make_handler() instead of __init__.
    """

    def __init__(self):
        super().__init__()
        self._shared_handler = self._make_handler()

    def _make_handler(self):
        """Factory for the shared tool handler. Override in subclasses to inject
        a custom operations provider (e.g. marketmaya.Operations for USB)."""
        return SharedToolHandler(self._dispatch_module_tool)

    def _handler(self):
        return self._shared_handler

    def _dispatch_module_tool(self, tool_name, arguments):
        """
        Override in each concrete orchestrator to handle module-specific tools.
        Called automatically when a tool_name is not in the 9 shared tools.
        """
        return f"Error: Unknown tool '{tool_name}'."
