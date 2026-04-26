"""Generate markdown reports from registry experiments.

Three modes:

  python _eval_report.py <id>                   -- write evals/<id>/report.md
  python _eval_report.py compare <id_a> <id_b>  -- write evals/compare_<a>_vs_<b>.md
  python _eval_report.py index                  -- regenerate evals/index.md

The single-run report mirrors the sections of the legacy _eval_analyze.py
script (emergence / behavior / engineering) but emits clean markdown so it
can be browsed on GitHub.  The compare report mirrors _eval_compare.py.
"""

from __future__ import annotations

import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from _eval_registry import (
    EVALS_DIR,
    experiment_dir,
    list_experiments,
    read_meta,
    read_run_data,
    write_report,
)

OEMS = ["ToyotaMotors", "FordAuto", "VolkswagenAG"]
TIER1S = ["BoschAuto", "ContiParts"]
DESIGNERS = ["EuroChip", "AmeriSemi"]
FOUNDRIES = ["TaiwanSemi", "KoreaSilicon"]
ALL_AGENTS = OEMS + TIER1S + DESIGNERS + FOUNDRIES

DEMAND_BY_ROUND = {1: 0.60, 2: 0.50, 3: 0.80, 4: 1.10, 5: 1.25,
                   6: 1.20, 7: 1.15, 8: 1.10, 9: 0.95, 10: 0.75}

# Crisis-vocabulary detector — borrowed from _eval_compare.py
CRISIS_WORDS = [
    r"\bcris[ei]s\b", r"\bshortage\b", r"\bshock\b", r"\bemergency\b",
    r"\bunprecedented\b", r"\bscarcit(?:y|ies)\b", r"\bpanic\b",
    r"\bhoard", r"\bbottleneck\b", r"\bconstraint\b", r"\bdisrupt",
]
CRISIS_RE = re.compile("|".join(CRISIS_WORDS), re.IGNORECASE)


# ---------------------------------------------------------------------------
# Per-run analytics — pure functions, return data structures
# ---------------------------------------------------------------------------
def _tier_avg(round_data: dict, ids: list[str], field: str) -> float:
    xs = [round_data["agents"][a][field] for a in ids if a in round_data["agents"]]
    return statistics.mean(xs) if xs else 0.0


def _order_totals_for_round(round_data: dict) -> dict[str, int]:
    totals: dict[str, int] = {}
    for evt in round_data.get("events", []):
        if evt.get("role") == "buyer":
            orders = (evt.get("decision") or {}).get("orders") or {}
            totals[evt["agent_id"]] = sum(
                int(v) for v in orders.values() if isinstance(v, (int, float))
            )
    return totals


def _crisis_vocab_density(round_data: dict) -> tuple[int, int]:
    """Returns (hits, total) for crisis-vocab regex against all LLM-generated
    text fields in this round (reasoning, insights, signal content, plan
    goals/tactics)."""
    texts: list[str] = []
    for evt in round_data.get("events", []):
        dec = evt.get("decision") or {}
        if not isinstance(dec, dict):
            continue
        if dec.get("reasoning"):
            texts.append(dec["reasoning"])
        for ins in dec.get("insights") or []:
            texts.append(str(ins))
        for sig in dec.get("signals") or []:
            if isinstance(sig, dict) and sig.get("content"):
                texts.append(sig["content"])
        plan = dec.get("plan") or {}
        if isinstance(plan, dict):
            for g in plan.get("goals") or []:
                texts.append(str(g))
            for t in plan.get("tactics") or []:
                texts.append(str(t))
            if plan.get("risk_assessment"):
                texts.append(str(plan["risk_assessment"]))
    hits = sum(1 for t in texts if CRISIS_RE.search(t))
    return hits, len(texts)


def _affect_means(round_data: dict) -> tuple[float, float]:
    fears: list[float] = []
    stress: list[float] = []
    for a in round_data["agents"].values():
        aff = a.get("affect") or {}
        if isinstance(aff, dict):
            if "fear" in aff:
                fears.append(float(aff.get("fear", 0) or 0))
            if "stress" in aff:
                stress.append(float(aff.get("stress", 0) or 0))
    return (
        statistics.mean(fears) if fears else 0.0,
        statistics.mean(stress) if stress else 0.0,
    )


