"""All 5 module orchestrators — hook implementations for each strategy plugin."""

import re

from utils.orchestrator.base_orchestrator import BaseOrchestrator
from utils.orchestrator.strategies_orchestrator import StrategiesOrchestrator
from utils.rag.retriever import common_retriever
from utils.mcp.handlers import dispatch_usb_tool, mlh_handler, res_handler, isb_handler, ise_handler
from prompts.usb_prompt import USB_SYSTEM_PROMPT
from prompts.mlh_prompt import MLH_SYSTEM_PROMPT
from prompts.res_prompt import RES_SYSTEM_PROMPT
from prompts.isb_prompt import ISB_SYSTEM_PROMPT
from prompts.ise_prompt import ISE_SYSTEM_PROMPT


# ── USB ────────────────────────────────────────────────────────────────────────

class Orchestrator(StrategiesOrchestrator):

    def __init__(self):
        super().__init__()
        self.system_prompt = USB_SYSTEM_PROMPT

    def _retriever(self):            return common_retriever
    def _context_label(self):        return "Relevant Documentation Context"

    def _dispatch_module_tool(self, tool_name, arguments):
        return dispatch_usb_tool(tool_name, arguments)
    def _save_tool_name(self):       return "create_and_save_strategy"
    def _module_prefix(self):        return "USB"

    def _tool_whitelist(self):
        return [
            "create_and_save_strategy", "validate_strategy", "get_validation_rules",
            "get_my_strategies", "delete_strategy", "get_strategy_record",
            "modify_strategy", "rename_strategy", "get_balance",
            "get_deploy_options", "deploy_strategy", "undeploy_strategy",
        ]

    def _strategy_json_wrap_keys(self):
        return {"create_and_save_strategy", "validate_strategy"}

    def _status_messages(self):
        return {
            "create_and_save_strategy": "Saving strategy to Market Maya...",
            "get_my_strategies":        "Fetching your strategies...",
            "delete_strategy":          "Deleting strategy...",
            "get_strategy_record":      "Fetching strategy record...",
            "modify_strategy":          "Saving changes...",
            "rename_strategy":          "Renaming strategy...",
            "get_balance":              "Fetching balance...",
            "get_deploy_options":       "Fetching deploy options...",
            "deploy_strategy":          "Deploying strategy to Market Maya...",
            "undeploy_strategy":        "Undeploying strategy...",
        }

    def _max_turns_msg(self):
        return "You have done enough research. Please provide the final strategy summary and ask for save confirmation now."

    def _confirm_save_instruction(self):
        return (
            "[SAVE NOW: Output ONLY a JSON block calling create_and_save_strategy. "
            "Use ALL field values from the preview tables above. "
            "Format exactly: {\"tool\": \"create_and_save_strategy\", \"arguments\": {\"strategy_json\": {...all fields...}}}]"
        )

    def _credits_check(self, msg):
        return "Insufficient credits" in msg or "credits" in msg.lower()

    def _process_error_msgs(self):
        return {
            "credits": "⚠️ **AI service unavailable**: The Runware AI account has insufficient credits. Please top up at app.runware.ai and try again.",
            "auth":    "⚠️ **Authentication error**: Invalid Runware API key. Please check your RUNWARE_API_KEY in .env.",
            "rate":    "⚠️ **Rate limit reached**: Too many requests. Please wait a moment and try again.",
            "conn":    "⚠️ **Connection error**: Could not reach the AI service. Check your internet connection and try again.",
        }


# Singleton instance
orchestrator = Orchestrator()


# ── MLH ────────────────────────────────────────────────────────────────────────

