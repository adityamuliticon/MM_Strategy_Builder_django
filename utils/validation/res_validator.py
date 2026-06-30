"""RES strategy validator — checks required fields for scalping/jobbing strategy configuration."""

from utils.validation.base_validator import BaseValidator


class RESValidator(BaseValidator):

    def validate_strategy(self, strategy_json):
        errors = []

        if not strategy_json.get("strategy_name", "").strip():
            errors.append("strategy_name is required.")

        average_value = strategy_json.get("average_value", 0)
        try:
            if float(average_value) <= 0:
                errors.append("average_value must be greater than 0.")
        except (TypeError, ValueError):
            errors.append("average_value must be a positive number.")

        lot = strategy_json.get("lot", 0)
        try:
            if int(lot) <= 0:
                errors.append("lot must be a positive integer.")
        except (TypeError, ValueError):
            errors.append("lot must be a positive integer.")

        is_trail_sl = strategy_json.get("is_trail_sl", False)
        reset_cycle_by_master_tpsl = strategy_json.get("reset_cycle_by_master_tpsl", False)
        if is_trail_sl and not reset_cycle_by_master_tpsl:
            errors.append("Trail SL requires 'reset_cycle_by_master_tpsl' to be enabled.")

        is_auto_rollover = strategy_json.get("is_auto_rollover", False)
        is_intraday = strategy_json.get("is_intraday", True)
        if is_auto_rollover and is_intraday:
            errors.append("Auto Rollover is only allowed in Positional (is_intraday=false) mode.")

        entry_time = strategy_json.get("intraday_entry_time", "09:20")
        exit_time = strategy_json.get("intraday_exit_time", "15:00")
        if entry_time and exit_time and entry_time >= exit_time:
            errors.append("intraday_entry_time must be before intraday_exit_time.")

        return errors


res_validator = RESValidator()
