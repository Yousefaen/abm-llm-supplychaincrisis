"""Session debug NDJSON logger (debug mode).

Writes to a local NDJSON file AND mirrors every entry to stdout. The file
is convenient for local inspection but is ephemeral in containerised
deployments (Railway, Fly, etc.) — stdout is the only channel those hosts
capture, so every dbg_log call must also land there or incidents become
invisible in production.
"""
from __future__ import annotations

import json
import os
import sys
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
    serialized = json.dumps(entry, default=str)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(serialized + "\n")
    except OSError:
        pass
    try:
        print(f"[dbg] {serialized}", file=sys.stdout, flush=True)
    except Exception:
        pass
    # endregion
