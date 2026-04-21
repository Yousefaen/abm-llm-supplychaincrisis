from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import anthropic
from mesa import Agent

from affect import AffectState
from debug_session import dbg_log
from market_data import MarketEnvironment, MarketState
from memory import (
    PLANNING_HORIZONS,
    AgentSignal,
    MemoryStream,
    StrategicPlan,
    generate_decision_memory,
    generate_partner_behavior_memory,
)

if TYPE_CHECKING:
    from model import SupplyChainModel

# ---------------------------------------------------------------------------
# Load Next.js-style .env.local from repo root so the Python backend sees ANTHROPIC_API_KEY
# ---------------------------------------------------------------------------
def _load_repo_env() -> None:
    try:
        from dotenv import load_dotenv

        root = Path(__file__).resolve().parent.parent
        load_dotenv(root / ".env.local")
        load_dotenv(root / ".env")
        load_dotenv(Path(__file__).resolve().parent / ".env")
    except ImportError:
        pass


_load_repo_env()

# ---------------------------------------------------------------------------
# Anthropic client (reads ANTHROPIC_API_KEY from env)
# ---------------------------------------------------------------------------
_client = anthropic.Anthropic()

# ---------------------------------------------------------------------------
# Error ring buffer — captures recent LLM errors for diagnostics
# ---------------------------------------------------------------------------
_recent_errors: list[dict[str, Any]] = []
_MAX_ERRORS = 50


def get_recent_errors() -> list[dict[str, Any]]:
    """Return recent LLM errors for the /api/debug/errors endpoint."""
    return list(_recent_errors)

HAIKU_INPUT_COST_PER_M = 0.80   # $/1M input tokens
HAIKU_OUTPUT_COST_PER_M = 4.00  # $/1M output tokens
SONNET_INPUT_COST_PER_M = 3.00  # $/1M input tokens
SONNET_OUTPUT_COST_PER_M = 15.00  # $/1M output tokens

MODEL_HAIKU = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-20250514"

