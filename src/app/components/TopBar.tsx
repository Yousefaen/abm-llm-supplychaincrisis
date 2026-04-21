"use client";

import Link from "next/link";
import {
  BarChart3,
  Loader2,
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
}: Props) {
  const isRunning = state.status === "running";
  const isComplete = state.status === "complete";

  // HistoryRound doesn't include per-round metrics yet — fall back to a
  // flat baseline so the sparkline renders calmly. Phase 4 will surface
  // real bullwhip history here; the real chart lives on /analytics.
  const bullwhipSeries = state.history.map(() => 0);
  const currentBullwhip = averageBullwhip(state.metrics?.bullwhip);

  return (
    <div className="flex items-center gap-4 px-4 h-12 border-b border-border bg-card/60 backdrop-blur-sm">
      {/* Brand — serif wordmark */}
      <Link href="/" className="flex items-center gap-2 shrink-0">
        <span className="font-serif text-lg leading-none tracking-tight">
          Supply&nbsp;Chain&nbsp;ABM
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

      {/* Transport controls — RTS-style: step, play/pause, reset */}
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

      {/* Ambient emergence signal: bullwhip sparkline. Silent unless it moves. */}
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span className="font-serif italic">bullwhip</span>
        <Sparkline values={bullwhipSeries} />
        <span className="font-mono text-foreground tabular-nums w-10">
          {currentBullwhip ? currentBullwhip.toFixed(2) : "—"}
        </span>
      </div>

      {/* Right-aligned: status + cost + analytics link */}
      <div className="ml-auto flex items-center gap-3">
        <Badge
          variant="outline"
          className="text-xs font-normal border-border/60"
        >
          {state.status === "error"
            ? "error"
            : isComplete
              ? "complete"
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
