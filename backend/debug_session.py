"""Session debug NDJSON logger (debug mode)."""
from __future__ import annotations

import json
import os
import time

_SESSION = "874682"
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_PATH = os.path.join(_ROOT, "debug-874682.log")


def dbg_log(
    location: str,
    message: str,
    data: dict | None = None,
    hypothesis_id: str = "",
    run_id: str = "",
) -> None:
    # region agent log
    entry = {
        "sessionId": _SESSION,
        "timestamp": int(time.time() * 1000),
        "location": location,
        "message": message,
        "data": data or {},
        "hypothesisId": hypothesis_id,
        "runId": run_id,
    }
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except OSError:
        pass
    # endregion