class MLHOrchestrator(BaseOrchestrator):

    def __init__(self):
        super().__init__()
        self.system_prompt = MLH_SYSTEM_PROMPT

    def _retriever(self):            return common_retriever
    def _handler(self):              return mlh_handler
    def _context_label(self):        return "Relevant Documentation Context"
    def _save_tool_name(self):       return "create_and_save_mlh_strategy"
    def _module_prefix(self):        return "MLH"

    def _temperature(self):          return 0.1
    def _final_temperature(self):    return 0.1
    def _null_content_check(self):   return False
    def _has_direct_yield(self):     return True

    def _tool_whitelist(self):
        return [
            "create_and_save_mlh_strategy", "mlh_validate_strategy", "mlh_get_validation_rules",
            "get_my_strategies", "delete_strategy", "get_strategy_record",
            "modify_strategy", "rename_strategy", "get_balance",
            "get_backtest_options", "run_backtest", "get_backtest_result",
            "get_deploy_options", "deploy_strategy", "undeploy_strategy",
        ]

    def _strategy_json_wrap_keys(self):
        return {"create_and_save_mlh_strategy"}

    def _status_messages(self):
        return {
            "create_and_save_mlh_strategy": "Saving Multi-Leg Hedger strategy to Market Maya...",
            "get_my_strategies":            "Fetching your strategies...",
            "delete_strategy":              "Deleting strategy...",
            "get_strategy_record":          "Fetching strategy record...",
            "modify_strategy":              "Saving changes...",
            "rename_strategy":              "Renaming strategy...",
            "get_balance":                  "Fetching balance...",
            "get_backtest_options":         "Fetching backtest options...",
            "run_backtest":                 "Running backtest (this may take 10–30 seconds)...",
            "get_backtest_result":          "Fetching backtest results...",
            "get_deploy_options":           "Fetching deploy options...",
            "deploy_strategy":              "Deploying strategy to Market Maya...",
            "undeploy_strategy":            "Undeploying strategy...",
        }

    def _max_turns_msg(self):
        return "Please provide the final strategy summary."

    def _confirm_save_instruction(self):
        return (
            "[SAVE NOW: Output ONLY a JSON block calling create_and_save_mlh_strategy. "
            "Use ALL field values from the preview tables above. "
            "Format exactly: {\"tool\": \"create_and_save_mlh_strategy\", \"arguments\": {\"strategy_json\": {...all fields including legs array...}}}]"
        )

    def _confirm_retry_msg_process(self):
        return (
            "You must output the JSON tool call block now. No explanations. Just this:\n"
            "{\"tool\": \"create_and_save_mlh_strategy\", \"arguments\": {\"strategy_json\": "
            "{\"strategy_name\": \"...\", \"trading_mode\": \"...\", \"exchange\": \"...\", "
            "\"legs\": [...all legs...], ... all other fields ...}}}"
        )

    def _confirm_retry_msg_stream(self):
        return (
            "Generate the JSON tool call block now. Output only:\n"
            "{\"tool\": \"create_and_save_mlh_strategy\", \"arguments\": {\"strategy_json\": {...}}}"
        )

    def _save_success_process(self, content, json_str, args, tool_result):
        clean_summary = re.sub(r'\{.*\}', '', content, flags=re.DOTALL).strip()
        if not clean_summary:
            clean_summary = content
        return clean_summary + "\n\n**Strategy Saved Successfully.**"


# Singleton instance
mlh_orchestrator = MLHOrchestrator()


# ── RES ────────────────────────────────────────────────────────────────────────

