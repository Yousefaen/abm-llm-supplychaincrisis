"""Side-by-side comparison of two eval JSONs.

Usage:  python _eval_compare.py <before.json> <after.json>
        (defaults to _eval_run_before.json and _eval_run_after.json)

Sections:
1. Fill rates by tier (structural: where does scarcity bite?)
2. Prices, orders, bullwhip stdev
3. Panic-emotion arc
4. Narrative-leakage check (did outcome numbers get role-played?)
5. Profit distribution
6. Crisis recognition — do agents actually register the crisis?
   (lexical signal, affect intensity, signal urgency, plan mentions)
"""
from __future__ import annotations

import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

before_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("_eval_run_before.json")
after_path  = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("_eval_run_after.json")

BEFORE = json.loads(before_path.read_text(encoding="utf-8"))
AFTER  = json.loads(after_path.read_text(encoding="utf-8"))
BEFORE_LABEL = before_path.stem.replace("_eval_run_", "")
AFTER_LABEL  = after_path.stem.replace("_eval_run_", "")
print(f"comparing: {BEFORE_LABEL} (before) vs {AFTER_LABEL} (after)")

OEMS = ["ToyotaMotors", "FordAuto", "VolkswagenAG"]
TIER1S = ["BoschAuto", "ContiParts"]
DESIGNERS = ["EuroChip", "AmeriSemi"]
FOUNDRIES = ["TaiwanSemi", "KoreaSilicon"]

def hdr(s: str) -> None:
    print("\n" + "=" * 78)
    print(s)
    print("=" * 78)

def tier_avg_fill(round_data: dict, ids: list[str]) -> float:
    xs = [round_data["agents"][i]["fill_rate"] for i in ids if i in round_data["agents"]]
    return statistics.mean(xs) if xs else 0.0

def tier_avg_price(round_data: dict, ids: list[str]) -> float:
    xs = [round_data["agents"][i]["current_price"] for i in ids if i in round_data["agents"]]
    return statistics.mean(xs) if xs else 0.0

def oem_order_total(round_data: dict, aid: str) -> int:
    for evt in round_data["events"]:
        if evt["role"] == "buyer" and evt["agent_id"] == aid:
            orders = (evt.get("decision") or {}).get("orders") or {}
            return sum(int(v) for v in orders.values() if isinstance(v, (int, float)))
    return 0

# ---------------------------------------------------------------------------
hdr("META")
print(f"{'metric':>28}  {'before':>12}  {'after':>12}")
print(f"{'wall-clock (s)':>28}  "
      f"{BEFORE['meta']['total_elapsed_sec']:>12.1f}  "
      f"{AFTER['meta']['total_elapsed_sec']:>12.1f}")
print(f"{'total cost ($)':>28}  "
      f"{BEFORE['meta']['total_cost_usd']:>12.4f}  "
      f"{AFTER['meta']['total_cost_usd']:>12.4f}")

# ---------------------------------------------------------------------------
hdr("FILL RATES BY TIER (lower=more scarcity). The key question.")

print(f"\n{'round':>5}  {'tier':>10}   {'before':>8}  {'after':>8}  {'delta':>8}")
for i, r_before in enumerate(BEFORE["per_round"]):
    r_after = AFTER["per_round"][i] if i < len(AFTER["per_round"]) else None
    if r_after is None:
        continue
    rn = r_before["round"]
    for name, ids in [("OEM", OEMS), ("Tier1", TIER1S), ("Designer", DESIGNERS), ("Foundry", FOUNDRIES)]:
        bf = tier_avg_fill(r_before, ids)
        af = tier_avg_fill(r_after, ids)
        delta = af - bf
        marker = " <--" if abs(delta) > 0.05 else ""
        print(f"{rn:>5}  {name:>10}   {bf:>8.2f}  {af:>8.2f}  {delta:>+8.2f}{marker}")

# ---------------------------------------------------------------------------
hdr("PRICE TRAJECTORIES BY TIER")

