"use client";

import { useEffect, useRef, useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import type {
  AgentState,
  EmotionalState,
  HistoryRound,
} from "../lib/types";
import { EMOTIONAL_COLORS, TIER_COLORS } from "../lib/types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type EntryKind = "round_header" | "signal" | "reflection" | "plan" | "decision";

interface FeedEntry {
  kind: EntryKind;
  round: number;
  agentId?: string;
  emotion?: EmotionalState;
  text: string;
  // signal-specific
  signalType?: string;
  recipient?: string | null;
  // plan-specific
  invalidated?: boolean;
}

// ---------------------------------------------------------------------------
// Colors
// ---------------------------------------------------------------------------

const SIGNAL_COLORS: Record<string, string> = {
  price_warning: "#f97316",
  loyalty_pledge: "#22c55e",
  threat: "#ef4444",
  information: "#3b82f6",
  request: "#eab308",
};

const KIND_LABELS: Record<EntryKind, string> = {
  round_header: "EVENT",
  signal: "SIGNAL",
  reflection: "THOUGHT",
  plan: "PLAN",
  decision: "DECISION",
};

// ---------------------------------------------------------------------------
// Build feed entries
// ---------------------------------------------------------------------------

interface Props {
  history: HistoryRound[];
  agents: Record<string, AgentState>;
  currentRound: number;
}

function buildFeed(
  history: HistoryRound[],
  agents: Record<string, AgentState>,
  currentRound: number,
): FeedEntry[] {
  const entries: FeedEntry[] = [];

  // Past rounds from history
  for (const round of history) {
    // Round header
    entries.push({
      kind: "round_header",
      round: round.round,
      text: round.event || `Round ${round.round}`,
    });

    // Decisions from history
    for (const [agentId, data] of Object.entries(round.agents)) {
      const dec = data.decision;
      if (!dec || (!dec.reasoning && !dec.allocations && !dec.orders)) continue;

      let summary = dec.reasoning ?? "";
      if (!summary) {
        if (dec.allocations) {
          const total = Object.values(dec.allocations).reduce(
            (a: number, b: unknown) => a + Number(b),
            0,
          );
          summary = `Allocated ${total} units across customers.`;
        } else if (dec.orders) {
          const total = Object.values(dec.orders).reduce(
            (a: number, b: unknown) => a + Number(b),
            0,
          );
          summary = `Ordered ${total} units from suppliers.`;
        }
      }

      entries.push({
        kind: "decision",
        round: round.round,
        agentId,
        emotion: (data.emotional_state ?? "confident") as EmotionalState,
        text: summary,
      });
    }
  }

  // Current round live data: signals, reflections, plans
  if (currentRound > 0 && Object.keys(agents).length > 0) {
    for (const [agentId, agent] of Object.entries(agents)) {
      // Signals sent
      if (agent.signals_sent) {
        for (const sig of agent.signals_sent) {
          entries.push({
            kind: "signal",
            round: currentRound,
            agentId,
            text: sig.content,
            signalType: sig.signal_type,
            recipient: sig.recipient,
          });
        }
      }

      // Reflections
      if (agent.reflections) {
        for (const insight of agent.reflections) {
          entries.push({
            kind: "reflection",
            round: currentRound,
            agentId,
            emotion: agent.emotional_state,
            text: insight,
          });
        }
      }

      // Plan (show if created this round or invalidated)
      if (agent.current_plan) {
        const plan = agent.current_plan;
        if (plan.created_round === currentRound) {
          const goalSummary = plan.goals.slice(0, 2).join("; ");
          entries.push({
            kind: "plan",
            round: currentRound,
            agentId,
            text: goalSummary,
            invalidated: plan.invalidated,
          });
        } else if (plan.invalidated) {
          entries.push({
            kind: "plan",
            round: currentRound,
            agentId,
            text: "Plan invalidated by market shock — replanning needed",
            invalidated: true,
          });
        }
      }
    }
  }

  return entries;
}

// ---------------------------------------------------------------------------
// Filter tabs
// ---------------------------------------------------------------------------

const FILTERS = [
  { key: "all", label: "All" },
  { key: "signal", label: "Signals" },
  { key: "reflection", label: "Thoughts" },
  { key: "decision", label: "Decisions" },
] as const;

type FilterKey = (typeof FILTERS)[number]["key"];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function EventLog({ history, agents, currentRound }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [filter, setFilter] = useState<FilterKey>("all");

  const allEntries = buildFeed(history, agents, currentRound);
  const entries =
    filter === "all"
      ? allEntries
      : allEntries.filter(
          (e) => e.kind === filter || e.kind === "round_header",
        );

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [entries.length]);

  return (
    <div className="flex flex-col h-full">
      {/* Header with filter tabs */}
      <div className="p-2 pb-0 border-b border-border flex items-center gap-2">
        <span className="text-sm font-semibold shrink-0">Activity</span>
        <div className="flex gap-1 ml-auto">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`text-[10px] px-2 py-0.5 rounded-full transition-colors ${
                filter === f.key
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted/50 text-muted-foreground hover:bg-muted"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <ScrollArea className="flex-1" ref={scrollRef}>
        <div className="p-2 space-y-1">
          {entries.length === 0 && (
            <p className="text-sm text-muted-foreground p-2">
              No events yet. Run a round to see agent activity.
            </p>
          )}
          {entries.map((entry, i) => (
            <FeedEntryRow key={i} entry={entry} />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Entry renderers
// ---------------------------------------------------------------------------

function FeedEntryRow({ entry }: { entry: FeedEntry }) {
  if (entry.kind === "round_header") {
    return <RoundHeader entry={entry} />;
  }
  if (entry.kind === "signal") {
    return <SignalRow entry={entry} />;
  }
  if (entry.kind === "reflection") {
    return <ReflectionRow entry={entry} />;
  }
  if (entry.kind === "plan") {
    return <PlanRow entry={entry} />;
  }
  return <DecisionRow entry={entry} />;
}

function RoundHeader({ entry }: { entry: FeedEntry }) {
  // Extract the "Q1 2020: ..." title
  const colon = entry.text.indexOf(".");
  const title = colon > 0 ? entry.text.slice(0, colon) : entry.text;
  const rest = colon > 0 ? entry.text.slice(colon + 1).trim() : "";

  return (
    <div className="pt-2 pb-1 first:pt-0">
      <div className="flex items-center gap-2">
        <div className="h-px flex-1 bg-border" />
        <span className="text-[10px] font-bold uppercase tracking-wider text-primary shrink-0">
          Round {entry.round}
        </span>
        <div className="h-px flex-1 bg-border" />
      </div>
      <p className="text-[11px] text-muted-foreground mt-0.5 leading-relaxed">
        <span className="font-semibold text-foreground">{title}.</span>{" "}
        {rest}
      </p>
    </div>
  );
}

function SignalRow({ entry }: { entry: FeedEntry }) {
  const color = SIGNAL_COLORS[entry.signalType ?? "information"] ?? "#888";
  const target = entry.recipient ?? "all partners";
  return (
    <div className="flex items-start gap-1.5 text-xs py-0.5 pl-1 border-l-2" style={{ borderColor: color }}>
      <div className="min-w-0 flex-1">
        <span className="font-semibold" style={{ color }}>
          {entry.agentId}
        </span>
        <span className="text-muted-foreground mx-1">{"\u2192"}</span>
        <span className="text-muted-foreground">{target}</span>
        <Badge
          variant="outline"
          className="ml-1.5 text-[9px] px-1 py-0 align-middle"
          style={{ borderColor: color, color }}
        >
          {(entry.signalType ?? "info").replace("_", " ")}
        </Badge>
        <p className="text-muted-foreground mt-0.5 leading-relaxed">
          &ldquo;{entry.text}&rdquo;
        </p>
      </div>
    </div>
  );
}

function ReflectionRow({ entry }: { entry: FeedEntry }) {
  return (
    <div className="flex items-start gap-1.5 text-xs py-0.5 pl-1 border-l-2 border-violet-500/50">
      <div className="min-w-0 flex-1">
        <span className="font-semibold text-violet-400">{entry.agentId}</span>
        <span className="text-violet-400/60 ml-1.5 text-[10px]">thinks</span>
        <p className="text-muted-foreground mt-0.5 italic leading-relaxed">
          {entry.text}
        </p>
      </div>
    </div>
  );
}

function PlanRow({ entry }: { entry: FeedEntry }) {
  return (
    <div
      className={`flex items-start gap-1.5 text-xs py-0.5 pl-1 border-l-2 ${
        entry.invalidated
          ? "border-red-500/50"
          : "border-emerald-500/50"
      }`}
    >
      <div className="min-w-0 flex-1">
        <span
          className={`font-semibold ${
            entry.invalidated ? "text-red-400" : "text-emerald-400"
          }`}
        >
          {entry.agentId}
        </span>
        <span
          className={`ml-1.5 text-[10px] ${
            entry.invalidated ? "text-red-400/60" : "text-emerald-400/60"
          }`}
        >
          {entry.invalidated ? "plan disrupted" : "sets strategy"}
        </span>
        <p className="text-muted-foreground mt-0.5 leading-relaxed">
          {entry.text}
        </p>
      </div>
    </div>
  );
}

function DecisionRow({ entry }: { entry: FeedEntry }) {
  return (
    <div className="flex items-start gap-1.5 text-xs py-0.5 pl-1 border-l-2 border-muted">
      <div className="min-w-0 flex-1">
        <span className="font-semibold text-foreground">{entry.agentId}</span>
        {entry.emotion && (
          <Badge
            variant="outline"
            className="ml-1.5 text-[9px] px-1 py-0 align-middle"
            style={{
              borderColor: EMOTIONAL_COLORS[entry.emotion],
              color: EMOTIONAL_COLORS[entry.emotion],
            }}
          >
            {entry.emotion}
          </Badge>
        )}
        <p className="text-muted-foreground mt-0.5 leading-relaxed">
          {entry.text}
        </p>
      </div>
    </div>
  );
}
