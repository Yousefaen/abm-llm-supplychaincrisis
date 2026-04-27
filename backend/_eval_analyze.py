"""Post-hoc analysis of _eval_run.json -- emergence, behavior, engineering."""
from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Windows cp1252 console chokes on non-ASCII; force utf-8 for stdout.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA = json.loads(Path("_eval_run.json").read_text(encoding="utf-8"))

meta = DATA["meta"]
rounds = DATA["per_round"]

OEMS = ["ToyotaMotors", "FordAuto", "VolkswagenAG"]
TIER1S = ["BoschAuto", "ContiParts"]
DESIGNERS = ["EuroChip", "AmeriSemi"]
FOUNDRIES = ["TaiwanSemi", "KoreaSilicon"]
ALL = OEMS + TIER1S + DESIGNERS + FOUNDRIES

DEMAND = {1: 0.60, 2: 0.50, 3: 0.80, 4: 1.10, 5: 1.25,
          6: 1.20, 7: 1.15, 8: 1.10, 9: 0.95, 10: 0.75}

def hdr(s: str) -> None:
    print("\n" + "=" * 72)
    print(s)
    print("=" * 72)

hdr("META")
print(f"rounds={meta['total_rounds']}  seed={meta['seed']}  "
      f"concurrency={meta['phase_concurrency']}")
print(f"wall-clock: {meta['total_elapsed_sec']:.1f}s   "
      f"total cost: ${meta['total_cost_usd']:.4f}")

# ---------------------------------------------------------------------------
# 1. EMERGENCE — bullwhip, fill rates, prices, inventory, profit
# ---------------------------------------------------------------------------
hdr("1. EMERGENCE")

# 1a. Order variance per tier per round -- classic bullwhip test
# Pull orders from events (role='buyer') since mid-chain agents overwrite
# current_decision with their supplier-phase allocations by snapshot time.
print("\nOrder totals per agent per round (summed across suppliers):")
print(f"  {'round':>5}  {'demand':>6}  "
      f"{'OEM_T':>5} {'OEM_F':>5} {'OEM_V':>5}  "
      f"{'T1_B':>5} {'T1_C':>5}  "
      f"{'CD_E':>5} {'CD_A':>5}")
order_totals: dict[int, dict[str, int]] = {}
for r in rounds:
    rn = r["round"]
    totals: dict[str, int] = {}
    for evt in r["events"]:
        if evt["role"] == "buyer":
            dec = evt.get("decision") or {}
            orders = dec.get("orders") or {}
            totals[evt["agent_id"]] = sum(
                int(v) for v in orders.values() if isinstance(v, (int, float))
            )
    order_totals[rn] = totals
    print(f"  {rn:>5}  {DEMAND[rn]:>6.2f}  "
          f"{totals.get('ToyotaMotors',0):>5} "
          f"{totals.get('FordAuto',0):>5} "
          f"{totals.get('VolkswagenAG',0):>5}  "
          f"{totals.get('BoschAuto',0):>5} "
          f"{totals.get('ContiParts',0):>5}  "
          f"{totals.get('EuroChip',0):>5} "
          f"{totals.get('AmeriSemi',0):>5}")

print("\nBullwhip — stdev of order totals within each tier per round:")
print(f"  {'round':>5}  {'OEM':>8}  {'Tier1':>8}  {'Designer':>10}  {'CV_amp':>8}")
for r in rounds:
    rn = r["round"]
    t = order_totals[rn]
    oem_o = [t.get(a, 0) for a in OEMS]
    t1_o = [t.get(a, 0) for a in TIER1S]
    cd_o = [t.get(a, 0) for a in DESIGNERS]
    s_oem = statistics.pstdev(oem_o) if len(oem_o) > 1 else 0
    s_t1 = statistics.pstdev(t1_o) if len(t1_o) > 1 else 0
    s_cd = statistics.pstdev(cd_o) if len(cd_o) > 1 else 0
    # Coefficient-of-variation amplification: CV at designer / CV at OEM
    mean_oem = statistics.mean(oem_o) or 1
    mean_cd = statistics.mean(cd_o) or 1
    cv_oem = s_oem / mean_oem if mean_oem else 0
    cv_cd = s_cd / mean_cd if mean_cd else 0
    cv_amp = (cv_cd / cv_oem) if cv_oem > 0 else float("nan")
    print(f"  {rn:>5}  {s_oem:>8.1f}  {s_t1:>8.1f}  {s_cd:>10.1f}  "
          f"{cv_amp:>8.2f}")

