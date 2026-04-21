"use client";

import type { AgentState, HistoryRound } from "../lib/types";

interface Props {
  history: HistoryRound[];
  currentEvent: string;
  thinkingAgent: string | null;
  agents: Record<string, AgentState>;
}

// Low-chrome serif ticker for the Live canvas. Shows the current scenario
// event and — while a round is running — whichever agent is currently
// thinking. Between rounds, shows the most recent completed event.
//
// The idea: one calm line of readable prose at the bottom of the graph.
// It is not a log — the full log lives on /analytics. This is just the
// peripheral signal that something is happening.
export default function Ticker({
  history,
  currentEvent,
  thinkingAgent,
  agents,
}: Props) {
  const last = history[history.length - 1];

  let body: string;
  if (thinkingAgent) {
    const name = agents[thinkingAgent]?.display_name ?? thinkingAgent;
    body = `${name} is deciding…`;
  } else if (currentEvent) {
    body = currentEvent;
  } else if (last?.event) {
    body = last.event;
  } else {
    body = "Press play to begin.";
  }

  return (
    <div className="absolute bottom-3 left-1/2 -translate-x-1/2 max-w-2xl w-[calc(100%-2rem)] px-5 py-3 rounded-full bg-card/80 backdrop-blur-sm border border-border/60 shadow-sm">
      <p className="font-serif text-base leading-snug text-foreground/85 text-center truncate">
        {body}
      </p>
    </div>
  );
}