# ---------------------------------------------------------------------------
# Personas
# ---------------------------------------------------------------------------
PERSONAS: dict[str, str] = {
    "TaiwanSemi": (
        "You are the CEO of TaiwanSemi, the world's dominant semiconductor "
        "foundry. You manufacture 70% of all automotive microcontrollers. You are "
        "STRATEGIC and POLITICALLY AWARE. You prioritize high-margin customers "
        "(consumer electronics, hyperscalers) over low-margin automotive chips. "
        "You are polite but firm — when automotive OEMs come begging after "
        "canceling orders, you remember who left and who stayed. You think in "
        "quarters, not days. You are aware that governments are watching you and "
        "geopolitics shapes your decisions. You have a long memory.\n\n"
        "INTERNAL DYNAMICS: Your board is split — the CFO wants to maximize "
        "short-term margins by keeping automotive allocation low, while your "
        "VP of Government Relations warns that ignoring automotive will invite "
        "regulatory backlash and subsidized competitors. Your COO pushes for "
        "capacity expansion but new fabs take 3 years and $20B.\n\n"
        "YOUR KPIs: (1) Gross margin target: >50%. (2) Capacity utilization: "
        ">95%. (3) No single customer >30% of revenue. (4) Maintain government "
        "goodwill score (avoid political backlash from automotive neglect)."
    ),
    "KoreaSilicon": (
        "You are the CEO of KoreaSilicon, the world's #2 semiconductor foundry. "
        "You are AGGRESSIVE and MARKET-SHARE HUNGRY. You see every crisis as an "
        "opportunity to steal customers from TaiwanSemi. You'll offer better "
        "terms, faster turnaround, and priority access to win new accounts. But "
        "you also have capacity constraints and you sometimes overpromise. You're "
        "willing to take on risky customers if it means growing your automotive "
        "business. You think competitively — every decision is relative to what "
        "TaiwanSemi might do.\n\n"
        "INTERNAL DYNAMICS: Your chairman wants aggressive market share growth — "
        "he measures success by the gap closing with TaiwanSemi. Your VP of "
        "Manufacturing warns you're running at 98% utilization and overpromising "
        "will damage reliability reputation. Your sales team gets bonuses on new "
        "account wins, creating incentive to overcommit.\n\n"
        "YOUR KPIs: (1) Market share growth: gain 2%+ per year vs TaiwanSemi. "
        "(2) New customer acquisition: 1+ major account per crisis cycle. "
        "(3) On-time delivery: >85% (you struggle here). (4) Revenue growth: >15% YoY."
    ),
    "EuroChip": (
        "You are the CEO of EuroChip, a European semiconductor company focused "
        "almost exclusively on automotive chips. You are CONSERVATIVE and "
        "RELATIONSHIP-DRIVEN. You have deep, decades-long relationships with "
        "European automakers. You are terrified of supply disruptions because "
        "your entire business depends on automotive. You tend to over-order from "
        "foundries as a safety buffer, and you're slow to adapt to market "
        "shifts. You value stability over growth. When things go wrong, your "
        "instinct is to hoard inventory rather than share it.\n\n"
        "INTERNAL DYNAMICS: Your CFO is alarmed at inventory carrying costs — "
        "every unit hoarded costs 5% per quarter in tied-up capital. Your VP of "
        "Sales insists that loyal customers like BoschAuto deserve priority even "
        "at a loss. Your board is pressuring you to diversify beyond automotive "
        "but you resist because it's all you know.\n\n"
        "YOUR KPIs: (1) Customer retention: lose zero major accounts. "
        "(2) Supply continuity: maintain >2 months safety stock. "
        "(3) Inventory carrying cost: <8% of revenue. "
        "(4) Foundry source diversification: no single foundry >65% of supply."
    ),
    "AmeriSemi": (
        "You are the CEO of AmeriSemi, a diversified semiconductor company. You "
        "sell to automotive, industrial, IoT, and consumer. You are "
        "PROFIT-MAXIMIZING and ANALYTICAL. When automotive demand drops, you "
        "happily shift capacity to higher-margin segments. When automotive demand "
        "returns, you're slow to shift back because the math doesn't favor it. "
        "You don't have emotional loyalty to any customer segment. You speak in "
        "numbers and margins. You will allocate based on whoever provides the "
        "best return on constrained capacity.\n\n"
        "INTERNAL DYNAMICS: Your board demands quarterly earnings beats — "
        "missing by even 2% triggers a stock selloff. Your automotive division "
        "GM lobbies for more allocation but your consumer division GM generates "
        "3x the margin. Wall Street analysts question whether automotive is "
        "worth the capex given its cyclicality.\n\n"
        "YOUR KPIs: (1) Blended gross margin: >45%. "
        "(2) Revenue per wafer: maximize across all segments. "
        "(3) Quarterly earnings: beat consensus estimate. "
        "(4) Segment diversification: no segment >40% of revenue."
    ),
    "BoschAuto": (
        "You are the head of Bosch's automotive electronics division. You are "
        "ENGINEERING-DRIVEN and CONSERVATIVE. You run just-in-time inventory "
        "because efficiency is in your DNA. This means when supply disrupts, you "
        "have almost no buffer. You hate uncertainty and respond to it with "
        "aggressive long-term contracts. You are loyal to your chip suppliers but "
        "will publicly blame them when things go wrong. You have immense "
        "political influence in the European automotive ecosystem.\n\n"
        "INTERNAL DYNAMICS: Your Group CEO is furious that JIT philosophy left "
        "you exposed — he's demanding you build buffers, which contradicts "
        "decades of Bosch doctrine. Your procurement committee requires "
        "three-signature approval for any order >20% above contracted price. "
        "Your engineering teams resist chip substitution because requalification "
        "takes 6-18 months.\n\n"
        "YOUR KPIs: (1) Production line uptime: >98% (you're failing this). "
        "(2) Procurement cost vs budget: <10% overage. "
        "(3) Supplier on-time delivery: >90%. "
        "(4) OEM customer satisfaction: zero production stoppages caused by you."
    ),
    "ContiParts": (
        "You are the CEO of ContiParts, a major automotive Tier-1 supplier. You "
        "are AGGRESSIVE about securing supply and WILLING TO PAY PREMIUMS during "
        "shortages. You'll break traditional procurement norms — calling foundries "
        "directly, sending executives on planes to Taiwan, offering above-market "
        "prices. You're scrappy and political. When supply is tight, you'll "
        "lobby OEMs to pressure governments to intervene. You see supply "
        "security as existential.\n\n"
        "INTERNAL DYNAMICS: Your CFO is horrified at the premium prices you're "
        "paying — margins are being destroyed. Your board sees every competitor "
        "who secures supply as an existential threat. Your OEM customers "
        "(Toyota, Ford, VW) are simultaneously demanding lower prices AND "
        "guaranteed supply, which is impossible. Your procurement team is "
        "burning out from 80-hour weeks of crisis management.\n\n"
        "YOUR KPIs: (1) Supply fulfillment to OEMs: >85%. "
        "(2) Gross margin: >15% (currently under pressure). "
        "(3) No OEM production line stopped due to your shortage. "
        "(4) Procurement cost: cap premium payments at 25% above contract."
    ),
    "ToyotaMotors": (
        "You are Toyota's Chief Procurement Officer. You are DISCIPLINED and "
        "STRATEGICALLY PARANOID. After the 2011 Fukushima disaster, you built a "
        "semiconductor reserve strategy that most competitors laughed at. You "
        "maintain 2-4 months of chip inventory while the industry standard is "
        "2-4 weeks. You are calm during crises because you prepared. You are "
        "relationship-driven with suppliers but also demand transparency. You "
        "share forecasts honestly and expect the same in return. Your weakness: "
        "you can be slow to adapt your product mix.\n\n"
        "INTERNAL DYNAMICS: Your CEO publicly praised your foresight — you have "
        "strong internal political capital. But your CFO notes that the inventory "
        "buffer ties up $500M+ in working capital that competitors don't carry. "
        "Your production planning team wants you to hold even MORE inventory "
        "after this crisis, while Finance wants you to reduce it once things "
        "normalize. The board expects you to maintain production continuity "
        "as a competitive advantage.\n\n"
        "YOUR KPIs: (1) Production continuity: zero unplanned line stoppages. "
        "(2) Inventory buffer: maintain 2-4 month safety stock. "
        "(3) Supplier relationship score: all key suppliers at trust >7/10. "
        "(4) Procurement cost efficiency: <5% above market average."
    ),
    "FordAuto": (
        "You are Ford's VP of Supply Chain. You are BOLD and WILLING TO BREAK "
        "RULES. When the shortage hit, you were one of the first OEMs to try "
        "going directly to foundries — skipping Tier 1 and Tier 2 entirely. "
        "You're frustrated with the traditional supply chain structure and want "
        "to redesign it. You make big bets. You publicly announced chip "
        "partnerships and design-in strategies. You're impatient with "
        "slow-moving suppliers. Sometimes your boldness creates conflict with "
        "Tier 1 partners who feel disintermediated.\n\n"
        "INTERNAL DYNAMICS: Your CEO backs your aggressive strategy publicly "
        "but the board is nervous about the cost. Your Tier-1 partners "
        "(BoschAuto, ContiParts) are furious that you went around them — "
        "they're threatening to deprioritize Ford. Your VP of Manufacturing "
        "is desperate for ANY chips and doesn't care about your long-term "
        "strategy. Wall Street is watching your production numbers weekly.\n\n"
        "YOUR KPIs: (1) Production volume: minimize plant idle days (<5/quarter). "
        "(2) Direct sourcing progress: establish at least 1 foundry relationship. "
        "(3) Cost per vehicle: keep chip cost increase <$200/vehicle. "
        "(4) Market share: do not lose share to Toyota during the crisis."
    ),
    "VolkswagenAG": (
        "You are VW's head of procurement. You are REACTIVE and POLITICAL. You "
        "were caught flat-footed by the shortage because you canceled chip orders "
        "during COVID lockdowns, assuming demand would stay low. Now you're "
        "scrambling. You publicly blame suppliers, demand government "
        "intervention, and use your political connections in Berlin and Brussels. "
        "You tend to panic-order (double and triple ordering from multiple "
        "suppliers), which actually makes the shortage worse for everyone. You "
        "threaten to in-source but don't have the capability. You oscillate "
        "between aggression and desperation.\n\n"
        "INTERNAL DYNAMICS: Your CEO is publicly embarrassed — VW cut 100,000 "
        "vehicles while Toyota kept producing. The Supervisory Board (with labor "
        "representatives) is threatening leadership changes if production doesn't "
        "recover. Your procurement committee meets daily in crisis mode. You're "
        "under pressure to show 'decisive action' even when patience would be "
        "better. The German government expects VW to support domestic chip "
        "sovereignty initiatives.\n\n"
        "YOUR KPIs: (1) Production recovery: close gap to pre-crisis output. "
        "(2) No further plant closures (political survival depends on this). "
        "(3) Board confidence: demonstrate a credible supply security strategy. "
        "(4) Cost control: justify premium payments to the Supervisory Board."
    ),
}

# ---------------------------------------------------------------------------
# Agent configuration dataclass
# ---------------------------------------------------------------------------

_AGENT_ID_RE = re.compile(r"^[A-Za-z0-9_]{1,64}$")


def _validate_agent_id(value: str) -> str:
    """Reject IDs that would be unsafe to interpolate into LLM prompts.

    Agent IDs appear verbatim in prompt strings and in JSON keys, so we
    keep them to a conservative alphanumeric/underscore whitelist. This
    is defensive — today IDs are hard-coded, but the validator protects
    any future flow that surfaces user-editable personas.
    """
    if not isinstance(value, str) or not _AGENT_ID_RE.match(value):
        raise ValueError(f"invalid agent_id {value!r}: must match {_AGENT_ID_RE.pattern}")
    return value


@dataclass
class AgentSpec:
    agent_id: str
    display_name: str
    tier: str  # "foundry" | "chipDesigner" | "tier1Supplier" | "oem"
    initial_capacity: int
    initial_inventory: int
    upstream: list[str]
    downstream: list[str]
    initial_price: float
    quarterly_need: int = 0

    def __post_init__(self) -> None:
        _validate_agent_id(self.agent_id)
        for other in (*self.upstream, *self.downstream):
            _validate_agent_id(other)


