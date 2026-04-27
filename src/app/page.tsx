"use client";

import { useCallback, useEffect, useState } from "react";
import { useSimulation } from "./lib/useSimulation";
import TopBar from "./components/TopBar";
import Scrubber from "./components/Scrubber";
import SupplyChainGraph from "./components/SupplyChainGraph";
import Ticker from "./components/Ticker";
import InspectPanel from "./components/InspectPanel";
import ActivityFeed from "./components/ActivityFeed";

export default function Home() {
  const {
    state,
    reset,
    step,
    fetchState,
    autoPlay,
    pause,
    loadReplay,
    setReplayRound,
    exitReplay,
  } = useSimulation();

  // Inspect selection. When set, we are in Inspect mode; otherwise Live.
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  // Scrubbing: when the user clicks a past round, we "freeze" the focus
  // to that round.  In replay mode this also drives state.agents back to
  // the historical snapshot so the graph + inspect panel reflect the
  // chosen round.
  const [focusedRound, setFocusedRound] = useState<number | null>(null);

  useEffect(() => {
    if (state.replay.active) return; // Don't poll live state during replay
    fetchState();
  }, [fetchState, state.replay.active]);

  // In replay mode, route scrubbing to setReplayRound so the agent state
  // updates with the focused round.
  const handleSelectRound = useCallback(
    (round: number | null) => {
      setFocusedRound(round);
      if (state.replay.active && round !== null) {
        setReplayRound(round);
      }
    },
    [state.replay.active, setReplayRound],
  );

  // RTS-style keyboard: space to toggle play/pause, Esc to return to live,
  // arrow keys to step. We guard against typing targets so the shortcuts
  // never fight a real input.
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.isContentEditable)
      ) {
        return;
      }

      if (e.key === " " || e.code === "Space") {
        e.preventDefault();
        if (state.status === "running") {
          pause();
        } else if (state.status !== "complete") {
          autoPlay();
        }
        return;
      }
      if (e.key === "Escape") {
        if (selectedAgent) {
          setSelectedAgent(null);
        } else if (focusedRound !== null) {
          setFocusedRound(null);
        }
        return;
      }
      if (e.key === "ArrowRight") {
        if (state.status !== "running" && state.status !== "complete") {
          step();
        }
        return;
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [state.status, selectedAgent, focusedRound, pause, autoPlay, step]);

  const handleSelectAgent = useCallback((agentId: string | null) => {
    setSelectedAgent(agentId);
  }, []);

  const agentData = selectedAgent ? state.agents[selectedAgent] : null;

  return (
    <main className="flex flex-col h-screen overflow-hidden bg-background">
      <TopBar
        state={state}
        onStep={step}
        onAutoPlay={autoPlay}
        onPause={pause}
        onReset={reset}
        onLoadReplay={loadReplay}
        onExitReplay={exitReplay}
      />

      {/* Hero area — Live canvas + right-side activity feed, or Inspect
          document when an agent is selected. The feed is hidden below lg
          breakpoints so the graph keeps room to breathe on tablets. */}
      <div className="flex-1 min-h-0 flex">
        <div className="flex-1 relative min-w-0">
          {agentData ? (
            <InspectPanel
              agent={agentData}
              currentRound={state.currentRound}
              onClose={() => setSelectedAgent(null)}
            />
          ) : (
            <div className="relative h-full">
              <SupplyChainGraph
                agents={state.agents}
                onSelectAgent={handleSelectAgent}
                selectedAgent={selectedAgent}
                thinkingAgent={state.thinkingAgent}
              />
              <Ticker
                history={state.history}
                currentEvent={state.currentEvent}
                thinkingAgent={state.thinkingAgent}
                agents={state.agents}
              />
            </div>
          )}
        </div>
        <aside className="hidden lg:flex w-80 xl:w-96 shrink-0">
          <ActivityFeed
            entries={state.liveFeed}
            agents={state.agents}
            thinkingAgent={state.thinkingAgent}
          />
        </aside>
      </div>

      <Scrubber
        currentRound={state.currentRound}
        totalRounds={state.totalRounds}
        history={state.history}
        focusedRound={focusedRound}
        onSelectRound={handleSelectRound}
      />
    </main>
  );
}