def _panic_fraction(round_data: dict) -> tuple[int, int]:
    c = Counter(a.get("emotional_state", "?") for a in round_data["agents"].values())
    return c.get("panicked", 0) + c.get("anxious", 0), sum(c.values())


def _signal_counts(round_data: dict) -> Counter:
    c: Counter = Counter()
    for evt in round_data.get("events", []):
        if evt.get("role") == "signaling":
            for s in evt["decision"].get("signals", []) or []:
                c[s.get("signal_type", "?")] += 1
    return c


def _first_crisis_utterance(rounds: list[dict]) -> tuple[int, str, str, str] | None:
    strict = re.compile(r"\b(cris[ei]s|shortage|shock|emergency)\b", re.IGNORECASE)
    for r in rounds:
        rn = r["round"]
        for evt in r.get("events", []):
            dec = evt.get("decision") or {}
            if not isinstance(dec, dict):
                continue
            if dec.get("reasoning") and strict.search(str(dec["reasoning"])):
                return rn, evt["agent_id"], evt.get("role", "?"), str(dec["reasoning"])[:200]
            for ins in dec.get("insights") or []:
                if strict.search(str(ins)):
                    return rn, evt["agent_id"], "reflection", str(ins)[:200]
            for sig in dec.get("signals") or []:
                if isinstance(sig, dict) and sig.get("content") and strict.search(sig["content"]):
                    return rn, evt["agent_id"], "signal", sig["content"][:200]
    return None


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------
def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def _esc(s: Any) -> str:
    """Escape pipe characters so they don't break tables."""
    return str(s).replace("|", "\\|")


