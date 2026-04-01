"""Structured JSON logger for DOE execution scripts.

Usage:
    from logger import get_logger
    log = get_logger("my_script")
    log.info("Processing started", count=42)
    log.warn("Threshold exceeded", value=95, limit=80)
    log.error("Failed to connect", host="api.example.com")

Output (one JSON object per line):
    {"level": "info", "message": "Processing started", "context": {"script": "my_script", "count": 42}, "timestamp": "2026-04-01T12:00:00Z"}
"""

import json
import sys
from datetime import datetime, timezone


class Logger:
    """Structured JSON logger that outputs one JSON line per log call."""

    def __init__(self, script_name: str) -> None:
        self.script_name = script_name

    def _emit(self, level: str, message: str, **context: object) -> None:
        entry = {
            "level": level,
            "message": message,
            "context": {"script": self.script_name, **context},
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        line = json.dumps(entry, default=str)
        dest = sys.stderr if level == "error" else sys.stdout
        print(line, file=dest, flush=True)

    def info(self, message: str, **context: object) -> None:
        self._emit("info", message, **context)

    def warn(self, message: str, **context: object) -> None:
        self._emit("warn", message, **context)

    def error(self, message: str, **context: object) -> None:
        self._emit("error", message, **context)

    def debug(self, message: str, **context: object) -> None:
        self._emit("debug", message, **context)


def get_logger(script_name: str) -> Logger:
    """Create a structured logger for the given script."""
    return Logger(script_name)


if __name__ == "__main__":
    # Quick smoke test
    log = get_logger("logger_test")
    log.info("Logger initialised", version="1.0.0")
    log.warn("Example warning", threshold=80)
    log.error("Example error", detail="something broke")
    log.debug("Debug trace", step=3)