for name, ids in [("Foundry", FOUNDRIES), ("Designer", DESIGNERS), ("Tier1", TIER1S)]:
    print(f"\n{name} avg price per round:")
    print(f"  {'round':>5}  {'before':>8}  {'after':>8}  {'delta':>8}")
    for i, r_before in enumerate(BEFORE["per_round"]):
        r_after = AFTER["per_round"][i] if i < len(AFTER["per_round"]) else None
        if r_after is None:
            continue
        bf = tier_avg_price(r_before, ids)
        af = tier_avg_price(r_after, ids)
        print(f"  {r_before['round']:>5}  {bf:>8.2f}  {af:>8.2f}  {af-bf:>+8.2f}")

# ---------------------------------------------------------------------------
hdr("OEM ORDER TOTALS (bullwhip signal)")

print(f"\n{'round':>5}  {'agent':>14}  {'before':>8}  {'after':>8}")
for i, r_before in enumerate(BEFORE["per_round"]):
    r_after = AFTER["per_round"][i] if i < len(AFTER["per_round"]) else None
    if r_after is None:
        continue
    for aid in OEMS:
        bf = oem_order_total(r_before, aid)
        af = oem_order_total(r_after, aid)
        print(f"  {r_before['round']:>3}  {aid:>14}  {bf:>8}  {af:>8}")

print(f"\nBullwhip: stdev of OEM totals per round")
print(f"  {'round':>5}  {'before':>8}  {'after':>8}")
for i, r_before in enumerate(BEFORE["per_round"]):
    r_after = AFTER["per_round"][i] if i < len(AFTER["per_round"]) else None
    if r_after is None:
        continue
    bf = statistics.pstdev([oem_order_total(r_before, a) for a in OEMS])
    af = statistics.pstdev([oem_order_total(r_after, a) for a in OEMS])
    print(f"  {r_before['round']:>5}  {bf:>8.1f}  {af:>8.1f}")

# ---------------------------------------------------------------------------
hdr("EMOTIONAL STATE — panic prevalence per round")

print(f"\n{'round':>5}  {'before (panicked/total)':>28}  {'after (panicked/total)':>28}")
def panic_count(r):
    c = Counter(a["emotional_state"] for a in r["agents"].values())
    p = c.get("panicked", 0) + c.get("anxious", 0)
    return p, sum(c.values())
for i, r_before in enumerate(BEFORE["per_round"]):
    r_after = AFTER["per_round"][i] if i < len(AFTER["per_round"]) else None
    if r_after is None:
        continue
    pb, tb = panic_count(r_before)
    pa, ta = panic_count(r_after)
    print(f"  {r_before['round']:>3}  {pb:>4}/{tb:<22}  {pa:>4}/{ta:<22}")

# ---------------------------------------------------------------------------
hdr("LEAKAGE CHECK — do reflections still cite outcome numbers?")
# Look for phrases that would only exist if the agent was reading the old
# narrative-leaked numbers from the prompt.
leak_patterns = [
    (r"\b(87|93|95|96|97|98|99|100)\s*%?\s*utiliz",  "utilization %"),
    (r"\b\d\.?\d?x\s*(baseline|spot|contract)",       "spot price multiple"),
    (r"\b(12|14|17|20|22|24|26)\s*weeks?\b",          "lead times in weeks"),
    (r"double[- ]ordering",                           "double-ordering phrase"),
    (r"\b30-?40%\s*(phantom|above)",                  "phantom demand %"),
    (r"Crisis\s*peak|CRISIS PEAK",                    "crisis peak label"),
]

def scan_reflections(data):
    hits = Counter()
    total = 0
    for r in data["per_round"]:
        for evt in r["events"]:
            if evt["role"] != "reflection":
                continue
            for insight in evt["decision"].get("insights", []):
                total += 1
                for pat, label in leak_patterns:
                    if re.search(pat, insight):
                        hits[label] += 1
    return hits, total

hits_b, n_b = scan_reflections(BEFORE)
hits_a, n_a = scan_reflections(AFTER)

print(f"\nReflection insights scanned: before={n_b}  after={n_a}")
print(f"\n{'leakage pattern':>28}  {'before hits':>12}  {'after hits':>12}")
for _, label in leak_patterns:
    print(f"  {label:>28}  {hits_b.get(label, 0):>12}  {hits_a.get(label, 0):>12}")