# ---------------------------------------------------------------------------
# Single-run report
# ---------------------------------------------------------------------------
def render_single_report(eid: str) -> str:
    meta = read_meta(eid)
    data = read_run_data(eid)
    rounds = data["per_round"]

    out: list[str] = []

    # -- header --
    out.append(f"# {eid} — {meta.get('label', '')}\n")
    out.append(f"_Generated_: {meta.get('created_at', '?')}  ")
    git = meta.get("git", {})
    out.append(
        f"_Branch_: `{git.get('branch','?')}`  "
        f"_Commit_: `{git.get('commit_short','?')}`"
        + ("  _(dirty tree)_" if git.get('dirty') else "")
    )
    cfg = meta.get("config", {})
    out.append(
        f"\n_Config_: seed={cfg.get('seed')}, "
        f"temperature={cfg.get('temperature')}, "
        f"rounds={cfg.get('total_rounds')}, "
        f"concurrency={cfg.get('phase_concurrency')}, "
        f"persona_variant=`{cfg.get('persona_variant','?')}`"
    )
    summ = meta.get("summary", {})
    out.append(
        f"\n_Summary_: wall-clock {summ.get('wall_clock_sec',0):.1f}s, "
        f"cost ${summ.get('total_cost_usd',0):.4f}, "
        f"errors {summ.get('error_count',0)}, "
        f"rounds {summ.get('rounds_completed', len(rounds))}/{cfg.get('total_rounds','?')}\n"
    )
    if meta.get("notes"):
        out.append(f"**Notes:** {meta['notes']}\n")

    # -- 1. Emergence --
    out.append("## 1. Emergence\n")

    # 1a. Order totals + bullwhip
    out.append("### Order totals per OEM (units)\n")
    rows: list[list[str]] = []
    for r in rounds:
        rn = r["round"]
        totals = _order_totals_for_round(r)
        rows.append([
            str(rn), f"{DEMAND_BY_ROUND.get(rn, 1.0):.2f}",
            *(str(totals.get(a, 0)) for a in OEMS),
        ])
    out.append(_md_table(
        ["Round", "Demand×", *OEMS],
        rows,
    ))

    out.append("\n### Bullwhip — stdev of order totals within each tier\n")
    rows = []
    for r in rounds:
        rn = r["round"]
        totals = _order_totals_for_round(r)
        s_oem = statistics.pstdev([totals.get(a, 0) for a in OEMS])
        s_t1 = statistics.pstdev([totals.get(a, 0) for a in TIER1S])
        s_cd = statistics.pstdev([totals.get(a, 0) for a in DESIGNERS])
        rows.append([str(rn), f"{s_oem:.1f}", f"{s_t1:.1f}", f"{s_cd:.1f}"])
    out.append(_md_table(["Round", "OEM σ", "Tier-1 σ", "Designer σ"], rows))

    # 1b. Fill rates
    out.append("\n### Fill rate by tier (1.0 = perfect supply)\n")
    rows = []
    for r in rounds:
        rows.append([
            str(r["round"]),
            f"{_tier_avg(r, OEMS, 'fill_rate'):.2f}",
            f"{_tier_avg(r, TIER1S, 'fill_rate'):.2f}",
            f"{_tier_avg(r, DESIGNERS, 'fill_rate'):.2f}",
            f"{_tier_avg(r, FOUNDRIES, 'fill_rate'):.2f}",
        ])
    out.append(_md_table(["Round", "OEM", "Tier-1", "Designer", "Foundry"], rows))

    # 1c. Prices
    out.append("\n### Average price by tier ($/unit)\n")
    rows = []
    for r in rounds:
        rows.append([
            str(r["round"]),
            f"{_tier_avg(r, FOUNDRIES, 'current_price'):.2f}",
            f"{_tier_avg(r, DESIGNERS, 'current_price'):.2f}",
            f"{_tier_avg(r, TIER1S, 'current_price'):.2f}",
        ])
    out.append(_md_table(["Round", "Foundry", "Designer", "Tier-1"], rows))

    # 1d. Profit distribution (final)
    out.append("\n### Cumulative profit at end of run ($)\n")
    end = rounds[-1]["agents"]
    rows = []
    for a in sorted(ALL_AGENTS, key=lambda x: -end.get(x, {}).get("profit", 0)):
        if a in end:
            rows.append([a, f"{end[a]['profit']:,.0f}"])
    out.append(_md_table(["Agent", "Profit"], rows))

    # -- 2. Behavior --
    out.append("\n## 2. Behavior\n")

    # 2a. Crisis-vocabulary density
    out.append("### Crisis-vocabulary density per round (hits / total LLM texts)\n")
    rows = []
    for r in rounds:
        hits, total = _crisis_vocab_density(r)
        pct = (100.0 * hits / total) if total else 0.0
        rows.append([
            str(r["round"]), f"{DEMAND_BY_ROUND.get(r['round'], 1.0):.2f}",
            f"{hits}/{total}", f"{pct:.0f}%",
        ])
    out.append(_md_table(["Round", "Demand×", "Hits/Total", "%"], rows))

    # 2b. Mean affect (fear, stress)
    out.append("\n### Mean affect intensity per round\n")
    rows = []
    for r in rounds:
        fear, stress = _affect_means(r)
        pp, total = _panic_fraction(r)
        rows.append([
            str(r["round"]),
            f"{fear:.2f}", f"{stress:.2f}",
            f"{pp}/{total}",
        ])
    out.append(_md_table(["Round", "Fear", "Stress", "Panicked+Anxious"], rows))

    # 2c. Signals
    out.append("\n### Signals emitted per round (by type)\n")
    all_types: set[str] = set()
    per_round_sigs: list[Counter] = []
    for r in rounds:
        c = _signal_counts(r)
        all_types |= set(c)
        per_round_sigs.append(c)
    types_sorted = sorted(all_types)
    rows = []
    for r, c in zip(rounds, per_round_sigs):
        rows.append([
            str(r["round"]),
            *(str(c.get(t, 0)) for t in types_sorted),
            str(sum(c.values())),
        ])
    out.append(_md_table(["Round", *types_sorted, "Total"], rows))

    # 2d. First crisis utterance
    fm = _first_crisis_utterance(rounds)
    out.append("\n### First explicit crisis/shortage/shock/emergency utterance\n")
    if fm:
        rn, aid, role, txt = fm
        out.append(f"- **R{rn}**, {aid} ({role}): _{_esc(txt)}_\n")
    else:
        out.append("_No explicit utterance across the run._\n")

    # -- 3. Engineering --
    out.append("\n## 3. Engineering\n")
    out.append("### Per-round wall-clock + cost\n")
    rows = []
    for r in rounds:
        rows.append([
            str(r["round"]),
            f"{r.get('elapsed_sec', 0):.1f}s",
            f"${r.get('round_cost_usd', 0):.4f}",
            str(len(r.get("events", []))),
            str(r.get("error_count", 0)),
        ])
    out.append(_md_table(["Round", "Wall-clock", "Cost", "Events", "Errors"], rows))

    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Compare report
