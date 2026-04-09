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
}

export default function RoundTimeline({
  currentRound,
  totalRounds,
  history,
}: Props) {
  const rounds = Array.from({ length: totalRounds }, (_, i) => i + 1);

  return (
    <div className="flex items-center gap-1.5">
      {rounds.map((r) => {
        const hist = history.find((h) => h.round === r);
        const isCurrent = r === currentRound;
        const isPast = r < currentRound;
        const title = hist?.event?.split(":")[0] ?? `Round ${r}`;

        return (
          <Tooltip key={r}>
            <TooltipTrigger>
              <div className="flex flex-col items-center gap-0.5">
                <div
                  className={`
                    w-8 h-8 rounded-full flex items-center justify-center text-xs font-mono font-semibold
                    transition-all cursor-default
                    ${
                      isCurrent
                        ? "bg-primary text-primary-foreground ring-2 ring-primary ring-offset-2 ring-offset-background"
                        : isPast
                          ? "bg-muted text-foreground"
                          : "bg-muted/40 text-muted-foreground"
                    }
                  `}
                >
                  {r}
                </div>
              </div>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              <p className="font-semibold">{title}</p>
              {hist?.event && (
                <p className="text-muted-foreground mt-1">{hist.event}</p>
              )}
            </TooltipContent>
          </Tooltip>
        );
      })}
    </div>
  );
}
