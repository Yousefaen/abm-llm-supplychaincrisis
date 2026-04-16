"""Memory stream and reflection system for supply-chain agents.

Adapted from the Stanford Generative Agents architecture (Park et al., 2023)
for the business/procurement domain.  Each agent maintains a chronological
memory stream of observations, decisions, and reflections.  Retrieval uses a
weighted combination of recency, importance, and relevance — no embeddings
required (tag-based relevance is sufficient for 9 agents over 10 rounds).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from affect import AffectState


# ---------------------------------------------------------------------------
# Memory record
# ---------------------------------------------------------------------------

@dataclass
class MemoryRecord:
    """A single entry in an agent's memory stream."""

    round: int                              # simulation round when this happened
    category: str                           # transaction | market | partner_behavior
                                            # | own_decision | consequence | reflection
    description: str                        # natural-language description
    importance: int                         # 1-10 (rule-based, see score_importance)
    tags: list[str] = field(default_factory=list)       # for relevance matching
    agent_ids_involved: list[str] = field(default_factory=list)
    source_indices: list[int] = field(default_factory=list)  # for reflections: pointers to source memories

    def to_dict(self) -> dict[str, Any]:
        return {
            "round": self.round,
            "category": self.category,
            "description": self.description,
            "importance": self.importance,
            "tags": self.tags,
        }


# ---------------------------------------------------------------------------
# Category-specific recency decay half-lives (in quarters/rounds)
# ---------------------------------------------------------------------------

_DECAY_HALF_LIVES: dict[str, float] = {
    "transaction": 4.0,        # price quotes fade in ~4 quarters
    "market": 3.0,             # market conditions change fast
    "partner_behavior": 8.0,   # grudges & loyalty last long
    "own_decision": 4.0,       # your own actions fade moderately
    "consequence": 6.0,        # consequences remembered longer
    "reflection": 10.0,        # synthesized insights are durable
}

_DEFAULT_HALF_LIFE = 5.0


# ---------------------------------------------------------------------------
# Rule-based importance scoring
# ---------------------------------------------------------------------------

def score_importance(
    category: str,
    *,
    fill_rate: float | None = None,
    price_change_pct: float | None = None,
    trust_score: float | None = None,
    trust_delta: float | None = None,
    is_shock_event: bool = False,
    is_seeking_alternatives: bool = False,
) -> int:
    """Assign importance 1-10 using simple business rules.  No LLM call."""

    base = 4  # default for routine events

    if category == "market":
        base = 6
        if is_shock_event:
            return 9

    if category == "reflection":
        return 8  # reflections are always high-importance

    # Fill rate signals
    if fill_rate is not None:
        if fill_rate < 0.3:
            base = max(base, 9)
        elif fill_rate < 0.5:
            base = max(base, 8)
        elif fill_rate < 0.7:
            base = max(base, 6)
        elif fill_rate >= 0.9:
            base = min(base, 3)

    # Price signals
    if price_change_pct is not None:
        if abs(price_change_pct) > 0.20:
            base = max(base, 8)
        elif abs(price_change_pct) > 0.10:
            base = max(base, 7)

    # Trust signals
    if trust_delta is not None:
        if trust_delta <= -2.0:
            base = max(base, 9)
        elif trust_delta <= -1.0:
            base = max(base, 7)
    if trust_score is not None and trust_score < 4.0:
        base = max(base, 8)

    # Partner seeking alternatives is alarming
    if is_seeking_alternatives:
        base = max(base, 8)

    return min(10, max(1, base))


# ---------------------------------------------------------------------------
# Memory stream
# ---------------------------------------------------------------------------

