SCENARIO_EVENTS: dict[int, str] = {
    1: (
        "Q1 2020: COVID-19 hits. Automotive production drops 40%. OEMs are "
        "canceling chip orders en masse to conserve cash. Consumer electronics "
        "demand is surging as everyone works from home."
    ),
    2: (
        "Q2 2020: Lockdowns continue. Foundries have shifted capacity to "
        "consumer electronics and hyperscale data centers, which pay higher "
        "margins. Automotive orders are at historic lows. Some chip designers "
        "are furloughing automotive teams."
    ),
    3: (
        "Q3 2020: Automotive demand starts recovering faster than anyone "
        "expected. Chinese auto sales bounce back first. OEMs try to reinstate "
        "canceled orders but find their slots have been given to consumer "
        "electronics companies. Lead times are extending."
    ),
    4: (
        "Q4 2020: Full demand recovery in automotive. But foundry capacity is "
        "fully allocated to other sectors. Lead times for automotive chips "
        "stretch to 6+ months. First reports of OEMs halting production lines "
        "due to chip shortages."
    ),
    5: (
        "Q1 2021: CRISIS PEAK. Ford idles 7 plants. VW cuts production by "
        "100,000 vehicles. Industry-wide losses projected at $110B. Governments "
        "begin pressuring foundries. Double-ordering is rampant \u2014 buyers "
        "ordering 2-3x what they need hoping to get half."
    ),
    6: (
        "Q2 2021: Foundries announce capacity expansion plans but new fabs take "
        "2-3 years to build. Price of automotive chips has risen 10-20%. OEMs "
        "start exploring direct foundry relationships, angering Tier-1 "
        "suppliers. Hoarding intensifies."
    ),
    7: (
        "Q3 2021: A fire at a major Japanese chip plant (Renesas) removes 5% "
        "of global automotive chip supply. The already-tight market tips into "
        "panic. Some OEMs are paying 10x normal prices on the spot market. "
        "Tier-1 suppliers are rationing."
    ),
    8: (
        "Q4 2021: Governments pass semiconductor subsidy bills (CHIPS Act "
        "momentum). Foundries promise to increase automotive allocation. But "
        "trust is broken \u2014 OEMs don\u2019t believe promises anymore. Inventory "
        "hoarding hits record levels."
    ),
    9: (
        "Q1 2022: Supply gradually improving but behavioral distortions persist. "
        "Double-ordering means apparent demand is 30% higher than real demand. "
        "Nobody knows what the true demand picture is. Some OEMs are sitting on "
        "excess inventory they panic-ordered."
    ),
    10: (
        "Q2 2022: Market normalizing. But the bullwhip effect hits \u2014 companies "
        "that over-ordered now have excess inventory and are canceling orders, "
        "which causes a mini demand shock going the other direction. Trust "
        "across the supply chain is at an all-time low."
    ),
}

TOTAL_ROUNDS = 10

# ---------------------------------------------------------------------------
# Mechanical effects — these override narrative-only scenario text with
# concrete parameter changes so the model and the story agree.
# ---------------------------------------------------------------------------

# Demand multipliers applied to each OEM's quarterly_need per round.
# 1.0 = baseline.  COVID cratered demand, then it surged back.
DEMAND_MULTIPLIERS: dict[int, float] = {
    1: 0.60,   # Q1 2020: COVID hits, auto demand drops 40%
    2: 0.50,   # Q2 2020: lockdowns deepen
    3: 0.80,   # Q3 2020: faster-than-expected recovery begins
    4: 1.10,   # Q4 2020: full recovery + pent-up demand
    5: 1.25,   # Q1 2021: crisis peak — everyone trying to buy
    6: 1.20,   # Q2 2021: still elevated, panic ordering
    7: 1.15,   # Q3 2021: Renesas fire adds urgency
    8: 1.10,   # Q4 2021: subsidy bills, slight cooling
    9: 0.95,   # Q1 2022: over-ordered inventory piling up
    10: 0.75,  # Q2 2022: bullwhip snap-back, cancellations
}

# Capacity shocks: {round: {agent_id: multiplier on capacity}}.
# e.g. Renesas fire in R7 removes ~30% of one foundry's capacity.
CAPACITY_SHOCKS: dict[int, dict[str, float]] = {
    7: {"KoreaSilicon": 0.70},   # Renesas-analog: fire knocks out capacity
    8: {"KoreaSilicon": 0.85},   # partial recovery
    9: {"KoreaSilicon": 1.00},   # restored
}

# Inventory carrying cost per unit per quarter (% of avg price in tier).
# Reflects storage, depreciation, obsolescence risk, tied-up capital.
INVENTORY_CARRYING_COST_PCT = 0.05  # 5% of unit price per quarter


def get_event_title(round_num: int) -> str:
    event = SCENARIO_EVENTS.get(round_num, "")
    colon_idx = event.find(":")
    return event[:colon_idx] if colon_idx > 0 else f"Round {round_num}"
