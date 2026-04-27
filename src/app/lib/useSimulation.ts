"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  getExperiment,
  getHistory,
  getServerConfig,
  getState,
  listExperiments,
  resetSimulation,
  runStepStream,
} from "./api";
import type {
  ActivityEntry,
  ActivityRole,
  AgentState,
  EmotionalState,
  ExperimentDetail,
  ExperimentRunRound,
  ExperimentSummary,
  HistoryRound,
  RoundMetrics,
  SSEAgentDecided,
  SSEError,
  SSEEvent,
  SSERoundComplete,
  Tier,
} from "./types";

export interface SimState {
  status: "idle" | "running" | "complete" | "error" | "replay";
  currentRound: number;
  totalRounds: number;
  currentEvent: string;
  agents: Record<string, AgentState>;
  metrics: RoundMetrics | null;
  totalCost: number;
  temperature: number;
  history: HistoryRound[];
  thinkingAgent: string | null;
  error: string | null;
  liveFeed: ActivityEntry[];
  // Replay mode — when an experiment is loaded, currentRound is bound to
  // the scrubber and state.agents reflects historical state at that round.
  replay: {
    active: boolean;
    experimentId: string | null;
    experimentLabel: string | null;
    perRound: ExperimentRunRound[];
    notes: string;
  };
  personaVariant: string;
  experiments: ExperimentSummary[];
}

const INITIAL: SimState = {
  status: "idle",
  currentRound: 0,
  totalRounds: 10,
  currentEvent: "",
  agents: {},
  metrics: null,
  totalCost: 0,
  temperature: 1.0,
  history: [],
  thinkingAgent: null,
  error: null,
  liveFeed: [],
  replay: {
    active: false,
    experimentId: null,
    experimentLabel: null,
    perRound: [],
    notes: "",
  },
  personaVariant: "hand-crafted",
  experiments: [],
};

// Cap on feed length so long auto-plays don't grow state without bound.
// 300 entries ≈ 10 rounds × ~30 streamed events per round with headroom.
const FEED_LIMIT = 300;

// Turn a streamed agent_decided event into a compact feed row. We condense
// each role into a one-line summary + optional detail; the UI handles any
// richer rendering (colors, truncation, badges).
function makeActivityEntry(
  event: SSEAgentDecided,
  round: number,
): ActivityEntry | null {
  const { agent_id, tier, role, decision } = event;
  const validRole: ActivityRole | null =
    role === "planning" ||
    role === "signaling" ||
    role === "buyer" ||
    role === "supplier" ||
    role === "reflection"
      ? role
      : null;
  if (!validRole) return null;

  let summary = "";
  let detail: string | undefined;

  if (validRole === "planning") {
    const plan = decision.plan;
    summary = plan?.invalidated
      ? "plan invalidated — replanning"
      : "sets strategy";
    detail = (plan?.goals ?? []).slice(0, 2).join("  ·  ");
  } else if (validRole === "signaling") {
    const signals = decision.signals ?? [];
    if (signals.length === 0) return null;
    const first = signals[0];
    const to = first.recipient ?? "all partners";
    summary = `${first.signal_type.replace("_", " ")} → ${to}`;
    detail = first.content;
    if (signals.length > 1) {
      detail += `  (+${signals.length - 1})`;
    }
  } else if (validRole === "reflection") {
    const insights = decision.insights ?? [];
    if (insights.length === 0) return null;
    summary = `${insights.length} insight${insights.length > 1 ? "s" : ""}`;
    detail = insights[0];
  } else if (validRole === "buyer") {
    const orders = decision.orders ?? {};
    const entries = Object.entries(orders).filter(
      ([, v]) => Number(v) > 0,
    );
    const total = entries.reduce((a, [, v]) => a + Number(v), 0);
    summary = total > 0 ? `orders ${total} units` : "no orders";
    const dests = entries.map(([k, v]) => `${v} from ${k}`).join(", ");
    detail = dests || undefined;
    if (decision.will_seek_alternatives) {
      detail = detail
        ? `seeking alternatives · ${detail}`
        : "seeking alternative suppliers";
    }
    if (decision.reasoning) {
      detail = detail
        ? `${detail} — ${decision.reasoning}`
        : decision.reasoning;
    }
  } else if (validRole === "supplier") {
    const allocs = decision.allocations ?? {};
    const held = decision.held_in_reserve ?? 0;
    const entries = Object.entries(allocs).filter(
      ([, v]) => Number(v) > 0,
    );
    const total = entries.reduce((a, [, v]) => a + Number(v), 0);
    summary =
      total > 0 ? `allocates ${total} units` : "no allocations";
    if (held > 0) summary += ` · holds ${held}`;
    const dests = entries.map(([k, v]) => `${v} → ${k}`).join(", ");
    detail = dests || undefined;
    if (decision.reasoning) {
      detail = detail
        ? `${detail} — ${decision.reasoning}`
        : decision.reasoning;
    }
  }

  return {
    id: `${round}-${agent_id}-${validRole}-${event_counter()}`,
    round,
    agentId: agent_id,
    tier: tier as Tier,
    role: validRole,
    emotion: decision.emotional_state as EmotionalState | undefined,
    summary,
    detail,
    timestamp: Date.now(),
  };
}

