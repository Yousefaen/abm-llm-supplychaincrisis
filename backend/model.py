from __future__ import annotations

import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable

from mesa import Model, DataCollector

# Max concurrent LLM calls per phase. The Anthropic tier-1 budget is ~50 RPM
# and ~40-50k ITPM; with ~9 agents × ~1.5-2k input tokens, 5 concurrent stays
# comfortably under both. Bump via PHASE_CONCURRENCY env var when your
# organisation's tier allows; the SDK auto-retries 429s so overshoot is
# self-healing, just slower.
PHASE_CONCURRENCY = max(1, int(os.environ.get("PHASE_CONCURRENCY", "5")))

from agents import (
    AGENT_SPECS,
    ChipDesignerAgent,
    FoundryAgent,
    OEMAgent,
    SupplyChainAgent,
    Tier1SupplierAgent,
    create_agent,
)
from debug_session import dbg_log
from market_data import MarketEnvironment
from memory import (
    generate_affect_memory,
    generate_consequence_memory,
    generate_market_intelligence_memory,
    generate_market_memory,
    generate_transaction_memory,
)
from scenarios import (
    CAPACITY_SHOCKS,
    DEMAND_MULTIPLIERS,
    EVENT_EMOTIONAL_VALENCE,
    INVENTORY_CARRYING_COST_PCT,
    SCENARIO_EVENTS,
    TOTAL_ROUNDS,
)


