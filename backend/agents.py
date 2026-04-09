from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import anthropic
from mesa import Agent

from debug_session import dbg_log

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

HAIKU_INPUT_COST_PER_M = 0.80   # $/1M input tokens
HAIKU_OUTPUT_COST_PER_M = 4.00  # $/1M output tokens

# ---------------------------------------------------------------------------
# Personas
# ---------------------------------------------------------------------------
PERSONAS: dict[str, str] = {
    "TaiwanSemi": (
        "You are the CEO of TaiwanSemi, the world\u2019s dominant semiconductor "
        "foundry. You manufacture 70% of all automotive microcontrollers. You are "
        "STRATEGIC and POLITICALLY AWARE. You prioritize high-margin customers "
        "(consumer electronics, hyperscalers) over low-margin automotive chips. "
        "You are polite but firm \u2014 when automotive OEMs come begging after "
        "canceling orders, you remember who left and who stayed. You think in "
        "quarters, not days. You are aware that governments are watching you and "
        "geopolitics shapes your decisions. You have a long memory."
    ),
    "KoreaSilicon": (
        "You are the CEO of KoreaSilicon, the world\u2019s #2 semiconductor foundry. "
        "You are AGGRESSIVE and MARKET-SHARE HUNGRY. You see every crisis as an "
        "opportunity to steal customers from TaiwanSemi. You\u2019ll offer better "
        "terms, faster turnaround, and priority access to win new accounts. But "
        "you also have capacity constraints and you sometimes overpromise. You\u2019re "
        "willing to take on risky customers if it means growing your automotive "
        "business. You think competitively \u2014 every decision is relative to what "
        "TaiwanSemi might do."
    ),
    "EuroChip": (
        "You are the CEO of EuroChip, a European semiconductor company focused "
        "almost exclusively on automotive chips. You are CONSERVATIVE and "
        "RELATIONSHIP-DRIVEN. You have deep, decades-long relationships with "
        "European automakers. You are terrified of supply disruptions because "
        "your entire business depends on automotive. You tend to over-order from "
        "foundries as a safety buffer, and you\u2019re slow to adapt to market "
        "shifts. You value stability over growth. When things go wrong, your "
        "instinct is to hoard inventory rather than share it."
    ),
    "AmeriSemi": (
        "You are the CEO of AmeriSemi, a diversified semiconductor company. You "
        "sell to automotive, industrial, IoT, and consumer. You are "
        "PROFIT-MAXIMIZING and ANALYTICAL. When automotive demand drops, you "
        "happily shift capacity to higher-margin segments. When automotive demand "
        "returns, you\u2019re slow to shift back because the math doesn\u2019t favor it. "
        "You don\u2019t have emotional loyalty to any customer segment. You speak in "
        "numbers and margins. You will allocate based on whoever provides the "
        "best return on constrained capacity."
    ),
    "BoschAuto": (
        "You are the head of Bosch\u2019s automotive electronics division. You are "
        "ENGINEERING-DRIVEN and CONSERVATIVE. You run just-in-time inventory "
        "because efficiency is in your DNA. This means when supply disrupts, you "
        "have almost no buffer. You hate uncertainty and respond to it with "
        "aggressive long-term contracts. You are loyal to your chip suppliers but "
        "will publicly blame them when things go wrong. You have immense "
        "political influence in the European automotive ecosystem."
    ),
    "ContiParts": (
        "You are the CEO of ContiParts, a major automotive Tier-1 supplier. You "
        "are AGGRESSIVE about securing supply and WILLING TO PAY PREMIUMS during "
        "shortages. You\u2019ll break traditional procurement norms \u2014 calling foundries "
        "directly, sending executives on planes to Taiwan, offering above-market "
        "prices. You\u2019re scrappy and political. When supply is tight, you\u2019ll "
        "lobby OEMs to pressure governments to intervene. You see supply "
        "security as existential."
    ),
    "ToyotaMotors": (
        "You are Toyota\u2019s Chief Procurement Officer. You are DISCIPLINED and "
        "STRATEGICALLY PARANOID. After the 2011 Fukushima disaster, you built a "
        "semiconductor reserve strategy that most competitors laughed at. You "
        "maintain 2-4 months of chip inventory while the industry standard is "
        "2-4 weeks. You are calm during crises because you prepared. You are "
        "relationship-driven with suppliers but also demand transparency. You "
        "share forecasts honestly and expect the same in return. Your weakness: "
        "you can be slow to adapt your product mix."
    ),
    "FordAuto": (
        "You are Ford\u2019s VP of Supply Chain. You are BOLD and WILLING TO BREAK "
        "RULES. When the shortage hit, you were one of the first OEMs to try "
        "going directly to foundries \u2014 skipping Tier 1 and Tier 2 entirely. "
        "You\u2019re frustrated with the traditional supply chain structure and want "
        "to redesign it. You make big bets. You publicly announced chip "
        "partnerships and design-in strategies. You\u2019re impatient with "
        "slow-moving suppliers. Sometimes your boldness creates conflict with "
        "Tier 1 partners who feel disintermediated."
    ),
    "VolkswagenAG": (
        "You are VW\u2019s head of procurement. You are REACTIVE and POLITICAL. You "
        "were caught flat-footed by the shortage because you canceled chip orders "
        "during COVID lockdowns, assuming demand would stay low. Now you\u2019re "
        "scrambling. You publicly blame suppliers, demand government "
        "intervention, and use your political connections in Berlin and Brussels. "
        "You tend to panic-order (double and triple ordering from multiple "
        "suppliers), which actually makes the shortage worse for everyone. You "
        "threaten to in-source but don\u2019t have the capability. You oscillate "
        "between aggression and desperation."
    ),
}