class MemoryStream:
    """Chronological memory store with recency/importance/relevance retrieval."""

    def __init__(self, owner_id: str):
        self.owner_id = owner_id
        self.records: list[MemoryRecord] = []

    def add(self, record: MemoryRecord) -> int:
        """Append a memory and return its index."""
        idx = len(self.records)
        self.records.append(record)
        return idx

    # ----------------------------------------------------------------
    # Retrieval
    # ----------------------------------------------------------------

    def retrieve(
        self,
        current_round: int,
        k: int = 10,
        context_tags: list[str] | None = None,
        context_agent_ids: list[str] | None = None,
        mood: "AffectState | None" = None,
    ) -> list[MemoryRecord]:
        """Return the top-k memories ranked by recency + importance + relevance.

        Base weights: recency 0.3, importance 0.35, relevance 0.35.

        When ``mood`` is provided, scoring is nudged toward **mood-congruent**
        memories (fearful/angry agents surface more negative memories, happy
        agents surface more positive ones) and ``fatigue`` adds gaussian noise
        + trims the retrieval budget to model limited cognitive bandwidth.
        """
        if not self.records:
            return []

        context_tags = context_tags or []
        context_agent_ids = context_agent_ids or []
        tag_set = set(context_tags)
        aid_set = set(context_agent_ids)

        # Fatigue-driven k trim & noise
        effective_k = k
        noise_sd = 0.0
        if mood is not None:
            load = mood.cognitive_load()
            if load > 0.3:
                effective_k = max(3, int(round(k * (1 - 0.4 * load))))
                noise_sd = 0.08 * load

        # Mood-driven bias toward negative vs positive memories.
        negative_tags = {
            "severe_shortage", "partial_shortage", "loss", "trust_break",
            "hoarding", "seeking_alternatives", "supply_crisis",
            "feeling_panicked", "feeling_angry", "feeling_anxious",
            "feeling_vindictive", "cancellation", "disruption",
        }
        positive_tags = {
            "reliable_delivery", "feeling_loyal", "feeling_confident",
            "loyalty_pledge",
        }
        neg_weight = 0.0
        pos_weight = 0.0
        if mood is not None:
            neg_weight = 0.35 * mood.fear + 0.25 * mood.anger
            pos_weight = 0.25 * mood.trust_joy + 0.15 * mood.pride

        scored: list[tuple[float, int, MemoryRecord]] = []

        # Pre-compute normalization bounds
        max_importance = max(r.importance for r in self.records)
        min_importance = min(r.importance for r in self.records)
        imp_range = max(max_importance - min_importance, 1)

        for idx, rec in enumerate(self.records):
            # --- Recency (exponential decay) ---
            rounds_ago = max(0, current_round - rec.round)
            half_life = _DECAY_HALF_LIVES.get(rec.category, _DEFAULT_HALF_LIFE)
            recency = math.exp(-0.693 * rounds_ago / half_life)  # 0.693 = ln(2)

            # --- Importance (normalized 0-1) ---
            importance = (rec.importance - min_importance) / imp_range

            # --- Relevance (tag + agent-id matching) ---
            relevance = 0.0
            if tag_set and rec.tags:
                overlap = len(tag_set & set(rec.tags))
                relevance = overlap / max(len(tag_set), 1)
            if aid_set and rec.agent_ids_involved:
                aid_overlap = len(aid_set & set(rec.agent_ids_involved))
                aid_score = aid_overlap / max(len(aid_set), 1)
                relevance = max(relevance, aid_score)

            score = recency * 0.30 + importance * 0.35 + relevance * 0.35

            # --- Mood-congruent bias ---
            if neg_weight > 0 or pos_weight > 0:
                rec_tags = set(rec.tags)
                if rec_tags & negative_tags:
                    score += neg_weight
                if rec_tags & positive_tags:
                    score += pos_weight

            # --- Fatigue noise ---
            if noise_sd > 0:
                score += random.gauss(0.0, noise_sd)

            scored.append((score, idx, rec))

        scored.sort(key=lambda t: t[0], reverse=True)
        return [rec for _, _, rec in scored[:effective_k]]

    def get_recent(self, n: int = 20) -> list[MemoryRecord]:
        """Return the N most recent memories (for reflection input)."""
        return self.records[-n:]

    def get_by_category(self, category: str) -> list[MemoryRecord]:
        return [r for r in self.records if r.category == category]

    def format_for_prompt(
        self,
        current_round: int,
        k: int = 10,
        context_tags: list[str] | None = None,
        context_agent_ids: list[str] | None = None,
        mood: "AffectState | None" = None,
    ) -> str:
        """Retrieve top-k memories and format them as a prompt section."""
        memories = self.retrieve(
            current_round, k, context_tags, context_agent_ids, mood=mood,
        )
        if not memories:
            return "No memories yet. This is the start of the simulation."

        lines: list[str] = []
        for mem in memories:
            tag_str = f" [{', '.join(mem.tags[:3])}]" if mem.tags else ""
            lines.append(f"[Round {mem.round} | {mem.category}]{tag_str} {mem.description}")
        return "\n".join(lines)

    def to_list(self) -> list[dict[str, Any]]:
        """Serialize all memories for API responses."""
        return [r.to_dict() for r in self.records]


