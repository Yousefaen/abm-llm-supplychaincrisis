"use client";

import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import type { EmotionalState, HistoryRound } from "../lib/types";
import { EMOTIONAL_COLORS, TIER_COLORS } from "../lib/types";

interface Props {
  history: HistoryRound[];
}

interface LogEntry {
  round: number;
  agentId: string;
  tier: string;
  emotion: EmotionalState;
  summary: string;
}

function buildEntries(history: HistoryRound[]): LogEntry[] {
  const entries: LogEntry[] = [];
  for (const round of history) {
    for (const [agentId, data] of Object.entries(round.agents)) {
      const dec = data.decision;
      if (!dec || (!dec.reasoning && !dec.allocations && !dec.orders)) continue;

      let summary = dec.reasoning ?? "";
      if (!summary) {
        if (dec.allocations) {
          const total = Object.values(dec.allocations).reduce(
            (a: number, b: unknown) => a + Number(b),
            0
          );
          summary = `Allocated ${total} units across customers.`;
        } else if (dec.orders) {
          const total = Object.values(dec.orders).reduce(
            (a: number, b: unknown) => a + Number(b),
            0
          );
          summary = `Ordered ${total} units from suppliers.`;
        }
      }

      entries.push({
        round: round.round,
        agentId,
        tier: data.decision?.type === "supplier" ? "supplier" : "buyer",
        emotion: (data.emotional_state ?? "confident") as EmotionalState,
        summary,
      });
    }
  }
  return entries;
}

export default function EventLog({ history }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const entries = buildEntries(history);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [entries.length]);

  return (
    <div className="flex flex-col h-full">
      <div className="p-3 pb-1 text-sm font-semibold border-b border-border">
        Event Log
      </div>
      <ScrollArea className="flex-1" ref={scrollRef}>
        <div className="p-3 space-y-2">
          {entries.length === 0 && (
            <p className="text-sm text-muted-foreground">
              No events yet. Run a round to see agent decisions.
            </p>
          )}
          {entries.map((entry, i) => (
            <div
              key={i}
              className="flex items-start gap-2 text-xs leading-relaxed"
            >
              <span className="shrink-0 font-mono text-muted-foreground w-5">
                R{entry.round}
              </span>
              <span className="shrink-0 font-semibold w-28 truncate">
                {entry.agentId}
              </span>
              <Badge
                variant="outline"
                className="shrink-0 text-[10px] px-1 py-0"
                style={{
                  borderColor: EMOTIONAL_COLORS[entry.emotion],
                  color: EMOTIONAL_COLORS[entry.emotion],
                }}
              >
                {entry.emotion}
              </Badge>
              <span className="text-muted-foreground">{entry.summary}</span>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