# ---------------------------------------------------------------------------
hdr("DECISION TEXT LEAKAGE — buyer/supplier reasoning")

def scan_decisions(data):
    hits = Counter()
    total = 0
    for r in data["per_round"]:
        for evt in r["events"]:
            if evt["role"] not in {"buyer", "supplier"}:
                continue
            reasoning = (evt.get("decision") or {}).get("reasoning", "")
            if not reasoning:
                continue
            total += 1
            for pat, label in leak_patterns:
                if re.search(pat, reasoning):
                    hits[label] += 1
    return hits, total

hits_b, n_b = scan_decisions(BEFORE)
hits_a, n_a = scan_decisions(AFTER)

print(f"\nBuyer/supplier reasonings scanned: before={n_b}  after={n_a}")
print(f"\n{'leakage pattern':>28}  {'before hits':>12}  {'after hits':>12}")
for _, label in leak_patterns:
    print(f"  {label:>28}  {hits_b.get(label, 0):>12}  {hits_a.get(label, 0):>12}")

# ---------------------------------------------------------------------------
hdr("PROFIT DISTRIBUTION — end of run")

print(f"\n{'agent':>14}  {'before':>14}  {'after':>14}")
end_b = BEFORE["per_round"][-1]["agents"]
end_a = AFTER["per_round"][-1]["agents"]
for aid in OEMS + TIER1S + DESIGNERS + FOUNDRIES:
    pb = end_b.get(aid, {}).get("profit", 0)
    pa = end_a.get(aid, {}).get("profit", 0)
    print(f"  {aid:>14}  ${pb:>13,.0f}  ${pa:>13,.0f}")

# ---------------------------------------------------------------------------
hdr("SAMPLE OUTPUTS FROM CRISIS ROUNDS (R5-R7) for qualitative read")

def sample_reflections(data, rounds, n=3):
    out = []
    for r in data["per_round"]:
        if r["round"] not in rounds:
            continue
        for evt in r["events"]:
            if evt["role"] == "reflection":
                for insight in evt["decision"].get("insights", [])[:1]:
                    out.append((r["round"], evt["agent_id"], insight))
    return out[:n]

print("\n--- BEFORE (R5-R7 reflections, 3 samples) ---")
for rn, aid, text in sample_reflections(BEFORE, [5, 6, 7], 3):
    print(f"\nR{rn} {aid}:")
    print(f"  {text[:400]}")

print("\n--- AFTER (R5-R7 reflections, 3 samples) ---")
for rn, aid, text in sample_reflections(AFTER, [5, 6, 7], 3):
    print(f"\nR{rn} {aid}:")
    print(f"  {text[:400]}")

# ---------------------------------------------------------------------------
hdr("CRISIS RECOGNITION — do agents register that they're in a crisis?")
# ---------------------------------------------------------------------------
#
# Six probes, measured per round in both runs:
#
#  (A) Lexical: how often do agents use crisis vocabulary in reasoning
#      (reasoning fields on decisions + insights on reflections + content
#      on signals + goals/tactics on plans). Crisis words are broad —
#      "crisis", "shortage", "shock", "emergency", "unprecedented",
#      "scarcity", "panic", "hoard", "bottleneck", "constraint".
#
#  (B) Affect intensity: mean fear + stress across all agents per round.
#
#  (C) Panic fraction: share of agents whose emotional_state is
#      panicked / anxious / angry / vindictive.
#
#  (D) Signal urgency: share of signals that are NOT "information"
#      (i.e. threat/price_warning/request/loyalty_pledge — action-oriented).
#
#  (E) Plan crisis mentions: fraction of strategic plans whose goals or
#      tactics contain crisis vocabulary.
#
#  (F) First-round of explicit "crisis" self-reference: the earliest round
#      where agents call what they're in a "crisis"/"shortage"/"shock"
#      using that exact word. Measures when the shoe drops.

