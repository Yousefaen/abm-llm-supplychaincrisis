"""Shared types + paths for the experiment registry.

Layout under repo-root ``evals/``:

  evals/
    index.md                          -- auto-generated ledger
    <experiment_id>/
      meta.json                       -- config + git context + summary
      run.json.gz                     -- raw per-round dump (gzipped)
      report.md                       -- auto-generated per-run report

Experiment IDs follow ``<YYYY-MM-DD>_<short-desc>`` so they sort lexically
by date and read naturally (e.g. ``2026-04-22_baseline``).

Both the run script (_eval_run.py) and the report tool (_eval_report.py)
go through this module so the path conventions and meta schema stay in
one place.
"""

from __future__ import annotations

import gzip
import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
EVALS_DIR = REPO_ROOT / "evals"

_ID_OK = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}_[a-z0-9-]+$")


def make_experiment_id(short_desc: str, date: datetime | None = None) -> str:
    """Compose an experiment id from today's date + a slug.  Slug is
    lower-cased and reduced to ``[a-z0-9-]+`` so paths stay portable."""
    d = (date or datetime.now()).strftime("%Y-%m-%d")
    slug = re.sub(r"[^a-z0-9]+", "-", short_desc.lower()).strip("-") or "run"
    return f"{d}_{slug}"


def validate_experiment_id(eid: str) -> None:
    if not _ID_OK.match(eid):
        raise ValueError(
            f"experiment id {eid!r} must match YYYY-MM-DD_<slug> "
            f"with slug in [a-z0-9-]+"
        )


def experiment_dir(eid: str) -> Path:
    validate_experiment_id(eid)
    return EVALS_DIR / eid


def list_experiments() -> list[str]:
    if not EVALS_DIR.exists():
        return []
    return sorted(
        p.name for p in EVALS_DIR.iterdir()
        if p.is_dir() and _ID_OK.match(p.name)
    )


# ---------------------------------------------------------------------------
# Meta schema
# ---------------------------------------------------------------------------
@dataclass
class GitContext:
    branch: str
    commit_short: str
    dirty: bool


@dataclass
class RunConfig:
    seed: int | None
    temperature: float
    total_rounds: int
    phase_concurrency: int
    scenario: str
    persona_variant: str = "hand-crafted"  # "hand-crafted" | "auto-fy<year>" | "auto-latest"


@dataclass
class RunSummary:
    wall_clock_sec: float
    total_cost_usd: float
    rounds_completed: int
    error_count: int


@dataclass
class ExperimentMeta:
    experiment_id: str
    label: str                  # short human description
    created_at: str             # ISO 8601
    git: GitContext
    config: RunConfig
    summary: RunSummary
    notes: str = ""


# ---------------------------------------------------------------------------
# Git context
# ---------------------------------------------------------------------------
def capture_git_context() -> GitContext:
    """Best-effort read of branch, short commit, and dirty status.  If git
    isn't available or repo is in an odd state, return placeholders rather
    than crashing the run."""
    def _git(*args: str) -> str:
        try:
            return subprocess.check_output(
                ["git", *args], cwd=REPO_ROOT,
                stderr=subprocess.DEVNULL, timeout=5,
            ).decode("utf-8", errors="replace").strip()
        except Exception:
            return ""

    branch = _git("rev-parse", "--abbrev-ref", "HEAD") or "?"
    commit = _git("rev-parse", "--short", "HEAD") or "?"
    status = _git("status", "--porcelain")
    return GitContext(branch=branch, commit_short=commit, dirty=bool(status))


# ---------------------------------------------------------------------------
# Read / write
# ---------------------------------------------------------------------------
def write_meta(eid: str, meta: ExperimentMeta) -> Path:
    d = experiment_dir(eid)
    d.mkdir(parents=True, exist_ok=True)
    p = d / "meta.json"
    p.write_text(json.dumps(asdict(meta), indent=2), encoding="utf-8")
    return p


def read_meta(eid: str) -> dict[str, Any]:
    p = experiment_dir(eid) / "meta.json"
    return json.loads(p.read_text(encoding="utf-8"))


def write_run_data(eid: str, data: dict[str, Any]) -> Path:
    d = experiment_dir(eid)
    d.mkdir(parents=True, exist_ok=True)
    p = d / "run.json.gz"
    with gzip.open(p, "wt", encoding="utf-8") as f:
        json.dump(data, f, default=str)
    return p


def read_run_data(eid: str) -> dict[str, Any]:
    p = experiment_dir(eid) / "run.json.gz"
    if not p.exists():
        # Fallback for migrated runs that came in as plain .json
        plain = experiment_dir(eid) / "run.json"
        if plain.exists():
            return json.loads(plain.read_text(encoding="utf-8"))
        raise FileNotFoundError(f"No run data found for {eid}")
    with gzip.open(p, "rt", encoding="utf-8") as f:
        return json.load(f)


def write_report(eid: str, markdown: str) -> Path:
    d = experiment_dir(eid)
    d.mkdir(parents=True, exist_ok=True)
    p = d / "report.md"
    p.write_text(markdown, encoding="utf-8")
    return p


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
