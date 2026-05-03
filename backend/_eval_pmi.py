"""PMI / GSCPI validation harness — correlate sim emergent metrics against
real public supply-chain stress indices for the 2020Q1-2022Q2 window.

Why this exists
---------------
The simulation's scenario events follow the actual 2020-2022 chip-shortage
calendar (COVID Q1 2020 -> Texas storm Q1 2021 -> Renesas fire Q3 2021 ->
CHIPS Act Q4 2021 -> Russia/Ukraine Q1 2022).  We can therefore ask:
does the simulation's *emergent* supply-chain stress signal correlate
with the *real* supply-chain stress signal over the same calendar
window?  This is the post-hoc external-validity claim that's hard to
make about plausibility-only LLM-agent simulators (e.g. MiroFish).

Primary external signal
-----------------------
NY Fed Global Supply Chain Pressure Index (GSCPI) — a composite of 27
supply-chain stress indicators, monthly, freely published, peer-reviewed.
We average the three monthly GSCPI values per calendar quarter to get a
quarterly score, then compare to the corresponding sim round.

Why not live-fetch from FRED
----------------------------
fred.stlouisfed.org times out / connection-resets when hit from urllib
on at least some networks (likely UA-based bot mitigation).  Rather than
ship a brittle live-fetch path, we expect the user to download the
GSCPI CSV manually (one click) and drop it at
``backend/data/fred_gscpi.csv``.  The download URL is in the README at
``backend/data/README.md``.

Sim-side signals
----------------
Three candidate stress proxies, each averaged across all 9 agents per
round:
  - 1 - average fill_rate across non-foundry tiers (low fill = high stress)
  - normalized average price index across all tiers (high prices = stress)
  - panic-emotion fraction (panicked + anxious agents / total)

We compute Pearson correlation of each sim metric against the GSCPI
series, plus a composite-z-score correlation.  Output is a markdown
report at ``evals/pmi_validation_<experiment_id>.md``.

Usage
-----
  python _eval_pmi.py <experiment_id>

Example:
  python _eval_pmi.py 2026-04-26_personas-fy2019-full
"""

from __future__ import annotations

import csv
import statistics
import sys
from collections import Counter
from pathlib import Path

from _eval_registry import (
    EVALS_DIR,
    REPO_ROOT,
    experiment_dir,
    read_meta,
    read_run_data,
)

# Sim round -> calendar quarter mapping.  Pinned to the scenario events
# encoded in scenarios.py:SCENARIO_EVENTS.
ROUND_TO_QUARTER: dict[int, tuple[int, int]] = {
    1:  (2020, 1),
    2:  (2020, 2),
    3:  (2020, 3),
    4:  (2020, 4),
    5:  (2021, 1),
    6:  (2021, 2),
    7:  (2021, 3),
    8:  (2021, 4),
    9:  (2022, 1),
    10: (2022, 2),
}

OEMS = ["ToyotaMotors", "FordAuto", "VolkswagenAG"]
TIER1S = ["BoschAuto", "ContiParts"]
DESIGNERS = ["EuroChip", "AmeriSemi"]
FOUNDRIES = ["TaiwanSemi", "KoreaSilicon"]
NON_FOUNDRY = OEMS + TIER1S + DESIGNERS  # foundries always show 1.0 fill in this sim

GSCPI_CSV_PATH = REPO_ROOT / "backend" / "data" / "fred_gscpi.csv"


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------
def _pearson(xs: list[float], ys: list[float]) -> float | None:
    """Pearson r for two equal-length numeric sequences. Returns None if
    either sequence is constant or lengths mismatch."""
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    sx = statistics.pstdev(xs)
    sy = statistics.pstdev(ys)
    if sx == 0 or sy == 0:
        return None
    mx = statistics.mean(xs)
    my = statistics.mean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / len(xs)
    return cov / (sx * sy)


def _zscore(xs: list[float]) -> list[float]:
    if not xs:
        return []
    mu = statistics.mean(xs)
    sd = statistics.pstdev(xs)
    if sd == 0:
        return [0.0 for _ in xs]
    return [(x - mu) / sd for x in xs]


