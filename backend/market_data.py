"""Historical market data and observable market environment.

Grounds the simulation in real semiconductor market conditions (2020-2022)
and provides a shared observable market state that all agents can see —
the equivalent of a "Bloomberg terminal" for the supply chain.

This is the key missing piece for emergent behavior: agents reason not just
about their bilateral partners, but about the *macro* environment.  Different
personas interpret the same data differently, creating divergent strategies
from shared stimuli (the Stanford Generative Agents insight).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from agents import SupplyChainAgent

# ---------------------------------------------------------------------------
# Historical data tables — real-world semiconductor market, Q1 2020 – Q2 2022
# ---------------------------------------------------------------------------
# Sources: TSMC/Samsung earnings, OICA auto production data, Susquehanna
# lead time tracker, IHS Markit, industry press.  Values are representative
# composites rounded for simulation purposes.

@dataclass
class HistoricalQuarter:
    """Real-world market snapshot for one quarter."""
    period: str                          # e.g. "Q1 2020"
    foundry_utilization_pct: float       # TSMC+Samsung combined utilization
    auto_production_index: float         # global auto production, 1.0 = 2019 baseline
    chip_spot_price_index: float         # automotive MCU spot price, 1.0 = 2019 avg
    lead_time_weeks: float               # order-to-delivery for automotive chips
    real_events: list[str]               # actual events that happened


HISTORICAL_DATA: dict[int, HistoricalQuarter] = {
    1: HistoricalQuarter(
        period="Q1 2020",
        foundry_utilization_pct=0.87,
        auto_production_index=0.72,
        chip_spot_price_index=0.95,
        lead_time_weeks=12,
        real_events=[
            "COVID-19 pandemic shuts auto plants worldwide",
            "TSMC sees consumer electronics surge, keeps fabs running at 87%",
            "Auto OEMs cancel chip orders to conserve cash",
        ],
    ),
    2: HistoricalQuarter(
        period="Q2 2020",
        foundry_utilization_pct=0.93,
        auto_production_index=0.55,
        chip_spot_price_index=0.98,
        lead_time_weeks=14,
        real_events=[
            "Global auto production hits lowest point since 2009 financial crisis",
            "Foundries reallocate wafer starts to consumer/data center segments",
            "TSMC revenue rises 29% YoY despite automotive collapse",
        ],
    ),
    3: HistoricalQuarter(
        period="Q3 2020",
        foundry_utilization_pct=0.96,
        auto_production_index=0.82,
        chip_spot_price_index=1.05,
        lead_time_weeks=17,
        real_events=[
            "China auto sales recover to 2019 levels; US/EU lagging",
            "OEMs try to reinstate canceled orders — foundry slots taken",
            "Lead times extend past 4 months for first time since 2018",
        ],
    ),
    4: HistoricalQuarter(
        period="Q4 2020",
        foundry_utilization_pct=0.99,
        auto_production_index=0.98,
        chip_spot_price_index=1.20,
        lead_time_weeks=22,
        real_events=[
            "VW halts production at Wolfsburg plant — first major OEM shutdown",
            "Continental warns of 'severe semiconductor bottleneck'",
            "TSMC reports foundry utilization approaching 100%",
            "Spot prices for automotive MCUs rise 20% above contract",
        ],
    ),
    5: HistoricalQuarter(
        period="Q1 2021",
        foundry_utilization_pct=1.00,
        auto_production_index=0.95,
        chip_spot_price_index=1.80,
        lead_time_weeks=26,
        real_events=[
            "Ford idles 7 plants; GM cuts Silverado/Sierra production",
            "Industry losses projected at $110B for the year",
            "Double-ordering rampant — true demand obscured by 30-40%",
            "Texas winter storm knocks out Samsung Austin fab for 6 weeks",
            "Suez Canal blockage disrupts component shipments",
        ],
    ),
    6: HistoricalQuarter(
        period="Q2 2021",
        foundry_utilization_pct=1.00,
        auto_production_index=0.88,
        chip_spot_price_index=2.50,
        lead_time_weeks=26,
        real_events=[
            "TSMC raises automotive chip prices 15-20%",
            "Spot market prices hit 2-3x contract for some MCUs",
            "Ford/GM announce direct foundry partnerships, angering Tier-1s",
            "EU announces European Chips Act framework",
        ],
    ),
    7: HistoricalQuarter(
        period="Q3 2021",
        foundry_utilization_pct=0.98,
        auto_production_index=0.82,
        chip_spot_price_index=3.20,
        lead_time_weeks=26,
        real_events=[
            "Renesas Naka fab fire (Mar 2021 impact continues into Q3)",
            "Toyota cuts global production by 40% in September",
            "Spot prices for some MCUs reach 10x contract levels",
            "Bosch CEO calls chip shortage 'the biggest crisis in auto industry'",
        ],
    ),
    8: HistoricalQuarter(
        period="Q4 2021",
        foundry_utilization_pct=0.97,
        auto_production_index=0.86,
        chip_spot_price_index=2.80,
        lead_time_weeks=24,
        real_events=[
            "US CHIPS Act passes Senate; $52B in semiconductor subsidies",
            "TSMC announces $12B Arizona fab (operational ~2024)",
            "Samsung announces $17B Taylor TX fab",
            "Inventory hoarding hits record — dealers sitting on unsold cars with missing chips",
        ],
    ),
    9: HistoricalQuarter(
        period="Q1 2022",
        foundry_utilization_pct=0.95,
        auto_production_index=0.90,
        chip_spot_price_index=2.20,
        lead_time_weeks=20,
        real_events=[
            "Supply gradually improving but behavioral distortions persist",
            "Apparent demand 30% higher than real demand due to phantom orders",
            "Some OEMs sitting on excess inventory from panic ordering",
            "Russia-Ukraine war creates new uncertainty for neon gas supply (40% from Ukraine)",
        ],
    ),
    10: HistoricalQuarter(
        period="Q2 2022",
        foundry_utilization_pct=0.92,
        auto_production_index=0.93,
        chip_spot_price_index=1.60,
        lead_time_weeks=16,
        real_events=[
            "CHIPS and Science Act signed into law (Aug 2022)",
            "Bullwhip effect: order cancellations cascade upstream",
            "Consumer electronics demand crashes — foundries scramble to fill auto",
            "Spot prices falling rapidly as phantom demand evaporates",
            "Trust across supply chain at all-time low",
        ],
    ),
}


# ---------------------------------------------------------------------------
# Observable market state — what agents can see each round
# ---------------------------------------------------------------------------

@dataclass
class MarketState:
    """Aggregate market intelligence observable by all agents.

    This is the simulation's equivalent of public market data — every agent
    can see it, but they interpret it through their own persona lens.
    """

    round: int
    period: str

    # From historical data (exogenous)
    foundry_utilization_pct: float       # how tight is foundry capacity?
    auto_production_index: float         # how is overall auto demand?
    chip_spot_price_index: float         # what are chips trading at on spot market?
    lead_time_weeks: float               # how long to get chips?
    real_events: list[str]               # what actually happened in the real world

    # From live agent behavior (endogenous) — computed from simulation state
    aggregate_demand_vs_supply: float    # total orders / total foundry capacity
    avg_price_offered: float             # volume-weighted avg across all suppliers
    industry_inventory_weeks: float      # total inventory / weekly consumption rate
    market_sentiment: str                # derived from agent emotional states
    pct_agents_panicked: float           # fraction of agents in panic/anxious state
    avg_fill_rate: float                 # industry-wide average fill rate
    total_hoarded_units: int             # units held in reserve across all suppliers
    price_trend: str                     # "rising", "stable", "falling"

    # Derived signals
    bullwhip_risk: str                   # "low", "moderate", "high", "extreme"
    supply_crunch_severity: str          # "none", "mild", "moderate", "severe", "crisis"

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
# Same data, different lens — this is what creates divergent agent behavior
# from shared stimuli (the core Stanford insight for emergence).

TIER_INTERPRETATION_FRAMES: dict[str, str] = {
    "foundry": (
        "As a foundry, you have PRICING POWER when utilization is high. "
        "You must decide: maximize short-term margins on scarce capacity, "
        "or invest in loyalty with automotive customers who may remember "
        "your choices when the cycle turns. Governments are watching — "
        "political backlash is a real risk if you visibly neglect automotive."
    ),
    "chipDesigner": (
        "As a chip designer, you are SQUEEZED from both sides. Foundry "
        "prices are rising while your OEM/Tier-1 customers resist passing "
        "costs through. You must balance upstream sourcing security against "
        "downstream margin preservation. Your design wins are your moat — "
        "losing a customer now could mean losing them permanently."
    ),
    "tier1Supplier": (
        "As a Tier-1 supplier, you are the SHOCK ABSORBER between chip "
        "makers and auto OEMs. Your customers demand guaranteed supply AND "
        "stable prices, which is impossible in a shortage. Some OEMs are "
        "trying to go around you directly to foundries — an existential "
        "threat to your business model. Your inventory buffer is your lifeline."
    ),
    "oem": (
        "As an OEM, you are the END CONSUMER of this supply chain. Every "
        "chip you can't get means a car you can't build — and lost revenue "
        "that competitors will capture. Your competitors' procurement "
        "strategies directly affect your allocation. You must decide: pay "
        "premium prices for security, or hold the line and risk production "
        "shutdowns?"
    ),
}


# ---------------------------------------------------------------------------
# MarketEnvironment — computes observable state from historical + live data
# ---------------------------------------------------------------------------

class MarketEnvironment:
    """Computes and maintains the observable market state each round.

    Combines exogenous historical data with endogenous agent behavior to
    create a shared information environment that all agents can observe.
    """

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

            # Demand side: buyers' quarterly needs
            if agent.spec.quarterly_need > 0:
                total_demand += agent.effective_quarterly_need
                total_weekly_consumption += agent.effective_quarterly_need / 13  # ~13 weeks/quarter

            # Supply side: foundry capacity
            if agent.tier == "foundry":
                total_foundry_capacity += agent.effective_capacity

            # Inventory across all agents
            total_inventory += agent.inventory

            # Supplier pricing and hoarding
            if agent.current_decision:
                if "price_offered" in agent.current_decision:
                    prices.append(float(agent.current_decision["price_offered"]))
                if "held_in_reserve" in agent.current_decision:
                    total_hoarded += int(agent.current_decision["held_in_reserve"])

        # Aggregate metrics
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

        # Market sentiment
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

        # Price trend
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

        # Bullwhip risk assessment
        if demand_vs_supply > 1.3 and pct_panicked > 0.4:
            bullwhip_risk = "extreme"
        elif demand_vs_supply > 1.15 or pct_panicked > 0.3:
            bullwhip_risk = "high"
        elif demand_vs_supply > 1.0:
            bullwhip_risk = "moderate"
        else:
            bullwhip_risk = "low"

        # Supply crunch severity
        if historical.foundry_utilization_pct >= 0.99 and avg_fill < 0.5:
            crunch = "crisis"
        elif historical.foundry_utilization_pct >= 0.97 and avg_fill < 0.7:
            crunch = "severe"
        elif historical.foundry_utilization_pct >= 0.95:
            crunch = "moderate"
        elif historical.foundry_utilization_pct >= 0.90:
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

        Includes the tier-specific interpretation frame so the same data
        triggers different reasoning in different agents.
        """
        interpretation = TIER_INTERPRETATION_FRAMES.get(tier, "")

        # Historical trend context (show previous round for comparison)
        trend_lines = []
        if len(self.history) >= 2:
            prev = self.history[-2]
            if state.chip_spot_price_index != prev.chip_spot_price_index:
                direction = "up" if state.chip_spot_price_index > prev.chip_spot_price_index else "down"
                trend_lines.append(
                    f"  Spot price trend: {direction} from "
                    f"{prev.chip_spot_price_index:.1f}x to "
                    f"{state.chip_spot_price_index:.1f}x baseline"
                )
            if state.lead_time_weeks != prev.lead_time_weeks:
                direction = "lengthening" if state.lead_time_weeks > prev.lead_time_weeks else "shortening"
                trend_lines.append(
                    f"  Lead times {direction}: {prev.lead_time_weeks:.0f} -> "
                    f"{state.lead_time_weeks:.0f} weeks"
                )
        trend_section = "\n".join(trend_lines) if trend_lines else ""

        events_text = "\n".join(f"  - {e}" for e in state.real_events[:4])

        lines = [
            f"MARKET INTELLIGENCE — {state.period}",
            f"  Foundry utilization: {state.foundry_utilization_pct:.0%}",
            f"  Auto production index: {state.auto_production_index:.2f}x (vs 2019 baseline)",
            f"  Chip spot price index: {state.chip_spot_price_index:.1f}x (vs 2019 baseline)",
            f"  Lead time: {state.lead_time_weeks:.0f} weeks (order-to-delivery)",
            "",
            "INDUSTRY CONDITIONS (from observable market behavior):",
            f"  Demand/supply ratio: {state.aggregate_demand_vs_supply:.2f}x",
            f"  Industry avg fill rate: {state.avg_fill_rate:.0%}",
            f"  Industry inventory: {state.industry_inventory_weeks:.1f} weeks of supply",
            f"  Market sentiment: {state.market_sentiment.upper()}",
            f"  Agents in distress: {state.pct_agents_panicked:.0%}",
            f"  Units hoarded industry-wide: {state.total_hoarded_units}",
            f"  Price trend: {state.price_trend}",
            f"  Bullwhip risk: {state.bullwhip_risk.upper()}",
            f"  Supply crunch: {state.supply_crunch_severity.upper()}",
        ]

        if trend_section:
            lines.append("")
            lines.append("TRENDS:")
            lines.append(trend_section)

        if events_text:
            lines.append("")
            lines.append("REAL-WORLD EVENTS THIS QUARTER:")
            lines.append(events_text)

        if interpretation:
            lines.append("")
            lines.append(f"STRATEGIC LENS ({tier.upper()}):")
            lines.append(f"  {interpretation}")

        return "\n".join(lines)

    def get_brief_summary(self, state: MarketState) -> str:
        """Short summary for signal generation and memory storage."""
        return (
            f"{state.period}: Foundries at {state.foundry_utilization_pct:.0%} "
            f"utilization, spot prices {state.chip_spot_price_index:.1f}x baseline, "
            f"lead times {state.lead_time_weeks:.0f}wk, "
            f"sentiment: {state.market_sentiment}, "
            f"crunch: {state.supply_crunch_severity}."
        )