class RESOrchestrator(BaseOrchestrator):

    def __init__(self):
        super().__init__()
        self.system_prompt = RES_SYSTEM_PROMPT

    def _retriever(self):            return common_retriever
    def _handler(self):              return res_handler
    def _context_label(self):        return "Relevant Documentation Context"
    def _save_tool_name(self):       return "create_and_save_res_strategy"
    def _module_prefix(self):        return "RES"

    def _temperature(self):          return 0.1
    def _final_temperature(self):    return None
    def _null_content_check(self):   return False
    def _has_direct_yield(self):     return True
    def _debug_json_str(self):       return True

    def _tool_whitelist(self):
        return [
            "create_and_save_res_strategy", "res_validate_strategy", "res_get_validation_rules",
            "get_my_strategies", "delete_strategy", "get_strategy_record",
            "modify_strategy", "rename_strategy", "get_balance",
            "get_backtest_options", "run_backtest", "get_backtest_result",
            "get_deploy_options", "deploy_strategy", "undeploy_strategy",
        ]

    def _strategy_json_wrap_keys(self):
        return {"create_and_save_res_strategy", "res_validate_strategy"}

    def _status_messages(self):
        return {
            "create_and_save_res_strategy": "Deploying scalping strategy to Market Maya...",
            "get_my_strategies":            "Fetching your strategies...",
            "delete_strategy":              "Deleting strategy...",
            "get_strategy_record":          "Fetching strategy record...",
            "modify_strategy":              "Saving changes...",
            "rename_strategy":              "Renaming strategy...",
            "get_balance":                  "Fetching balance...",
            "get_backtest_options":         "Fetching backtest options...",
            "run_backtest":                 "Running backtest (this may take 10–30 seconds)...",
            "get_backtest_result":          "Fetching backtest results...",
            "get_deploy_options":           "Fetching deploy options...",
            "deploy_strategy":              "Deploying strategy to Market Maya...",
            "undeploy_strategy":            "Undeploying strategy...",
        }

    def _max_turns_msg(self):
        return "Please provide the final strategy summary and ask for save confirmation."

    def _confirm_save_instruction(self):
        return (
            "[SAVE NOW: Output ONLY a JSON block calling create_and_save_res_strategy. "
            "Use ALL field values from the preview tables above. "
            "Format exactly: {\"tool\": \"create_and_save_res_strategy\", \"arguments\": {\"strategy_json\": {...all fields...}}}]"
        )

    def _process_error_msgs(self):
        return {
            "credits": "⚠️ **AI service unavailable**: Insufficient credits. Please top up and try again.",
            "auth":    "⚠️ **Authentication error**: Invalid Runware API key.",
            "rate":    "⚠️ **Rate limit reached**: Please wait a moment and try again.",
            "conn":    "⚠️ **Connection error**: Could not reach the AI service.",
        }

    def _stream_error_msgs(self):
        return {
            "credits": "⚠️ **AI service unavailable**: Insufficient credits.",
            "auth":    "⚠️ **Authentication error**: Invalid Runware API key.",
            "rate":    "⚠️ **Rate limit reached**: Please wait a moment.",
            "conn":    "⚠️ **Connection error**: Could not reach the AI service.",
        }

    def _confirm_retry_msg_process(self):
        return (
            "You must output the JSON tool call block now. No explanations. Just this:\n"
            "{\"tool\": \"create_and_save_res_strategy\", \"arguments\": {\"strategy_json\": "
            "{\"strategy_name\": \"...\", \"main_exchange\": \"...\", \"main_segment\": \"...\", "
            "\"main_symbol\": \"...\", ... all other fields from the preview ...}}}"
        )

    def _stream_empty_confirm_msg(self):
        return "⚠️ I'm sorry, I encountered an error while generating the strategy payload. Please try saying 'yes' again."

    def _save_success_process(self, content, json_str, args, tool_result):
        clean_summary = re.sub(r'\{.*\}', '', content, flags=re.DOTALL).strip()
        if not clean_summary:
            clean_summary = content
        strategy_name = args.get("strategy_json", {}).get("strategy_name", "Unknown")
        api_data = tool_result.get("data", [])
        deploy_id = api_data[0].get("id", "N/A") if isinstance(api_data, list) and api_data else "N/A"
        return (
            f"{clean_summary}\n\n✅ **Strategy Saved Successfully!**\n\n"
            f"| Detail | Value |\n"
            f"| :--- | :--- |\n"
            f"| **Strategy Name** | {strategy_name} |\n"
            f"| **Deployment ID** | {deploy_id} |\n"
            f"| **Status** | Created (Not yet active) |\n\n"
            f"Your strategy has been saved to Market Maya. "
            f"You can now activate it from the Market Maya terminal."
        )

    def _save_success_stream(self, args, tool_result):
        strategy_name = args.get("strategy_json", {}).get("strategy_name", "Unknown")
        api_data = tool_result.get("data", [])
        deploy_id = api_data[0].get("id", "N/A") if isinstance(api_data, list) and api_data else "N/A"
        return (
            f"\n\n✅ **Strategy Saved Successfully!**\n\n"
            f"| Detail | Value |\n"
            f"| :--- | :--- |\n"
            f"| **Strategy Name** | {strategy_name} |\n"
            f"| **Deployment ID** | {deploy_id} |\n"
            f"| **Status** | Created (Not yet active) |\n\n"
            f"Your strategy has been saved to Market Maya. "
            f"You can now activate it from the Market Maya terminal."
        )


# Singleton instance
res_orchestrator = RESOrchestrator()


# ── ISB ────────────────────────────────────────────────────────────────────────