# 1b. Fill rate trajectories
print("\nFill rate per tier per round (1.0 = perfect supply):")
print(f"  {'round':>5}  {'OEM':>6}  {'Tier1':>6}  {'Designer':>9}  {'Foundry':>8}")
for r in rounds:
    rn = r["round"]
    ag = r["agents"]
    def tier_avg(ids):
        xs = [ag[i]["fill_rate"] for i in ids if i in ag]
        return statistics.mean(xs) if xs else 0
    print(f"  {rn:>5}  {tier_avg(OEMS):>6.2f}  {tier_avg(TIER1S):>6.2f}  "
          f"{tier_avg(DESIGNERS):>9.2f}  {tier_avg(FOUNDRIES):>8.2f}")

# 1c. Price trajectories
print("\nAverage price per tier per round ($/unit):")
print(f"  {'round':>5}  {'Foundry':>8}  {'Designer':>9}  {'Tier1':>6}")
for r in rounds:
    rn = r["round"]
    ag = r["agents"]
    def tier_price(ids):
        xs = [ag[i]["current_price"] for i in ids if i in ag]
        return statistics.mean(xs) if xs else 0
    print(f"  {rn:>5}  {tier_price(FOUNDRIES):>8.2f}  "
          f"{tier_price(DESIGNERS):>9.2f}  {tier_price(TIER1S):>6.2f}")

# 1d. Inventory trajectory (OEM focus — they hoard in crisis, dump in snap-back)
print("\nInventory per agent per round:")
print(f"  {'round':>5}  " + " ".join(f"{a[:10]:>10}" for a in ALL))
for r in rounds:
    rn = r["round"]
    ag = r["agents"]
    print(f"  {rn:>5}  " + " ".join(
        f"{ag[a]['inventory']:>10}" if a in ag else f"{'-':>10}" for a in ALL))

# 1e. Profit trajectory
print("\nCumulative profit ($) per agent by end of run:")
end = rounds[-1]["agents"]
for a in sorted(ALL, key=lambda x: -end.get(x, {}).get("profit", 0)):
    if a in end:
        p = end[a]["profit"]
        print(f"  {a:>14}  ${p:>12,.0f}")

# ---------------------------------------------------------------------------
# 2. BEHAVIOR — signals, grudges, trust, emotions, reflections, replans
# ---------------------------------------------------------------------------
hdr("2. BEHAVIOR")

# 2a. Signal traffic by round and type
print("\nSignals emitted per round (type × count):")
signals_by_round: dict[int, Counter] = defaultdict(Counter)
signal_examples: list[tuple[int, str, str, str, str]] = []  # round, sender, type, recipient, content
for r in rounds:
    rn = r["round"]
    for evt in r["events"]:
        if evt["role"] == "signaling":
            sigs = evt["decision"].get("signals", [])
            for s in sigs:
                stype = s.get("signal_type", "?")
                signals_by_round[rn][stype] += 1
                signal_examples.append((
                    rn, evt["agent_id"], stype,
                    s.get("recipient", "all"),
                    (s.get("content") or "")[:160],
                ))
all_types = sorted({t for c in signals_by_round.values() for t in c})
print(f"  {'round':>5}  " + " ".join(f"{t[:14]:>14}" for t in all_types) + f"  {'total':>6}")
for rn in sorted(signals_by_round):
    c = signals_by_round[rn]
    row = f"  {rn:>5}  " + " ".join(f"{c.get(t,0):>14}" for t in all_types)
    print(row + f"  {sum(c.values()):>6}")

