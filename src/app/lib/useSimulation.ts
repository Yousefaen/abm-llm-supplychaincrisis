"use client";

import { useCallback, useRef, useState } from "react";
import {
  getHistory,
  getState,
  resetSimulation,
  runStepStream,
} from "./api";
import type {
  AgentState,
  HistoryRound,
  RoundMetrics,
  SSEAgentDecided,
  SSEEvent,
  SSERoundComplete,
} from "./types";

export interface SimState {
  status: "idle" | "running" | "complete" | "error";
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
};

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
          setState((s) => ({
            ...s,
            thinkingAgent: e.agent_id,
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
          }));
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

  return { state, reset, step, fetchState, autoPlay, pause };
}
