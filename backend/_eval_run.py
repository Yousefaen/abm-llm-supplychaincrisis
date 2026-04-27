"""Headless 10-round driver for effectiveness evaluation.

Captures per-round full state, decisions, signals, plans, reflections, phase
timings, token/cost accumulation, and any LLM errors.  Writes a complete
experiment to the registry under ``evals/<experiment_id>/``:

  meta.json        -- config, git context, run summary
  run.json.gz      -- raw per-round dump
  report.md        -- auto-generated analysis (via _eval_report)

Then refreshes ``evals/index.md`` so the new run shows up in the ledger.

Usage:
  python _eval_run.py                 -- auto label "run", today's date
  python _eval_run.py --label foo     -- custom slug, e.g. "personas-fy2019"
  python _eval_run.py --notes "..."   -- free-text notes baked into meta.json
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.chdir(Path(__file__).parent)

# Silence dbg_log before importing anything that uses it, so we don't
# flood stdout with ~30 lines/round * 10 rounds.
import debug_session
debug_session.dbg_log = lambda *a, **kw: None

import model as model_mod
from model import SupplyChainModel
from agents import get_recent_errors
from _eval_registry import (
    EVALS_DIR,
    ExperimentMeta,
    GitContext,
    RunConfig,
    RunSummary,
    capture_git_context,
    experiment_dir,
    make_experiment_id,
    now_iso,
    write_meta,
    write_run_data,
    write_report,
)

SEED = 42
TEMP = 1.0
DEFAULT_TOTAL_ROUNDS = 10

# CLI parsing
_args = list(sys.argv[1:])

def _pop_flag(name: str, default: str | None = None) -> str | None:
    if name in _args:
        i = _args.index(name)
        _args.pop(i)
        if i < len(_args):
            return _args.pop(i)
    return default

label = _pop_flag("--label", "run") or "run"
notes = _pop_flag("--notes", "") or ""
persona_variant = _pop_flag("--persona-variant", "hand-crafted") or "hand-crafted"
TOTAL_ROUNDS = int(_pop_flag("--rounds", str(DEFAULT_TOTAL_ROUNDS)))

eid = make_experiment_id(label)
exp_dir = experiment_dir(eid)
exp_dir.mkdir(parents=True, exist_ok=True)

print(f"experiment id: {eid}")
print(f"output dir:    {exp_dir.relative_to(EVALS_DIR.parent)}")
print(f"PHASE_CONCURRENCY = {model_mod.PHASE_CONCURRENCY}")
print(f"Running {TOTAL_ROUNDS} rounds, seed={SEED}, temperature={TEMP}\n")

m = SupplyChainModel(temperature=TEMP, seed=SEED)
print(f"agents: {list(m.agents_map.keys())}\n")

per_round: list[dict] = []
all_events: list[dict] = []  # flat timeline, all events across all rounds
prior_error_count = 0  # diff against rolling buffer to count only NEW errors this round

t_start_run = time.time()

for round_idx in range(1, TOTAL_ROUNDS + 1):
    events_this_round: list[dict] = []
    t_round_start = time.time()
    cost_before = m.total_cost

    def on_decision(entry: dict, _r=round_idx) -> None:
        evt = {
            "round": _r,
            "t_rel": time.time() - t_round_start,
            "agent_id": entry["agent_id"],
            "tier": entry["tier"],
            "role": entry.get("role", ""),
            "decision": entry.get("decision", {}),
            "input_tokens": entry.get("input_tokens", 0),
            "output_tokens": entry.get("output_tokens", 0),
        }
        events_this_round.append(evt)
        all_events.append(evt)

    try:
        result = m.advance_quarter(on_decision)
    except Exception as exc:
        print(f"FAIL at round {round_idx}: {type(exc).__name__}: {exc}")
        import traceback
        traceback.print_exc(limit=5)
        break

    elapsed = time.time() - t_round_start
    round_cost = m.total_cost - cost_before

    # get_recent_errors() returns the global rolling buffer.  Diff against the
    # count we observed at end of the previous round so error_count and
    # errors_sample reflect only NEW failures this round (fixes the
    # carry-forward bug flagged in evals/run_2026-04-22.md).
    all_errors_now = get_recent_errors()
    new_errors = all_errors_now[prior_error_count:]
    prior_error_count = len(all_errors_now)

    # Snapshot state post-round (metrics, per-agent KPIs, memory counts)
    state = m.get_full_state()

    # Extract per-agent snapshot with just the numbers we need for analysis
    agents_snap = {}
    for aid, a in state["agents"].items():
        agents_snap[aid] = {
            "tier": a["tier"],
            "inventory": a["inventory"],
            "capacity": a["capacity"],
            "current_price": a["current_price"],
            "fill_rate": a["fill_rate"],
            "revenue": a["revenue"],
            "costs": a["costs"],
            "profit": a["profit"],
            "round_revenue": a["round_revenue"],
            "round_costs": a["round_costs"],
            "emotional_state": a["emotional_state"],
            "affect": a["affect"],
            "trust_scores": a["trust_scores"],
            "effective_quarterly_need": a["effective_quarterly_need"],
            "memory_count": a["memory_count"],
            "reflections": a["reflections"],
            "parse_failure_count": a["parse_failure_count"],
            "current_decision": a["current_decision"],
        }

    per_round.append({
        "round": round_idx,
        "event": state.get("current_event", ""),
        "elapsed_sec": elapsed,
        "round_cost_usd": round_cost,
        "cumulative_cost_usd": m.total_cost,
        "metrics": state.get("metrics"),
        "market_state": state.get("market_state"),
        "agents": agents_snap,
        "events": events_this_round,
        "status": state.get("status"),
        "error_count": len(new_errors),
        "errors_sample": new_errors,
    })

    print(
        f"  round {round_idx:2d}/{TOTAL_ROUNDS}  "
        f"{elapsed:5.1f}s  "
        f"${round_cost:.4f}  "
        f"events={len(events_this_round):2d}  "
        f"errors={len(new_errors)}  "
        f"status={result.get('status')}"
    )

total_elapsed = time.time() - t_start_run
print(f"\n=== run complete: {total_elapsed:.1f}s total, ${m.total_cost:.4f} total ===")

# ----- write to registry -----
run_data = {
    "meta": {
        "seed": SEED,
        "temperature": TEMP,
        "total_rounds": TOTAL_ROUNDS,
        "phase_concurrency": model_mod.PHASE_CONCURRENCY,
        "total_elapsed_sec": total_elapsed,
        "total_cost_usd": m.total_cost,
        "scenario_name": "The Great Semiconductor Shortage",
    },
    "per_round": per_round,
}

total_errors = sum(r["error_count"] for r in per_round)

meta = ExperimentMeta(
    experiment_id=eid,
    label=label,
    created_at=now_iso(),
    git=capture_git_context(),
    config=RunConfig(
        seed=SEED,
        temperature=TEMP,
        total_rounds=TOTAL_ROUNDS,
        phase_concurrency=model_mod.PHASE_CONCURRENCY,
        scenario="The Great Semiconductor Shortage",
        persona_variant=persona_variant,
    ),
    summary=RunSummary(
        wall_clock_sec=total_elapsed,
        total_cost_usd=m.total_cost,
        rounds_completed=len(per_round),
        error_count=total_errors,
    ),
    notes=notes,
)

write_meta(eid, meta)
write_run_data(eid, run_data)

# Generate the per-run report and refresh the index
from _eval_report import render_index, render_single_report

write_report(eid, render_single_report(eid))
(EVALS_DIR / "index.md").write_text(render_index(), encoding="utf-8")

print(f"\nwrote {experiment_dir(eid).relative_to(EVALS_DIR.parent)}/")
print(f"  meta.json")
print(f"  run.json.gz")
print(f"  report.md")
print(f"refreshed evals/index.md")