# 2b. Example signals from the crisis peak (R5-R7)
print("\nSample signals from R5-R7 (crisis peak):")
crisis_sigs = [s for s in signal_examples if 5 <= s[0] <= 7]
for rn, sender, stype, recip, content in crisis_sigs[:8]:
    print(f"  R{rn} {sender} -> {recip} [{stype}]:")
    print(f"    \"{content}\"")

# 2c. Grudge emergence per agent (looking at affect.grudge dict)
print("\nGrudge scores (nonzero) by round:")
for r in rounds:
    rn = r["round"]
    lines = []
    for aid, a in r["agents"].items():
        g = (a.get("affect") or {}).get("grudge") or {}
        for target, val in g.items():
            if val >= 0.2:  # threshold for "significant" grudge
                lines.append(f"    {aid} vs {target}: {val:.2f}")
    if lines:
        print(f"  R{rn}:")
        for ln in lines:
            print(ln)

# 2d. Trust scores evolution — focus on OEMs->tier1 trust through crisis
print("\nOEM trust scores for Tier-1s (higher=more trusted):")
print(f"  {'round':>5}  "
      f"{'Toy->Bosch':>10} {'Toy->Conti':>10}  "
      f"{'Ford->Bosch':>10} {'Ford->Conti':>10}  "
      f"{'VW->Bosch':>10} {'VW->Conti':>10}")
for r in rounds:
    rn = r["round"]
    ag = r["agents"]
    def ts(a, t):
        return (ag.get(a, {}).get("trust_scores") or {}).get(t, 0)
    print(f"  {rn:>5}  "
          f"{ts('ToyotaMotors','BoschAuto'):>10.1f} {ts('ToyotaMotors','ContiParts'):>10.1f}  "
          f"{ts('FordAuto','BoschAuto'):>10.1f} {ts('FordAuto','ContiParts'):>10.1f}  "
          f"{ts('VolkswagenAG','BoschAuto'):>10.1f} {ts('VolkswagenAG','ContiParts'):>10.1f}")

# 2e. Emotional-state distribution per round
print("\nEmotional state distribution:")
for r in rounds:
    rn = r["round"]
    c = Counter(a.get("emotional_state", "?") for a in r["agents"].values())
    print(f"  R{rn}: " + ", ".join(f"{k}={v}" for k, v in c.most_common()))

# 2f. Reflections — count + content sample
print("\nReflection insights per round:")
reflections_by_round = defaultdict(list)
for r in rounds:
    rn = r["round"]
    for evt in r["events"]:
        if evt["role"] == "reflection":
            ins = evt["decision"].get("insights", [])
            for i in ins:
                reflections_by_round[rn].append((evt["agent_id"], i))
for rn in sorted(reflections_by_round):
    print(f"  R{rn}: {len(reflections_by_round[rn])} insights")

print("\nSample reflections (one per agent, middle of crisis R5-R6):")
seen = set()
for rn in [5, 6, 7]:
    for aid, ins in reflections_by_round.get(rn, []):
        if aid not in seen and len(seen) < 6:
            print(f"  R{rn} {aid}: {ins[:220]}")
            seen.add(aid)

# 2g. Plans — count of planning events per round, emergency replans
print("\nPlanning events per round (fresh + emergency replans):")
plans_per_round = defaultdict(int)
replan_flags_per_round = defaultdict(int)
for r in rounds:
    rn = r["round"]
    for evt in r["events"]:
        if evt["role"] == "planning":
            plans_per_round[rn] += 1
            plan = evt["decision"].get("plan") or {}
            if plan.get("invalidated") or plan.get("created_at_round") == rn:
                # best-effort flag — look at reason if present
                pass
for rn in sorted(plans_per_round):
    print(f"  R{rn}: {plans_per_round[rn]} plans")

