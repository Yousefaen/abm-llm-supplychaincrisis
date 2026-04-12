"use client";

import { useEffect, useState } from "react";
import { useSimulation } from "./lib/useSimulation";
import SimulationControls from "./components/SimulationControls";
import SupplyChainGraph from "./components/SupplyChainGraph";
import AgentCard from "./components/AgentCard";
import MetricsDashboard from "./components/MetricsDashboard";
import EventLog from "./components/EventLog";
import RoundTimeline from "./components/RoundTimeline";

export default function Home() {
  const { state, reset, step, fetchState, autoPlay, pause } = useSimulation();
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  useEffect(() => {
    fetchState();
  }, [fetchState]);

  const agentData = selectedAgent ? state.agents[selectedAgent] : null;

  return (
    <main className="flex flex-col h-screen overflow-hidden">
      {/* Top controls bar */}
      <div className="shrink-0 p-3 border-b border-border">
        <SimulationControls
          state={state}
          onStep={step}
          onAutoPlay={autoPlay}
          onPause={pause}
          onReset={reset}
        />
      </div>

      {/* Round timeline */}
      <div className="shrink-0 px-3 pt-2">
        <RoundTimeline
          currentRound={state.currentRound}
          totalRounds={state.totalRounds}
          history={state.history}
        />
      </div>

      {/* Main content area */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-3 p-3 min-h-0">
        {/* Left: Supply chain graph */}
        <div className="lg:col-span-2 rounded-lg border border-border bg-card overflow-hidden">
          <SupplyChainGraph
            agents={state.agents}
            onSelectAgent={setSelectedAgent}
            selectedAgent={selectedAgent}
            thinkingAgent={state.thinkingAgent}
          />
        </div>

        {/* Right: Agent detail panel */}
        <div className="rounded-lg border border-border bg-card overflow-auto">
          {agentData ? (
            <AgentCard agent={agentData} />
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm p-6">
              Click an agent node to view details
            </div>
          )}
        </div>
      </div>

      {/* Bottom: Metrics + Activity Feed */}
      <div className="shrink-0 grid grid-cols-1 lg:grid-cols-2 gap-3 px-3 pb-3 max-h-[45vh]">
        <div className="rounded-lg border border-border bg-card overflow-auto">
          <MetricsDashboard history={state.history} agents={state.agents} />
        </div>
        <div className="rounded-lg border border-border bg-card overflow-hidden">
          <EventLog
            history={state.history}
            agents={state.agents}
            currentRound={state.currentRound}
          />
        </div>
      </div>
    </main>
  );
}
