"use client";

import {
  FastForward,
  Loader2,
  Pause,
  Play,
  RotateCcw,
  SkipForward,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import type { SimState } from "../lib/useSimulation";

interface Props {
  state: SimState;
  onStep: () => void;
  onAutoPlay: () => void;
  onPause: () => void;
  onReset: (temperature: number) => void;
}

export default function SimulationControls({
  state,
  onStep,
  onAutoPlay,
  onPause,
  onReset,
}: Props) {
  const isRunning = state.status === "running";
  const isComplete = state.status === "complete";
  const eventTitle = state.currentEvent
    ? state.currentEvent.split(":")[0]
    : "Not started";

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border border-border bg-card p-3">
      {/* Playback controls */}
      <div className="flex items-center gap-1.5">
        <Button
          size="sm"
          variant="outline"
          onClick={() => onReset(state.temperature)}
          title="Reset"
        >
          <RotateCcw className="h-4 w-4" />
        </Button>

        <Button
          size="sm"
          variant="outline"
          onClick={onStep}
          disabled={isRunning || isComplete}
          title="Step one round"
        >
          {isRunning ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <SkipForward className="h-4 w-4" />
          )}
        </Button>

        <Button
          size="sm"
          variant="outline"
          onClick={isRunning ? onPause : onAutoPlay}
          disabled={isComplete}
          title={isRunning ? "Pause" : "Auto-play all rounds"}
        >
          {isRunning ? (
            <Pause className="h-4 w-4" />
          ) : (
            <Play className="h-4 w-4" />
          )}
        </Button>

        <Button
          size="sm"
          variant="outline"
          onClick={onAutoPlay}
          disabled={isRunning || isComplete}
          title="Fast-forward to end"
        >
          <FastForward className="h-4 w-4" />
        </Button>
      </div>

      <Separator orientation="vertical" className="h-6" />

      {/* Round indicator */}
      <div className="flex items-center gap-2 text-sm">
        <span className="font-mono font-semibold">
          Round {state.currentRound}/{state.totalRounds}
        </span>
        <span className="text-muted-foreground">{eventTitle}</span>
      </div>

      <Separator orientation="vertical" className="h-6" />

      {/* Temperature toggle */}
      <div className="flex items-center gap-2 text-sm">
        <span className="text-muted-foreground">Deterministic</span>
        <Switch
          checked={state.temperature === 1.0}
          onCheckedChange={(checked) => onReset(checked ? 1.0 : 0.0)}
        />
        <span className="text-muted-foreground">Exploratory</span>
      </div>

      <Separator orientation="vertical" className="h-6" />

      {/* Status and cost */}
      <div className="flex items-center gap-2">
        <Badge
          variant={
            isComplete
              ? "default"
              : isRunning
                ? "secondary"
                : state.status === "error"
                  ? "destructive"
                  : "outline"
          }
        >
          {state.status === "error"
            ? "Error"
            : isComplete
              ? "Complete"
              : isRunning
                ? state.thinkingAgent
                  ? `${state.thinkingAgent} thinking...`
                  : "Running..."
                : "Ready"}
        </Badge>

        <span className="text-xs text-muted-foreground font-mono">
          ${state.totalCost.toFixed(4)}
        </span>
      </div>

      {state.error && (
        <span className="text-xs text-destructive ml-auto max-w-xs truncate">
          {state.error}
        </span>
      )}
    </div>
  );
}
