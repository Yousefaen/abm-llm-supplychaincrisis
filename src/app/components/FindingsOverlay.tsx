"use client";

import { useMemo, useState } from "react";
import { ChevronDown, ChevronUp, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ExperimentRunRound } from "../lib/types";
import type { SimState } from "../lib/useSimulation";

interface Props {
  state: SimState;
}

// Crisis-vocabulary detector — same word list as backend _eval_report.py
// so the overlay numbers match what's in the registered report.md.
const CRISIS_RE = new RegExp(
  [
    "\\bcris[ei]s\\b",
    "\\bshortage\\b",
    "\\bshock\\b",
    "\\bemergency\\b",
    "\\bunprecedented\\b",
    "\\bscarcit(?:y|ies)\\b",
    "\\bpanic\\b",
    "\\bhoard",
    "\\bbottleneck\\b",
    "\\bconstraint\\b",
    "\\bdisrupt",
  ].join("|"),
  "i",
);

const CRISIS_STRICT_RE = /\b(cris[ei]s|shortage|shock|emergency)\b/i;

const OEMS = ["ToyotaMotors", "FordAuto", "VolkswagenAG"];

interface RoundFindings {
  vocabHits: number;
  vocabTotal: number;
  panicCount: number;
  panicTotal: number;
  bullwhipSigma: number;
}

interface RunFindings {
  firstCrisisRound: number | null;
  firstCrisisAgent: string | null;
  firstCrisisText: string | null;
}

function computeRoundFindings(round: ExperimentRunRound): RoundFindings {
  const texts: string[] = [];
  for (const evt of round.events ?? []) {
    const dec = evt.decision ?? {};
    if ((dec as { reasoning?: string }).reasoning) {
      texts.push((dec as { reasoning: string }).reasoning);
    }
    const insights = (dec as { insights?: string[] }).insights ?? [];
    for (const ins of insights) texts.push(String(ins));
    const signals = (dec as { signals?: { content?: string }[] }).signals ?? [];
    for (const sig of signals) {
      if (sig?.content) texts.push(sig.content);
    }
    const plan = (dec as { plan?: { goals?: string[]; tactics?: unknown[]; risk_assessment?: string } }).plan;
    if (plan) {
      for (const g of plan.goals ?? []) texts.push(String(g));
      for (const t of plan.tactics ?? []) texts.push(String(t));
      if (plan.risk_assessment) texts.push(String(plan.risk_assessment));
    }
  }
  const vocabHits = texts.filter((t) => CRISIS_RE.test(t)).length;

  // Panic fraction from the round's agent snapshot
  const agentList = Object.values(round.agents);
  const panicCount = agentList.filter(
    (a) => a.emotional_state === "panicked" || a.emotional_state === "anxious",
  ).length;

  // Bullwhip σ: stdev of OEM order totals from the buyer events
  const oemOrders: Record<string, number> = {};
  for (const evt of round.events ?? []) {
    if (evt.role === "buyer" && OEMS.includes(evt.agent_id)) {
      const orders = (evt.decision as { orders?: Record<string, number> }).orders ?? {};
      oemOrders[evt.agent_id] = Object.values(orders).reduce(
        (s, v) => s + (Number(v) || 0),
        0,
      );
    }
  }
  const oemTotals = OEMS.map((a) => oemOrders[a] ?? 0);
  const mean = oemTotals.reduce((s, v) => s + v, 0) / oemTotals.length;
  const variance =
    oemTotals.reduce((s, v) => s + (v - mean) ** 2, 0) / oemTotals.length;

  return {
    vocabHits,
    vocabTotal: texts.length,
    panicCount,
    panicTotal: agentList.length,
    bullwhipSigma: Math.sqrt(variance),
  };
}

