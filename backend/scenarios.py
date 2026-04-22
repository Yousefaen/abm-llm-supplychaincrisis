# Scenario narrative describes TRIGGER EVENTS only — things happening in the
# real world that agents would read about in the news. Supply-chain
# consequences (utilization, lead times, spot prices, panic, hoarding) must
# EMERGE from agent behavior given the mechanical forcings below
# (DEMAND_MULTIPLIERS, CAPACITY_SHOCKS), not be announced in the prompt.
# Telling agents "foundries at 100%" makes them role-play the outcome instead
# of producing it.
SCENARIO_EVENTS: dict[int, str] = {
    1: (
        "Q1 2020: The COVID-19 pandemic begins its global spread. Governments "
        "across Europe and North America impose lockdowns and public-health "
        "orders. Auto assembly plants in Italy, Spain, and Michigan shut down. "
        "Consumer discretionary spending shifts sharply as workforces move to "
        "remote work."
    ),
    2: (
        "Q2 2020: Lockdowns deepen across most major auto markets. Dealerships "
        "close in many regions. Governments launch broad fiscal stimulus. "
        "Consumer electronics demand surges as households invest in laptops, "
        "monitors, and gaming hardware for home use."
    ),
    3: (
        "Q3 2020: China lifts most COVID restrictions; auto sales in the PRC "
        "return to pre-pandemic levels. US and European markets begin phased "
        "reopenings. The speed of the Chinese rebound exceeds most forecasts."
    ),
    4: (
        "Q4 2020: Pent-up consumer demand drives auto sales sharply higher in "
        "most markets. US stimulus checks boost discretionary purchases. "
        "Vaccine rollouts begin in several countries, improving consumer "
        "confidence."
    ),
    5: (
        "Q1 2021: A severe winter storm hits Texas, disrupting industrial "
        "operations across the state including semiconductor fabrication in "
        "Austin. The Ever Given container ship blocks the Suez Canal for six "
        "days, halting a major share of Asia-Europe shipping."
    ),
    6: (
        "Q2 2021: The European Commission proposes the European Chips Act "
        "framework, signaling large public investment in domestic "
        "semiconductor capacity. Several OEMs publicly explore direct foundry "
        "partnerships, bypassing traditional Tier-1 intermediaries."
    ),
    7: (
        "Q3 2021: A fire at Renesas Electronics' Naka semiconductor fab in "
        "Japan damages production equipment used for automotive "
        "microcontrollers. Recovery is expected to take months. Toyota "
        "preemptively announces a 40% cut to global production for September."
    ),
    8: (
        "Q4 2021: The US CHIPS Act passes the Senate, authorizing roughly "
        "$52B in semiconductor subsidies. TSMC announces a $12B fab in "
        "Arizona and Samsung a $17B fab in Taylor, Texas — both expected to "
        "be operational around 2024."
    ),
    9: (
        "Q1 2022: Russia invades Ukraine. Neon gas — critical for "
        "semiconductor lithography and roughly 40% of which is sourced from "
        "Ukrainian suppliers — faces immediate supply uncertainty. Energy "
        "prices across Europe rise sharply."
    ),
    10: (
        "Q2 2022: The CHIPS and Science Act is signed into law in the US. "
        "Rising inflation and higher interest rates begin to pressure "
        "household budgets. The pandemic-era work-from-home buying surge is "
        "clearly over; consumer electronics demand softens."
    ),
}

TOTAL_ROUNDS = 10

# ---------------------------------------------------------------------------
# Mechanical effects — these are the exogenous forcings that drive behavior.
# Narrative text describes triggers; these knobs set the quantitative stakes.
# ---------------------------------------------------------------------------

# Demand multipliers applied to each OEM's quarterly_need per round.
# 1.0 = baseline.  COVID cratered demand, then it surged back.
DEMAND_MULTIPLIERS: dict[int, float] = {
    1: 0.60,   # Q1 2020: COVID hits, auto demand drops 40%
    2: 0.50,   # Q2 2020: lockdowns deepen
    3: 0.80,   # Q3 2020: faster-than-expected recovery begins
    4: 1.10,   # Q4 2020: full recovery + pent-up demand
    5: 1.25,   # Q1 2021: peak demand coincides with capacity shocks
    6: 1.20,   # Q2 2021: still elevated
    7: 1.15,   # Q3 2021: Renesas fire
    8: 1.10,   # Q4 2021: slight cooling
    9: 0.95,   # Q1 2022: softening
    10: 0.75,  # Q2 2022: consumer-electronics demand fading
}

# Capacity shocks: {round: {agent_id: multiplier on capacity}}.
# e.g. Renesas-analog fire in R7 removes ~30% of one foundry's capacity.
CAPACITY_SHOCKS: dict[int, dict[str, float]] = {
    7: {"KoreaSilicon": 0.70},   # fire knocks out capacity
    8: {"KoreaSilicon": 0.85},   # partial recovery
    9: {"KoreaSilicon": 1.00},   # restored
}

# Inventory carrying cost per unit per quarter (% of avg price in tier).
# Reflects storage, depreciation, obsolescence risk, tied-up capital.
INVENTORY_CARRYING_COST_PCT = 0.05  # 5% of unit price per quarter


# ---------------------------------------------------------------------------
# Emotional valence of each scenario event.  Applied to ALL agents before
# decisions in that round — captures the mood-shaping effect of a news shock
# (a pandemic or a war shifts mood independently of supply-chain mechanics).
#
# Deltas are typically in [-0.5, 0.5].  ``fear``, ``greed``, ``stress``,
# ``morale`` keys are read; missing keys default to 0.
# ---------------------------------------------------------------------------
EVENT_EMOTIONAL_VALENCE: dict[int, dict[str, float]] = {
    1:  {"fear": 0.10, "stress": 0.15, "morale": -0.05},   # COVID hits
    2:  {"fear": 0.15, "stress": 0.20, "morale": -0.10},   # lockdowns deepen
    3:  {"greed": 0.10, "stress": 0.10},                   # recovery surprise
    4:  {"fear": 0.10, "stress": 0.15, "greed": 0.15, "morale": 0.05},  # recovery / optimism
    5:  {"fear": 0.25, "stress": 0.30, "morale": -0.15},   # Texas storm + Suez
    6:  {"greed": 0.15, "stress": 0.10},                   # policy signal, strategic positioning
    7:  {"fear": 0.30, "stress": 0.30, "morale": -0.15},   # Renesas fire
    8:  {"greed": 0.10, "morale": 0.10},                   # CHIPS Act passes Senate
    9:  {"fear": 0.25, "stress": 0.25, "morale": -0.10},   # Russia-Ukraine war
    10: {"fear": 0.05, "stress": 0.10, "morale": -0.05},   # demand softening
}


def get_event_title(round_num: int) -> str:
    event = SCENARIO_EVENTS.get(round_num, "")
    colon_idx = event.find(":")
    return event[:colon_idx] if colon_idx > 0 else f"Round {round_num}"