# ---------------------------------------------------------------------------
# Memory generation helpers (called from model.py after resolution)
# ---------------------------------------------------------------------------

def generate_market_memory(round_num: int, event_text: str) -> MemoryRecord:
    """Create a memory from the scenario event."""
    # Detect shock events by keywords
    shock_keywords = {"fire", "crisis", "panic", "drops", "halting", "idles"}
    is_shock = any(kw in event_text.lower() for kw in shock_keywords)

    tags = ["market_event"]
    if "price" in event_text.lower():
        tags.append("price_change")
    if "shortage" in event_text.lower() or "shortage" in event_text.lower():
        tags.append("shortage")
    if "government" in event_text.lower() or "chips act" in event_text.lower():
        tags.append("policy")
    if "hoarding" in event_text.lower():
        tags.append("hoarding")
    if "cancel" in event_text.lower():
        tags.append("cancellation")
    if "fire" in event_text.lower():
        tags.append("disruption")

    return MemoryRecord(
        round=round_num,
        category="market",
        description=event_text[:200],  # truncate if needed
        importance=score_importance("market", is_shock_event=is_shock),
        tags=tags,
    )


def generate_transaction_memory(
    round_num: int,
    agent_id: str,
    partner_id: str,
    ordered: int,
    delivered: int,
    price: float,
    is_supplier: bool,
) -> MemoryRecord:
    """Create a memory from a transaction outcome."""
    fill = delivered / ordered if ordered > 0 else 1.0

    if is_supplier:
        desc = (
            f"{partner_id} ordered {ordered} units. "
            f"We delivered {delivered} at ${price:.0f}/unit "
            f"(fill rate: {fill:.0%})."
        )
    else:
        desc = (
            f"Ordered {ordered} units from {partner_id}. "
            f"Received {delivered} at ${price:.0f}/unit "
            f"(fill rate: {fill:.0%})."
        )

    tags = ["transaction", partner_id]
    if fill < 0.5:
        tags.append("severe_shortage")
    elif fill < 0.8:
        tags.append("partial_shortage")
    if fill >= 0.9:
        tags.append("reliable_delivery")

    return MemoryRecord(
        round=round_num,
        category="transaction",
        description=desc,
        importance=score_importance("transaction", fill_rate=fill),
        tags=tags,
        agent_ids_involved=[partner_id],
    )


def generate_consequence_memory(
    round_num: int,
    agent_id: str,
    profit: float,
    fill_rate: float,
    trust_changes: dict[str, float],
) -> MemoryRecord:
    """Create a memory summarizing the round's consequences."""
    lines = [f"Round {round_num} outcome: profit ${profit:+.0f}, overall fill rate {fill_rate:.0%}."]

    trust_tags: list[str] = []
    involved: list[str] = []
    worst_delta = 0.0
    for pid, delta in trust_changes.items():
        if abs(delta) >= 0.5:
            direction = "improved" if delta > 0 else "declined"
            lines.append(f"Trust with {pid} {direction} by {abs(delta):.1f}.")
            involved.append(pid)
            if delta < worst_delta:
                worst_delta = delta
        if delta <= -1.0:
            trust_tags.append("trust_break")

    tags = ["consequence"]
    if profit < 0:
        tags.append("loss")
    if fill_rate < 0.5:
        tags.append("severe_shortage")
    tags.extend(trust_tags)

    return MemoryRecord(
        round=round_num,
        category="consequence",
        description=" ".join(lines),
        importance=score_importance(
            "consequence",
            fill_rate=fill_rate,
            trust_delta=worst_delta if worst_delta != 0 else None,
        ),
        tags=tags,
        agent_ids_involved=involved,
    )