class ISBOrchestrator(BaseOrchestrator):

    def __init__(self):
        super().__init__()
        self.system_prompt = ISB_SYSTEM_PROMPT

    def _retriever(self):            return common_retriever
    def _handler(self):              return isb_handler
    def _context_label(self):        return "Relevant ISB Documentation"
    def _save_tool_name(self):       return "create_and_save_isb_strategy"
    def _module_prefix(self):        return "ISB"

    def _tool_whitelist(self):
        return [
            "create_and_save_isb_strategy", "isb_validate_strategy", "isb_generate_payload",
            "get_my_strategies", "delete_strategy", "get_strategy_record",
            "modify_strategy", "rename_strategy", "get_balance",
            "get_deploy_options", "deploy_strategy", "undeploy_strategy",
        ]

    def _strategy_json_wrap_keys(self):
        return {"create_and_save_isb_strategy", "isb_validate_strategy", "isb_generate_payload"}

    def _status_messages(self):
        return {
            "create_and_save_isb_strategy": "Saving strategy to Market Maya...",
            "get_my_strategies":            "Fetching your strategies...",
            "delete_strategy":              "Deleting strategy...",
            "get_strategy_record":          "Fetching strategy record...",
            "modify_strategy":              "Saving changes...",
            "rename_strategy":              "Renaming strategy...",
            "get_balance":                  "Fetching balance...",
            "get_deploy_options":           "Fetching deploy options...",
            "deploy_strategy":              "Deploying strategy to Market Maya...",
            "undeploy_strategy":            "Undeploying strategy...",
        }

    def _max_turns_msg(self):
        return "Summarise the strategy and ask for save confirmation now."

    def _confirm_save_instruction(self):
        return (
            "[SAVE NOW: Output ONLY a JSON block calling create_and_save_isb_strategy. "
            "Use ALL field values from the preview tables above. "
            "Format exactly: {\"tool\": \"create_and_save_isb_strategy\", \"arguments\": {\"strategy_json\": {...all fields...}}}]"
        )

    def _process_error_msgs(self):
        return {
            "credits": "⚠️ **AI service unavailable**: Insufficient credits. Please top up at app.runware.ai.",
            "auth":    "⚠️ **Authentication error**: Invalid Runware API key. Check your RUNWARE_API_KEY in .env.",
            "rate":    "⚠️ **Rate limit reached**: Too many requests. Please wait a moment and try again.",
            "conn":    "⚠️ **Connection error**: Could not reach the AI service. Check your internet connection.",
        }


# Singleton instance
isb_orchestrator = ISBOrchestrator()


# ── ISE ────────────────────────────────────────────────────────────────────────

class ISEOrchestrator(BaseOrchestrator):

    def __init__(self):
        super().__init__()
        self.system_prompt = ISE_SYSTEM_PROMPT

    def _retriever(self):            return common_retriever
    def _handler(self):              return ise_handler
    def _context_label(self):        return "Relevant ISE Documentation"
    def _save_tool_name(self):       return "create_and_save_ise_strategy"
    def _module_prefix(self):        return "ISE"
    def _confirm_in_stream(self):    return False

    def _tool_whitelist(self):
        return [
            "create_and_save_ise_strategy", "ise_validate_strategy", "ise_generate_payload",
            "get_my_strategies", "delete_strategy", "get_strategy_record",
            "modify_strategy", "rename_strategy", "get_balance",
            "get_backtest_options", "run_backtest", "get_backtest_result",
            "get_deploy_options", "deploy_strategy", "undeploy_strategy",
        ]

    def _strategy_json_wrap_keys(self):
        return {"create_and_save_ise_strategy", "ise_validate_strategy", "ise_generate_payload"}

    def _status_messages(self):
        return {
            "create_and_save_ise_strategy": "Saving strategy to Market Maya...",
            "get_my_strategies":            "Fetching your strategies...",
            "delete_strategy":              "Deleting strategy...",
            "get_strategy_record":          "Fetching strategy record...",
            "modify_strategy":              "Saving changes...",
            "rename_strategy":              "Renaming strategy...",
            "get_balance":                  "Fetching balance...",
            "get_backtest_options":         "Fetching backtest options...",
            "run_backtest":                 "Running backtest (this may take 10–30 seconds)...",
            "get_backtest_result":          "Fetching backtest results...",
            "get_deploy_options":           "Fetching deploy options...",
            "deploy_strategy":              "Deploying strategy to Market Maya...",
            "undeploy_strategy":            "Undeploying strategy...",
        }

    def _max_turns_msg(self):
        return "Summarise the strategy and ask for save confirmation now."

    def _confirm_save_instruction(self):
        return (
            "[SAVE NOW: Output ONLY a JSON block calling create_and_save_ise_strategy. "
            "Use ALL field values from the preview tables above. "
            "Format exactly: {\"tool\": \"create_and_save_ise_strategy\", \"arguments\": {\"strategy_json\": {...all fields...}}}]"
        )

    def _process_error_msgs(self):
        return {
            "credits": "⚠️ **AI service unavailable**: Insufficient credits. Please top up at app.runware.ai.",
            "auth":    "⚠️ **Authentication error**: Invalid Runware API key. Check your RUNWARE_API_KEY in .env.",
            "rate":    "⚠️ **Rate limit reached**: Too many requests. Please wait a moment and try again.",
            "conn":    "⚠️ **Connection error**: Could not reach the AI service. Check your internet connection.",
        }


# Singleton instance
ise_orchestrator = ISEOrchestrator()