class SupplyChainModel(Model):
    """Mesa model orchestrating the semiconductor supply-chain simulation."""

    def __init__(self, temperature: float = 1.0, seed: int | None = None):
        super().__init__(seed=seed)
        self.temperature = temperature
        self.total_rounds = TOTAL_ROUNDS
        self.current_event: str = ""
        self.total_cost: float = 0.0
        self.status: str = "idle"

        # Market environment — shared observable state for all agents
        self.market_env = MarketEnvironment()
        self.current_market_state = None

        # Lookup for agents by their string id
        self.agents_map: dict[str, SupplyChainAgent] = {}

        # Grouped references for tier-by-tier stepping
        self.oems: list[OEMAgent] = []
        self.tier1s: list[Tier1SupplierAgent] = []
        self.designers: list[ChipDesignerAgent] = []
        self.foundries: list[FoundryAgent] = []

        # Create all agents
        for spec in AGENT_SPECS.values():
            agent = create_agent(self, spec)
            self.agents_map[spec.agent_id] = agent
            if isinstance(agent, OEMAgent):
                self.oems.append(agent)
            elif isinstance(agent, Tier1SupplierAgent):
                self.tier1s.append(agent)
            elif isinstance(agent, ChipDesignerAgent):
                self.designers.append(agent)
            elif isinstance(agent, FoundryAgent):
                self.foundries.append(agent)

        # DataCollector
        self.datacollector = DataCollector(
            model_reporters={
                "round": lambda m: m.time,
                "event": lambda m: m.current_event,
                "total_cost": lambda m: m.total_cost,
            },
            agent_reporters={
                "agent_id": lambda a: a.agent_id,
                "tier": lambda a: a.tier,
                "inventory": lambda a: a.inventory,
                "capacity": lambda a: a.effective_capacity,
                "current_price": lambda a: a.current_price,
                "emotional_state": lambda a: a.emotional_state,
                "affect": lambda a: a.affect.to_dict(),
                "cognitive_load": lambda a: a.last_cognitive_load,
                "fill_rate": lambda a: a.fill_rate,
                "trust_scores": lambda a: dict(a.trust_scores),
                "decision": lambda a: dict(a.current_decision) if a.current_decision else {},
                "profit": lambda a: round(a.revenue - a.costs, 2),
            },
        )

        # Round-level decision log (for streaming to frontend)
        self.round_decisions: list[dict[str, Any]] = []

        # Optional callback fired for every round_decisions entry as it's
        # produced — lets the SSE endpoint stream incrementally instead of
        # waiting for the entire round to complete. Cleared each round.
        self._decision_callback: Callable[[dict[str, Any]], None] | None = None

        # Serializes the ``total_cost += …`` read-modify-write in agents._call_llm
        # once LLM calls are parallelized within a phase. Python's ``+=`` on a
        # float is NOT atomic, so concurrent workers would drop cost updates.
        self._cost_lock = threading.Lock()

    # ------------------------------------------------------------------
    # One quarter of the simulation (API entry point)
    # ------------------------------------------------------------------
    # Mesa 3.5 replaces instance ``step`` with _wrapped_step (returns None).
    # Never call model.step() from FastAPI expecting a dict — use advance_quarter().
    def advance_quarter(
        self,
        decision_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        """Execute one round. Returns a summary dict for the API.

        ``decision_callback`` is invoked from the worker thread for each
        entry appended to ``round_decisions`` (agent decisions, plans,
        reflections, signals). Callers must marshal it back to their own
        thread/event loop.
        """
        self._decision_callback = decision_callback
        current_round = int(self.time) + 1  # Mesa time is 0-indexed
        if current_round > self.total_rounds:
            self.status = "complete"
            return {"status": "complete", "round": int(self.time)}

        # region agent log
        dbg_log(
            "model.py:advance_quarter",
            "round_start",
            {"current_round": current_round, "mesa_time": float(self.time)},
            "H2",
        )
        # endregion

        try:
            self.status = "running"
            self.current_event = SCENARIO_EVENTS.get(current_round, "No event.")
            self.round_decisions = []

            # Store market event as memory for all agents
            market_mem = generate_market_memory(current_round, self.current_event)
            for agent in self.agents_map.values():
                agent.memory_stream.add(market_mem)

            # Apply mechanical scenario effects for this round
            self._apply_scenario_effects(current_round)

            # ----------------------------------------------------------
            # Phase 0a: MARKET INTELLIGENCE — compute observable state
            # All agents see the same aggregate data but interpret it
            # through their tier-specific lens (Stanford emergence driver)
            # ----------------------------------------------------------
            self.current_market_state = self.market_env.compute_market_state(
                current_round, self.agents_map,
            )
            for agent in self.agents_map.values():
                agent.market_state = self.current_market_state

            # Store market intelligence as a memory for all agents
            brief = self.market_env.get_brief_summary(self.current_market_state)
            intel_mem = generate_market_intelligence_memory(
                round_num=current_round,
                brief_summary=brief,
                supply_crunch_severity=self.current_market_state.supply_crunch_severity,
                bullwhip_risk=self.current_market_state.bullwhip_risk,
                spot_price_index=self.current_market_state.chip_spot_price_index,
                foundry_utilization_pct=self.current_market_state.foundry_utilization_pct,
            )
            for agent in self.agents_map.values():
                agent.memory_stream.add(intel_mem)

            # ----------------------------------------------------------
            # Phase 0b: STRATEGIC PLANNING (Sonnet)
            # Create plans at round 1, refresh every 3 rounds,
            # emergency replan on shock events
            # ----------------------------------------------------------
            self._run_planning(current_round)

            # Clear current decisions and per-round financials
            for agent in self.agents_map.values():
                agent.current_decision = {}
                agent.round_revenue = 0.0
                agent.round_costs = 0.0
                agent.inventory_cost = 0.0

            # ----------------------------------------------------------
            # Phase 0c: SIGNALING — agents send pre-decision messages
            # ----------------------------------------------------------
            self._run_signaling(current_round)

            # ----------------------------------------------------------
            # Phase 1: ORDERING (bottom-up). Agents within a tier run in
            # parallel; tiers serialize because each tier reads the prior
            # tier's current_decision via _format_partner_actions.
            # ----------------------------------------------------------
            for agent, _, exc in self._parallel_map(self.oems, lambda a: a.step()):
                if exc is None:
                    self._record_decision(agent)

            for agent, _, exc in self._parallel_map(self.tier1s, lambda a: a.step()):
                if exc is None:
                    self._record_decision(agent, role="buyer")

            for agent, _, exc in self._parallel_map(self.designers, lambda a: a.step()):
                if exc is None:
                    self._record_decision(agent, role="buyer")

            # ----------------------------------------------------------
            # Phase 2: ALLOCATION (top-down). Same fan-out pattern.
            # ----------------------------------------------------------
            for agent, _, exc in self._parallel_map(self.foundries, lambda a: a.step()):
                if exc is None:
                    self._record_decision(agent)

            for agent, _, exc in self._parallel_map(self.designers, lambda a: a.supply_step()):
                if exc is None:
                    self._record_decision(agent, role="supplier")

            for agent, _, exc in self._parallel_map(self.tier1s, lambda a: a.supply_step()):
                if exc is None:
                    self._record_decision(agent, role="supplier")

            # ----------------------------------------------------------
            # Phase 3: RESOLUTION — flow allocations and compute fill rates
            # ----------------------------------------------------------
            self._resolve_allocations()

            # region agent log
            dbg_log(
                "model.py:advance_quarter",
                "after_resolve",
                {
                    "toyota_inventory": (
                        self.agents_map["ToyotaMotors"].inventory
                        if "ToyotaMotors" in self.agents_map
                        else None
                    ),
                    "decisions_recorded": len(self.round_decisions),
                },
                "H4",
            )
            # endregion

            # ----------------------------------------------------------
            # Phase 3.5: AFFECT UPDATE — realized outcomes shape emotions
            # ----------------------------------------------------------
            self._update_affect(current_round)

            # ----------------------------------------------------------
            # Phase 4: MEMORY GENERATION — create memories from this round
            # ----------------------------------------------------------
            self._generate_round_memories(current_round)

            # ----------------------------------------------------------
            # Phase 5: REFLECTION — agents synthesize patterns (Sonnet)
            # ----------------------------------------------------------
            self._run_reflections(current_round)

            # Apply inventory carrying costs
            self._apply_carrying_costs()

            # Advance time
            self.time = float(current_round)

            # Collect data
            self.datacollector.collect(self)

            if current_round >= self.total_rounds:
                self.status = "complete"
            else:
                self.status = "idle"

            summary = self._build_round_summary(current_round)
            # region agent log
            dbg_log(
                "model.py:advance_quarter",
                "round_end",
                {"summary_round": summary.get("round"), "status": summary.get("status")},
                "H2",
            )
            # endregion
            return summary
        except Exception as exc:
            # region agent log
            dbg_log(
                "model.py:advance_quarter",
                "step_inner_exception",
                {"exc_type": type(exc).__name__, "current_round": current_round},
                "H4",
            )
            # endregion
            raise

    def step(self) -> None:
        """Mesa calls this via the internal schedule; API must use advance_quarter()."""
        self.advance_quarter()

    # ------------------------------------------------------------------
    # Scenario effects — apply demand/capacity modifiers each round
    # ------------------------------------------------------------------
    def _apply_scenario_effects(self, current_round: int) -> None:
        """Apply mechanical scenario effects so narrative and model agree."""
        # Demand multiplier
        demand_mult = DEMAND_MULTIPLIERS.get(current_round, 1.0)
        for agent in self.agents_map.values():
            if agent.spec.quarterly_need > 0:
                agent.effective_quarterly_need = int(
                    agent.spec.quarterly_need * demand_mult
                )

        # Capacity shocks
        shocks = CAPACITY_SHOCKS.get(current_round, {})
        for aid, mult in shocks.items():
            agent = self.agents_map.get(aid)
            if agent:
                agent.effective_capacity = int(agent.spec.initial_capacity * mult)

        # Reset unshocked agents to base capacity
        for agent in self.agents_map.values():
            if agent.agent_id not in shocks:
                agent.effective_capacity = agent.spec.initial_capacity

        # ── Narrative -> affect: scenario event nudges everyone's mood ──
        event_valence = EVENT_EMOTIONAL_VALENCE.get(current_round, {})
        if event_valence:
            for agent in self.agents_map.values():
                agent.affect.update_from_event_valence(
                    fear=event_valence.get("fear", 0.0),
                    greed=event_valence.get("greed", 0.0),
                    stress=event_valence.get("stress", 0.0),
                    morale=event_valence.get("morale", 0.0),
                )

    # ------------------------------------------------------------------
    # Signaling — pre-decision communication between agents
    # ------------------------------------------------------------------
    def _run_signaling(self, current_round: int) -> None:
        """Each agent generates 0-2 signals concurrently, then we route
        them to recipients after every agent has responded."""
        for agent in self.agents_map.values():
            agent.signals_received = []

        all_signals = []
        all_agents = list(self.agents_map.values())
        for agent, signals, exc in self._parallel_map(
            all_agents, lambda a: a.generate_signals()
        ):
            if exc is not None or not signals:
                continue
            all_signals.extend(signals)
            self._emit_decision({
                "agent_id": agent.agent_id,
                "tier": agent.tier,
                "role": "signaling",
                "decision": {
                    "signals": [s.to_dict() for s in signals],
                },
                "input_tokens": agent.last_input_tokens,
                "output_tokens": agent.last_output_tokens,
            })

        # Route signals to recipients AND propagate affective contagion:
        # receivers drift toward the sender's emotional tone, weighted by how
        # much they trust the sender.
        def _alpha(receiver: SupplyChainAgent, sender_id: str) -> float:
            # Trust 1..10 -> 0.02..0.20 coupling strength
            trust = receiver.trust_scores.get(sender_id, 5.0)
            return max(0.02, min(0.20, 0.02 * trust))

        for signal in all_signals:
            if signal.recipient is None:
                sender = self.agents_map.get(signal.sender)
                if sender:
                    for pid in sender.spec.upstream + sender.spec.downstream:
                        partner = self.agents_map.get(pid)
                        if partner:
                            partner.signals_received.append(signal)
                            partner.affect.update_from_signal(
                                sender_valence=signal.affect_valence,
                                sender_arousal=signal.affect_arousal,
                                alpha=_alpha(partner, signal.sender),
                            )
            else:
                recipient = self.agents_map.get(signal.recipient)
                if recipient:
                    recipient.signals_received.append(signal)
                    recipient.affect.update_from_signal(
                        sender_valence=signal.affect_valence,
                        sender_arousal=signal.affect_arousal,
                        alpha=_alpha(recipient, signal.sender),
                    )

    # ------------------------------------------------------------------
    # Strategic planning — create/refresh/invalidate multi-quarter plans
    # ------------------------------------------------------------------
    def _run_planning(self, current_round: int) -> None:
        """Create or refresh strategic plans for agents."""
        # Detect if this round has a shock that should trigger emergency replan
        has_capacity_shock = current_round in CAPACITY_SHOCKS
        prev_demand = DEMAND_MULTIPLIERS.get(current_round - 1, 1.0)
        curr_demand = DEMAND_MULTIPLIERS.get(current_round, 1.0)
        demand_shift = abs(curr_demand - prev_demand) > 0.15

        planners: list[tuple[SupplyChainAgent, bool]] = []
        for agent in self.agents_map.values():
            emergency = False
            needs_plan = False

            if current_round == 1:
                needs_plan = True
            elif current_round % 3 == 1:
                needs_plan = True
            elif has_capacity_shock or demand_shift:
                if agent.current_plan and not agent.current_plan.invalidated:
                    agent.current_plan.invalidated = True
                    needs_plan = True
                    emergency = True

            if needs_plan:
                planners.append((agent, emergency))

        if not planners:
            return

        # Map agent -> emergency flag so the closure can resolve it
        emergency_by_id = {a.agent_id: e for a, e in planners}
        plan_agents = [a for a, _ in planners]

        for agent, plan, exc in self._parallel_map(
            plan_agents,
            lambda a: a.create_plan(emergency=emergency_by_id[a.agent_id]),
        ):
            if exc is not None or plan is None:
                continue
            self._emit_decision({
                "agent_id": agent.agent_id,
                "tier": agent.tier,
                "role": "planning",
                "decision": {"plan": plan.to_dict()},
                "input_tokens": agent.last_input_tokens,
                "output_tokens": agent.last_output_tokens,
            })

    # ------------------------------------------------------------------
    # Affect update — realized outcomes shape emotions, then decay
    # ------------------------------------------------------------------
    def _update_affect(self, current_round: int) -> None:
        """Update every agent's AffectState from this round's realized
        outcomes and partner behavior, then decay and accumulate fatigue.

        Also writes an ``affect_change`` memory when the agent's dominant
        emotion has flipped to a strong state.
        """
        for agent in self.agents_map.values():
            pre_dominant = agent.affect.dominant_emotion()
            pre_intensity = self._dominant_intensity(agent.affect)

            partner_fills: dict[str, float] = {}
            partner_hoarding: dict[str, int] = {}
            partner_seeking: dict[str, bool] = {}

            # For buyers: partner fills come from supplier_performance
            perf = agent.last_consequences.get("supplier_performance") or {}
            for sid, info in perf.items():
                ordered = info.get("ordered", 0)
                received = info.get("received", 0)
                if ordered > 0:
                    partner_fills[sid] = received / ordered
                else:
                    partner_fills[sid] = 1.0
                supplier_agent = self.agents_map.get(sid)
                if supplier_agent is not None:
                    held = int(supplier_agent.current_decision.get("held_in_reserve", 0) or 0)
                    partner_hoarding[sid] = held

            # For suppliers: "customer seeking alternatives" is a betrayal
            cons = agent.last_consequences.get("customer_fill_rates") or {}
            for bid in cons:
                buyer = self.agents_map.get(bid)
                if buyer is not None:
                    seek = bool(buyer.current_decision.get("will_seek_alternatives", False))
                    if seek:
                        partner_seeking[bid] = True

            profit = agent.last_consequences.get("profit_this_round")
            agent.affect.update_from_outcome(
                fill_rate=agent.fill_rate if agent.tier != "foundry" else None,
                profit=profit,
                partner_fills=partner_fills or None,
                partner_hoarding=partner_hoarding or None,
                partner_seeking_alternatives=partner_seeking or None,
            )

            # Fatigue accumulates with stress, then we decay transient emotions.
            agent.affect.accumulate_fatigue()
            agent.affect.decay()

            # Record an affect_change memory when the dominant emotion is
            # strong and has shifted meaningfully from the previous round.
            post_dominant = agent.affect.dominant_emotion()
            post_intensity = self._dominant_intensity(agent.affect)
            if post_intensity >= 0.45 and (
                post_dominant != pre_dominant or post_intensity - pre_intensity >= 0.2
            ):
                # Pick a trigger description
                trigger = self._affect_trigger_text(
                    agent, partner_fills, partner_seeking
                )
                agent.memory_stream.add(
                    generate_affect_memory(
                        round_num=current_round,
                        agent_id=agent.agent_id,
                        dominant_emotion=post_dominant,
                        trigger=trigger,
                        involved_agents=list(partner_fills.keys())
                        + list(partner_seeking.keys()),
                        intensity=post_intensity,
                    )
                )

    @staticmethod
    def _dominant_intensity(affect) -> float:
        emos = [
            affect.fear, affect.anger, affect.trust_joy,
            affect.pride, affect.shame, affect.greed,
        ]
        return max(emos) if emos else 0.0

    @staticmethod
    def _affect_trigger_text(
        agent: "SupplyChainAgent",
        partner_fills: dict[str, float],
        partner_seeking: dict[str, bool],
    ) -> str:
        bad_fills = sorted(
            ((pid, f) for pid, f in partner_fills.items() if f < 0.7),
            key=lambda kv: kv[1],
        )
        if bad_fills:
            pid, f = bad_fills[0]
            return f"low fill rate from {pid} ({f:.0%})"
        if partner_seeking:
            pid = next(iter(partner_seeking))
            return f"{pid} is seeking alternative suppliers"
        if agent.fill_rate < 0.7:
            return f"overall fill rate low ({agent.fill_rate:.0%})"
        return "cumulative pressure this round"

    # ------------------------------------------------------------------
    # Memory generation — create memories from resolution outcomes
    # ------------------------------------------------------------------
    def _generate_round_memories(self, current_round: int) -> None:
        """After resolution, generate transaction and consequence memories."""
        # Transaction memories from supplier consequences
        for supplier in list(self.foundries) + list(self.designers) + list(self.tier1s):
            cons = supplier.last_consequences.get("customer_fill_rates", {})
            for buyer_id, info in cons.items():
                # Supplier's memory of this transaction
                supplier.memory_stream.add(generate_transaction_memory(
                    current_round, supplier.agent_id, buyer_id,
                    ordered=info["ordered"],
                    delivered=info["delivered"],
                    price=supplier.current_price,
                    is_supplier=True,
                ))

        # Transaction + consequence memories for buyers
        for buyer in list(self.oems) + list(self.tier1s) + list(self.designers):
            perf = buyer.last_consequences.get("supplier_performance", {})
            trust_changes: dict[str, float] = {}
            for sid, info in perf.items():
                buyer.memory_stream.add(generate_transaction_memory(
                    current_round, buyer.agent_id, sid,
                    ordered=info["ordered"],
                    delivered=info["received"],
                    price=info["price_paid"],
                    is_supplier=False,
                ))
                # Compute trust delta for consequence memory
                old_trust = buyer.trust_scores.get(sid, 5.0)
                trust_changes[sid] = round(old_trust - 7.0, 1)  # delta from baseline

            # Consequence summary memory
            profit = buyer.last_consequences.get("profit_this_round", 0)
            buyer.memory_stream.add(generate_consequence_memory(
                current_round, buyer.agent_id,
                profit=profit,
                fill_rate=buyer.fill_rate,
                trust_changes=trust_changes,
            ))

        # Consequence memories for suppliers
        for supplier in list(self.foundries) + list(self.designers) + list(self.tier1s):
            profit = supplier.last_consequences.get("profit_this_round", 0)
            cons = supplier.last_consequences.get("customer_fill_rates", {})
            trust_changes = {}
            for bid, info in cons.items():
                trust_changes[bid] = info.get("trust_delta", 0)
            supplier.memory_stream.add(generate_consequence_memory(
                current_round, supplier.agent_id,
                profit=profit,
                fill_rate=1.0,  # suppliers always "fill" in their own terms
                trust_changes=trust_changes,
            ))

    # ------------------------------------------------------------------
    # Reflection — agents generate higher-order insights via Sonnet
    # ------------------------------------------------------------------
    def _run_reflections(self, current_round: int) -> None:
        """Run reflection for all agents after memories are generated."""
        if current_round < 2:
            return  # Not enough memories to reflect on in round 1

        for agent, insights, exc in self._parallel_map(
            list(self.agents_map.values()), lambda a: a.reflect()
        ):
            if exc is not None or not insights:
                continue
            self._emit_decision({
                "agent_id": agent.agent_id,
                "tier": agent.tier,
                "role": "reflection",
                "decision": {"insights": insights},
                "input_tokens": agent.last_input_tokens,
                "output_tokens": agent.last_output_tokens,
            })

    # ------------------------------------------------------------------
    # Inventory carrying costs
    # ------------------------------------------------------------------
    def _apply_carrying_costs(self) -> None:
        for agent in self.agents_map.values():
            if agent.inventory > 0 and agent.current_price > 0:
                cost = agent.inventory * agent.current_price * INVENTORY_CARRYING_COST_PCT
            elif agent.inventory > 0:
                # OEMs don't have a sell price; use avg purchase price
                cost = agent.inventory * 30.0 * INVENTORY_CARRYING_COST_PCT
            else:
                cost = 0.0
            agent.inventory_cost = cost
            agent.round_costs += cost
            agent.costs += cost

    # ------------------------------------------------------------------
    # Resolve allocations: map supplier decisions to buyer receipts
    # ------------------------------------------------------------------
    def _resolve_allocations(self) -> None:
        """Walk the supply chain top-down: foundries → designers → tier1 → OEMs.
        For each supplier decision, update downstream buyers' inventories and
        compute fill rates. Uses price+trust weighting for allocation priority."""

        # Foundries supply to chip designers
        self._resolve_tier(self.foundries, self.designers)
        # Chip designers supply to tier-1
        self._resolve_tier(self.designers, self.tier1s)
        # Tier-1 supply to OEMs
        self._resolve_tier(self.tier1s, self.oems)

    def _resolve_tier(
        self,
        suppliers: list[SupplyChainAgent],
        buyers: list[SupplyChainAgent],
    ) -> None:
        """Resolve one tier of the supply chain with price+trust-weighted
        allocation and financial tracking."""

        for supplier in suppliers:
            sup_decision = supplier.current_decision
            allocations = sup_decision.get("allocations", {})
            held = int(sup_decision.get("held_in_reserve", 0))
            sell_price = float(sup_decision.get("price_offered", supplier.current_price))
            total_supply = supplier.inventory + supplier.effective_capacity
            total_allocated_by_llm = sum(int(v) for v in allocations.values())

            # Build per-buyer demand from this supplier
            buyer_demands: dict[str, int] = {}
            buyer_max_prices: dict[str, float] = {}
            for buyer in buyers:
                buyer_orders = buyer.current_decision.get("orders", {})
                amount_ordered = int(buyer_orders.get(supplier.agent_id, 0))
                # Grudge penalties surface as a per-supplier ceiling (set by
                # the buyer step); fall back to the global ceiling.
                per_sup = buyer.current_decision.get("max_price_per_supplier") or {}
                max_price = float(
                    per_sup.get(supplier.agent_id,
                                buyer.current_decision.get("max_price_willing_to_pay", 0))
                )
                if amount_ordered > 0:
                    buyer_demands[buyer.agent_id] = amount_ordered
                    buyer_max_prices[buyer.agent_id] = max_price

            # ── Price+trust-weighted allocation ──
            # The LLM decides allocations, but we adjust them:
            # 1. Buyers who can't meet the price get reduced allocation
            # 2. Supplier's trust toward each buyer weights the allocation
            adjusted_allocs: dict[str, int] = {}
            distributable = max(0, total_supply - held)

            if buyer_demands:
                # Compute priority score for each buyer
                scores: dict[str, float] = {}
                for bid, ordered in buyer_demands.items():
                    # Price factor: 0 if buyer can't pay, 1.0 if they match or exceed
                    price_factor = min(buyer_max_prices[bid] / sell_price, 1.5) if sell_price > 0 else 1.0
                    # Trust factor: supplier's trust in this buyer (1-10 → 0.1-1.0)
                    trust = supplier.trust_scores.get(bid, 5.0)
                    trust_factor = trust / 10.0
                    # Emotional factor: grudges + anger punish; trust_joy helps
                    emo_factor = supplier.affect.allocation_emotional_factor(bid)
                    # Combined score — price leads, trust and affect each matter
                    scores[bid] = (
                        price_factor * 0.5
                        + trust_factor * 0.3
                        + emo_factor * 0.2
                    )

                # Sort buyers by score (highest priority first)
                sorted_buyers = sorted(scores.keys(), key=lambda b: scores[b], reverse=True)

                remaining = distributable
                for bid in sorted_buyers:
                    wanted = buyer_demands[bid]
                    llm_alloc = int(allocations.get(bid, 0))
                    # Use LLM's allocation as a baseline but cap by what's actually available
                    # and boost/reduce based on priority score
                    score_mult = scores[bid]
                    target = min(int(llm_alloc * score_mult), wanted, remaining)
                    target = max(0, target)
                    adjusted_allocs[bid] = target
                    remaining -= target

                # If there's remaining supply after priority allocation, distribute to underserved
                if remaining > 0:
                    for bid in sorted_buyers:
                        shortfall = buyer_demands[bid] - adjusted_allocs[bid]
                        if shortfall > 0:
                            extra = min(shortfall, remaining)
                            adjusted_allocs[bid] += extra
                            remaining -= extra
                            if remaining <= 0:
                                break
            else:
                # No buyers ordered from this supplier
                for bid in allocations:
                    adjusted_allocs[bid] = 0

            # ── Deliver and track financials ──
            supplier_revenue = 0.0
            consequence_customers: dict[str, Any] = {}
            total_delivered_all = 0

            for buyer in buyers:
                bid = buyer.agent_id
                ordered = buyer_demands.get(bid, 0)
                allocated = adjusted_allocs.get(bid, 0)
                delivered = min(allocated, ordered)
                total_delivered_all += delivered

                # Financial: buyer pays supplier's price for delivered units
                transaction_value = delivered * sell_price
                supplier_revenue += transaction_value
                buyer.round_costs += transaction_value
                buyer.costs += transaction_value

                # Update buyer inventory
                buyer.inventory += delivered

                # Trust mechanical adjustment: fill rate affects trust
                if ordered > 0:
                    fill = delivered / ordered
                    old_trust = buyer.trust_scores.get(supplier.agent_id, 5.0)
                    # Fill rate > 80% → trust goes up; < 50% → trust drops
                    if fill >= 0.8:
                        delta = min(0.5, (fill - 0.8) * 2.5)
                    elif fill < 0.5:
                        delta = max(-1.5, (fill - 0.5) * 3.0)
                    else:
                        delta = (fill - 0.65) * 1.0
                    # Mean-reversion toward baseline 7.0 so trust can recover
                    # once supply normalises (prevents permanent distrust lock-in).
                    delta += 0.1 * (7.0 - old_trust)
                    new_trust = max(1.0, min(10.0, old_trust + delta))
                    buyer.trust_scores[supplier.agent_id] = round(new_trust, 1)
                else:
                    fill = 1.0
                    old_trust = buyer.trust_scores.get(supplier.agent_id, 5.0)
                    new_trust = old_trust
                    delta = 0.0

                # Build consequence data for this supplier
                consequence_customers[bid] = {
                    "ordered": ordered,
                    "delivered": delivered,
                    "fill_rate": fill,
                    "trust_delta": round(new_trust - old_trust, 1),
                    "trust_now": round(new_trust, 1),
                }

            # Supplier revenue
            supplier.round_revenue += supplier_revenue
            supplier.revenue += supplier_revenue

            # Update supplier inventory
            supplier.inventory = max(0, total_supply - total_delivered_all - held)

            # Store supplier consequences
            supplier.last_consequences = {
                "customer_fill_rates": consequence_customers,
                "revenue_earned": supplier_revenue,
            }

        # ── Buyer-side consequences and fill rates ──
        for buyer in buyers:
            ordered_map: dict[str, int] = {}
            received_map: dict[str, int] = {}
            supplier_perf: dict[str, Any] = {}

            buyer_orders = buyer.current_decision.get("orders", {})

            for supplier in suppliers:
                sid = supplier.agent_id
                amount_ordered = int(buyer_orders.get(sid, 0))
                ordered_map[sid] = amount_ordered

                # The delivery amount: read from supplier's consequence data
                cons = supplier.last_consequences.get("customer_fill_rates", {})
                buyer_cons = cons.get(buyer.agent_id, {})
                delivered = buyer_cons.get("delivered", 0)
                received_map[sid] = delivered

                sell_price = float(supplier.current_decision.get(
                    "price_offered", supplier.current_price
                ))
                supplier_perf[sid] = {
                    "ordered": amount_ordered,
                    "received": delivered,
                    "price_paid": sell_price,
                }

            # Consume quarterly need from inventory
            consumed = min(buyer.inventory, buyer.effective_quarterly_need)
            buyer.inventory = max(0, buyer.inventory - consumed)

            # OEMs earn revenue from selling vehicles (simplified)
            if buyer.tier == "oem" and consumed > 0:
                oem_sell_price = 100.0  # simplified vehicle-component margin
                oem_revenue = consumed * oem_sell_price
                buyer.round_revenue += oem_revenue
                buyer.revenue += oem_revenue

            # Fill rate
            total_ordered = sum(ordered_map.values())
            total_received = sum(received_map.values())
            buyer.fill_rate = (
                total_received / total_ordered
                if total_ordered > 0 else 1.0
            )

            # Store result for history
            buyer.round_results.append({
                "ordered": ordered_map,
                "received": received_map,
                "fill_rate": buyer.fill_rate,
            })

            # Store buyer consequences
            buyer.last_consequences = {
                "supplier_performance": supplier_perf,
                "total_cost_this_round": buyer.round_costs,
                "inventory_carrying_cost": buyer.inventory_cost,
                "profit_this_round": buyer.round_revenue - buyer.round_costs,
                "cumulative_profit": buyer.revenue - buyer.costs,
            }

        # Seller-side round results
        for supplier in suppliers:
            supplier.round_results.append({
                "_round": self.time,
                "ordered": {},
                "received": {},
                "fill_rate": 1.0,
            })
            # Add financial data to supplier consequences
            supplier.last_consequences["profit_this_round"] = (
                supplier.round_revenue - supplier.round_costs
            )
            supplier.last_consequences["cumulative_profit"] = (
                supplier.revenue - supplier.costs
            )

        # Save decision to history for all agents
        for agent in list(suppliers) + list(buyers):
            if agent.current_decision:
                agent.decision_history.append(dict(agent.current_decision))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _emit_decision(self, entry: dict[str, Any]) -> None:
        """Append to round_decisions and fire the streaming callback if set."""
        self.round_decisions.append(entry)
        cb = self._decision_callback
        if cb is not None:
            try:
                cb(entry)
            except Exception as exc:
                dbg_log(
                    "model.py:_emit_decision",
                    "callback_failed",
                    {"exc_type": type(exc).__name__, "exc_msg": str(exc)[:200]},
                    "H1",
                )

    def _parallel_map(
        self,
        agents: list[SupplyChainAgent],
        fn: Callable[[SupplyChainAgent], Any],
    ):
        """Run ``fn(agent)`` for each agent concurrently, bounded by
        PHASE_CONCURRENCY. Yields ``(agent, result, exception)`` tuples
        in completion order so callers can stream per-agent output as
        soon as each finishes.

        Thread safety: each agent only mutates its own state during
        ``step``/``supply_step``/``reflect``/``create_plan``/``generate_signals``,
        and reads of peer state within the same phase are limited to fields
        set in the prior phase (already stable). That's why we can fan-out
        within a phase but still serialize phases.
        """
        if not agents:
            return
        with ThreadPoolExecutor(
            max_workers=min(PHASE_CONCURRENCY, len(agents)),
            thread_name_prefix="phase",
        ) as pool:
            futures = {pool.submit(fn, a): a for a in agents}
            for fut in as_completed(futures):
                agent = futures[fut]
                try:
                    yield agent, fut.result(), None
                except Exception as exc:
                    dbg_log(
                        "model.py:_parallel_map",
                        "agent_exception",
                        {
                            "agent_id": agent.agent_id,
                            "exc_type": type(exc).__name__,
                            "exc_msg": str(exc)[:200],
                        },
                        "H2",
                    )
                    yield agent, None, exc

    def _record_decision(self, agent: SupplyChainAgent, role: str = "") -> None:
        self._emit_decision({
            "agent_id": agent.agent_id,
            "tier": agent.tier,
            "role": role or ("supplier" if "allocations" in agent.current_decision else "buyer"),
            "decision": dict(agent.current_decision),
            "input_tokens": agent.last_input_tokens,
            "output_tokens": agent.last_output_tokens,
        })

    def _build_round_summary(self, round_num: int) -> dict[str, Any]:
        agents_state: dict[str, Any] = {}
        for aid, agent in self.agents_map.items():
            agents_state[aid] = {
                "agent_id": aid,
                "display_name": agent.display_name,
                "tier": agent.tier,
                "inventory": agent.inventory,
                "capacity": agent.effective_capacity,
                "current_price": agent.current_price,
                "emotional_state": agent.emotional_state,
                "affect": agent.affect.to_dict(),
                "cognitive_load": agent.last_cognitive_load,
                "fill_rate": agent.fill_rate,
                "trust_scores": dict(agent.trust_scores),
                "current_decision": dict(agent.current_decision) if agent.current_decision else None,
                "decision_history": agent.decision_history[-3:],
                "round_results": agent.round_results[-3:],
                "revenue": round(agent.revenue, 2),
                "costs": round(agent.costs, 2),
                "profit": round(agent.revenue - agent.costs, 2),
                "round_revenue": round(agent.round_revenue, 2),
                "round_costs": round(agent.round_costs, 2),
                "effective_quarterly_need": agent.effective_quarterly_need,
                # Memory, reflection & planning data
                "memories": agent.memory_stream.to_list()[-15:],  # last 15 memories
                "reflections": agent.reflections,
                "memory_count": len(agent.memory_stream.records),
                "current_plan": agent.current_plan.to_dict() if agent.current_plan else None,
                "signals_sent": [s.to_dict() for s in agent.signals_sent],
                "signals_received": [s.to_dict() for s in agent.signals_received],
            }

        metrics = self._compute_metrics()

        return {
            "status": self.status,
            "round": round_num,
            "total_rounds": self.total_rounds,
            "event": self.current_event,
            "agents": agents_state,
            "decisions": self.round_decisions,
            "metrics": metrics,
            "market_state": self.current_market_state.to_dict() if self.current_market_state else None,
            "total_cost": round(self.total_cost, 6),
        }

    def _compute_metrics(self) -> dict[str, Any]:
        fill_rates: dict[str, float] = {}
        hoarding_index: dict[str, int] = {}
        trust_matrix: dict[str, dict[str, float]] = {}
        price_index: dict[str, float] = {"foundry": 0, "chipDesigner": 0, "tier1Supplier": 0}
        tier_counts: dict[str, int] = {"foundry": 0, "chipDesigner": 0, "tier1Supplier": 0}

        for aid, agent in self.agents_map.items():
            fill_rates[aid] = round(agent.fill_rate, 3)
            held = int(agent.current_decision.get("held_in_reserve", 0)) if agent.current_decision else 0
            hoarding_index[aid] = held
            trust_matrix[aid] = dict(agent.trust_scores)

            if agent.tier in price_index:
                price_index[agent.tier] += agent.current_price
                tier_counts[agent.tier] += 1

        for tier in price_index:
            if tier_counts[tier] > 0:
                price_index[tier] = round(price_index[tier] / tier_counts[tier], 2)

        # Bullwhip: ratio of order variance per tier
        bullwhip: dict[str, float] = {}
        for tier_name, agents_list in [
            ("oem", self.oems),
            ("tier1Supplier", self.tier1s),
            ("chipDesigner", self.designers),
        ]:
            total_orders = []
            for a in agents_list:
                orders = a.current_decision.get("orders", {})
                total_orders.append(sum(int(v) for v in orders.values()))
            if total_orders:
                mean_o = sum(total_orders) / len(total_orders)
                var_o = sum((x - mean_o) ** 2 for x in total_orders) / max(len(total_orders), 1)
                bullwhip[tier_name] = round(var_o, 1)
            else:
                bullwhip[tier_name] = 0

        return {
            "fill_rates": fill_rates,
            "hoarding_index": hoarding_index,
            "trust_matrix": trust_matrix,
            "price_index": price_index,
            "bullwhip": bullwhip,
        }

    def get_full_state(self) -> dict[str, Any]:
        """Return the full simulation state for the frontend."""
        agents_state: dict[str, Any] = {}
        for aid, agent in self.agents_map.items():
            agents_state[aid] = {
                "agent_id": aid,
                "display_name": agent.display_name,
                "tier": agent.tier,
                "inventory": agent.inventory,
                "capacity": agent.effective_capacity,
                "current_price": agent.current_price,
                "emotional_state": agent.emotional_state,
                "affect": agent.affect.to_dict(),
                "cognitive_load": agent.last_cognitive_load,
                "fill_rate": agent.fill_rate,
                "trust_scores": dict(agent.trust_scores),
                "current_decision": dict(agent.current_decision) if agent.current_decision else None,
                "decision_history": agent.decision_history[-3:],
                "round_results": agent.round_results[-3:],
                "revenue": round(agent.revenue, 2),
                "costs": round(agent.costs, 2),
                "profit": round(agent.revenue - agent.costs, 2),
                "round_revenue": round(agent.round_revenue, 2),
                "round_costs": round(agent.round_costs, 2),
                "effective_quarterly_need": agent.effective_quarterly_need,
                # Memory & reflection data
                "memories": agent.memory_stream.to_list()[-15:],
                "reflections": agent.reflections,
                "memory_count": len(agent.memory_stream.records),
                "parse_failure_count": agent.parse_failure_count,
                "consecutive_parse_failures": agent.consecutive_parse_failures,
                "last_parse_failure_round": agent.last_parse_failure_round,
                "degraded": agent.consecutive_parse_failures >= 2,
            }

        return {
            "status": self.status,
            "current_round": int(self.time),
            "total_rounds": self.total_rounds,
            "current_event": self.current_event,
            "agents": agents_state,
            "metrics": self._compute_metrics() if self.time > 0 else None,
            "market_state": self.current_market_state.to_dict() if self.current_market_state else None,
            "total_cost": round(self.total_cost, 6),
            "scenario_name": "The Great Semiconductor Shortage",
            "temperature": self.temperature,
        }

    def get_history(self) -> dict[str, Any]:
        """Return DataCollector output formatted for charting."""
        model_df = self.datacollector.get_model_vars_dataframe()
        agent_df = self.datacollector.get_agent_vars_dataframe()

        rounds: list[dict[str, Any]] = []
        for step_idx in range(len(model_df)):
            row = model_df.iloc[step_idx]
            step_agents = agent_df.xs(step_idx, level="Step") if step_idx in agent_df.index.get_level_values("Step") else None

            agent_data: dict[str, Any] = {}
            if step_agents is not None:
                for _, arow in step_agents.iterrows():
                    aid = arow.get("agent_id", "")
                    if aid:
                        agent_data[aid] = {
                            "inventory": arow.get("inventory", 0),
                            "current_price": arow.get("current_price", 0),
                            "emotional_state": arow.get("emotional_state", ""),
                            "affect": arow.get("affect", {}),
                            "cognitive_load": arow.get("cognitive_load", 0.0),
                            "fill_rate": arow.get("fill_rate", 1.0),
                            "trust_scores": arow.get("trust_scores", {}),
                            "decision": arow.get("decision", {}),
                        }

            rounds.append({
                "round": int(row.get("round", step_idx + 1)),
                "event": row.get("event", ""),
                "total_cost": row.get("total_cost", 0),
                "agents": agent_data,
            })

        return {"rounds": rounds}