# ---------------------------------------------------------------------------
# GSCPI loader
# ---------------------------------------------------------------------------
def load_gscpi_quarterly(csv_path: Path) -> dict[tuple[int, int], float]:
    """Read FRED-format GSCPI CSV (DATE,GSCPI columns, monthly cadence) and
    return {(year, quarter): mean_value}.  Missing months (e.g. ``.`` in
    FRED CSVs) are skipped; quarters with <2 valid months are dropped."""
    if not csv_path.exists():
        raise FileNotFoundError(
            f"GSCPI CSV not found at {csv_path}.  Download from "
            f"https://fred.stlouisfed.org/series/GSCPI and place at this path. "
            f"See backend/data/README.md for instructions."
        )

    monthly: dict[tuple[int, int], float] = {}
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        date_col = next((c for c in reader.fieldnames or [] if c.lower() in ("date", "observation_date")), None)
        val_col = next((c for c in reader.fieldnames or [] if c.upper() in ("GSCPI", "VALUE")), None)
        if not date_col or not val_col:
            raise ValueError(f"Could not find DATE/GSCPI columns in {csv_path}; got {reader.fieldnames}")
        for row in reader:
            d = row[date_col]
            v = row[val_col]
            if v in ("", ".", None):
                continue
            try:
                year, month = int(d[:4]), int(d[5:7])
                value = float(v)
            except (ValueError, IndexError):
                continue
            monthly[(year, month)] = value

    # Aggregate to quarterly mean
    quarter_buckets: dict[tuple[int, int], list[float]] = {}
    for (year, month), value in monthly.items():
        q = (month - 1) // 3 + 1
        quarter_buckets.setdefault((year, q), []).append(value)

    return {
        key: statistics.mean(values)
        for key, values in quarter_buckets.items()
        if len(values) >= 2
    }


# ---------------------------------------------------------------------------
# Sim-side stress signals
# ---------------------------------------------------------------------------
def _avg_fill(round_data: dict, ids: list[str]) -> float:
    xs = [round_data["agents"][a]["fill_rate"] for a in ids if a in round_data["agents"]]
    return statistics.mean(xs) if xs else 1.0


def _avg_price(round_data: dict, ids: list[str]) -> float:
    xs = [round_data["agents"][a]["current_price"] for a in ids if a in round_data["agents"]]
    return statistics.mean(xs) if xs else 0.0


def _panic_fraction(round_data: dict) -> float:
    c = Counter(a.get("emotional_state", "?") for a in round_data["agents"].values())
    total = sum(c.values()) or 1
    return (c.get("panicked", 0) + c.get("anxious", 0)) / total


