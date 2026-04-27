"""One-shot migration: existing _eval_run_*.json files into the new registry.

Maps the three pre-registry runs to commits we have in git history and
synthesises meta.json for each, then drops the raw JSON into the registry
as run.json.gz and writes report.md.

Run once after the registry layout is in place; subsequent runs go through
_eval_run.py directly.
"""

from __future__ import annotations

import json
from pathlib import Path

from _eval_registry import (
    EVALS_DIR,
    ExperimentMeta,
    GitContext,
    RunConfig,
    RunSummary,
    experiment_dir,
    now_iso,
    write_meta,
    write_run_data,
    write_report,
)
from _eval_report import render_index, render_single_report

BACKEND_DIR = Path(__file__).parent

# (json_filename, experiment_id, label, commit, notes, persona_variant)
MIGRATIONS = [
    (
        "_eval_run_before.json",
        "2026-04-22_baseline",
        "baseline",
        "9fc5f60",
        "Original eval baseline — before scenario prompt rewrite. "
        "Documented in evals/run_2026-04-22.md.",
        "hand-crafted",
    ),
    (
        "_eval_run_after.json",
        "2026-04-22_scenario-rewrite",
        "scenario-rewrite",
        "7305d0a",
        "After rewriting SCENARIO_EVENTS to remove outcome descriptions "
        "(narrative-leakage fix). Pair with 2026-04-22_baseline.",
        "hand-crafted",
    ),
    (
        "_eval_run_rebalanced.json",
        "2026-04-22_capacity-rebalance",
        "capacity-rebalance",
        "a853e9d",
        "After rebalancing AGENT_SPECS capacities to approximate real "
        "auto-semi ratios. Pair with 2026-04-22_scenario-rewrite.",
        "hand-crafted",
    ),
]


def migrate_one(
    json_filename: str, eid: str, label: str, commit: str,
    notes: str, persona_variant: str,
) -> None:
    src = BACKEND_DIR / json_filename
    if not src.exists():
        print(f"  [{eid}] source {json_filename} missing — skip")
        return

    data = json.loads(src.read_text(encoding="utf-8"))
    meta_in = data.get("meta", {})
    rounds = data.get("per_round", [])

    # Run-level error_count: take the highest cumulative count seen across
    # rounds (matches what the rolling buffer reports at end-of-run).
    err_max = max((r.get("error_count", 0) for r in rounds), default=0)

    meta = ExperimentMeta(
        experiment_id=eid,
        label=label,
        created_at=now_iso(),
        git=GitContext(branch="main", commit_short=commit, dirty=False),
        config=RunConfig(
            seed=meta_in.get("seed"),
            temperature=meta_in.get("temperature", 1.0),
            total_rounds=meta_in.get("total_rounds", len(rounds)),
            phase_concurrency=meta_in.get("phase_concurrency", 5),
            scenario=meta_in.get("scenario_name", "The Great Semiconductor Shortage"),
            persona_variant=persona_variant,
        ),
        summary=RunSummary(
            wall_clock_sec=float(meta_in.get("total_elapsed_sec", 0)),
            total_cost_usd=float(meta_in.get("total_cost_usd", 0)),
            rounds_completed=len(rounds),
            error_count=err_max,
        ),
        notes=notes,
    )

    write_meta(eid, meta)
    write_run_data(eid, data)
    md = render_single_report(eid)
    write_report(eid, md)
    print(f"  [{eid}] migrated -> {experiment_dir(eid).relative_to(BACKEND_DIR.parent)}")


def main() -> None:
    EVALS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Migrating {len(MIGRATIONS)} legacy runs into {EVALS_DIR.relative_to(BACKEND_DIR.parent)}/\n")
    for args in MIGRATIONS:
        migrate_one(*args)

    # Regenerate the index
    idx = EVALS_DIR / "index.md"
    idx.write_text(render_index(), encoding="utf-8")
    print(f"\nwrote {idx.relative_to(BACKEND_DIR.parent)}")


if __name__ == "__main__":
    main()