def generate_decision_memory(
    round_num: int,
    agent_id: str,
    decision: dict[str, Any],
    role: str,
) -> MemoryRecord:
    """Create a memory from the agent's own decision."""
    if role == "supplier":
        allocs = decision.get("allocations", {})
        held = decision.get("held_in_reserve", 0)
        price = decision.get("price_offered", 0)
        reasoning = decision.get("reasoning", "")
        desc = (
            f"Allocated {allocs} to customers, held {held} in reserve "
            f"at ${price:.0f}/unit. Reasoning: {reasoning}"
        )
        tags = ["own_decision", "allocation"]
        if held > 0:
            tags.append("hoarding")
    else:
        orders = decision.get("orders", {})
        max_price = decision.get("max_price_willing_to_pay", 0)
        reasoning = decision.get("reasoning", "")
        seek_alt = decision.get("will_seek_alternatives", False)
        desc = (
            f"Ordered {orders} from suppliers, "
            f"willing to pay up to ${max_price:.0f}/unit. "
            f"Reasoning: {reasoning}"
        )
        tags = ["own_decision", "order"]
        if seek_alt:
            tags.append("seeking_alternatives")

    emotional = decision.get("emotional_state", "")
    if emotional:
        tags.append(f"feeling_{emotional}")

    strategy = decision.get("strategy_shift")
    if strategy:
        tags.append("strategy_shift")
        desc += f" Strategy shift: {strategy}"

    return MemoryRecord(
        round=round_num,
        category="own_decision",
        description=desc[:300],
        importance=score_importance("own_decision"),
        tags=tags,
        agent_ids_involved=list(
            (decision.get("allocations") or decision.get("orders") or {}).keys()
        ),
    )


def generate_market_intelligence_memory(
    round_num: int,
    brief_summary: str,
    supply_crunch_severity: str,
    bullwhip_risk: str,
    spot_price_index: float,
    foundry_utilization_pct: float,
) -> MemoryRecord:
    """Create a memory from observable aggregate market intelligence.

    Distinct from market event memories — these represent what the agent
    can observe about overall market conditions (like reading a Bloomberg
    terminal), not just the narrative scenario text.
    """
    tags = ["market_intelligence"]
    if supply_crunch_severity in ("severe", "crisis"):
        tags.append("supply_crisis")
    if bullwhip_risk in ("high", "extreme"):
        tags.append("bullwhip_risk")
    if spot_price_index > 2.0:
        tags.append("price_spike")
    if foundry_utilization_pct > 0.95:
        tags.append("capacity_constrained")

    # Higher importance when market conditions are extreme
    is_shock = supply_crunch_severity in ("severe", "crisis") or bullwhip_risk == "extreme"

    return MemoryRecord(
        round=round_num,
        category="market",
        description=f"Market intelligence: {brief_summary}",
        importance=score_importance("market", is_shock_event=is_shock),
        tags=tags,
    )


def generate_partner_behavior_memory(
    round_num: int,
    observer_id: str,
    partner_id: str,
    partner_decision: dict[str, Any],
    relationship: str,  # "supplier" or "customer"
) -> MemoryRecord:
    """Create a memory from observing a partner's visible action."""
    tags = ["partner_behavior", partner_id]

    if "orders" in partner_decision:
        order_to_us = partner_decision["orders"].get(observer_id, 0)
        emotional = partner_decision.get("emotional_state", "unknown")
        seeking = partner_decision.get("will_seek_alternatives", False)
        desc = (
            f"Customer {partner_id} ordered {order_to_us} units from us "
            f"(emotional state: {emotional})."
        )
        if seeking:
            desc += f" WARNING: {partner_id} is seeking alternative suppliers."
            tags.append("seeking_alternatives")
        importance = score_importance(
            "partner_behavior", is_seeking_alternatives=seeking
        )
    elif "allocations" in partner_decision:
        alloc_to_us = partner_decision["allocations"].get(observer_id, 0)
        price = partner_decision.get("price_offered", 0)
        emotional = partner_decision.get("emotional_state", "unknown")
        desc = (
            f"Supplier {partner_id} offered us {alloc_to_us} units "
            f"at ${price:.0f}/unit (emotional state: {emotional})."
        )
        tags.append(partner_id)
        importance = score_importance("partner_behavior")
    else:
        return MemoryRecord(
            round=round_num,
            category="partner_behavior",
            description=f"No visible action from {partner_id} this round.",
            importance=2,
            tags=tags,
            agent_ids_involved=[partner_id],
        )

    return MemoryRecord(
        round=round_num,
        category="partner_behavior",
        description=desc,
        importance=importance,
        tags=tags,
        agent_ids_involved=[partner_id],
    )


