
import sys
import json
import datetime
from typing import Any, Dict
from core.config.config import get_log_level

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

class JSONFormatter:
    @staticmethod
    def format(record: Dict[str, Any]) -> str:
        return json.dumps(record, separators=(",", ":"), sort_keys=True)

class StdoutHandler:
    def emit(self, message: str):
        print(message, file=sys.stdout)

class Logger:
    def __init__(self, level: str = None, handler=None, formatter=None):
        self.level = (level or get_log_level()).upper()
        self.handler = handler or StdoutHandler()
        self.formatter = formatter or JSONFormatter()

    def _should_log(self, level: str) -> bool:
        return LOG_LEVELS.index(level) >= LOG_LEVELS.index(self.level)

    def _log(self, level: str, msg: str, **kwargs):
        if not self._should_log(level):
            return
        record = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": level,
            "message": msg,
        }
        # Separate extra fields
        for k, v in kwargs.items():
            record[k] = v
        self.handler.emit(self.formatter.format(record))

    def debug(self, msg: str, **kwargs):
        self._log("DEBUG", msg, **kwargs)

    def info(self, msg: str, **kwargs):
        self._log("INFO", msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self._log("WARNING", msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self._log("ERROR", msg, **kwargs)

    def critical(self, msg: str, **kwargs):
        self._log("CRITICAL", msg, **kwargs)
