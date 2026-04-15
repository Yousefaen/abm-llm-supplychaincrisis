SCENARIO_EVENTS: dict[int, str] = {
    1: (
        "Q1 2020: COVID-19 hits. Automotive production drops 40% (OICA data: "
        "global output falls to 72% of 2019 baseline). OEMs cancel chip orders "
        "to conserve cash. Meanwhile TSMC reports 87% utilization \u2014 consumer "
        "electronics and data center demand is surging as everyone works from "
        "home. Chip spot prices holding at 0.95x baseline."
    ),
    2: (
        "Q2 2020: Lockdowns deepen. Global auto production hits lowest point "
        "since 2009 (55% of baseline). Foundries at 93% utilization, "
        "reallocating wafer starts to consumer/data center (3x margin vs auto). "
        "TSMC revenue rises 29% YoY despite automotive collapse. Lead times "
        "extend to 14 weeks. Some chip designers furloughing automotive teams."
    ),
    3: (
        "Q3 2020: Automotive demand recovers faster than expected \u2014 China auto "
        "sales back to 2019 levels, US/EU lagging (82% of baseline). OEMs try "
        "to reinstate canceled orders but foundry slots are taken. Foundries "
        "now at 96% utilization. Lead times jump to 17 weeks. Spot prices "
        "start creeping up to 1.05x baseline."
    ),
    4: (
        "Q4 2020: Full demand recovery (98% of baseline) but foundry capacity "
        "at 99% utilization \u2014 effectively maxed out. Lead times stretch to 22 "
        "weeks (5+ months). VW halts Wolfsburg production. Continental warns of "
        "'severe semiconductor bottleneck'. Spot prices rise to 1.2x baseline. "
        "First wave of panic ordering begins."
    ),
    5: (
        "Q1 2021: CRISIS PEAK. Foundries at 100% utilization \u2014 zero slack. "
        "Ford idles 7 plants, GM cuts Silverado production, VW cuts 100K "
        "vehicles. Industry losses projected at $110B. Double-ordering rampant "
        "(true demand obscured by 30-40%). Texas winter storm knocks out "
        "Samsung Austin fab for 6 weeks. Suez Canal blockage disrupts "
        "shipments. Spot prices surge to 1.8x baseline. Lead times hit 26 weeks."
    ),
    6: (
        "Q2 2021: Foundries still at 100% utilization. TSMC raises automotive "
        "chip prices 15-20%. Spot market prices hit 2.5x baseline (some MCUs "
        "at 3x contract). Ford and GM announce direct foundry partnerships, "
        "angering Tier-1 suppliers. EU announces European Chips Act framework. "
        "Hoarding intensifies. Lead times still 26 weeks."
    ),
    7: (
        "Q3 2021: Renesas Naka fab fire impact continues \u2014 removes ~5% of "
        "global automotive chip supply. Toyota cuts global production 40% in "
        "September. Spot prices peak at 3.2x baseline (some MCUs at 10x "
        "contract). Bosch CEO calls it 'biggest crisis in auto industry'. "
        "Foundry utilization 98% (slight easing). Lead times 26 weeks."
    ),
    8: (
        "Q4 2021: US CHIPS Act passes Senate ($52B in subsidies). TSMC "
        "announces $12B Arizona fab, Samsung $17B Taylor TX fab \u2014 but won't "
        "be operational until 2024. Spot prices ease slightly to 2.8x. "
        "Foundry utilization 97%. Lead times start shortening to 24 weeks. "
        "But trust is broken \u2014 OEMs don\u2019t believe promises. Inventory hoarding "
        "hits record levels."
    ),
    9: (
        "Q1 2022: Supply gradually improving. Foundry utilization eases to 95%. "
        "Spot prices decline to 2.2x baseline. Lead times shorten to 20 weeks. "
        "But behavioral distortions persist \u2014 apparent demand 30% above real "
        "demand from phantom orders. Some OEMs sitting on excess inventory. "
        "Russia-Ukraine war creates new neon gas supply uncertainty (40% from "
        "Ukraine). Nobody knows what true demand is."
    ),
    10: (
        "Q2 2022: CHIPS and Science Act signed into law. Bullwhip effect hits "
        "hard \u2014 order cancellations cascade upstream. Consumer electronics "
        "demand crashes; foundries scramble to fill automotive at 92% "
        "utilization. Spot prices falling rapidly (1.6x baseline). Lead times "
        "back to 16 weeks. Trust across supply chain at all-time low. Companies "
        "that over-ordered have excess inventory; those that under-ordered "
        "still face gaps."
    ),
}

TOTAL_ROUNDS = 10

# ---------------------------------------------------------------------------
# Mechanical effects \u2014 these override narrative-only scenario text with
# concrete parameter changes so the model and the story agree.
# ---------------------------------------------------------------------------

# Demand multipliers applied to each OEM's quarterly_need per round.
# 1.0 = baseline.  COVID cratered demand, then it surged back.
DEMAND_MULTIPLIERS: dict[int, float] = {
    1: 0.60,   # Q1 2020: COVID hits, auto demand drops 40%
    2: 0.50,   # Q2 2020: lockdowns deepen
    3: 0.80,   # Q3 2020: faster-than-expected recovery begins
    4: 1.10,   # Q4 2020: full recovery + pent-up demand
    5: 1.25,   # Q1 2021: crisis peak \u2014 everyone trying to buy
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