function computeRunFindings(perRound: ExperimentRunRound[]): RunFindings {
  for (const r of perRound) {
    for (const evt of r.events ?? []) {
      const dec = evt.decision ?? {};
      const reasoning = (dec as { reasoning?: string }).reasoning;
      if (reasoning && CRISIS_STRICT_RE.test(reasoning)) {
        return {
          firstCrisisRound: r.round,
          firstCrisisAgent: evt.agent_id,
          firstCrisisText: reasoning.slice(0, 160),
        };
      }
      const insights = (dec as { insights?: string[] }).insights ?? [];
      for (const ins of insights) {
        if (CRISIS_STRICT_RE.test(String(ins))) {
          return {
            firstCrisisRound: r.round,
            firstCrisisAgent: evt.agent_id,
            firstCrisisText: String(ins).slice(0, 160),
          };
        }
      }
      const signals = (dec as { signals?: { content?: string }[] }).signals ?? [];
      for (const sig of signals) {
        if (sig?.content && CRISIS_STRICT_RE.test(sig.content)) {
          return {
            firstCrisisRound: r.round,
            firstCrisisAgent: evt.agent_id,
            firstCrisisText: sig.content.slice(0, 160),
          };
        }
      }
    }
  }
  return { firstCrisisRound: null, firstCrisisAgent: null, firstCrisisText: null };
}

// Compact stat readout for the overlay header.
function Stat({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[9px] uppercase tracking-widest text-muted-foreground font-mono">
        {label}
      </span>
      <span
        className="text-base font-mono tabular-nums text-foreground leading-none"
        title={hint}
      >
        {value}
      </span>
    </div>
  );
}

export default function FindingsOverlay({ state }: Props) {
  const [collapsed, setCollapsed] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  const perRound = state.replay.perRound;

  const roundFindings: RoundFindings | null = useMemo(() => {
    if (!perRound.length || state.currentRound < 1) return null;
    const r = perRound[state.currentRound - 1];
    if (!r) return null;
    return computeRoundFindings(r);
  }, [perRound, state.currentRound]);

  const runFindings: RunFindings = useMemo(
    () => computeRunFindings(perRound),
    [perRound],
  );

  if (!state.replay.active || dismissed || !roundFindings) {
    return null;
  }

  const vocabPct =
    roundFindings.vocabTotal > 0
      ? Math.round((100 * roundFindings.vocabHits) / roundFindings.vocabTotal)
      : 0;

  return (
    <div className="absolute top-4 right-4 z-30 max-w-sm bg-background/95 backdrop-blur-sm border border-border rounded-md shadow-sm">
      {/* Header strip */}
      <div className="flex items-center gap-2 px-3 py-1.5 border-b border-border/60">
        <span className="text-[10px] uppercase tracking-widest font-mono text-muted-foreground">
          Findings · R{state.currentRound}
        </span>
        <span className="ml-auto flex items-center gap-0.5">
          <Button
            variant="ghost"
            size="icon"
            className="h-5 w-5"
            onClick={() => setCollapsed((c) => !c)}
            title={collapsed ? "Expand" : "Collapse"}
          >
            {collapsed ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronUp className="h-3 w-3" />
            )}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-5 w-5"
            onClick={() => setDismissed(true)}
            title="Dismiss"
          >
            <X className="h-3 w-3" />
          </Button>
        </span>
      </div>

      {!collapsed && (
        <div className="px-3 py-3 space-y-3">
          {/* Per-round metrics */}
          <div className="grid grid-cols-3 gap-3">
            <Stat
              label="crisis vocab"
              value={`${vocabPct}%`}
              hint={`${roundFindings.vocabHits} hits across ${roundFindings.vocabTotal} LLM-generated texts this round`}
            />
            <Stat
              label="panic"
              value={`${roundFindings.panicCount}/${roundFindings.panicTotal}`}
              hint="agents in panicked or anxious emotional state"
            />
            <Stat
              label="OEM σ"
              value={roundFindings.bullwhipSigma.toFixed(0)}
              hint="stdev of OEM order totals — bullwhip indicator"
            />
          </div>

          {/* Run-level finding */}
          {runFindings.firstCrisisRound !== null && (
            <div className="text-[11px] text-muted-foreground border-t border-border/40 pt-2 leading-snug">
              <div className="font-mono uppercase tracking-widest text-[9px] mb-1">
                first crisis utterance
              </div>
              <span className="font-mono">R{runFindings.firstCrisisRound}</span>
              {runFindings.firstCrisisAgent && (
                <span className="font-mono">
                  {" "}· {runFindings.firstCrisisAgent}
                </span>
              )}
              {runFindings.firstCrisisText && (
                <p className="font-serif italic mt-1 text-foreground/80 line-clamp-3">
                  &ldquo;{runFindings.firstCrisisText}&rdquo;
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
