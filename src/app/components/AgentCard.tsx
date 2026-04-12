"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type {
  AgentSignal,
  AgentState,
  EmotionalState,
  MemoryRecord,
  StrategicPlan,
} from "../lib/types";
import { EMOTIONAL_COLORS, TIER_COLORS, TIER_LABELS } from "../lib/types";

// ---------------------------------------------------------------------------
// Collapsible section
// ---------------------------------------------------------------------------

function Section({
  title,
  icon,
  iconColor,
  badge,
  defaultOpen = false,
  children,
}: {
  title: string;
  icon?: React.ReactNode;
  iconColor?: string;
  badge?: React.ReactNode;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center gap-1.5 text-sm font-medium py-1 hover:text-foreground/80 transition-colors"
      >
        {icon ?? (
          iconColor && (
            <span
              className="w-2 h-2 rounded-full shrink-0"
              style={{ backgroundColor: iconColor }}
            />
          )
        )}
        <span>{title}</span>
        {badge}
        <span className="ml-auto text-[10px] text-muted-foreground">
          {open ? "\u25B4" : "\u25BE"}
        </span>
      </button>
      {open && <div className="mt-1">{children}</div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components (unchanged from original, just extracted)
// ---------------------------------------------------------------------------

function EmotionBadge({ emotion }: { emotion: EmotionalState }) {
  return (
    <Badge
      variant="outline"
      className="text-xs"
      style={{
        borderColor: EMOTIONAL_COLORS[emotion] ?? "#888",
        color: EMOTIONAL_COLORS[emotion] ?? "#888",
      }}
    >
      {emotion}
    </Badge>
  );
}

function TrustBar({ name, score }: { name: string; score: number }) {
  const pct = (score / 10) * 100;
  const color = score >= 7 ? "#22c55e" : score >= 4 ? "#eab308" : "#ef4444";
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-28 truncate text-muted-foreground">{name}</span>
      <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <span className="w-6 text-right font-mono">{score}</span>
    </div>
  );
}

const SIGNAL_TYPE_COLORS: Record<string, string> = {
  price_warning: "#f97316",
  loyalty_pledge: "#22c55e",
  threat: "#ef4444",
  information: "#3b82f6",
  request: "#eab308",
};

function SignalEntry({
  signal,
  direction,
}: {
  signal: AgentSignal;
  direction: "sent" | "received";
}) {
  const color = SIGNAL_TYPE_COLORS[signal.signal_type] ?? "#888";
  const arrow = direction === "sent" ? "\u2192" : "\u2190";
  const other =
    direction === "sent" ? signal.recipient ?? "all partners" : signal.sender;
  return (
    <div className="flex gap-2 text-xs py-1">
      <span className="font-mono text-muted-foreground min-w-[14px]">
        {arrow}
      </span>
      <div className="flex-1 min-w-0">
        <span
          className="inline-block text-[10px] font-medium uppercase tracking-wide mr-1"
          style={{ color }}
        >
          {signal.signal_type.replace("_", " ")}
        </span>
        <span className="text-muted-foreground">
          {direction === "sent" ? `To ${other}` : `From ${other}`}:{" "}
          {signal.content}
        </span>
      </div>
    </div>
  );
}

const CATEGORY_COLORS: Record<string, string> = {
  transaction: "#3b82f6",
  market: "#f97316",
  partner_behavior: "#8b5cf6",
  own_decision: "#22c55e",
  consequence: "#eab308",
  reflection: "#a855f7",
};

function MemoryEntry({ memory }: { memory: MemoryRecord }) {
  const color = CATEGORY_COLORS[memory.category] ?? "#888";
  const importanceDots = Math.min(5, Math.ceil(memory.importance / 2));
  return (
    <div className="flex gap-2 text-xs py-1 border-b border-border/30 last:border-0">
      <div className="flex flex-col items-center gap-0.5 pt-0.5 min-w-[36px]">
        <span className="font-mono text-muted-foreground">R{memory.round}</span>
        <div className="flex gap-px">
          {Array.from({ length: importanceDots }).map((_, i) => (
            <div
              key={i}
              className="w-1 h-1 rounded-full"
              style={{ backgroundColor: color }}
            />
          ))}
        </div>
      </div>
      <div className="flex-1 min-w-0">
        <span
          className="inline-block text-[10px] font-medium uppercase tracking-wide mr-1"
          style={{ color }}
        >
          {memory.category.replace("_", " ")}
        </span>
        <span className="text-muted-foreground leading-relaxed">
          {memory.description.length > 150
            ? memory.description.slice(0, 150) + "..."
            : memory.description}
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main AgentCard
// ---------------------------------------------------------------------------

interface Props {
  agent: AgentState;
}

export default function AgentCard({ agent }: Props) {
  const decision = agent.current_decision;
  const isSupplier = !!decision?.allocations;
  const isBuyer = !!decision?.orders;

  const hasSignals =
    (agent.signals_sent && agent.signals_sent.length > 0) ||
    (agent.signals_received && agent.signals_received.length > 0);
  const hasReflections = agent.reflections && agent.reflections.length > 0;
  const hasMemories = agent.memories && agent.memories.length > 0;

  return (
    <div className="p-3 space-y-3 h-full overflow-auto">
      {/* ===== ALWAYS VISIBLE: Header ===== */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: TIER_COLORS[agent.tier] }}
          />
          <h2 className="text-lg font-semibold">{agent.display_name}</h2>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-xs">
            {TIER_LABELS[agent.tier]}
          </Badge>
          <EmotionBadge emotion={agent.emotional_state} />
        </div>
      </div>

      {/* ===== ALWAYS VISIBLE: Status row ===== */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div>
          <div className="text-xl font-bold font-mono">{agent.inventory}</div>
          <div className="text-[10px] text-muted-foreground">Inventory</div>
        </div>
        <div>
          <div className="text-xl font-bold font-mono">{agent.capacity}</div>
          <div className="text-[10px] text-muted-foreground">Capacity</div>
        </div>
        <div>
          <div className="text-xl font-bold font-mono">
            {(agent.fill_rate * 100).toFixed(0)}%
          </div>
          <div className="text-[10px] text-muted-foreground">Fill Rate</div>
        </div>
      </div>

      {/* ===== ALWAYS VISIBLE: Financials compact row ===== */}
      {(agent.revenue > 0 || agent.costs > 0) && (
        <div className="flex items-center justify-between text-xs px-1">
          <span className="text-green-500 font-mono">
            +${(agent.revenue / 1000).toFixed(1)}k
          </span>
          <span className="text-red-400 font-mono">
            -${(agent.costs / 1000).toFixed(1)}k
          </span>
          <span
            className={`font-bold font-mono ${agent.profit >= 0 ? "text-green-500" : "text-red-400"}`}
          >
            = {agent.profit >= 0 ? "+" : ""}${(agent.profit / 1000).toFixed(1)}k
          </span>
        </div>
      )}

      {/* ===== ALWAYS VISIBLE: Current reasoning ===== */}
      {decision?.reasoning && (
        <div className="rounded-md bg-muted/30 p-2">
          <p className="text-xs text-muted-foreground leading-relaxed">
            {decision.reasoning}
          </p>
          {decision.strategy_shift && (
            <p className="text-xs text-amber-500 mt-1 font-medium">
              Strategy shift: {decision.strategy_shift}
            </p>
          )}
        </div>
      )}

      <Separator />

      {/* ===== EXPANDED BY DEFAULT: Strategic Insights ===== */}
      {hasReflections && (
        <Section
          title="Strategic Insights"
          iconColor="#8b5cf6"
          defaultOpen={true}
        >
          <div className="space-y-1.5">
            {agent.reflections!.map((insight, i) => (
              <div
                key={i}
                className="rounded-md bg-violet-500/10 border border-violet-500/20 p-2 text-xs text-muted-foreground italic leading-relaxed"
              >
                {insight}
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* ===== EXPANDED BY DEFAULT: Communications ===== */}
      {hasSignals && (
        <Section
          title="Communications"
          iconColor="#06b6d4"
          badge={
            <span className="text-[10px] text-muted-foreground font-normal ml-1">
              ({(agent.signals_sent?.length ?? 0) + (agent.signals_received?.length ?? 0)})
            </span>
          }
          defaultOpen={true}
        >
          <div className="space-y-1">
            {agent.signals_sent?.map((sig: AgentSignal, i: number) => (
              <SignalEntry key={`sent-${i}`} signal={sig} direction="sent" />
            ))}
            {agent.signals_received?.map((sig: AgentSignal, i: number) => (
              <SignalEntry key={`recv-${i}`} signal={sig} direction="received" />
            ))}
          </div>
        </Section>
      )}

      {/* ===== COLLAPSED BY DEFAULT: Strategic Plan ===== */}
      {agent.current_plan && (
        <Section
          title="Strategic Plan"
          iconColor="#10b981"
          badge={
            agent.current_plan.invalidated ? (
              <Badge variant="destructive" className="text-[9px] px-1 py-0 ml-1">
                INVALIDATED
              </Badge>
            ) : undefined
          }
          defaultOpen={false}
        >
          <PlanContent plan={agent.current_plan} />
        </Section>
      )}

      {/* ===== COLLAPSED BY DEFAULT: Allocations / Orders ===== */}
      {isSupplier && decision?.allocations && (
        <Section
          title={`Allocations ($${decision.price_offered}/unit)`}
          iconColor="#22c55e"
          defaultOpen={false}
        >
          <div className="space-y-1">
            {Object.entries(decision.allocations).map(([name, units]) => (
              <div
                key={name}
                className="flex justify-between text-xs text-muted-foreground"
              >
                <span>{name}</span>
                <span className="font-mono">{units} units</span>
              </div>
            ))}
            {(decision.held_in_reserve ?? 0) > 0 && (
              <div className="flex justify-between text-xs text-amber-500">
                <span>Held in reserve</span>
                <span className="font-mono">{decision.held_in_reserve} units</span>
              </div>
            )}
          </div>
        </Section>
      )}

      {isBuyer && decision?.orders && (
        <Section
          title={`Orders (max $${decision.max_price_willing_to_pay}/unit)`}
          iconColor="#3b82f6"
          defaultOpen={false}
        >
          <div className="space-y-1">
            {Object.entries(decision.orders).map(([name, units]) => (
              <div
                key={name}
                className="flex justify-between text-xs text-muted-foreground"
              >
                <span>{name}</span>
                <span className="font-mono">{units} units</span>
              </div>
            ))}
            {decision.will_seek_alternatives && (
              <div className="text-xs text-amber-500 mt-1">
                Seeking alternative suppliers
              </div>
            )}
          </div>
        </Section>
      )}

      {/* ===== COLLAPSED BY DEFAULT: Trust Scores ===== */}
      {agent.trust_scores && Object.keys(agent.trust_scores).length > 0 && (
        <Section title="Trust Scores" iconColor="#eab308" defaultOpen={false}>
          <div className="space-y-1.5">
            {Object.entries(agent.trust_scores).map(([name, score]) => (
              <TrustBar key={name} name={name} score={score} />
            ))}
          </div>
        </Section>
      )}

      {/* ===== COLLAPSED BY DEFAULT: Memory Stream ===== */}
      {hasMemories && (
        <Section
          title="Memory Stream"
          iconColor="#3b82f6"
          badge={
            agent.memory_count != null ? (
              <span className="text-[10px] text-muted-foreground font-normal ml-1">
                ({agent.memory_count} total)
              </span>
            ) : undefined
          }
          defaultOpen={false}
        >
          <div className="space-y-1">
            {agent.memories!.map((mem: MemoryRecord, i: number) => (
              <MemoryEntry key={i} memory={mem} />
            ))}
          </div>
        </Section>
      )}

      {/* ===== COLLAPSED BY DEFAULT: Decision History ===== */}
      {agent.decision_history.length > 0 && (
        <Section title="Recent History" defaultOpen={false}>
          <div className="space-y-2">
            {agent.decision_history.map((dec, i) => (
              <Card key={i} className="bg-muted/30">
                <CardContent className="p-2 text-xs space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-medium">
                      Round {i + 1}
                    </span>
                    {dec.emotional_state && (
                      <EmotionBadge
                        emotion={dec.emotional_state as EmotionalState}
                      />
                    )}
                  </div>
                  <p className="text-muted-foreground">{dec.reasoning}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Plan content (extracted for Section use)
// ---------------------------------------------------------------------------

function PlanContent({ plan }: { plan: StrategicPlan }) {
  return (
    <div className={`space-y-1.5 ${plan.invalidated ? "opacity-60" : ""}`}>
      <div className="text-[10px] text-muted-foreground">
        Created R{plan.created_round}, {plan.horizon}Q horizon
      </div>
      {plan.goals.map((goal, i) => (
        <div key={i} className="flex gap-2 text-xs">
          <span className="text-emerald-500 font-medium min-w-[16px]">
            {i + 1}.
          </span>
          <span className="text-muted-foreground">{goal}</span>
        </div>
      ))}
      {Object.keys(plan.tactics).length > 0 && (
        <div className="mt-1 pt-1 border-t border-border/30">
          {Object.entries(plan.tactics).map(([partner, tactic]) => (
            <div key={partner} className="flex gap-2 text-xs py-0.5">
              <span className="text-blue-400 font-mono min-w-[90px] truncate">
                {partner}
              </span>
              <span className="text-muted-foreground">{tactic}</span>
            </div>
          ))}
        </div>
      )}
      <div className="text-xs text-amber-500/80 mt-1">
        Risk: {plan.risk_assessment}
      </div>
    </div>
  );
}
