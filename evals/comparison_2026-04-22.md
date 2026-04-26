# Scenario-prompt rewrite — before/after comparison (2026-04-22)

**Run setup:** same seed (42), same PHASE_CONCURRENCY (5), same temperature (1.0), same agents. Only change: `scenarios.py:SCENARIO_EVENTS` rewritten to describe trigger events only; `market_data.py` no longer surfaces historical utilization %, spot-price index, lead-time weeks, or auto-production index to the prompt; `HISTORICAL_DATA.real_events` rewritten to describe world triggers (COVID, storm, fire, war, CHIPS Act) without supply-chain outcomes.

## Top-line verdict

The narrative-leakage hypothesis was confirmed. Crisis outcome-phrases are nearly eliminated from agent reasoning. Bullwhip amplification dropped 5-12× across crisis rounds and panic emotions muted, indicating the prior run's crisis signature was partly *performed* in response to prompt hints. The foundry bottleneck still does not bind — that is a *structural* (capacity calibration) problem, not a prompt problem.

## Leakage elimination — the sharpest test

Regex-scanning 243 reflections + 130 buyer/supplier reasoning texts for phrases that only existed in the old narrative:

| Leakage pattern | Before hits | After hits | Reduction |
|---|---|---|---|
| Utilization % (reflections) | 23 | 0 | 100% |
| Spot price multiple (reflections) | 61 | 4 | 93% |
| Lead times in weeks (reflections) | 32 | 1 | 97% |
| Double-ordering phrase | 5 | 0 | 100% |
| Utilization % (decisions) | 21 | 3 | 86% |
| Spot price multiple (decisions) | 47 | 12 | 74% |
| Lead times in weeks (decisions) | 16 | 1 | 94% |

Residual hits in decisions (the "3 utilization %" and "12 spot price multiple") appear to be agents *deriving* these outcome metrics from their own observations, which is what we wanted. They're no longer reciting the narrator.

## Bullwhip amplification collapsed

Stdev of OEM order totals per round, before vs after:

| Round | Before | After | Delta |
|---|---|---|---|
| R3 | 355 | 119 | -66% |
| R4 | 547 | 131 | -76% |
| R5 | 676 | 56 | **-92%** |
| R6 | 386 | 107 | -72% |
| R7 | 282 | 60 | -79% |

The R5 peak dropped from 676 → 56. In the before-run, VolkswagenAG alone ordered 1814 units in R5; in the after-run, peak VW orders were 909 (R2) and they ordered only 536 in R5. Agents panic-ordering less when not told a crisis peak is happening.

## Panic emotion muted

Panicked + anxious agents per round:

| Round | Before | After |
|---|---|---|
| R4 | 3/9 | 1/9 |
| R5 | 5/9 | 4/9 |
| R6 | 5/9 | 1/9 |
| R7 | 6/9 | 5/9 |
| R8 | 6/9 | 3/9 |

Panic still emerges R5-R10 (world news + mechanical demand shocks + capacity shock still trigger fear via `EVENT_EMOTIONAL_VALENCE`) but less uniformly. The before-run's R6-R8 near-universal panic was partly a response to the "crisis peak" labeling.

## Fill rates — the structural problem persists

| Round | Tier | Before | After |
|---|---|---|---|
| R5 | OEM | 0.28 | 0.46 |
| R5 | Tier1 | 1.00 | 1.00 |
| R5 | Designer | 1.00 | 1.00 |
| R5 | Foundry | 1.00 | 1.00 |
| R7 | OEM | 0.31 | 0.71 |
| R7 | Tier1-Foundry | 1.00 | 1.00 |

**The foundry bottleneck still never binds.** OEM fill rates improved somewhat (less panic ordering = less mismatch vs Tier-1 capacity) but Tier-1s, Designers, and Foundries all report 1.00 fill rate every round in both runs. The real-world crisis was driven by foundries being unable to meet designer demand; in this model, foundry capacity (~1600 units combined) remains above designer demand (~2400-peak) *only nominally* — because designers order enough to saturate their own output, not enough to saturate foundry capacity.

This is a **calibration** issue, not a prompt issue. To make foundries bind: cut combined foundry capacity in half, or double designer/tier-1 orders. I'd suggest halving foundry capacity first — it preserves historical accuracy (foundries *were* supply-limited in 2020-2022, not just allocation-limited).

## Profit distribution more balanced

| Agent | Before | After |
|---|---|---|
| FordAuto | $13,028 | $75,853 |
| ToyotaMotors | $67,182 | $88,526 |
| VolkswagenAG | $55,278 | $64,534 |
| BoschAuto | $284,544 | $251,822 |
| ContiParts | $218,568 | $222,015 |

Tier-1s still win the crisis but less decisively. OEMs as a group fare better. Ford especially — the before-run had Ford essentially bankrupted by its own dysfunctional ordering pattern; in the after-run that pathology is much reduced.

## Reflections now show true emergent pattern detection

### Before (R5, TaiwanSemi)
> *"Pricing Disconnect Crisis: Across rounds 3-5, despite market conditions reaching crisis levels (**utilization 87%→100%, spot prices 0.9x→1.8x, lead times 12→26 weeks**), we've achieved zero revenue..."*

The bolded metrics are lifted directly from prompt text.

### After (R5, TaiwanSemi)
> *"The phantom demand epidemic across both EuroChip (367→424→651→1097→693) and AmeriSemi (257→338→597→486→657) with zero actual conversions for 5 consecutive rounds despite rising prices ($11→$14) reveals a systemic market failure where allocation-based systems incentivize hoarding over commitment — TaiwanSemi must immediately pivot to deposit-required or contract-based ordering to capture actual revenue."*

The agent cites its own observations of peer order trajectories, names the pattern ("phantom demand epidemic"), proposes a structural fix ("deposit-required or contract-based ordering"). This is the kind of emergent insight the architecture was built to produce — and it only shows up clearly when the narrator isn't doing the work for it.

## What this run tells us

1. **Narrative leakage was real and substantial.** The before-run's bullwhip, panic, and crisis aesthetics were partly *performance* in response to prompt hints about those outcomes.
2. **Emergent crisis dynamics still exist** — world events (COVID lockdowns, Texas storm, Renesas fire, Russia-Ukraine) combined with mechanical demand/capacity shocks still produce rising prices, panic, trust decay, and bullwhip. They're just less melodramatic and more bottom-up.
3. **The foundry bottleneck remains structurally absent.** No amount of prompt rewriting will fix that. Calibration of `AGENT_SPECS` foundry capacity is the next lever.
4. **Agents reasoning more about peer behavior** ("phantom demand epidemic" detected from VW order trajectories) rather than cited external numbers. This is a win for the generative-agents architecture.

## Remaining issues carried forward

- Foundry capacity calibration (structural).
- Signal → order causal link still weak.
- Parse failures slightly up (3 → 5 unique). Both runs hit the same fundamental issue: long `reasoning` text with special chars breaking the JSON parser.
- FordAuto inventory bug — needs investigation; persists in both runs.
