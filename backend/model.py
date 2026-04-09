from __future__ import annotations

from typing import Any

from mesa import Model, DataCollector

from agents import (
    AGENT_SPECS,
    HAIKU_INPUT_COST_PER_M,
    HAIKU_OUTPUT_COST_PER_M,
    ChipDesignerAgent,
    FoundryAgent,
    OEMAgent,
    SupplyChainAgent,
    Tier1SupplierAgent,
    create_agent,
)
from debug_session import dbg_log
from scenarios import (
    CAPACITY_SHOCKS,
    DEMAND_MULTIPLIERS,
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
                "fill_rate": lambda a: a.fill_rate,
                "trust_scores": lambda a: dict(a.trust_scores),
                "decision": lambda a: dict(a.current_decision) if a.current_decision else {},
                "profit": lambda a: round(a.revenue - a.costs, 2),
            },
        )

        # Round-level decision log (for streaming to frontend)
        self.round_decisions: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # One quarter of the simulation (API entry point)
    # ------------------------------------------------------------------
    # Mesa 3.5 replaces instance ``step`` with _wrapped_step (returns None).
    # Never call model.step() from FastAPI expecting a dict — use advance_quarter().
    def advance_quarter(self) -> dict[str, Any]:
        """Execute one round. Returns a summary dict for the API."""
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

            # Apply mechanical scenario effects for this round
            self._apply_scenario_effects(current_round)

            # Clear current decisions and per-round financials
            for agent in self.agents_map.values():
                agent.current_decision = {}
                agent.round_revenue = 0.0
                agent.round_costs = 0.0
                agent.inventory_cost = 0.0

            # ----------------------------------------------------------
            # Phase 1: ORDERING (bottom-up)
            # OEMs order -> Tier-1 orders -> Chip Designers order
            # ----------------------------------------------------------
            for oem in self.oems:
                oem.step()
                self._record_decision(oem)

            for t1 in self.tier1s:
                t1.step()  # buyer step
                self._record_decision(t1, role="buyer")

            for cd in self.designers:
                cd.step()  # buyer step
                self._record_decision(cd, role="buyer")

            # ----------------------------------------------------------
            # Phase 2: ALLOCATION (top-down)
            # Foundries allocate -> Chip Designers allocate -> Tier-1 allocates
            # ----------------------------------------------------------
            for foundry in self.foundries:
                foundry.step()
                self._record_decision(foundry)

            for cd in self.designers:
                cd.supply_step()
                self._record_decision(cd, role="supplier")

            for t1 in self.tier1s:
                t1.supply_step()
                self._record_decision(t1, role="supplier")

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

            # Accumulate LLM API cost
            for agent in self.agents_map.values():
                self.total_cost += (
                    agent.last_input_tokens * HAIKU_INPUT_COST_PER_M / 1_000_000
                    + agent.last_output_tokens * HAIKU_OUTPUT_COST_PER_M / 1_000_000
                )

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
                max_price = float(buyer.current_decision.get("max_price_willing_to_pay", 0))
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
                    # Combined score — price matters more than trust
                    scores[bid] = price_factor * 0.6 + trust_factor * 0.4

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
            buyer.inventory -= consumed

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
    def _record_decision(self, agent: SupplyChainAgent, role: str = "") -> None:
        self.round_decisions.append({
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
            }

        return {
            "status": self.status,
            "current_round": int(self.time),
            "total_rounds": self.total_rounds,
            "current_event": self.current_event,
            "agents": agents_state,
            "metrics": self._compute_metrics() if self.time > 0 else None,
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