# ---------------------------------------------------------------------------
def render_compare_report(id_a: str, id_b: str) -> str:
    meta_a = read_meta(id_a)
    meta_b = read_meta(id_b)
    data_a = read_run_data(id_a)
    data_b = read_run_data(id_b)
    rounds_a = data_a["per_round"]
    rounds_b = data_b["per_round"]
    n = min(len(rounds_a), len(rounds_b))

    out: list[str] = []
    out.append(f"# Comparison — `{id_a}` vs `{id_b}`\n")
    out.append(f"- **A** ({id_a}): {meta_a.get('label','')}  "
               f"persona=`{meta_a.get('config',{}).get('persona_variant','?')}`  "
               f"commit=`{meta_a.get('git',{}).get('commit_short','?')}`")
    out.append(f"- **B** ({id_b}): {meta_b.get('label','')}  "
               f"persona=`{meta_b.get('config',{}).get('persona_variant','?')}`  "
               f"commit=`{meta_b.get('git',{}).get('commit_short','?')}`\n")

    # Meta side-by-side
    out.append("## Meta\n")
    sa, sb = meta_a.get("summary", {}), meta_b.get("summary", {})
    out.append(_md_table(
        ["Metric", "A", "B"],
        [
            ["wall-clock (s)",
             f"{sa.get('wall_clock_sec', 0):.1f}",
             f"{sb.get('wall_clock_sec', 0):.1f}"],
            ["total cost ($)",
             f"{sa.get('total_cost_usd', 0):.4f}",
             f"{sb.get('total_cost_usd', 0):.4f}"],
            ["errors",
             str(sa.get('error_count', 0)),
             str(sb.get('error_count', 0))],
        ],
    ))

    # Fill rates
    out.append("\n## Fill rates by tier\n")
    rows = []
    for i in range(n):
        ra, rb = rounds_a[i], rounds_b[i]
        for tier_name, ids in [("OEM", OEMS), ("Tier-1", TIER1S),
                               ("Designer", DESIGNERS), ("Foundry", FOUNDRIES)]:
            fa = _tier_avg(ra, ids, "fill_rate")
            fb = _tier_avg(rb, ids, "fill_rate")
            rows.append([
                str(ra["round"]), tier_name,
                f"{fa:.2f}", f"{fb:.2f}", f"{fb-fa:+.2f}",
            ])
    out.append(_md_table(["Round", "Tier", "A", "B", "Δ"], rows))

    # Prices
    out.append("\n## Prices by tier ($/unit)\n")
    rows = []
    for i in range(n):
        ra, rb = rounds_a[i], rounds_b[i]
        for tier_name, ids in [("Foundry", FOUNDRIES),
                               ("Designer", DESIGNERS),
                               ("Tier-1", TIER1S)]:
            pa = _tier_avg(ra, ids, "current_price")
            pb = _tier_avg(rb, ids, "current_price")
            rows.append([
                str(ra["round"]), tier_name,
                f"{pa:.2f}", f"{pb:.2f}", f"{pb-pa:+.2f}",
            ])
    out.append(_md_table(["Round", "Tier", "A", "B", "Δ"], rows))

    # Bullwhip stdev
    out.append("\n## Bullwhip — stdev of OEM order totals\n")
    rows = []
    for i in range(n):
        ra, rb = rounds_a[i], rounds_b[i]
        sa_v = statistics.pstdev([_order_totals_for_round(ra).get(a, 0) for a in OEMS])
        sb_v = statistics.pstdev([_order_totals_for_round(rb).get(a, 0) for a in OEMS])
        rows.append([str(ra["round"]), f"{sa_v:.1f}", f"{sb_v:.1f}", f"{sb_v-sa_v:+.1f}"])
    out.append(_md_table(["Round", "A", "B", "Δ"], rows))

    # Panic prevalence
    out.append("\n## Emotional state — panicked+anxious / total\n")
    rows = []
    for i in range(n):
        ra, rb = rounds_a[i], rounds_b[i]
        pa, ta = _panic_fraction(ra)
        pb_v, tb = _panic_fraction(rb)
        rows.append([str(ra["round"]), f"{pa}/{ta}", f"{pb_v}/{tb}"])
    out.append(_md_table(["Round", "A", "B"], rows))

    # Crisis vocabulary density
    out.append("\n## Crisis-vocabulary density (hits / total LLM texts)\n")
    rows = []
    for i in range(n):
        ra, rb = rounds_a[i], rounds_b[i]
        ha, ta = _crisis_vocab_density(ra)
        hb, tb = _crisis_vocab_density(rb)
        pa = (100.0 * ha / ta) if ta else 0.0
        pb_v = (100.0 * hb / tb) if tb else 0.0
        rows.append([
            str(ra["round"]),
            f"{ha}/{ta} ({pa:.0f}%)",
            f"{hb}/{tb} ({pb_v:.0f}%)",
        ])
    out.append(_md_table(["Round", "A", "B"], rows))

    # Profit at end
    out.append("\n## Cumulative profit at end of run ($)\n")
    end_a = rounds_a[n-1]["agents"]
    end_b = rounds_b[n-1]["agents"]
    rows = []
    for a in ALL_AGENTS:
        pa = end_a.get(a, {}).get("profit", 0)
        pb = end_b.get(a, {}).get("profit", 0)
        rows.append([a, f"{pa:,.0f}", f"{pb:,.0f}", f"{pb-pa:+,.0f}"])
    out.append(_md_table(["Agent", "A", "B", "Δ"], rows))

    # First crisis utterance
    fa = _first_crisis_utterance(rounds_a)
    fb = _first_crisis_utterance(rounds_b)
    out.append("\n## First explicit crisis utterance\n")
    if fa:
        out.append(f"- **A R{fa[0]}** {fa[1]} ({fa[2]}): _{_esc(fa[3])}_\n")
    else:
        out.append("- **A**: no explicit utterance\n")
    if fb:
        out.append(f"- **B R{fb[0]}** {fb[1]} ({fb[2]}): _{_esc(fb[3])}_\n")
    else:
        out.append("- **B**: no explicit utterance\n")

    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Index ledger