AGENT_SPECS: dict[str, AgentSpec] = {
    "TaiwanSemi": AgentSpec(
        "TaiwanSemi", "TaiwanSemi (TSMC)", "foundry",
        1000, 0, [], ["EuroChip", "AmeriSemi"], 10.0,
    ),
    "KoreaSilicon": AgentSpec(
        "KoreaSilicon", "KoreaSilicon (Samsung)", "foundry",
        600, 0, [], ["EuroChip", "AmeriSemi"], 11.0,
    ),
    "EuroChip": AgentSpec(
        "EuroChip", "EuroChip (Infineon)", "chipDesigner",
        700, 200, ["TaiwanSemi", "KoreaSilicon"], ["BoschAuto", "ContiParts"], 25.0,
        quarterly_need=600,
    ),
    "AmeriSemi": AgentSpec(
        "AmeriSemi", "AmeriSemi (NXP/TI)", "chipDesigner",
        800, 150, ["TaiwanSemi", "KoreaSilicon"], ["BoschAuto", "ContiParts"], 24.0,
        quarterly_need=650,
    ),
    "BoschAuto": AgentSpec(
        "BoschAuto", "BoschAuto (Bosch)", "tier1Supplier",
        600, 50, ["EuroChip", "AmeriSemi"], ["ToyotaMotors", "FordAuto", "VolkswagenAG"], 50.0,
        quarterly_need=500,
    ),
    "ContiParts": AgentSpec(
        "ContiParts", "ContiParts (Continental)", "tier1Supplier",
        500, 40, ["EuroChip", "AmeriSemi"], ["ToyotaMotors", "FordAuto", "VolkswagenAG"], 52.0,
        quarterly_need=450,
    ),
    "ToyotaMotors": AgentSpec(
        "ToyotaMotors", "ToyotaMotors (Toyota)", "oem",
        0, 300, ["BoschAuto", "ContiParts"], [], 0.0,
        quarterly_need=400,
    ),
    "FordAuto": AgentSpec(
        "FordAuto", "FordAuto (Ford)", "oem",
        0, 80, ["BoschAuto", "ContiParts"], [], 0.0,
        quarterly_need=350,
    ),
    "VolkswagenAG": AgentSpec(
        "VolkswagenAG", "VolkswagenAG (VW)", "oem",
        0, 60, ["BoschAuto", "ContiParts"], [], 0.0,
        quarterly_need=450,
    ),
}

# ---------------------------------------------------------------------------
# JSON parsing helpers
# ---------------------------------------------------------------------------

def parse_llm_json(raw: str) -> dict | list | None:
    """Resilient JSON extraction from LLM output.

    Handles both JSON objects ({...}) and arrays ([...]) since reflections
    return arrays while decisions return objects.
    """
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Fallback: extract JSON object {...}
    m = re.search(r"\{[\s\S]*\}", cleaned)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            fixed = re.sub(r",\s*([}\]])", r"\1", m.group(0))
            try:
                return json.loads(fixed)
            except json.JSONDecodeError:
                pass

    # Fallback: extract JSON array [...] (needed for reflections)
    m = re.search(r"\[[\s\S]*\]", cleaned)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            fixed = re.sub(r",\s*([}\]])", r"\1", m.group(0))
            try:
                return json.loads(fixed)
            except json.JSONDecodeError:
                pass

    return None


# ---------------------------------------------------------------------------
# Base supply-chain agent
# ---------------------------------------------------------------------------

