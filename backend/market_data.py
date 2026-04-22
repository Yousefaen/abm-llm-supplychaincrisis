"""Historical news feed and observable market environment.

The agents see two kinds of world information:

1. **Exogenous news** — what happened in the outside world this quarter
   (pandemic, storm, fab fire, policy change). These are TRIGGERS, not
   outcomes. A real procurement exec would read them in the news.

2. **Endogenous observables** — aggregate metrics computed from live agent
   behavior (industry avg fill rate, sentiment from agents' emotional states,
   hoarding totals, price trend, bullwhip risk). These EMERGE from the
   simulation, not announced to it.

Deliberately excluded from the prompt: utilization percentages, spot price
indices, lead times, auto production indices. Those are *outcomes* of the
crisis; including them as inputs would cause agents to role-play the crisis
instead of producing it. The dataclass retains them for post-hoc comparison
against ground truth, but format_for_prompt does not surface them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from agents import SupplyChainAgent

# ---------------------------------------------------------------------------
# Historical news feed — Q1 2020 – Q2 2022
# ---------------------------------------------------------------------------
# real_events holds only TRIGGER events (world happenings agents could read
# in a newspaper). Supply-chain outcomes like "foundry utilization 100%",
# "double-ordering rampant", "OEMs idle plants" are deliberately omitted —
# those should emerge from agent behavior, not be told to agents.
#
# The numeric fields (foundry_utilization_pct, auto_production_index, etc.)
# are retained for post-hoc ground-truth comparison but NOT surfaced to the
# LLM prompt.

@dataclass
class HistoricalQuarter:
    """Real-world market snapshot for one quarter (ground-truth reference)."""
    period: str
    foundry_utilization_pct: float       # kept for analysis — not in prompt
    auto_production_index: float         # kept for analysis — not in prompt
    chip_spot_price_index: float         # kept for analysis — not in prompt
    lead_time_weeks: float               # kept for analysis — not in prompt
    real_events: list[str]               # triggers only — surfaced to agents


HISTORICAL_DATA: dict[int, HistoricalQuarter] = {
    1: HistoricalQuarter(
        period="Q1 2020",
        foundry_utilization_pct=0.87,
        auto_production_index=0.72,
        chip_spot_price_index=0.95,
        lead_time_weeks=12,
        real_events=[
            "COVID-19 pandemic declared; governments impose lockdowns",
            "Auto assembly plants shut in Italy, Spain, US Midwest",
            "Remote work mandates drive laptop and monitor purchases",
        ],
    ),
    2: HistoricalQuarter(
        period="Q2 2020",
        foundry_utilization_pct=0.93,
        auto_production_index=0.55,
        chip_spot_price_index=0.98,
        lead_time_weeks=14,
        real_events=[
            "Lockdowns deepen; dealerships closed in most markets",
            "US CARES Act and European stimulus programs launched",
            "Gaming console, webcam, and home-office hardware sales surge",
        ],
    ),
    3: HistoricalQuarter(
        period="Q3 2020",
        foundry_utilization_pct=0.96,
        auto_production_index=0.82,
        chip_spot_price_index=1.05,
        lead_time_weeks=17,
        real_events=[
            "China lifts most COVID restrictions; PRC auto sales recover fully",
            "Phased reopenings begin in US and EU",
            "Vaccine candidates enter late-stage trials",
        ],
    ),
    4: HistoricalQuarter(
        period="Q4 2020",
        foundry_utilization_pct=0.99,
        auto_production_index=0.98,
        chip_spot_price_index=1.20,
        lead_time_weeks=22,
        real_events=[
            "Pfizer/BioNTech and Moderna vaccines receive emergency authorization",
            "US stimulus checks distributed; consumer discretionary spending rises",
            "Pent-up auto demand returns faster than most OEMs forecast",
        ],
    ),
    5: HistoricalQuarter(
        period="Q1 2021",
        foundry_utilization_pct=1.00,
        auto_production_index=0.95,
        chip_spot_price_index=1.80,
        lead_time_weeks=26,
        real_events=[
            "Severe Texas winter storm disrupts industrial operations in Austin",
            "Ever Given blocks Suez Canal for six days",
            "Global vaccine rollout accelerates",
        ],
    ),
    6: HistoricalQuarter(
        period="Q2 2021",
        foundry_utilization_pct=1.00,
        auto_production_index=0.88,
        chip_spot_price_index=2.50,
        lead_time_weeks=26,
        real_events=[
            "European Commission proposes European Chips Act framework",
            "Several OEMs publicly explore direct foundry partnerships",
            "Reopening continues in most developed markets",
        ],
    ),
    7: HistoricalQuarter(
        period="Q3 2021",
        foundry_utilization_pct=0.98,
        auto_production_index=0.82,
        chip_spot_price_index=3.20,
        lead_time_weeks=26,
        real_events=[
            "Fire at Renesas Naka fab damages automotive-MCU production equipment",
            "Toyota announces 40% global production cut for September",
            "Delta variant drives new case surges in several countries",
        ],
    ),
    8: HistoricalQuarter(
        period="Q4 2021",
        foundry_utilization_pct=0.97,
        auto_production_index=0.86,
        chip_spot_price_index=2.80,
        lead_time_weeks=24,
        real_events=[
            "US CHIPS Act passes Senate ($52B in semiconductor subsidies)",
            "TSMC announces $12B Arizona fab; Samsung announces $17B Taylor TX fab",
            "Omicron variant emerges, renewing supply-chain concerns",
        ],
    ),
    9: HistoricalQuarter(
        period="Q1 2022",
        foundry_utilization_pct=0.95,
        auto_production_index=0.90,
        chip_spot_price_index=2.20,
        lead_time_weeks=20,
        real_events=[
            "Russia invades Ukraine",
            "Neon gas supply uncertain (Ukraine supplies ~40% of semiconductor neon)",
            "European energy prices spike; inflation pressure rises",
        ],
    ),
    10: HistoricalQuarter(
        period="Q2 2022",
        foundry_utilization_pct=0.92,
        auto_production_index=0.93,
        chip_spot_price_index=1.60,
        lead_time_weeks=16,
        real_events=[
            "CHIPS and Science Act signed into law in the US",
            "US Federal Reserve raises interest rates; inflation remains elevated",
            "Work-from-home hardware spending clearly slowing",
        ],
    ),
}


# ---------------------------------------------------------------------------
# Observable market state — what agents can see each round
# ---------------------------------------------------------------------------

@dataclass
class MarketState:
    """Aggregate market intelligence observable by all agents.

    Retains exogenous historical fields for post-hoc comparison, but the
    prompt formatter surfaces only the endogenous (emergent) metrics plus
    the news-trigger events.
    """

    round: int
    period: str

    # Exogenous (kept for analysis + frontend display, NOT in prompt)
    foundry_utilization_pct: float
    auto_production_index: float
    chip_spot_price_index: float
    lead_time_weeks: float
    real_events: list[str]

    # Endogenous — computed from live agent behavior (these ARE in the prompt)
    aggregate_demand_vs_supply: float
    avg_price_offered: float
    industry_inventory_weeks: float
    market_sentiment: str
    pct_agents_panicked: float
    avg_fill_rate: float
    total_hoarded_units: int
    price_trend: str
    bullwhip_risk: str
    supply_crunch_severity: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "round": self.round,
            "period": self.period,
            "foundry_utilization_pct": self.foundry_utilization_pct,
            "auto_production_index": self.auto_production_index,
            "chip_spot_price_index": self.chip_spot_price_index,
            "lead_time_weeks": self.lead_time_weeks,
            "real_events": self.real_events,
            "aggregate_demand_vs_supply": self.aggregate_demand_vs_supply,
            "avg_price_offered": self.avg_price_offered,
            "industry_inventory_weeks": self.industry_inventory_weeks,
            "market_sentiment": self.market_sentiment,
            "pct_agents_panicked": self.pct_agents_panicked,
            "avg_fill_rate": self.avg_fill_rate,
            "total_hoarded_units": self.total_hoarded_units,
            "price_trend": self.price_trend,
            "bullwhip_risk": self.bullwhip_risk,
            "supply_crunch_severity": self.supply_crunch_severity,
        }


# ---------------------------------------------------------------------------
# Tier-specific interpretation frames
# ---------------------------------------------------------------------------
# Same observable data, different lens — this creates divergent behavior from
# shared stimuli (the core Stanford insight for emergence). These frames are
# strategic role descriptions, not outcome predictions, so they stay.

TIER_INTERPRETATION_FRAMES: dict[str, str] = {
    "foundry": (
        "As a foundry, you sit at the apex of the chip supply chain. Your "
        "allocation choices cascade all the way down to car production. "
        "Consider: maximize short-term margin on scarce capacity, or invest "
        "in long-term customer loyalty. Governments are watching — visible "
        "neglect of strategic industries can invite political backlash."
    ),
    "chipDesigner": (
        "As a chip designer, you are squeezed from both sides. Foundry costs "
        "and lead times affect your upstream supply; OEM and Tier-1 "
        "customers resist cost pass-through. You must balance upstream "
        "sourcing security against downstream margin. Design wins are your "
        "moat — a customer lost now may be lost permanently."
    ),
    "tier1Supplier": (
        "As a Tier-1 supplier, you are the shock absorber between chip "
        "makers and auto OEMs. Customers demand guaranteed supply AND stable "
        "prices — an impossibility in a shortage. Some OEMs may try to go "
        "around you directly to foundries, an existential threat to your "
        "model. Your inventory buffer is your lifeline."
    ),
    "oem": (
        "As an OEM, you are the end consumer of this supply chain. Every "
        "chip you cannot obtain means a car you cannot build, and revenue "
        "competitors will capture. Competitors' procurement choices affect "
        "your allocation. Decide: pay premium prices for security, or hold "
        "the line and risk production shutdowns."
    ),
}


# ---------------------------------------------------------------------------
# MarketEnvironment — computes observable state from historical + live data
# ---------------------------------------------------------------------------

class MarketEnvironment:
    """Computes and maintains the observable market state each round."""

    def __init__(self) -> None:
        self.history: list[MarketState] = []
        self._prev_avg_price: float | None = None

    def compute_market_state(
        self,
        current_round: int,
        agents: dict[str, "SupplyChainAgent"],
    ) -> MarketState:
        """Compute the observable market state for this round.

        Called at the START of each round, before agents make decisions.
        Uses previous round's agent state for endogenous metrics.
        """
        historical = HISTORICAL_DATA.get(current_round)
        if not historical:
            historical = HistoricalQuarter(
                period=f"Round {current_round}",
                foundry_utilization_pct=0.90,
                auto_production_index=1.0,
                chip_spot_price_index=1.0,
                lead_time_weeks=14,
                real_events=[],
            )

        # --- Endogenous metrics from agent state ---
        total_demand = 0
        total_foundry_capacity = 0
        total_inventory = 0
        total_weekly_consumption = 0
        total_hoarded = 0
        prices: list[float] = []
        emotional_states: list[str] = []
        fill_rates: list[float] = []

        for agent in agents.values():
            emotional_states.append(agent.emotional_state)
            fill_rates.append(agent.fill_rate)

            if agent.spec.quarterly_need > 0:
                total_demand += agent.effective_quarterly_need
                total_weekly_consumption += agent.effective_quarterly_need / 13

            if agent.tier == "foundry":
                total_foundry_capacity += agent.effective_capacity

            total_inventory += agent.inventory

            if agent.current_decision:
                if "price_offered" in agent.current_decision:
                    prices.append(float(agent.current_decision["price_offered"]))
                if "held_in_reserve" in agent.current_decision:
                    total_hoarded += int(agent.current_decision["held_in_reserve"])

        demand_vs_supply = (
            total_demand / total_foundry_capacity
            if total_foundry_capacity > 0 else 1.0
        )

        avg_price = sum(prices) / len(prices) if prices else 0.0

        inv_weeks = (
            total_inventory / total_weekly_consumption
            if total_weekly_consumption > 0 else 0.0
        )

        panicked_states = {"panicked", "anxious", "angry", "vindictive"}
        n_panicked = sum(1 for e in emotional_states if e in panicked_states)
        pct_panicked = n_panicked / len(emotional_states) if emotional_states else 0.0

        avg_fill = sum(fill_rates) / len(fill_rates) if fill_rates else 1.0

        if pct_panicked > 0.6:
            sentiment = "panic"
        elif pct_panicked > 0.3:
            sentiment = "fearful"
        elif avg_fill < 0.6:
            sentiment = "distressed"
        elif avg_fill > 0.85 and pct_panicked < 0.2:
            sentiment = "stable"
        else:
            sentiment = "uncertain"

        if self._prev_avg_price is not None and avg_price > 0:
            pct_change = (avg_price - self._prev_avg_price) / self._prev_avg_price if self._prev_avg_price > 0 else 0
            if pct_change > 0.05:
                price_trend = "rising"
            elif pct_change < -0.05:
                price_trend = "falling"
            else:
                price_trend = "stable"
        else:
            price_trend = "stable"
        self._prev_avg_price = avg_price

        if demand_vs_supply > 1.3 and pct_panicked > 0.4:
            bullwhip_risk = "extreme"
        elif demand_vs_supply > 1.15 or pct_panicked > 0.3:
            bullwhip_risk = "high"
        elif demand_vs_supply > 1.0:
            bullwhip_risk = "moderate"
        else:
            bullwhip_risk = "low"

        # Supply-crunch severity from ENDOGENOUS state (fill rate + dem/sup ratio)
        # rather than historical utilization. Lets crunch emerge when supply
        # actually fails to meet demand, not because we told agents so.
        if avg_fill < 0.40 and demand_vs_supply > 1.25:
            crunch = "crisis"
        elif avg_fill < 0.60 and demand_vs_supply > 1.10:
            crunch = "severe"
        elif avg_fill < 0.80:
            crunch = "moderate"
        elif avg_fill < 0.95:
            crunch = "mild"
        else:
            crunch = "none"

        state = MarketState(
            round=current_round,
            period=historical.period,
            foundry_utilization_pct=historical.foundry_utilization_pct,
            auto_production_index=historical.auto_production_index,
            chip_spot_price_index=historical.chip_spot_price_index,
            lead_time_weeks=historical.lead_time_weeks,
            real_events=historical.real_events,
            aggregate_demand_vs_supply=round(demand_vs_supply, 2),
            avg_price_offered=round(avg_price, 2),
            industry_inventory_weeks=round(inv_weeks, 1),
            market_sentiment=sentiment,
            pct_agents_panicked=round(pct_panicked, 2),
            avg_fill_rate=round(avg_fill, 2),
            total_hoarded_units=total_hoarded,
            price_trend=price_trend,
            bullwhip_risk=bullwhip_risk,
            supply_crunch_severity=crunch,
        )

        self.history.append(state)
        return state

    def format_for_prompt(self, state: MarketState, tier: str) -> str:
        """Format market state for an agent's decision prompt.

        Surfaces only:
        - period label
        - news triggers from real_events (what happened in the world)
        - endogenous observables (metrics an industry participant could
          compute from their own data + public behavior of peers)
        - the tier-specific strategic lens

        Exogenous indices (foundry utilization %, chip spot price index,
        auto production index, lead-time weeks) are deliberately OMITTED
        so they cannot be used as outcome cheats.
        """
        interpretation = TIER_INTERPRETATION_FRAMES.get(tier, "")

        events_text = "\n".join(f"  - {e}" for e in state.real_events[:4])

        lines = [
            f"MARKET INTELLIGENCE — {state.period}",
            "",
            "INDUSTRY CONDITIONS (observed from your own operations and peer behavior):",
            f"  Demand/supply ratio (aggregate orders vs foundry capacity): {state.aggregate_demand_vs_supply:.2f}x",
            f"  Industry avg fill rate last round: {state.avg_fill_rate:.0%}",
            f"  Industry inventory: {state.industry_inventory_weeks:.1f} weeks of supply",
            f"  Market sentiment: {state.market_sentiment.upper()}",
            f"  Fraction of partners in distress: {state.pct_agents_panicked:.0%}",
            f"  Units held in reserve industry-wide: {state.total_hoarded_units}",
            f"  Price trend last round: {state.price_trend}",
            f"  Bullwhip risk (derived): {state.bullwhip_risk.upper()}",
            f"  Supply crunch (derived): {state.supply_crunch_severity.upper()}",
        ]

        if events_text:
            lines.append("")
            lines.append("REAL-WORLD NEWS THIS QUARTER:")
            lines.append(events_text)

        if interpretation:
            lines.append("")
            lines.append(f"STRATEGIC LENS ({tier.upper()}):")
            lines.append(f"  {interpretation}")

        return "\n".join(lines)

    def get_brief_summary(self, state: MarketState) -> str:
        """Short summary for signal generation and memory storage.

        Endogenous-only, mirrors format_for_prompt's scope.
        """
        return (
            f"{state.period}: sentiment={state.market_sentiment}, "
            f"avg fill={state.avg_fill_rate:.0%}, "
            f"bullwhip risk={state.bullwhip_risk}, "
            f"crunch={state.supply_crunch_severity}, "
            f"price trend={state.price_trend}."
        )