# ---------------------------------------------------------------------------
def render_index() -> str:
    out: list[str] = []
    out.append("# Eval index\n")
    out.append(
        "_Auto-generated by `_eval_report.py index`. One row per experiment "
        "in `evals/`. Sorted newest-first._\n"
    )

    rows = []
    for eid in sorted(list_experiments(), reverse=True):
        try:
            meta = read_meta(eid)
        except FileNotFoundError:
            continue
        cfg = meta.get("config", {})
        summ = meta.get("summary", {})
        git = meta.get("git", {})
        rows.append([
            f"[{eid}]({eid}/report.md)",
            _esc(meta.get("label", "")),
            _esc(cfg.get("persona_variant", "?")),
            str(cfg.get("seed", "?")),
            str(cfg.get("total_rounds", "?")),
            f"${summ.get('total_cost_usd', 0):.2f}",
            str(summ.get("error_count", 0)),
            f"`{git.get('commit_short', '?')}`",
        ])
    out.append(_md_table(
        ["ID", "Label", "Persona", "Seed", "Rounds", "Cost", "Errors", "Commit"],
        rows,
    ))
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    if args[0] == "index":
        md = render_index()
        out_path = EVALS_DIR / "index.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding="utf-8")
        print(f"wrote {out_path.relative_to(EVALS_DIR.parent)}")
        return

    if args[0] == "compare":
        if len(args) < 3:
            print("usage: _eval_report.py compare <id_a> <id_b>")
            sys.exit(2)
        id_a, id_b = args[1], args[2]
        md = render_compare_report(id_a, id_b)
        out_path = EVALS_DIR / f"compare_{id_a}_vs_{id_b}.md"
        out_path.write_text(md, encoding="utf-8")
        print(f"wrote {out_path.relative_to(EVALS_DIR.parent)}")
        return

    # Single-run mode
    eid = args[0]
    md = render_single_report(eid)
    out_path = write_report(eid, md)
    print(f"wrote {out_path.relative_to(EVALS_DIR.parent)}")


if __name__ == "__main__":
    main()