def compute_sim_signals(experiment_id: str) -> dict[str, list[float]]:
    """Return per-round sim signals indexed in round order (R1..R10).

    Keys:
      stress_from_fill -- 1 - mean(non_foundry fill rates)
      stress_from_price -- mean across-tier price index, normalized to z
      stress_from_panic -- panicked+anxious fraction across all 9 agents
      composite_z      -- mean z-score of the three above per round
    """
    data = read_run_data(experiment_id)
    rounds = data["per_round"]

    fill_stress: list[float] = []
    price_avg: list[float] = []
    panic_frac: list[float] = []
    for r in rounds:
        fill_stress.append(1.0 - _avg_fill(r, NON_FOUNDRY))
        # Average across foundry+designer+tier1 prices, normalized later
        prices = [_avg_price(r, ids) for ids in (FOUNDRIES, DESIGNERS, TIER1S)]
        price_avg.append(statistics.mean(prices))
        panic_frac.append(_panic_fraction(r))

    # Z-normalize each signal so they're scale-comparable for the composite
    z_fill = _zscore(fill_stress)
    z_price = _zscore(price_avg)
    z_panic = _zscore(panic_frac)
    composite = [statistics.mean(z) for z in zip(z_fill, z_price, z_panic)]

    return {
        "stress_from_fill": fill_stress,
        "stress_from_price": price_avg,
        "stress_from_panic": panic_frac,
        "composite_z": composite,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def render_report(
    experiment_id: str,
    sim_signals: dict[str, list[float]],
    gscpi_quarterly: dict[tuple[int, int], float],
) -> str:
    meta = read_meta(experiment_id)

    # Build paired series for rounds where we have GSCPI data
    rounds_present = []
    gscpi_aligned = []
    for rn, (year, q) in ROUND_TO_QUARTER.items():
        if (year, q) in gscpi_quarterly:
            rounds_present.append(rn)
            gscpi_aligned.append(gscpi_quarterly[(year, q)])

    out: list[str] = []
    out.append(f"# PMI/GSCPI validation — `{experiment_id}`\n")
    out.append(f"_Experiment label_: {meta.get('label', '')}  ")
    out.append(f"_Persona variant_: `{meta.get('config', {}).get('persona_variant', '?')}`")
    out.append(
        "\nThis report compares the simulation's emergent supply-chain stress "
        "signals against the NY Fed Global Supply Chain Pressure Index "
        "(GSCPI) over the calendar window represented by the scenario "
        "(2020Q1-2022Q2). Pearson correlation coefficients on aligned "
        "quarterly series.\n"
    )
    out.append(
        f"_GSCPI quarters available_: {len(rounds_present)}/{len(ROUND_TO_QUARTER)}  "
        f"_Source_: NY Fed via FRED, series GSCPI. "
        f"https://fred.stlouisfed.org/series/GSCPI\n"
    )

    out.append("## Aligned series\n")
    out.append("| Round | Quarter | GSCPI | sim stress (fill) | sim stress (price) | sim stress (panic) | sim composite-z |")
    out.append("|---|---|---|---|---|---|---|")
    for rn in rounds_present:
        year, q = ROUND_TO_QUARTER[rn]
        gscpi_v = gscpi_quarterly[(year, q)]
        out.append(
            f"| {rn} | {year}Q{q} | {gscpi_v:.2f} | "
            f"{sim_signals['stress_from_fill'][rn-1]:.2f} | "
            f"{sim_signals['stress_from_price'][rn-1]:.2f} | "
            f"{sim_signals['stress_from_panic'][rn-1]:.2f} | "
            f"{sim_signals['composite_z'][rn-1]:+.2f} |"
        )

    out.append("\n## Pearson correlation with GSCPI\n")
    out.append("| Sim signal | Pearson r | n quarters |")
    out.append("|---|---|---|")
    for label, sig_key in [
        ("1 − fill rate (non-foundry)", "stress_from_fill"),
        ("avg price index (z-style)", "stress_from_price"),
        ("panic+anxious fraction", "stress_from_panic"),
        ("composite z-score", "composite_z"),
    ]:
        sig_aligned = [sim_signals[sig_key][rn-1] for rn in rounds_present]
        r = _pearson(sig_aligned, gscpi_aligned)
        r_str = f"{r:+.3f}" if r is not None else "—"
        out.append(f"| {label} | {r_str} | {len(rounds_present)} |")

    out.append("\n## How to read this\n")
    out.append(
        "- **Pearson r near +1**: sim's emergent stress signal rises and "
        "falls in lockstep with the real GSCPI across the 2020-2022 window."
    )
    out.append(
        "- **r near 0**: sim emerges stress on a different timeline than "
        "reality — possibly because architecture, persona priors, or "
        "scenario forcings don't track real conditions tightly."
    )
    out.append(
        "- **r near -1**: sim is anti-correlated with reality — a problem."
    )
    out.append(
        "\nGSCPI itself is a composite of 27 sub-indicators (PMI, "
        "transportation costs, delivery times, etc.).  Correlating against "
        "the composite is the cleanest single-number test; for a deeper "
        "validation the harness can be extended to ISM Supplier Deliveries, "
        "ISM Prices Paid, and ISM Inventories sub-indices once we have an "
        "ISM data subscription."
    )
    return "\n".join(out) + "\n"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    experiment_id = sys.argv[1]

    print(f"loading sim signals for {experiment_id}...")
    sim_signals = compute_sim_signals(experiment_id)

    print(f"loading GSCPI from {GSCPI_CSV_PATH.relative_to(REPO_ROOT)}...")
    gscpi = load_gscpi_quarterly(GSCPI_CSV_PATH)
    print(f"  {len(gscpi)} quarterly observations available")

    md = render_report(experiment_id, sim_signals, gscpi)
    out_path = EVALS_DIR / f"pmi_validation_{experiment_id}.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"wrote {out_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