CRISIS_WORDS = [
    r"\bcris[ei]s\b", r"\bshortage\b", r"\bshock\b", r"\bemergency\b",
    r"\bunprecedented\b", r"\bscarcit(?:y|ies)\b", r"\bpanic\b",
    r"\bhoard", r"\bbottleneck\b", r"\bconstraint\b", r"\bdisrupt",
]
CRISIS_RE = re.compile("|".join(CRISIS_WORDS), re.IGNORECASE)

def collect_texts_per_round(data):
    """Returns {round: [text1, text2, ...]} from all LLM-generated fields."""
    out = defaultdict(list)
    for r in data["per_round"]:
        rn = r["round"]
        for evt in r["events"]:
            dec = evt.get("decision") or {}
            if isinstance(dec, dict):
                if dec.get("reasoning"):
                    out[rn].append(dec["reasoning"])
                for ins in dec.get("insights", []) or []:
                    out[rn].append(str(ins))
                for sig in dec.get("signals", []) or []:
                    if isinstance(sig, dict) and sig.get("content"):
                        out[rn].append(sig["content"])
                plan = dec.get("plan") or {}
                if isinstance(plan, dict):
                    for g in plan.get("goals", []) or []:
                        out[rn].append(str(g))
                    for t in plan.get("tactics", []) or []:
                        out[rn].append(str(t))
                    if plan.get("risk_assessment"):
                        out[rn].append(str(plan["risk_assessment"]))
    return out

def crisis_hits_per_round(texts_by_round):
    """Per round: (hit_count, total_texts, agents_with_hit)."""
    out = {}
    for rn, texts in texts_by_round.items():
        hits = sum(1 for t in texts if CRISIS_RE.search(t))
        out[rn] = (hits, len(texts), hits / len(texts) if texts else 0.0)
    return out

texts_b = collect_texts_per_round(BEFORE)
texts_a = collect_texts_per_round(AFTER)
hits_b = crisis_hits_per_round(texts_b)
hits_a = crisis_hits_per_round(texts_a)

print("\n(A) Crisis-vocabulary density per round (hits / total LLM texts):")
print(f"  {'round':>5}  {'demand':>7}  {'before':>22}  {'after':>22}")
DEMAND = {1: 0.60, 2: 0.50, 3: 0.80, 4: 1.10, 5: 1.25,
          6: 1.20, 7: 1.15, 8: 1.10, 9: 0.95, 10: 0.75}
for rn in sorted(set(hits_b) | set(hits_a)):
    hb = hits_b.get(rn, (0, 0, 0))
    ha = hits_a.get(rn, (0, 0, 0))
    print(f"  {rn:>5}  {DEMAND.get(rn, 1.0):>7.2f}  "
          f"{hb[0]:>4}/{hb[1]:<4} ({hb[2]:>4.0%})      "
          f"{ha[0]:>4}/{ha[1]:<4} ({ha[2]:>4.0%})")

# (B) Affect intensity — mean fear + stress per round
def affect_metrics(data):
    per_round = {}
    for r in data["per_round"]:
        rn = r["round"]
        fears = []
        stress = []
        for a in r["agents"].values():
            aff = a.get("affect") or {}
            if isinstance(aff, dict):
                if "fear" in aff:
                    fears.append(float(aff.get("fear", 0) or 0))
                if "stress" in aff:
                    stress.append(float(aff.get("stress", 0) or 0))
        per_round[rn] = (
            statistics.mean(fears) if fears else 0.0,
            statistics.mean(stress) if stress else 0.0,
        )
    return per_round

aff_b = affect_metrics(BEFORE)
aff_a = affect_metrics(AFTER)

print("\n(B) Mean affect intensity per round (fear, stress across all agents):")
print(f"  {'round':>5}  {'before-fear':>11}  {'before-stress':>13}  {'after-fear':>11}  {'after-stress':>13}")
for rn in sorted(set(aff_b) | set(aff_a)):
    fb, sb = aff_b.get(rn, (0, 0))
    fa, sa = aff_a.get(rn, (0, 0))
    print(f"  {rn:>5}  {fb:>11.2f}  {sb:>13.2f}  {fa:>11.2f}  {sa:>13.2f}")