// Monotonic counter so entries always get a unique, stable React key even
// when several arrive within the same millisecond.
let _eventCounter = 0;
function event_counter(): number {
  return ++_eventCounter;
}

export function useSimulation() {
  const [state, setState] = useState<SimState>(INITIAL);
  const abortRef = useRef<AbortController | null>(null);
  const autoPlayRef = useRef(false);

  const reset = useCallback(async (temperature = 1.0) => {
    try {
      abortRef.current?.abort();
      autoPlayRef.current = false;
      const data = await resetSimulation(temperature);
      setState({
        ...INITIAL,
        temperature,
        agents: data.agents,
        totalRounds: data.total_rounds,
      });
    } catch (err) {
      setState((s) => ({
        ...s,
        status: "error",
        error: String(err),
      }));
    }
  }, []);

  const step = useCallback(async () => {
    setState((s) => ({ ...s, status: "running", error: null, thinkingAgent: null }));

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await runStepStream((event: SSEEvent) => {
        if (event.type === "agent_decided") {
          const e = event as SSEAgentDecided;
          setState((s) => {
            const round = s.currentRound + 1;
            const entry = makeActivityEntry(e, round);
            const nextFeed = entry
              ? [...s.liveFeed, entry].slice(-FEED_LIMIT)
              : s.liveFeed;
            return {
              ...s,
              thinkingAgent: e.agent_id,
              liveFeed: nextFeed,
              agents: {
                ...s.agents,
                [e.agent_id]: {
                  ...s.agents[e.agent_id],
                  current_decision: e.decision,
                  emotional_state:
                    e.decision.emotional_state ??
                    s.agents[e.agent_id]?.emotional_state ??
                    "confident",
                },
              },
            };
          });
        } else if (event.type === "round_complete") {
          const e = event as SSERoundComplete;
          setState((s) => ({
            ...s,
            status: e.status === "complete" ? "complete" : "idle",
            currentRound: e.round,
            totalRounds: e.total_rounds,
            currentEvent: e.event,
            agents: e.agents,
            metrics: e.metrics,
            totalCost: e.total_cost,
            thinkingAgent: null,
          }));
        } else if (event.type === "error") {
          const e = event as SSEError;
          setState((s) => ({
            ...s,
            status: "error",
            error: e.exc_type ? `${e.exc_type}: ${e.message}` : e.message,
            thinkingAgent: null,
          }));
        }
      }, controller.signal);

      // Fetch updated history
      const hist = await getHistory();
      setState((s) => ({ ...s, history: hist.rounds }));
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setState((s) => ({
          ...s,
          status: "error",
          error: String(err),
          thinkingAgent: null,
        }));
      }
    }
  }, []);

  const fetchState = useCallback(async () => {
    try {
      const data = await getState();
      const hist = await getHistory();
      setState((s) => ({
        ...s,
        status: (data.status as SimState["status"]) || "idle",
        currentRound: data.current_round,
        totalRounds: data.total_rounds,
        currentEvent: data.current_event,
        agents: data.agents,
        metrics: data.metrics,
        totalCost: data.total_cost,
        temperature: data.temperature,
        history: hist.rounds,
      }));
    } catch (err) {
      setState((s) => ({ ...s, status: "error", error: String(err) }));
    }
  }, []);

  const autoPlay = useCallback(async () => {
    autoPlayRef.current = true;
    try {
      while (autoPlayRef.current) {
        const snap = await getState();
        if (snap.status === "complete" || !autoPlayRef.current) break;
        await step();
        // Small pause between rounds for visual effect
        await new Promise((r) => setTimeout(r, 500));
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setState((s) => ({
          ...s,
          status: "error",
          error: String(err),
          thinkingAgent: null,
        }));
      }
    }
  }, [step]);

  const pause = useCallback(() => {
    autoPlayRef.current = false;
    abortRef.current?.abort();
  }, []);

  // -------------------------------------------------------------------
  // Replay mode — load a registry experiment and walk through its rounds
  // without paying for a 14-min live LLM run. Used for the demo path.
  // -------------------------------------------------------------------

  // Project a single registry round into the SimState shape so the
  // existing graph / inspect / activity-feed components don't need to
  // know anything about replay.
  const projectRound = useCallback(
    (detail: ExperimentDetail, roundIdx: number): Partial<SimState> => {
      const r = detail.run.per_round[roundIdx - 1];
      if (!r) return {};
      const agents: Record<string, AgentState> = {};
      for (const [aid, snap] of Object.entries(r.agents)) {
        // Pad missing fields with sane defaults so the UI doesn't NPE.
        agents[aid] = {
          agent_id: aid,
          display_name: aid,
          tier: snap.tier,
          inventory: snap.inventory,
          capacity: snap.capacity ?? 0,
          current_price: snap.current_price,
          emotional_state: snap.emotional_state,
          fill_rate: snap.fill_rate,
          trust_scores: snap.trust_scores ?? {},
          current_decision: snap.current_decision ?? null,
          decision_history: [],
          round_results: [],
          revenue: snap.revenue ?? 0,
          costs: snap.costs ?? 0,
          profit: snap.profit ?? 0,
          round_revenue: snap.round_revenue ?? 0,
          round_costs: snap.round_costs ?? 0,
          effective_quarterly_need: snap.effective_quarterly_need ?? 0,
          memories: snap.memories ?? [],
          reflections: snap.reflections ?? [],
          memory_count: snap.memory_count ?? 0,
          current_plan: snap.current_plan ?? null,
          signals_sent: snap.signals_sent ?? [],
          signals_received: snap.signals_received ?? [],
        };
      }

      // Build an activity feed from the round events so the side panel
      // populates for replay rounds the same way it does live.
      const feed: ActivityEntry[] = [];
      for (const evt of r.events ?? []) {
        const fakeSse: SSEAgentDecided = {
          type: "agent_decided",
          agent_id: evt.agent_id,
          tier: evt.tier as Tier,
          role: evt.role,
          decision: evt.decision,
        };
        const entry = makeActivityEntry(fakeSse, r.round);
        if (entry) feed.push(entry);
      }

      return {
        currentRound: r.round,
        currentEvent: r.event,
        agents,
        metrics: r.metrics,
        totalCost: r.cumulative_cost_usd,
        liveFeed: feed,
      };
    },
    [],
  );

  const detailRef = useRef<ExperimentDetail | null>(null);

  const loadReplay = useCallback(
    async (experimentId: string) => {
      try {
        autoPlayRef.current = false;
        abortRef.current?.abort();
        const detail = await getExperiment(experimentId);
        detailRef.current = detail;
        const totalRounds = detail.run.per_round.length;
        const projection = projectRound(detail, totalRounds); // jump to final round
        const history: HistoryRound[] = detail.run.per_round.map((r) => ({
          round: r.round,
          event: r.event,
          total_cost: r.cumulative_cost_usd,
          agents: Object.fromEntries(
            Object.entries(r.agents).map(([aid, snap]) => [
              aid,
              {
                inventory: snap.inventory,
                current_price: snap.current_price,
                emotional_state: snap.emotional_state,
                fill_rate: snap.fill_rate,
                trust_scores: snap.trust_scores ?? {},
                decision: snap.current_decision ?? {},
              },
            ]),
          ),
        }));
        setState((s) => ({
          ...s,
          ...projection,
          status: "replay",
          totalRounds,
          history,
          replay: {
            active: true,
            experimentId,
            experimentLabel: detail.meta.label,
            perRound: detail.run.per_round,
            notes: detail.meta.notes ?? "",
          },
          personaVariant: detail.meta.config?.persona_variant ?? "hand-crafted",
          thinkingAgent: null,
          error: null,
        }));
      } catch (err) {
        setState((s) => ({ ...s, status: "error", error: String(err) }));
      }
    },
    [projectRound],
  );

  const setReplayRound = useCallback(
    (round: number) => {
      const detail = detailRef.current;
      if (!detail) return;
      const projection = projectRound(detail, round);
      setState((s) => ({ ...s, ...projection }));
    },
    [projectRound],
  );

  const exitReplay = useCallback(async () => {
    detailRef.current = null;
    setState((s) => ({
      ...s,
      replay: { active: false, experimentId: null, experimentLabel: null, perRound: [], notes: "" },
    }));
    try {
      const data = await getState();
      const hist = await getHistory();
      setState((s) => ({
        ...s,
        status: (data.status as SimState["status"]) || "idle",
        currentRound: data.current_round,
        totalRounds: data.total_rounds,
        currentEvent: data.current_event,
        agents: data.agents,
        metrics: data.metrics,
        totalCost: data.total_cost,
        history: hist.rounds,
        liveFeed: [],
      }));
    } catch {
      // server may be unavailable; replay exit should still clear state
    }
  }, []);

  // Discover available experiments + server-side persona variant on mount.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [{ experiments }, cfg] = await Promise.all([
          listExperiments(),
          getServerConfig().catch(() => ({ persona_variant: "hand-crafted" })),
        ]);
        if (!cancelled) {
          setState((s) => ({ ...s, experiments, personaVariant: cfg.persona_variant }));
        }
      } catch {
        // Endpoints unavailable — fall through silently; live mode still works.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return {
    state,
    reset,
    step,
    fetchState,
    autoPlay,
    pause,
    loadReplay,
    setReplayRound,
    exitReplay,
  };
}
