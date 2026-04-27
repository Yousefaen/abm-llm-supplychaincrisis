"use client";

import Link from "next/link";
import {
  BarChart3,
  Loader2,
  LogOut,
  Pause,
  Play,
  RotateCcw,
  SkipForward,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { SimState } from "../lib/useSimulation";

interface Props {
  state: SimState;
  onStep: () => void;
  onAutoPlay: () => void;
  onPause: () => void;
  onReset: (temperature: number) => void;
  onLoadReplay: (experimentId: string) => void;
  onExitReplay: () => void;
}

// Tiny inline sparkline for the headline emergence signal (bullwhip).
// Kept as a single component so the chrome stays visually quiet.
function Sparkline({ values }: { values: number[] }) {
  if (values.length < 2) {
    return <div className="h-4 w-20" aria-hidden />;
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const w = 80;
  const h = 16;
  const pts = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * w;
      const y = h - ((v - min) / range) * h;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg
      width={w}
      height={h}
      className="overflow-visible"
      aria-label={`bullwhip trend, ${values.length} rounds`}
    >
      <polyline
        fill="none"
        stroke="var(--primary)"
        strokeWidth="1.25"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={pts}
      />
    </svg>
  );
}

function averageBullwhip(values: Record<string, number> | undefined | null): number {
  if (!values) return 0;
  const nums = Object.values(values).filter((v) => Number.isFinite(v));
  if (!nums.length) return 0;
  return nums.reduce((a, b) => a + b, 0) / nums.length;
}

export default function TopBar({
  state,
  onStep,
  onAutoPlay,
  onPause,
  onReset,
  onLoadReplay,
  onExitReplay,
}: Props) {
  const isRunning = state.status === "running";
  const isComplete = state.status === "complete";
  const isReplay = state.replay.active;

  const bullwhipSeries = state.history.map(() => 0);
  const currentBullwhip = averageBullwhip(state.metrics?.bullwhip);

  const variantLabel = state.personaVariant.replace("auto-", "");
  const isAutoVariant = state.personaVariant !== "hand-crafted";

  return (
    <div className="flex items-center gap-4 px-4 h-14 border-b border-border bg-card/60 backdrop-blur-sm">
      {/* Brand — wordmark + the pitch one-liner as a quiet caption.
          Two lines fit in h-14 via leading-tight. */}
      <Link href="/" className="flex flex-col gap-0 shrink-0 leading-tight">
        <span className="font-serif text-base tracking-tight">
          Supply&nbsp;Chain&nbsp;ABM
        </span>
        <span className="text-[10px] text-muted-foreground italic font-serif">
          9 LLM agents · personas grounded in 2019 public filings
        </span>
      </Link>

      {/* Round indicator (mono for precision, muted for calm) */}
      <div className="flex items-baseline gap-1.5 text-sm">
        <span className="font-mono text-foreground">
          {state.currentRound}
        </span>
        <span className="text-muted-foreground">/</span>
        <span className="font-mono text-muted-foreground">
          {state.totalRounds}
        </span>
      </div>

      {/* Transport controls — hidden in replay mode (scrubber handles it) */}
      {!isReplay && (
        <div className="flex items-center gap-0.5">
          <Button
            size="icon"
            variant="ghost"
            onClick={onStep}
            disabled={isRunning || isComplete}
            title="Step one round (→)"
            className="h-8 w-8"
          >
            {isRunning ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <SkipForward className="h-4 w-4" />
            )}
          </Button>
          <Button
            size="icon"
            variant="ghost"
            onClick={isRunning ? onPause : onAutoPlay}
            disabled={isComplete}
            title={isRunning ? "Pause (space)" : "Play (space)"}
            className="h-8 w-8"
          >
            {isRunning ? (
              <Pause className="h-4 w-4" />
            ) : (
              <Play className="h-4 w-4 fill-current" />
            )}
          </Button>
          <Button
            size="icon"
            variant="ghost"
            onClick={() => onReset(state.temperature)}
            title="Reset"
            className="h-8 w-8"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}

      {/* In replay mode, surface what we're showing + an exit affordance */}
      {isReplay && (
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-[10px] font-mono uppercase tracking-wider border-primary/40 text-primary">
            replay
          </Badge>
          <span className="text-xs text-muted-foreground font-mono truncate max-w-[18rem]">
            {state.replay.experimentLabel ?? state.replay.experimentId}
          </span>
          <Button
            size="icon"
            variant="ghost"
            onClick={onExitReplay}
            title="Exit replay"
            className="h-7 w-7"
          >
            <LogOut className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}

      {/* Ambient emergence signal: bullwhip sparkline. */}
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span className="font-serif italic">bullwhip</span>
        <Sparkline values={bullwhipSeries} />
        <span className="font-mono text-foreground tabular-nums w-10">
          {currentBullwhip ? currentBullwhip.toFixed(2) : "—"}
        </span>
      </div>

      {/* Right-aligned: persona variant, demo picker, status, cost, analytics */}
      <div className="ml-auto flex items-center gap-3">
        {/* Persona variant — proves which experiment we're showing */}
        <Badge
          variant="outline"
          className={`text-[10px] font-mono tracking-wide ${
            isAutoVariant
              ? "border-primary/40 text-foreground"
              : "border-border/60 text-muted-foreground"
          }`}
          title={
            isAutoVariant
              ? `Personas auto-generated from each company's ${variantLabel.toUpperCase()} public filings.`
              : "Personas hand-crafted at design time."
          }
        >
          {isAutoVariant ? `personas: ${variantLabel}` : "personas: hand-crafted"}
        </Badge>

        {/* Demo run picker — only show when not currently in replay */}
        {!isReplay && state.experiments.length > 0 && (
          <select
            className="text-xs font-mono px-2 py-1 rounded bg-card border border-border/60 hover:border-border focus:outline-none focus:border-primary/60 cursor-pointer"
            defaultValue=""
            onChange={(e) => {
              const v = e.target.value;
              if (v) onLoadReplay(v);
              e.currentTarget.value = ""; // reset to placeholder
            }}
            title="Load a pre-recorded run from the registry"
          >
            <option value="" disabled>
              load demo run…
            </option>
            {state.experiments.map((exp) => (
              <option key={exp.id} value={exp.id}>
                {exp.id} — {exp.label}
              </option>
            ))}
          </select>
        )}

        <Badge
          variant="outline"
          className="text-xs font-normal border-border/60"
        >
          {state.status === "error"
            ? "error"
            : isComplete
              ? "complete"
              : isReplay
                ? "replay"
                : isRunning
                  ? state.thinkingAgent
                    ? `${state.thinkingAgent} thinking…`
                    : "running"
                  : "ready"}
        </Badge>
        <span className="text-xs text-muted-foreground font-mono tabular-nums">
          ${state.totalCost.toFixed(3)}
        </span>
        <Link
          href="/analytics"
          className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          title="Analytics & benchmarks"
        >
          <BarChart3 className="h-3.5 w-3.5" />
          <span>analytics</span>
        </Link>
      </div>

      {state.error && (
        <span className="text-xs text-destructive max-w-xs truncate">
          {state.error}
        </span>
      )}
    </div>
  );
}