# (C) Panic fraction already covered above — re-print inline
print("\n(C) Panic fraction — already printed in 'EMOTIONAL STATE' section above.")

# (D) Signal urgency
def signal_urgency(data):
    per_round = {}
    for r in data["per_round"]:
        rn = r["round"]
        c = Counter()
        for evt in r["events"]:
            if evt["role"] != "signaling":
                continue
            for s in evt["decision"].get("signals", []) or []:
                c[s.get("signal_type", "?")] += 1
        total = sum(c.values())
        non_info = total - c.get("information", 0)
        per_round[rn] = (non_info, total, non_info / total if total else 0.0)
    return per_round

sig_b = signal_urgency(BEFORE)
sig_a = signal_urgency(AFTER)

print("\n(D) Signal urgency — non-information signals as share of total:")
print(f"  {'round':>5}  {'before':>18}  {'after':>18}")
for rn in sorted(set(sig_b) | set(sig_a)):
    nb, tb, fb = sig_b.get(rn, (0, 0, 0))
    na, ta, fa = sig_a.get(rn, (0, 0, 0))
    print(f"  {rn:>5}  {nb:>3}/{tb:<3} ({fb:>4.0%})        "
          f"{na:>3}/{ta:<3} ({fa:>4.0%})")

# (E) Plan crisis mentions
def plan_crisis_mentions(data):
    per_round = {}
    for r in data["per_round"]:
        rn = r["round"]
        plans = []
        for evt in r["events"]:
            if evt["role"] != "planning":
                continue
            plan = evt["decision"].get("plan") or {}
            texts = []
            for g in plan.get("goals", []) or []:
                texts.append(str(g))
            for t in plan.get("tactics", []) or []:
                texts.append(str(t))
            if plan.get("risk_assessment"):
                texts.append(str(plan["risk_assessment"]))
            if texts:
                plans.append(any(CRISIS_RE.search(t) for t in texts))
        per_round[rn] = (sum(plans), len(plans))
    return per_round

plan_b = plan_crisis_mentions(BEFORE)
plan_a = plan_crisis_mentions(AFTER)

print("\n(E) Strategic plans containing crisis vocabulary:")
print(f"  {'round':>5}  {'before':>12}  {'after':>12}")
for rn in sorted(set(plan_b) | set(plan_a)):
    hb, tb = plan_b.get(rn, (0, 0))
    ha, ta = plan_a.get(rn, (0, 0))
    if tb or ta:
        print(f"  {rn:>5}  {hb}/{tb:<10}  {ha}/{ta:<10}")

# (F) First round anyone calls it a crisis explicitly
CRISIS_STRICT = re.compile(r"\b(cris[ei]s|shortage|shock|emergency)\b", re.IGNORECASE)
def first_crisis_mention(data):
    for r in data["per_round"]:
        rn = r["round"]
        for evt in r["events"]:
            dec = evt.get("decision") or {}
            if not isinstance(dec, dict):
                continue
            for key in ("reasoning",):
                if dec.get(key) and CRISIS_STRICT.search(str(dec[key])):
                    return rn, evt["agent_id"], evt["role"], str(dec[key])[:180]
            for ins in dec.get("insights", []) or []:
                if CRISIS_STRICT.search(str(ins)):
                    return rn, evt["agent_id"], "reflection", str(ins)[:180]
            for sig in dec.get("signals", []) or []:
                if isinstance(sig, dict) and sig.get("content") and CRISIS_STRICT.search(sig["content"]):
                    return rn, evt["agent_id"], "signal", sig["content"][:180]
    return None

fm_b = first_crisis_mention(BEFORE)
fm_a = first_crisis_mention(AFTER)

print("\n(F) Earliest explicit 'crisis/shortage/shock/emergency' utterance:")
if fm_b:
    rn, aid, role, text = fm_b
    print(f"  BEFORE  R{rn}  {aid} ({role}): {text}")
else:
    print("  BEFORE: no explicit utterance across 10 rounds")
if fm_a:
    rn, aid, role, text = fm_a
    print(f"  AFTER   R{rn}  {aid} ({role}): {text}")
else:
    print("  AFTER: no explicit utterance across 10 rounds")
