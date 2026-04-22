"use client";

import { useEffect, useRef } from "react";
import type { ActivityEntry, AgentState, ActivityRole } from "../lib/types";
import { EMOTIONAL_COLORS, TIER_COLORS } from "../lib/types";

interface Props {
  entries: ActivityEntry[];
  agents: Record<string, AgentState>;
  thinkingAgent: string | null;
}

// Short role labels — kept lowercase to match the serif/muted aesthetic
// used elsewhere. "signal" is shorter than "signaling"; "allocate" matches
// the supplier phase language in the backend more directly than "supplier".
const ROLE_LABELS: Record<ActivityRole, string> = {
  planning: "plan",
  signaling: "signal",
  buyer: "order",
  supplier: "allocate",
  reflection: "reflect",
};

// Role colors drawn from the existing palette so the feed reads as part of
// the same document: sage = plan, amber = signal/reflect, dusty blue = order,
// plum = allocate. Keeps the RTS feel calm instead of neon.
const ROLE_COLORS: Record<ActivityRole, string> = {
  planning: "#7A8A5F",
  signaling: "#C2995A",
  buyer: "#547587",
  supplier: "#6F5B7E",
  reflection: "#B6804A",
};

export default function ActivityFeed({
  entries,
  agents,
  thinkingAgent,
}: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  // Auto-scroll to newest unless the user has scrolled up to read older
  // entries. Re-engages follow-mode once they return to the bottom.
  const followRef = useRef(true);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el || !followRef.current) return;
    el.scrollTop = el.scrollHeight;
  }, [entries.length]);

  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    const atBottom =
      el.scrollHeight - el.scrollTop - el.clientHeight < 48;
    followRef.current = atBottom;
  };

  return (
    <div className="flex flex-col h-full border-l border-border bg-card/40 backdrop-blur-sm">
      <div className="px-4 h-10 flex items-center border-b border-border/60 gap-2 shrink-0">
        <span className="font-serif text-sm leading-none">Activity</span>
        <span className="text-[10px] text-muted-foreground font-mono ml-auto tabular-nums">
          {entries.length} events
        </span>
      </div>
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto"
      >
        {entries.length === 0 ? (
          <p className="px-4 py-8 text-xs text-muted-foreground/70 italic text-center font-serif leading-relaxed">
            Press play to watch agents deliberate in real time.
          </p>
        ) : (
          <ul className="flex flex-col divide-y divide-border/40">
            {entries.map((entry) => (
              <ActivityRow
                key={entry.id}
                entry={entry}
                agent={agents[entry.agentId]}
                isThinking={thinkingAgent === entry.agentId}
              />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function ActivityRow({
  entry,
  agent,
  isThinking,
}: {
  entry: ActivityEntry;
  agent: AgentState | undefined;
  isThinking: boolean;
}) {
  const { agentId, tier, role, summary, detail, emotion, round } = entry;
  const displayName = agent?.display_name ?? agentId;
  const tierColor = TIER_COLORS[tier];
  const roleColor = ROLE_COLORS[role] ?? tierColor;
  const emotionColor = emotion ? EMOTIONAL_COLORS[emotion] : undefined;

  return (
    <li
      className={`px-3 py-2 border-l-2 transition-colors ${
        isThinking ? "bg-primary/5" : "hover:bg-muted/20"
      }`}
      style={{ borderColor: roleColor }}
    >
      <div className="flex items-baseline gap-1.5 text-xs min-w-0">
        <span
          className="font-semibold truncate shrink-0"
          style={{ color: tierColor }}
        >
          {displayName}
        </span>
        <span
          className="text-[9px] uppercase tracking-wider font-mono shrink-0"
          style={{ color: roleColor }}
        >
          {ROLE_LABELS[role] ?? role}
        </span>
        {emotion && (
          <span
            className="text-[9px] italic font-serif truncate"
            style={{ color: emotionColor }}
          >
            {emotion}
          </span>
        )}
        <span className="ml-auto text-[9px] text-muted-foreground font-mono tabular-nums shrink-0">
          R{round}
        </span>
      </div>
      <p className="text-[11px] text-foreground/90 leading-snug mt-0.5">
        {summary}
      </p>
      {detail && (
        <p className="text-[10px] text-muted-foreground leading-snug italic font-serif mt-0.5 line-clamp-3">
          {detail}
        </p>
      )}
    </li>
  );
}