def generate_affect_memory(
    round_num: int,
    agent_id: str,
    dominant_emotion: str,
    trigger: str,
    involved_agents: list[str] | None = None,
    intensity: float = 0.5,
) -> MemoryRecord:
    """Create a memory entry for a notable shift in affective state.

    Emitted when an agent's dominant emotion crosses a salience threshold so
    the agent can later remember "I panicked in Q3 after KoreaSilicon
    starved us" alongside the transactional record.
    """
    desc = (
        f"I felt {dominant_emotion} (intensity {intensity:.2f}). "
        f"Trigger: {trigger}"
    )
    tags = ["affect_change", f"feeling_{dominant_emotion}"]
    if intensity >= 0.7:
        tags.append("strong_feeling")
    importance = 5 + int(round(min(intensity, 1.0) * 4))
    return MemoryRecord(
        round=round_num,
        category="own_decision",
        description=desc,
        importance=importance,
        tags=tags,
        agent_ids_involved=involved_agents or [],
    )


def generate_reflection_memory(
    round_num: int,
    insight: str,
    source_indices: list[int],
    involved_agents: list[str] | None = None,
) -> MemoryRecord:
    """Create a reflection memory from an LLM-generated insight."""
    tags = ["reflection"]
    if involved_agents:
        tags.extend(involved_agents)

    return MemoryRecord(
        round=round_num,
        category="reflection",
        description=insight,
        importance=8,
        tags=tags,
        agent_ids_involved=involved_agents or [],
        source_indices=source_indices,
    )


# ---------------------------------------------------------------------------
# Strategic planning
# ---------------------------------------------------------------------------

# Planning horizons per tier (in quarters/rounds)
PLANNING_HORIZONS: dict[str, int] = {
    "foundry": 3,
    "chipDesigner": 3,
    "tier1Supplier": 2,
    "oem": 4,
}


@dataclass
class StrategicPlan:
    """A multi-quarter strategic plan for a supply-chain agent."""

    created_round: int
    horizon: int                            # how many rounds this plans for
    goals: list[str]                        # 2-4 strategic goals
    tactics: dict[str, str]                 # per-partner tactical approach
    risk_assessment: str                    # what could go wrong
    invalidated: bool = False               # set True when a shock makes plan obsolete

    def to_dict(self) -> dict[str, Any]:
        return {
            "created_round": self.created_round,
            "horizon": self.horizon,
            "goals": self.goals,
            "tactics": self.tactics,
            "risk_assessment": self.risk_assessment,
            "invalidated": self.invalidated,
        }

    def format_for_prompt(self) -> str:
        """Format plan as a prompt section."""
        status = "INVALIDATED - needs revision" if self.invalidated else "ACTIVE"
        lines = [
            f"Strategic Plan (created Round {self.created_round}, "
            f"horizon: {self.horizon} quarters, status: {status}):",
        ]
        for i, goal in enumerate(self.goals, 1):
            lines.append(f"  Goal {i}: {goal}")
        if self.tactics:
            lines.append("  Partner tactics:")
            for partner, tactic in self.tactics.items():
                lines.append(f"    {partner}: {tactic}")
        lines.append(f"  Key risk: {self.risk_assessment}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Inter-agent signaling
# ---------------------------------------------------------------------------

@dataclass
class AgentSignal:
    """A pre-decision signal from one agent to another (or broadcast)."""

    sender: str
    recipient: str | None           # None = broadcast to all partners
    signal_type: str                # price_warning | loyalty_pledge | threat
                                    # | information | request
    content: str                    # 1-2 sentences, natural language
    round: int
    # Affective payload — used by the receiver for emotional contagion.
    # Captured at emission time from the sender's AffectState.
    affect_valence: float = 0.0     # -1..1
    affect_arousal: float = 0.3     # 0..1

    def to_dict(self) -> dict[str, Any]:
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "signal_type": self.signal_type,
            "content": self.content,
            "round": self.round,
            "affect_valence": round(self.affect_valence, 3),
            "affect_arousal": round(self.affect_arousal, 3),
        }
