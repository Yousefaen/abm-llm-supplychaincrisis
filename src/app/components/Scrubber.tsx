"use client";

import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { HistoryRound } from "../lib/types";

interface Props {
  currentRound: number;
  totalRounds: number;
  history: HistoryRound[];
  // When set, the scrubber is in time-machine mode and shows a preview
  // position that differs from the live current round.
  focusedRound?: number | null;
  onSelectRound?: (round: number | null) => void;
  disabled?: boolean;
}

// Horizontal round timeline across the bottom of the app. Doubles as:
//   - status indicator (where are we now),
//   - time machine (click to scrub back through completed rounds).
//
// Kept visually quiet: a hairline track with small dots, the current
// round marked in terracotta, past rounds in a soft neutral, future
// rounds as hollow. No chrome.
export default function Scrubber({
  currentRound,
  totalRounds,
  history,
  focusedRound,
  onSelectRound,
  disabled = false,
}: Props) {
  const rounds = Array.from({ length: totalRounds }, (_, i) => i + 1);
  const focused = focusedRound ?? currentRound;

  return (
    <div className="flex items-center gap-3 px-4 h-10 border-t border-border bg-card/60 backdrop-blur-sm">
      <span className="text-[11px] uppercase tracking-widest text-muted-foreground font-mono">
        round
      </span>
      <div className="flex items-center gap-1 flex-1">
        {rounds.map((r) => {
          const hist = history.find((h) => h.round === r);
          const isLive = r === currentRound;
          const isFocused = r === focused;
          const isPast = r <= currentRound;
          const interactive = isPast && !disabled && !!onSelectRound;
          const title = hist?.event?.split(":")[0] ?? `Round ${r}`;

          return (
            <Tooltip key={r}>
              <TooltipTrigger
                disabled={!interactive}
                onClick={() =>
                  onSelectRound?.(r === focusedRound ? null : r)
                }
                className={`
                  group relative h-6 flex-1 min-w-[18px] max-w-[64px]
                  flex items-center justify-center
                  ${interactive ? "cursor-pointer" : "cursor-default"}
                `}
              >
                <span
                  className={`
                    block h-1.5 w-full rounded-full transition-all
                    ${
                      isFocused
                        ? "bg-primary"
                        : isLive
                          ? "bg-primary/60"
                          : isPast
                            ? "bg-foreground/25 group-hover:bg-foreground/45"
                            : "bg-foreground/8"
                    }
                  `}
                />
                {isFocused && (
                  <span className="absolute -top-3 text-[10px] font-mono text-primary">
                    {r}
                  </span>
                )}
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs">
                <p className="font-medium">
                  Round {r}
                  {isLive ? " · live" : isPast ? "" : " · not yet"}
                </p>
                {hist?.event && (
                  <p className="text-muted-foreground mt-0.5 text-xs">
                    {title}
                  </p>
                )}
              </TooltipContent>
            </Tooltip>
          );
        })}
      </div>
      {focusedRound && focusedRound !== currentRound && (
        <button
          type="button"
          onClick={() => onSelectRound?.(null)}
          className="text-[11px] text-muted-foreground hover:text-foreground font-mono"
          title="Return to live round (Esc)"
        >
          back to live
        </button>
      )}
    </div>
  );
}