# 2h. Signal -> order-shift correlation (same-agent, next-round)
# Test: if BoschAuto sent a "price_warning" at R_t, did its suppliers (designers)
# reduce their next-round allocations to BoschAuto? This is a weak test — just
# checks directional movement.
print("\nSignal->behavior: orders to sender in round after signal emitted:")
for stype in ["price_warning", "threat", "loyalty_pledge"]:
    pairs: list[tuple[str, int, int, int]] = []
    for r in rounds[:-1]:
        rn = r["round"]
        next_r = rounds[rn]  # next round (0-indexed)
        for evt in r["events"]:
            if evt["role"] == "signaling":
                sigs = evt["decision"].get("signals", [])
                for s in sigs:
                    if s.get("signal_type") != stype:
                        continue
                    sender = evt["agent_id"]
                    recip = s.get("recipient")
                    if not recip:
                        continue
                    # Find what recipient ordered/allocated TO sender in next round
                    recip_agent = next_r["agents"].get(recip)
                    if not recip_agent:
                        continue
                    dec = recip_agent.get("current_decision") or {}
                    orders = dec.get("orders") or {}
                    allocs = dec.get("allocations") or {}
                    amt = int(orders.get(sender, 0) or allocs.get(sender, 0) or 0)
                    # What did recipient order/allocate to sender in the current round?
                    recip_prev = r["agents"].get(recip) or {}
                    prev_dec = recip_prev.get("current_decision") or {}
                    prev = int((prev_dec.get("orders") or {}).get(sender, 0)
                               or (prev_dec.get("allocations") or {}).get(sender, 0) or 0)
                    pairs.append((sender + "->" + recip, rn, prev, amt))
    if pairs:
        print(f"  {stype}: {len(pairs)} signal events")
        shifted = [(p[3] - p[2]) for p in pairs]
        up = sum(1 for d in shifted if d > 0)
        down = sum(1 for d in shifted if d < 0)
        same = sum(1 for d in shifted if d == 0)
        print(f"    next-round amount vs same-round: up={up}  down={down}  unchanged={same}")
        if shifted:
            print(f"    mean delta: {statistics.mean(shifted):+.1f}  "
                  f"median: {statistics.median(shifted):+.1f}")

# ---------------------------------------------------------------------------
# 3. ENGINEERING — timing, cost, errors, parallelism profile
# ---------------------------------------------------------------------------
hdr("3. ENGINEERING")

print(f"\nPer-round wall-clock and cost:")
print(f"  {'round':>5}  {'sec':>6}  {'cost':>8}  {'events':>6}  {'errors':>6}")
for r in rounds:
    print(f"  {r['round']:>5}  {r['elapsed_sec']:>6.1f}  "
          f"${r['round_cost_usd']:>6.4f}  {len(r['events']):>6}  {r['error_count']:>6}")
mean_round = statistics.mean(r["elapsed_sec"] for r in rounds)
print(f"\n  mean round: {mean_round:.1f}s   "
      f"p95: {sorted([r['elapsed_sec'] for r in rounds])[-1]:.1f}s   "
      f"total cost: ${sum(r['round_cost_usd'] for r in rounds):.4f}")

# Parallelism profile — for each role-phase, time span = last event t_rel - first
print("\nPhase-duration profile per round (role: span across all agents):")
for r in rounds:
    rn = r["round"]
    by_role: dict[str, list[float]] = defaultdict(list)
    for evt in r["events"]:
        by_role[evt["role"]].append(evt["t_rel"])
    parts = []
    for role in ["planning", "signaling", "buyer", "supplier", "reflection"]:
        if role in by_role:
            ts = by_role[role]
            parts.append(f"{role[:4]}={min(ts):.1f}-{max(ts):.1f}s({len(ts)})")
    print(f"  R{rn}: " + "  ".join(parts))

# Error types captured
print("\nErrors captured across run:")
for r in rounds:
    if r.get("errors_sample"):
        for e in r["errors_sample"]:
            print(f"  R{r['round']}: {e}")