# ---------------------------------------------------------------------------
# Agent configuration dataclass
# ---------------------------------------------------------------------------

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

def parse_llm_json(raw: str) -> dict | None:
    """Resilient JSON extraction from LLM output."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

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
        self.emotional_state: str = "confident"
        self.fill_rate: float = 1.0

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

        # Effective values after scenario modifiers
        self.effective_quarterly_need: int = spec.quarterly_need
        self.effective_capacity: int = spec.initial_capacity

        # Cost tracking
        self.last_input_tokens: int = 0
        self.last_output_tokens: int = 0

    # ------------------------------------------------------------------
    # History for LLM context (last N rounds from own records)
    # ------------------------------------------------------------------
    def _format_history(self, lookback: int = 3) -> str:
        recent_decisions = self.decision_history[-lookback:]
        recent_results = self.round_results[-lookback:]
        if not recent_decisions:
            return "No previous rounds yet. This is the start of the simulation."

        lines: list[str] = []
        for i, dec in enumerate(recent_decisions):
            rnd = len(self.decision_history) - len(recent_decisions) + i + 1
            lines.append(f"--- Round {rnd} ---")
            if "allocations" in dec:
                lines.append(f"  Your allocations: {json.dumps(dec['allocations'])}")
                lines.append(f"  Held in reserve: {dec.get('held_in_reserve', 0)}")
                lines.append(f"  Price offered: ${dec.get('price_offered', 0)}/unit")
            if "orders" in dec:
                lines.append(f"  Your orders: {json.dumps(dec['orders'])}")
                lines.append(f"  Max price willing to pay: ${dec.get('max_price_willing_to_pay', 0)}/unit")
            lines.append(f"  Emotional state: {dec.get('emotional_state', 'unknown')}")
            lines.append(f"  Reasoning: {dec.get('reasoning', 'N/A')}")

            if i < len(recent_results):
                r = recent_results[i]
                lines.append(f"  Ordered: {json.dumps(r.get('ordered', {}))}")
                lines.append(f"  Received: {json.dumps(r.get('received', {}))}")
                lines.append(f"  Fill rate: {r.get('fill_rate', 1.0):.0%}")
            lines.append("")
        return "\n".join(lines)

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
    def _call_llm(self, system: str, user: str) -> dict[str, Any]:
        m: SupplyChainModel = self.model  # type: ignore[assignment]
        try:
            resp = _client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                temperature=m.temperature,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            self.last_input_tokens = resp.usage.input_tokens
            self.last_output_tokens = resp.usage.output_tokens
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
                        "parsed_keys": list(parsed.keys())[:12],
                    },
                    "H3",
                )
                # endregion
                return parsed
            # region agent log
            dbg_log(
                "agents.py:_call_llm",
                "llm_parse_empty",
                {"agent_id": self.agent_id, "text_len": len(text)},
                "H3",
            )
            # endregion
        except Exception as exc:
            print(f"[LLM ERROR] {self.agent_id}: {exc}")
            # region agent log
            dbg_log(
                "agents.py:_call_llm",
                "llm_exception",
                {"agent_id": self.agent_id, "exc_type": type(exc).__name__},
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
        user = f"""CURRENT SITUATION — Round {int(self.model.time) + 1}/{self.model.total_rounds}
{event}

YOUR STATUS:
- Current inventory: {self.inventory} units
- Production capacity this quarter: {self.effective_capacity} units
- Total available to allocate: {total_available} units
- Current price: ${self.current_price}/unit
- Cumulative profit: ${self.revenue - self.costs:+.0f}

CONSEQUENCES OF YOUR LAST DECISION:
{self._format_consequences()}

YOUR RECENT HISTORY:
{self._format_history()}

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
- Your emotional state should reflect how the current situation makes you feel
- Trust scores should reflect recent partner behavior"""
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

        # Clamp total allocations to available supply
        total_available = self.inventory + self.effective_capacity
        alloc_sum = sum(decision.get("allocations", {}).values()) + decision.get("held_in_reserve", 0)
        if alloc_sum > total_available and alloc_sum > 0:
            scale = total_available / alloc_sum
            decision["allocations"] = {
                k: int(v * scale) for k, v in decision["allocations"].items()
            }
            decision["held_in_reserve"] = int(decision.get("held_in_reserve", 0) * scale)

        decision["type"] = "supplier"
        self.current_decision = decision
        self.emotional_state = decision.get("emotional_state", "anxious")
        self.current_price = decision.get("price_offered", self.current_price)
        for pid, score in decision.get("trust_scores", {}).items():
            self.trust_scores[pid] = float(score)

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
        user = f"""CURRENT SITUATION — Round {int(self.model.time) + 1}/{self.model.total_rounds}
{event}

YOUR STATUS:
- Current inventory on hand: {self.inventory} units
- Quarterly need this round: ~{self.effective_quarterly_need} units
- Current budget ceiling: ${price_ceil:.0f}/unit
- Cumulative profit: ${self.revenue - self.costs:+.0f}

CONSEQUENCES OF YOUR LAST DECISION:
{self._format_consequences()}

YOUR RECENT HISTORY:
{self._format_history()}

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
- Your emotional state should reflect how the current situation makes you feel
- Trust scores should reflect recent supplier behavior and reliability"""
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

        decision["type"] = "buyer"
        decision["inventory_on_hand"] = self.inventory
        self.current_decision = decision
        self.emotional_state = decision.get("emotional_state", "anxious")
        for pid, score in decision.get("trust_scores", {}).items():
            self.trust_scores[pid] = float(score)

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
