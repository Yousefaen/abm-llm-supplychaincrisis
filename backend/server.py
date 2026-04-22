"""FastAPI server wrapping the Mesa supply-chain model."""
from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents import get_recent_errors
from debug_session import dbg_log
from model import SupplyChainModel

# ---------------------------------------------------------------------------
# Global model instance (in-memory, just like the spec says)
# ---------------------------------------------------------------------------
_model: SupplyChainModel | None = None
_lock = asyncio.Lock()


def _get_model() -> SupplyChainModel:
    global _model
    if _model is None:
        _model = SupplyChainModel(temperature=1.0)
    return _model


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ResetRequest(BaseModel):
    temperature: float = 1.0
    seed: int | None = None


class StepResponse(BaseModel):
    status: str
    round: int
    total_rounds: int
    event: str
    agents: dict[str, Any]
    decisions: list[dict[str, Any]]
    metrics: dict[str, Any]
    total_cost: float


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # region agent log
    m = _get_model()
    dbg_log(
        "server.py:lifespan",
        "app_startup_model_ready",
        {"agent_count": len(m.agents_map), "time": float(m.time)},
        "H1",
    )
    # endregion
    yield

app = FastAPI(title="Supply Chain ABM Simulator", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/reset")
async def reset_simulation(req: ResetRequest | None = None):
    global _model
    async with _lock:
        temp = req.temperature if req else 1.0
        seed = req.seed if req else None
        _model = SupplyChainModel(temperature=temp, seed=seed)
        st = _model.get_full_state()
        # region agent log
        dbg_log(
            "server.py:reset_simulation",
            "reset_ok",
            {
                "temperature": temp,
                "seed_set": seed is not None,
                "agents": len(st.get("agents", {})),
                "status": st.get("status"),
            },
            "H1",
        )
        # endregion
        return st


@app.post("/api/step")
async def run_step():
    """Run one round of the simulation. Returns the full round summary."""
    async with _lock:
        model = _get_model()
        if model.status == "complete":
            raise HTTPException(400, "Simulation already complete. Reset first.")
        # region agent log
        dbg_log(
            "server.py:run_step",
            "step_begin",
            {"model_time_before": float(model.time), "status": model.status},
            "H1",
        )
        # endregion
        try:
            result = await asyncio.to_thread(model.advance_quarter)
        except Exception as exc:
            # region agent log
            dbg_log(
                "server.py:run_step",
                "step_exception",
                {"exc_type": type(exc).__name__},
                "H1",
            )
            # endregion
            raise
        # region agent log
        dbg_log(
            "server.py:run_step",
            "step_ok",
            {
                "round": result.get("round"),
                "status": result.get("status"),
                "decisions_len": len(result.get("decisions", [])),
                "agents_len": len(result.get("agents", {})),
            },
            "H2",
        )
        # endregion
        return result


@app.post("/api/step/stream")
async def run_step_stream():
    """Run one round and stream agent decisions as SSE events.

    Events are pushed as each agent decides (via a thread-safe callback from
    the worker thread), not batched at round end. A heartbeat comment is
    sent on idle so intermediate proxies (Vercel, Cloudflare) don't close
    the connection during long Sonnet calls.
    """
    import json
    import traceback

    HEARTBEAT_SECONDS = 10.0

    async def event_stream():
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def on_decision(entry: dict[str, Any]) -> None:
            # Fires from the worker thread inside model._emit_decision.
            # Marshal the entry onto the asyncio event loop safely.
            try:
                loop.call_soon_threadsafe(queue.put_nowait, ("decision", entry))
            except RuntimeError:
                pass  # loop closed — stream was aborted

        async with _lock:
            model = _get_model()
            if model.status == "complete":
                yield f"data: {json.dumps({'type': 'error', 'message': 'complete'})}\n\n"
                return

            # region agent log
            dbg_log(
                "server.py:run_step_stream",
                "stream_step_locked",
                {"model_time": float(model.time)},
                "H5",
            )
            # endregion

            async def run_round() -> None:
                try:
                    result = await asyncio.to_thread(
                        model.advance_quarter, on_decision
                    )
                    queue.put_nowait(("done", result))
                except Exception as exc:
                    # region agent log
                    dbg_log(
                        "server.py:run_step_stream",
                        "stream_step_exception",
                        {
                            "exc_type": type(exc).__name__,
                            "exc_msg": str(exc)[:500],
                        },
                        "H1",
                    )
                    # endregion
                    queue.put_nowait((
                        "error",
                        {
                            "exc_type": type(exc).__name__,
                            "message": str(exc)[:500],
                            "traceback": traceback.format_exc()[-2000:],
                        },
                    ))

            round_task = asyncio.create_task(run_round())

            try:
                while True:
                    try:
                        kind, payload = await asyncio.wait_for(
                            queue.get(), timeout=HEARTBEAT_SECONDS,
                        )
                    except asyncio.TimeoutError:
                        # SSE comment line — ignored by clients but keeps
                        # proxies from idling the connection closed.
                        yield ": keepalive\n\n"
                        continue

                    if kind == "decision":
                        dec = payload
                        yield (
                            "data: "
                            + json.dumps({
                                "type": "agent_decided",
                                "agent_id": dec["agent_id"],
                                "tier": dec["tier"],
                                "role": dec.get("role", ""),
                                "decision": dec["decision"],
                            })
                            + "\n\n"
                        )
                    elif kind == "done":
                        result = payload
                        yield (
                            "data: "
                            + json.dumps({
                                "type": "round_complete",
                                "round": result["round"],
                                "total_rounds": result["total_rounds"],
                                "event": result["event"],
                                "agents": result["agents"],
                                "metrics": result["metrics"],
                                "total_cost": result["total_cost"],
                                "status": result["status"],
                            })
                            + "\n\n"
                        )
                        break
                    elif kind == "error":
                        yield (
                            "data: "
                            + json.dumps({
                                "type": "error",
                                "message": payload.get("message", "unknown"),
                                "exc_type": payload.get("exc_type"),
                                "traceback": payload.get("traceback"),
                            })
                            + "\n\n"
                        )
                        break
            finally:
                # Make sure the worker thread has settled before releasing
                # the lock — prevents a second /api/step overlapping with
                # an in-flight advance_quarter.
                try:
                    await round_task
                except Exception:
                    pass

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/state")
async def get_state():
    async with _lock:
        model = _get_model()
        return model.get_full_state()


@app.get("/api/history")
async def get_history():
    async with _lock:
        model = _get_model()
        return model.get_history()


@app.get("/api/debug/errors")
async def get_debug_errors():
    """Return recent LLM errors for diagnostics."""
    return {"errors": get_recent_errors(), "count": len(get_recent_errors())}


if __name__ == "__main__":
    import uvicorn

    # Default 8010: port 8000 is often blocked on Windows (Hyper-V / excluded ranges → WinError 10013).
    _port = int(os.environ.get("PORT", "8010"))
    _host = os.environ.get("HOST", "127.0.0.1")
    uvicorn.run("server:app", host=_host, port=_port, reload=True)