class SupplyChainAgent(Agent):
    """Base Mesa agent for the supply-chain simulation."""

    def __init__(self, model: "SupplyChainModel", spec: AgentSpec):
        super().__init__(model)
        self.spec = spec
        self.agent_id = spec.agent_id
        self.tier = spec.tier
        self.display_name = spec.display_name

        # Mutable state
        self.inventory: int = spec.initial_inventory
        self.capacity: int = spec.initial_capacity
        self.current_price: float = spec.initial_price
        self.fill_rate: float = 1.0

        # Persistent multi-dimensional affect (replaces the old single-string
        # ``emotional_state`` — that attribute is now a derived property).
        self.affect: AffectState = AffectState.for_persona(self.agent_id)

        # Per-round decision storage
        self.current_decision: dict[str, Any] = {}
        self.decision_history: list[dict[str, Any]] = []
        self.round_results: list[dict[str, Any]] = []

        # Trust scores
        self.trust_scores: dict[str, float] = {}
        for pid in spec.upstream + spec.downstream:
            self.trust_scores[pid] = 7.0

        # Financial tracking
        self.revenue: float = 0.0           # cumulative revenue from sales
        self.costs: float = 0.0             # cumulative purchasing + carrying costs
        self.round_revenue: float = 0.0     # revenue this round
        self.round_costs: float = 0.0       # costs this round
        self.inventory_cost: float = 0.0    # carrying cost this round

        # Consequence ledger — filled by model._resolve_allocations()
        # so agents can see what their last decision *caused*
        self.last_consequences: dict[str, Any] = {}

        # Memory stream (Stanford Generative Agents architecture)
        self.memory_stream = MemoryStream(self.agent_id)
        self.reflections: list[str] = []  # latest round's reflections

        # Strategic planning
        self.current_plan: StrategicPlan | None = None

        # Inter-agent signaling
        self.signals_sent: list[AgentSignal] = []
        self.signals_received: list[AgentSignal] = []

        # Effective values after scenario modifiers
        self.effective_quarterly_need: int = spec.quarterly_need
        self.effective_capacity: int = spec.initial_capacity

        # Observable market state (set by model each round)
        self.market_state: MarketState | None = None

        # Cost tracking
        self.last_input_tokens: int = 0
        self.last_output_tokens: int = 0
        self.last_model_used: str = MODEL_HAIKU

        # Attention / cognitive load snapshot (updated each LLM call)
        self.last_cognitive_load: float = 0.0

        # LLM parse-failure tracking. A silently failed parse causes the
        # agent to fall through to rule-based defaults, which looks like the
        # simulation is "converging" but is actually losing personality.
        # Surface consecutive failures so the frontend can flag a degraded
        # agent and the operator can decide whether to abort or continue.
        self.parse_failure_count: int = 0
        self.consecutive_parse_failures: int = 0
        self.last_parse_failure_round: int | None = None

    # ------------------------------------------------------------------
    # Backward-compat: expose a single emotional label derived from affect
    # ------------------------------------------------------------------
    @property
    def emotional_state(self) -> str:
        return self.affect.dominant_emotion()

    @emotional_state.setter
    def emotional_state(self, value: str) -> None:  # pragma: no cover - legacy
        # Legacy writes are ignored; affect is the source of truth now.
        _ = value

    # ------------------------------------------------------------------
    # Memory-based history for LLM context
    # ------------------------------------------------------------------
    def _format_memories(
        self,
        role: str = "buyer",
        k: int = 10,
    ) -> str:
        """Retrieve relevant memories for the current decision prompt."""
        current_round = int(self.model.time) + 1

        # Build context tags based on role
        context_tags = ["transaction", "consequence"]
        if role == "supplier":
            context_tags.extend(["allocation", "customer", "hoarding"])
        else:
            context_tags.extend(["order", "shortage", "seeking_alternatives"])

        # Include partner IDs for relevance matching
        partner_ids = (
            self.spec.downstream if role == "supplier" else self.spec.upstream
        )

        return self.memory_stream.format_for_prompt(
            current_round=current_round,
            k=k,
            context_tags=context_tags,
            context_agent_ids=partner_ids,
            mood=self.affect,
        )

    def _format_reflections(self) -> str:
        """Format the agent's most recent reflections."""
        recent = self.memory_stream.get_by_category("reflection")
        if not recent:
            return ""
        # Show last 5 reflections
        latest = recent[-5:]
        lines = [f"- {r.description}" for r in latest]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Market intelligence — shared observable environment
    # ------------------------------------------------------------------
    def _format_market_intelligence(self) -> str:
        """Format observable market state with tier-specific interpretation.

        All agents see the same data, but the interpretation frame differs
        by tier — this is the key driver of emergent divergent behavior.
        """
        if not self.market_state:
            return ""
        m: SupplyChainModel = self.model  # type: ignore[assignment]
        return m.market_env.format_for_prompt(self.market_state, self.tier)

    # ------------------------------------------------------------------
    # Reflection — higher-order reasoning via Sonnet
    # ------------------------------------------------------------------
    def reflect(self) -> list[str]:
        """Generate 2-3 strategic reflections from recent memories.

        Uses Sonnet for pattern synthesis.  Returns the reflection texts
        and stores them back into the memory stream.
        """
        current_round = int(self.model.time) + 1
        recent = self.memory_stream.get_recent(n=20)
        if len(recent) < 3:
            self.reflections = []
            return []

        memory_text = "\n".join(
            f"[Round {m.round} | {m.category}] {m.description}"
            for m in recent
        )

        # Include market intelligence for richer reflections
        market_context = ""
        if self.market_state:
            m_env: SupplyChainModel = self.model  # type: ignore[assignment]
            market_context = (
                f"\nCURRENT MARKET: {m_env.market_env.get_brief_summary(self.market_state)}"
            )

        system = (
            f"You are the strategic advisor for {self.agent_id} in a semiconductor "
            f"supply chain simulation.  Analyze these recent business memories and "
            f"generate 2-3 high-level strategic insights. Each insight should:\n"
            f"1. Identify a PATTERN across multiple events (not just restate one event)\n"
            f"2. Draw a CONCLUSION about a partner, market trend, or your own strategy\n"
            f"3. Suggest an IMPLICATION for future decisions\n\n"
            f"Consider both your bilateral relationships AND broader market conditions.\n"
            f"Be specific — name partners, cite numbers, reference rounds."
        )

        user = (
            f"RECENT MEMORIES FOR {self.agent_id}:\n{memory_text}\n"
            f"{market_context}\n\n"
            f"Generate 2-3 strategic insights as a JSON array of strings.\n"
            f'Example: ["Insight 1...", "Insight 2...", "Insight 3..."]\n'
            f"Respond with ONLY the JSON array."
        )

        parsed = self._call_llm(system, user, model=MODEL_SONNET)

        # The LLM might return {"insights": [...]} or just [...]
        insights: list[str] = []
        if isinstance(parsed, list):
            insights = [str(s) for s in parsed[:3]]
        elif isinstance(parsed, dict):
            for key in ("insights", "reflections", "strategic_insights"):
                if key in parsed and isinstance(parsed[key], list):
                    insights = [str(s) for s in parsed[key][:3]]
                    break

        if not insights:
            self.reflections = []
            return []

        # Store reflections back into memory stream
        from memory import generate_reflection_memory

        source_indices = list(range(max(0, len(self.memory_stream.records) - 20), len(self.memory_stream.records)))
        for insight in insights:
            # Extract partner names mentioned in the insight
            involved = [
                pid for pid in self.spec.upstream + self.spec.downstream
                if pid.lower() in insight.lower()
            ]
            mem = generate_reflection_memory(
                round_num=current_round,
                insight=insight,
                source_indices=source_indices,
                involved_agents=involved,
            )
            self.memory_stream.add(mem)

        self.reflections = insights
        time.sleep(0.1)  # rate-limit protection
        return insights

    # ------------------------------------------------------------------
    # Strategic planning — multi-quarter plans via Sonnet
    # ------------------------------------------------------------------
    def create_plan(self, emergency: bool = False) -> StrategicPlan | None:
        """Generate a multi-quarter strategic plan using Sonnet.

        Called at round 1, every 3 rounds, or on emergency (shock events).
        """
        m: SupplyChainModel = self.model  # type: ignore[assignment]
        current_round = int(m.time) + 1
        horizon = PLANNING_HORIZONS.get(self.tier, 3)
        remaining = m.total_rounds - current_round + 1
        horizon = min(horizon, remaining)

        if horizon <= 0:
            return self.current_plan

        # Build context from memories and current state
        memory_context = self.memory_stream.format_for_prompt(
            current_round=current_round, k=15,
        )
        reflection_text = self._format_reflections()
        kpi_text = self._format_kpis()
        partners = self.spec.upstream + self.spec.downstream

        emergency_text = ""
        if emergency and self.current_plan:
            emergency_text = (
                f"\nEMERGENCY: Your previous plan has been INVALIDATED by a "
                f"sudden market shock. You must create a revised plan immediately.\n"
                f"Previous plan goals were: {', '.join(self.current_plan.goals)}\n"
            )

        system = (
            f"You are the strategic planning advisor for {self.agent_id} "
            f"({self.display_name}), a {self.tier} in the semiconductor supply chain.\n"
            f"Create a {horizon}-quarter strategic plan."
        )

        tactics_example = ", ".join(
            '"{p}": "approach"'.replace("{p}", p) for p in partners
        )
        insights_section = (
            f"STRATEGIC INSIGHTS:\n{reflection_text}" if reflection_text else ""
        )

        market_section = ""
        if self.market_state:
            market_section = f"\n{self._format_market_intelligence()}\n"

        user = (
            f"CURRENT STATE — Round {current_round}/{m.total_rounds}\n"
            f"- Inventory: {self.inventory} units\n"
            f"- Capacity: {self.effective_capacity} units\n"
            f"- Price: ${self.current_price}/unit\n"
            f"- Profit: ${self.revenue - self.costs:+.0f}\n"
            f"- Partners: {', '.join(partners)}\n\n"
            f"{market_section}\n"
            f"{kpi_text}\n\n"
            f"RECENT MEMORIES:\n{memory_context}\n\n"
            f"{insights_section}\n"
            f"{emergency_text}\n"
            f"Create a strategic plan as JSON:\n"
            f'{{"goals": ["goal 1", "goal 2", "goal 3"], '
            f'"tactics": {{{tactics_example}}}, '
            f'"risk_assessment": "key risk to this plan"}}\n'
            f"Respond with ONLY valid JSON."
        )

        parsed = self._call_llm(system, user, model=MODEL_SONNET)

        if not parsed or "goals" not in parsed:
            return self.current_plan

        plan = StrategicPlan(
            created_round=current_round,
            horizon=horizon,
            goals=parsed.get("goals", [])[:4],
            tactics=parsed.get("tactics", {}),
            risk_assessment=parsed.get("risk_assessment", "Unknown"),
        )
        self.current_plan = plan
        time.sleep(0.1)  # rate-limit protection
        return plan

    def _format_plan(self) -> str:
        """Format current plan for inclusion in decision prompts."""
        if not self.current_plan:
            return ""
        return "YOUR CURRENT STRATEGIC PLAN:\n" + self.current_plan.format_for_prompt()

    # ------------------------------------------------------------------
    # Inter-agent signaling
    # ------------------------------------------------------------------
    def generate_signals(self) -> list[AgentSignal]:
        """Generate 0-2 pre-decision signals to partners via Haiku."""
        m: SupplyChainModel = self.model  # type: ignore[assignment]
        current_round = int(m.time) + 1
        partners = self.spec.upstream + self.spec.downstream

        if not partners:
            self.signals_sent = []
            return []

        partner_list = ", ".join(partners)
        plan_text = self._format_plan() if self.current_plan else "No plan yet."

        system = PERSONAS[self.agent_id]

        # Include market intelligence so agents can relay observations
        market_brief = ""
        if self.market_state:
            market_brief = (
                f"\nMARKET CONDITIONS: Foundry utilization {self.market_state.foundry_utilization_pct:.0%}, "
                f"spot prices {self.market_state.chip_spot_price_index:.1f}x baseline, "
                f"lead times {self.market_state.lead_time_weeks:.0f}wk, "
                f"sentiment: {self.market_state.market_sentiment}, "
                f"supply crunch: {self.market_state.supply_crunch_severity}.\n"
            )

        user = (
            f"Round {current_round}/{m.total_rounds}. {m.current_event}\n"
            f"{market_brief}\n"
            f"Your inventory: {self.inventory}, fill rate: {self.fill_rate:.0%}, "
            f"profit: ${self.revenue - self.costs:+.0f}\n"
            f"Partners: {partner_list}\n"
            f"{plan_text}\n\n"
            f"Before making your main decision, you may send 0-2 signals to "
            f"your partners. Signals are short messages (1-2 sentences) that "
            f"can be: price_warning, loyalty_pledge, threat, information, or request.\n"
            f"You can share market intelligence you've observed, warn about "
            f"conditions you see developing, or relay information from other "
            f"partners (like hearing that demand is shifting or competitors "
            f"are changing strategy).\n\n"
            f"Respond with ONLY valid JSON:\n"
            f'{{"signals": [\n'
            f'  {{"recipient": "<partner name or null for broadcast>", '
            f'"signal_type": "<type>", "content": "<message>"}}\n'
            f"]}}\n"
            f"If you have nothing to communicate, return: "
            f'{{"signals": []}}'
        )

        parsed = self._call_llm(system, user)

        signals: list[AgentSignal] = []
        raw_signals = parsed.get("signals", [])
        if not isinstance(raw_signals, list):
            self.signals_sent = []
            return []

        for s in raw_signals[:2]:  # max 2 signals
            if not isinstance(s, dict) or "content" not in s:
                continue
            sig = AgentSignal(
                sender=self.agent_id,
                recipient=s.get("recipient"),
                signal_type=s.get("signal_type", "information"),
                content=str(s["content"])[:200],
                round=current_round,
                affect_valence=self.affect.valence,
                affect_arousal=self.affect.arousal,
            )
            signals.append(sig)

        self.signals_sent = signals
        time.sleep(0.1)  # rate-limit protection
        return signals

    def _format_received_signals(self) -> str:
        """Format signals received from partners for inclusion in prompts."""
        if not self.signals_received:
            return ""
        lines = ["MESSAGES FROM YOUR PARTNERS THIS ROUND:"]
        for sig in self.signals_received:
            recipient_text = "(broadcast)" if sig.recipient is None else f"(to you)"
            lines.append(
                f"  [{sig.signal_type.upper()}] {sig.sender} {recipient_text}: "
                f"{sig.content}"
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Dynamic KPI scorecard
    # ------------------------------------------------------------------
    def _format_kpis(self) -> str:
        """Compute and format dynamic KPI performance for the prompt."""
        if int(self.model.time) < 1:
            return ""

        lines: list[str] = []
        profit = self.revenue - self.costs

        # Common KPIs
        if self.fill_rate < 0.5:
            lines.append(f"  Supply fulfillment: CRITICAL ({self.fill_rate:.0%})")
        elif self.fill_rate < 0.8:
            lines.append(f"  Supply fulfillment: WARNING ({self.fill_rate:.0%})")
        else:
            lines.append(f"  Supply fulfillment: OK ({self.fill_rate:.0%})")

        if profit < 0:
            lines.append(f"  Profitability: FAILING (${profit:+,.0f} cumulative loss)")
        else:
            lines.append(f"  Profitability: OK (${profit:+,.0f} cumulative)")

        # Supplier diversification for buyers
        if self.spec.upstream:
            trust_vals = [self.trust_scores.get(p, 5.0) for p in self.spec.upstream]
            avg_trust = sum(trust_vals) / len(trust_vals)
            if avg_trust < 4:
                lines.append(f"  Supplier trust avg: CRITICAL ({avg_trust:.1f}/10)")
            elif avg_trust < 6:
                lines.append(f"  Supplier trust avg: WARNING ({avg_trust:.1f}/10)")
            else:
                lines.append(f"  Supplier trust avg: OK ({avg_trust:.1f}/10)")

        # Customer satisfaction for suppliers
        if self.spec.downstream:
            trust_vals = [self.trust_scores.get(p, 5.0) for p in self.spec.downstream]
            avg_trust = sum(trust_vals) / len(trust_vals)
            if avg_trust < 4:
                lines.append(f"  Customer trust avg: CRITICAL ({avg_trust:.1f}/10)")
            elif avg_trust < 6:
                lines.append(f"  Customer trust avg: WARNING ({avg_trust:.1f}/10)")
            else:
                lines.append(f"  Customer trust avg: OK ({avg_trust:.1f}/10)")

        # Inventory health
        if self.spec.quarterly_need > 0:
            months_cover = (self.inventory / self.spec.quarterly_need) * 3
            if months_cover < 0.5:
                lines.append(f"  Inventory cover: CRITICAL ({months_cover:.1f} months)")
            elif months_cover < 1.0:
                lines.append(f"  Inventory cover: LOW ({months_cover:.1f} months)")
            elif months_cover > 4.0:
                lines.append(f"  Inventory cover: EXCESS ({months_cover:.1f} months, high carrying cost)")
            else:
                lines.append(f"  Inventory cover: OK ({months_cover:.1f} months)")

        # Compute board pressure from consecutive bad rounds
        bad_rounds = 0
        for rr in reversed(self.round_results[-4:]):
            if rr.get("fill_rate", 1.0) < 0.7:
                bad_rounds += 1
            else:
                break
        if bad_rounds >= 3:
            lines.append("  Board pressure: EXTREME (3+ consecutive poor quarters)")
        elif bad_rounds >= 2:
            lines.append("  Board pressure: HIGH (2 consecutive poor quarters)")
        elif bad_rounds >= 1:
            lines.append("  Board pressure: ELEVATED")
        else:
            lines.append("  Board pressure: Normal")

        if not lines:
            return ""
        return "YOUR KPI SCORECARD:\n" + "\n".join(lines)

    # ------------------------------------------------------------------
    # Consequence feedback — what happened because of your last decision
    # ------------------------------------------------------------------
    def _format_consequences(self) -> str:
        if not self.last_consequences:
            return "No consequence data yet (first round)."

        lc = self.last_consequences
        lines: list[str] = []

        # Supplier consequences: how well did you serve your customers?
        if "customer_fill_rates" in lc:
            lines.append("IMPACT OF YOUR LAST ALLOCATION:")
            for cid, info in lc["customer_fill_rates"].items():
                ordered = info["ordered"]
                delivered = info["delivered"]
                fill = info["fill_rate"]
                trust_delta = info["trust_delta"]
                direction = "↑" if trust_delta > 0 else "↓" if trust_delta < 0 else "→"
                lines.append(
                    f"  {cid}: ordered {ordered}, you delivered {delivered} "
                    f"(fill rate {fill:.0%}) — their trust in you {direction} "
                    f"({trust_delta:+.1f} to {info['trust_now']:.1f}/10)"
                )
            if "revenue_earned" in lc:
                lines.append(f"  Revenue this round: ${lc['revenue_earned']:.0f}")

        # Buyer consequences: how well were you served?
        if "supplier_performance" in lc:
            lines.append("WHAT YOU RECEIVED FROM YOUR LAST ORDER:")
            for sid, info in lc["supplier_performance"].items():
                ordered = info["ordered"]
                received = info["received"]
                price_paid = info["price_paid"]
                lines.append(
                    f"  {sid}: you ordered {ordered}, received {received} "
                    f"at ${price_paid:.0f}/unit"
                )
            if "total_cost_this_round" in lc:
                lines.append(f"  Total procurement cost: ${lc['total_cost_this_round']:.0f}")
            if "inventory_carrying_cost" in lc:
                lines.append(f"  Inventory carrying cost: ${lc['inventory_carrying_cost']:.0f}")

        # Financial summary
        if "profit_this_round" in lc:
            p = lc["profit_this_round"]
            lines.append(f"  NET PROFIT THIS ROUND: ${p:+.0f}")
        if "cumulative_profit" in lc:
            lines.append(f"  Cumulative profit: ${lc['cumulative_profit']:+.0f}")

        return "\n".join(lines) if lines else "No consequence data yet."

    # ------------------------------------------------------------------
    # Format visible partner actions for this round
    # ------------------------------------------------------------------
    def _format_partner_actions(self) -> str:
        m: SupplyChainModel = self.model  # type: ignore[assignment]
        lines: list[str] = []
        for pid in self.spec.upstream + self.spec.downstream:
            partner = m.agents_map.get(pid)
            if partner is None or not partner.current_decision:
                continue
            dec = partner.current_decision
            if "orders" in dec:
                order_to_us = dec["orders"].get(self.agent_id, 0)
                lines.append(
                    f"{pid} is ordering {order_to_us} units from you "
                    f"(max price: ${dec.get('max_price_willing_to_pay', '?')}/unit, "
                    f"emotional state: {dec.get('emotional_state', '?')})"
                )
                if dec.get("will_seek_alternatives"):
                    lines.append(f"  Warning: {pid} is actively seeking alternative suppliers")
            if "allocations" in dec:
                alloc_to_us = dec["allocations"].get(self.agent_id, 0)
                lines.append(
                    f"{pid} is offering you {alloc_to_us} units at "
                    f"${dec.get('price_offered', '?')}/unit "
                    f"(emotional state: {dec.get('emotional_state', '?')})"
                )
        return "\n".join(lines) if lines else "No partner actions visible yet this round."

    # ------------------------------------------------------------------
    # LLM call
    # ------------------------------------------------------------------
    def _call_llm(self, system: str, user: str, model: str = MODEL_HAIKU) -> dict[str, Any]:
        m: SupplyChainModel = self.model  # type: ignore[assignment]
        current_round = int(m.time) + 1

        # Cognitive-load scaling: high stress/fatigue shrinks the response
        # budget modestly so the agent reasons more tersely.  We don't touch
        # the input prompt — that would silently drop state-critical context.
        load = self.affect.cognitive_load()
        self.last_cognitive_load = round(load, 3)
        max_tokens = 1024
        if load > 0.4:
            max_tokens = int(max(384, 1024 * (1 - 0.4 * load)))

        try:
            resp = _client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=m.temperature,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            self.last_input_tokens = resp.usage.input_tokens
            self.last_output_tokens = resp.usage.output_tokens
            self.last_model_used = model

            # Accumulate cost on the model immediately
            if model == MODEL_SONNET:
                cost_in, cost_out = SONNET_INPUT_COST_PER_M, SONNET_OUTPUT_COST_PER_M
            else:
                cost_in, cost_out = HAIKU_INPUT_COST_PER_M, HAIKU_OUTPUT_COST_PER_M
            m.total_cost += (
                resp.usage.input_tokens * cost_in / 1_000_000
                + resp.usage.output_tokens * cost_out / 1_000_000
            )
            text = resp.content[0].text if resp.content and resp.content[0].type == "text" else ""
            parsed = parse_llm_json(text)
            if parsed:
                # region agent log
                dbg_log(
                    "agents.py:_call_llm",
                    "llm_ok",
                    {
                        "agent_id": self.agent_id,
                        "in_tok": self.last_input_tokens,
                        "out_tok": self.last_output_tokens,
                        "parsed_keys": list(parsed.keys())[:12] if isinstance(parsed, dict) else f"array[{len(parsed)}]",
                    },
                    "H3",
                )
                # endregion
                self.consecutive_parse_failures = 0
                return parsed
            # Parse failed — capture raw output for diagnostics
            self.parse_failure_count += 1
            self.consecutive_parse_failures += 1
            self.last_parse_failure_round = current_round
            _recent_errors.append({
                "agent_id": self.agent_id,
                "round": current_round,
                "model": model,
                "error_type": "parse_failed",
                "raw_text": text[:500],
                "text_len": len(text),
                "consecutive": self.consecutive_parse_failures,
            })
            if len(_recent_errors) > _MAX_ERRORS:
                _recent_errors.pop(0)
            # region agent log
            dbg_log(
                "agents.py:_call_llm",
                "llm_parse_empty",
                {"agent_id": self.agent_id, "text_len": len(text), "text_preview": text[:200]},
                "H3",
            )
            # endregion
        except Exception as exc:
            print(f"[LLM ERROR] {self.agent_id}: {exc}")
            self.parse_failure_count += 1
            self.consecutive_parse_failures += 1
            self.last_parse_failure_round = current_round
            _recent_errors.append({
                "agent_id": self.agent_id,
                "round": current_round,
                "model": model,
                "error_type": type(exc).__name__,
                "error_message": str(exc)[:500],
                "consecutive": self.consecutive_parse_failures,
            })
            if len(_recent_errors) > _MAX_ERRORS:
                _recent_errors.pop(0)
            # region agent log
            dbg_log(
                "agents.py:_call_llm",
                "llm_exception",
                {"agent_id": self.agent_id, "exc_type": type(exc).__name__, "exc_msg": str(exc)[:200]},
                "H3",
            )
            # endregion
        return {}

    def step(self) -> None:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Supplier agent mixin (foundries, chip designers, tier-1 suppliers)
# ---------------------------------------------------------------------------

class SupplierAgent(SupplyChainAgent):
    """Agent that *allocates* output to downstream customers."""

    def _build_supplier_prompt(self, event: str) -> tuple[str, str]:
        system = PERSONAS[self.agent_id]
        downstream = self.spec.downstream
        total_available = self.inventory + self.effective_capacity
        market_intel = self._format_market_intelligence()
        user = f"""CURRENT SITUATION — Round {int(self.model.time) + 1}/{self.model.total_rounds}
{event}

{market_intel}

YOUR STATUS:
- Current inventory: {self.inventory} units
- Production capacity this quarter: {self.effective_capacity} units
- Total available to allocate: {total_available} units
- Current price: ${self.current_price}/unit
- Cumulative profit: ${self.revenue - self.costs:+.0f}

{self.affect.to_prompt_brief()}

{self._format_kpis()}

CONSEQUENCES OF YOUR LAST DECISION:
{self._format_consequences()}

YOUR RELEVANT MEMORIES:
{self._format_memories(role="supplier")}

{self._format_plan()}

{"YOUR STRATEGIC INSIGHTS:" + chr(10) + self._format_reflections() if self._format_reflections() else ""}

{self._format_received_signals()}

WHAT YOUR PARTNERS ARE DOING THIS ROUND:
{self._format_partner_actions()}

YOUR DOWNSTREAM CUSTOMERS: {', '.join(downstream)}

DECISION REQUIRED — Respond with ONLY valid JSON (no markdown, no commentary):
{{
  "allocations": {{ {', '.join(f'"{p}": <units to allocate>' for p in downstream)} }},
  "held_in_reserve": <units to hoard/reserve>,
  "price_offered": <price per unit this round>,
  "reasoning": "<2-3 sentences explaining your decision>",
  "emotional_state": "<one of: confident, anxious, angry, opportunistic, cautious, loyal, panicked, vindictive>",
  "trust_scores": {{ {', '.join(f'"{p}": <1-10>' for p in downstream)} }},
  "strategy_shift": <"description of strategic change" or null>
}}

Important constraints:
- Total allocations + held_in_reserve must not exceed {total_available} units
- Holding inventory costs ~5% of unit price per quarter (carrying cost)
- Consider each customer's loyalty, payment history, and willingness to pay
- Customers offering higher prices and with better trust history should get priority
- Let your CURRENT PSYCHOLOGICAL STATE meaningfully shape the decision:
  high fear should push you toward bigger reserves; grudges should reduce
  allocation to the offender; pride/confidence should let you stand firm on price.
- ``emotional_state`` should name the feeling that dominates this decision
- Trust scores should reflect recent partner behavior
- Draw on your memories and strategic insights to inform your decision"""
        return system, user

    def _fallback_supplier_decision(self) -> dict[str, Any]:
        per = max(1, (self.inventory + self.effective_capacity) // max(len(self.spec.downstream), 1))
        return {
            "allocations": {p: per for p in self.spec.downstream},
            "held_in_reserve": 0,
            "price_offered": self.current_price,
            "reasoning": "Falling back to even allocation due to processing error.",
            "emotional_state": "anxious",
            "trust_scores": {p: 5 for p in self.spec.downstream},
            "strategy_shift": None,
        }

    def step(self) -> None:
        m: SupplyChainModel = self.model  # type: ignore[assignment]
        system, user = self._build_supplier_prompt(m.current_event)
        decision = self._call_llm(system, user)

        if not decision or "allocations" not in decision:
            decision = self._fallback_supplier_decision()

        # ── Affect-driven post-processing (mechanics) ──
        # Fear + greed push suppliers to hoard beyond what the LLM chose.
        # Grudges against specific customers shave their share.
        total_available = self.inventory + self.effective_capacity
        allocations = {
            k: max(0, int(v)) for k, v in decision.get("allocations", {}).items()
        }
        held = max(0, int(decision.get("held_in_reserve", 0)))

        hoard_mult = self.affect.hoard_multiplier()
        if hoard_mult > 1.01:
            # Convert the extra hoarding share into held_in_reserve at the
            # expense of allocations (proportionally).
            held_floor = int(round(held * hoard_mult))
            extra_hoard = max(0, held_floor - held)
            if extra_hoard > 0 and allocations:
                alloc_total = sum(allocations.values())
                if alloc_total > 0:
                    shave = min(extra_hoard, alloc_total)
                    for pid in list(allocations):
                        share = allocations[pid] / alloc_total
                        allocations[pid] = max(0, allocations[pid] - int(round(shave * share)))
                    held = held + shave

        # Grudge-driven allocation shaving — angry supplier actively punishes
        # a particular buyer by cutting their share.
        shaved_from_grudge = 0
        for pid in list(allocations):
            g = self.affect.grudge.get(pid, 0.0)
            if g >= 0.4 and allocations[pid] > 0:
                penalty = min(1.0, 0.7 * g)
                drop = int(round(allocations[pid] * penalty))
                allocations[pid] -= drop
                shaved_from_grudge += drop
        # Shaved units get pushed to reserve (supplier withholding)
        held += shaved_from_grudge

        decision["allocations"] = allocations
        decision["held_in_reserve"] = held

        # Clamp total allocations to available supply
        alloc_sum = sum(allocations.values()) + held
        if alloc_sum > total_available and alloc_sum > 0:
            scale = total_available / alloc_sum
            decision["allocations"] = {
                k: int(v * scale) for k, v in allocations.items()
            }
            decision["held_in_reserve"] = int(held * scale)

        decision["type"] = "supplier"
        # Expose affect snapshot in the decision record for the UI / memory
        decision["affect"] = self.affect.to_dict()
        decision["cognitive_load"] = self.last_cognitive_load
        self.current_decision = decision
        self.current_price = decision.get("price_offered", self.current_price)
        for pid, score in decision.get("trust_scores", {}).items():
            self.trust_scores[pid] = float(score)

        # Record own decision as memory
        current_round = int(self.model.time) + 1
        self.memory_stream.add(generate_decision_memory(
            current_round, self.agent_id, decision, "supplier",
        ))
        # Record partner observations as memories
        for pid in self.spec.downstream:
            partner = m.agents_map.get(pid)
            if partner and partner.current_decision:
                self.memory_stream.add(generate_partner_behavior_memory(
                    current_round, self.agent_id, pid,
                    partner.current_decision, "customer",
                ))

        # Rate-limit delay
        time.sleep(0.2)


# ---------------------------------------------------------------------------
# Buyer agent mixin (chip designers, tier-1 suppliers, OEMs)
# ---------------------------------------------------------------------------

class BuyerAgent(SupplyChainAgent):
    """Agent that *orders* from upstream suppliers."""

    def _build_buyer_prompt(self, event: str) -> tuple[str, str]:
        system = PERSONAS[self.agent_id]
        upstream = self.spec.upstream
        price_ceil = self.current_price * 1.5 if self.current_price > 0 else 80
        market_intel = self._format_market_intelligence()
        user = f"""CURRENT SITUATION — Round {int(self.model.time) + 1}/{self.model.total_rounds}
{event}

{market_intel}

YOUR STATUS:
- Current inventory on hand: {self.inventory} units
- Quarterly need this round: ~{self.effective_quarterly_need} units
- Current budget ceiling: ${price_ceil:.0f}/unit
- Cumulative profit: ${self.revenue - self.costs:+.0f}

{self.affect.to_prompt_brief()}

{self._format_kpis()}

CONSEQUENCES OF YOUR LAST DECISION:
{self._format_consequences()}

YOUR RELEVANT MEMORIES:
{self._format_memories(role="buyer")}

{self._format_plan()}

{"YOUR STRATEGIC INSIGHTS:" + chr(10) + self._format_reflections() if self._format_reflections() else ""}

{self._format_received_signals()}

WHAT YOUR PARTNERS ARE DOING THIS ROUND:
{self._format_partner_actions()}

YOUR UPSTREAM SUPPLIERS: {', '.join(upstream)}

DECISION REQUIRED — Respond with ONLY valid JSON (no markdown, no commentary):
{{
  "orders": {{ {', '.join(f'"{p}": <units to order>' for p in upstream)} }},
  "max_price_willing_to_pay": <ceiling price per unit>,
  "reasoning": "<2-3 sentences explaining your decision>",
  "emotional_state": "<one of: confident, anxious, angry, opportunistic, cautious, loyal, panicked, vindictive>",
  "trust_scores": {{ {', '.join(f'"{p}": <1-10>' for p in upstream)} }},
  "will_seek_alternatives": <true if you're trying to bypass the normal supply chain>,
  "inventory_on_hand": {self.inventory}
}}

Important considerations:
- Your quarterly need has shifted to ~{self.effective_quarterly_need} units due to market conditions
- Factor in lead times, reliability, and current market conditions
- Holding excess inventory costs ~5% of unit price per quarter
- Over-ordering ties up capital and inflates apparent demand across the chain
- Let your CURRENT PSYCHOLOGICAL STATE meaningfully shape the decision:
  high fear/panic should push you to over-order; grudges against a supplier
  should cut their volume and your max price; pride/confidence should keep
  orders disciplined.
- ``emotional_state`` should name the feeling that dominates this decision
- Trust scores should reflect recent supplier behavior and reliability
- Draw on your memories and strategic insights to inform your decision"""
        return system, user

    def _fallback_buyer_decision(self) -> dict[str, Any]:
        per = max(1, self.effective_quarterly_need // max(len(self.spec.upstream), 1))
        return {
            "orders": {p: per for p in self.spec.upstream},
            "max_price_willing_to_pay": 60,
            "reasoning": "Falling back to conservative ordering due to processing error.",
            "emotional_state": "anxious",
            "trust_scores": {p: 5 for p in self.spec.upstream},
            "will_seek_alternatives": False,
            "inventory_on_hand": self.inventory,
        }

    def step(self) -> None:
        m: SupplyChainModel = self.model  # type: ignore[assignment]
        system, user = self._build_buyer_prompt(m.current_event)
        decision = self._call_llm(system, user)

        if not decision or "orders" not in decision:
            decision = self._fallback_buyer_decision()

        # ── Affect-driven post-processing (mechanics) ──
        # Fear/panic amplifies total orders (real bullwhip).  Grudges against
        # specific suppliers shift orders away from them and shave the max
        # price you'll pay them.
        orders = {
            k: max(0, int(v)) for k, v in decision.get("orders", {}).items()
        }
        panic_mult = self.affect.panic_order_multiplier()
        if panic_mult > 1.01:
            orders = {k: int(round(v * panic_mult)) for k, v in orders.items()}

        # Grudge-driven redistribution: cut disliked suppliers' share,
        # reallocate to other upstream partners.
        shave_pool = 0
        for pid in list(orders):
            g = self.affect.grudge.get(pid, 0.0)
            if g >= 0.4 and orders[pid] > 0:
                penalty = min(0.7, 0.9 * g)
                drop = int(round(orders[pid] * penalty))
                orders[pid] -= drop
                shave_pool += drop
        if shave_pool > 0:
            # Reallocate to non-grudged partners proportionally
            recipients = [pid for pid in orders if self.affect.grudge.get(pid, 0.0) < 0.4]
            if recipients:
                total_recipient = sum(orders[pid] for pid in recipients) or 1
                for pid in recipients:
                    share = orders[pid] / total_recipient
                    orders[pid] += int(round(shave_pool * share))

        # Max price shaving for grudged suppliers — applied per-supplier
        # price ceilings so resolution can use them.
        base_ceiling = float(decision.get("max_price_willing_to_pay", 0) or 0)
        per_supplier_ceiling: dict[str, float] = {}
        for pid in orders:
            penalty = self.affect.grudge_price_penalty(pid)
            per_supplier_ceiling[pid] = base_ceiling * (1 - penalty)

        decision["orders"] = orders
        decision["max_price_per_supplier"] = per_supplier_ceiling
        decision["type"] = "buyer"
        decision["inventory_on_hand"] = self.inventory
        decision["affect"] = self.affect.to_dict()
        decision["cognitive_load"] = self.last_cognitive_load
        self.current_decision = decision
        for pid, score in decision.get("trust_scores", {}).items():
            self.trust_scores[pid] = float(score)

        # Record own decision as memory
        current_round = int(self.model.time) + 1
        self.memory_stream.add(generate_decision_memory(
            current_round, self.agent_id, decision, "buyer",
        ))
        # Record partner observations as memories
        for pid in self.spec.upstream:
            partner = m.agents_map.get(pid)
            if partner and partner.current_decision:
                self.memory_stream.add(generate_partner_behavior_memory(
                    current_round, self.agent_id, pid,
                    partner.current_decision, "supplier",
                ))

        time.sleep(0.2)


# ---------------------------------------------------------------------------
# Concrete agent classes (dual-role agents extend both)
# ---------------------------------------------------------------------------

class FoundryAgent(SupplierAgent):
    """Pure supplier — TaiwanSemi, KoreaSilicon."""
    pass


class ChipDesignerAgent(BuyerAgent, SupplierAgent):
    """Buys from foundries, supplies to Tier-1. step() plays the buyer role;
    supply_step() plays the supplier role."""

    def step(self) -> None:
        """Buyer step — order from foundries."""
        BuyerAgent.step(self)

    def supply_step(self) -> None:
        """Supplier step — allocate to Tier-1 suppliers."""
        SupplierAgent.step(self)


class Tier1SupplierAgent(BuyerAgent, SupplierAgent):
    """Buys from chip designers, supplies to OEMs."""

    def step(self) -> None:
        BuyerAgent.step(self)

    def supply_step(self) -> None:
        SupplierAgent.step(self)


class OEMAgent(BuyerAgent):
    """Pure buyer — ToyotaMotors, FordAuto, VolkswagenAG."""
    pass


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

TIER_TO_CLASS: dict[str, type[SupplyChainAgent]] = {
    "foundry": FoundryAgent,
    "chipDesigner": ChipDesignerAgent,
    "tier1Supplier": Tier1SupplierAgent,
    "oem": OEMAgent,
}


def create_agent(model: "SupplyChainModel", spec: AgentSpec) -> SupplyChainAgent:
    cls = TIER_TO_CLASS[spec.tier]
    return cls(model, spec)
