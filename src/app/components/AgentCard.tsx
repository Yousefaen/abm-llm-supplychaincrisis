"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { AgentState, EmotionalState } from "../lib/types";
import { EMOTIONAL_COLORS, TIER_COLORS, TIER_LABELS } from "../lib/types";

interface Props {
  agent: AgentState;
}

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
  const color =
    score >= 7 ? "#22c55e" : score >= 4 ? "#eab308" : "#ef4444";
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

export default function AgentCard({ agent }: Props) {
  const decision = agent.current_decision;
  const isSupplier = !!decision?.allocations;
  const isBuyer = !!decision?.orders;

  return (
    <div className="p-4 space-y-4 h-full overflow-auto">
      {/* Header */}
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

      <Separator />

      {/* Status */}
      <div className="grid grid-cols-3 gap-3 text-center">
        <div>
          <div className="text-2xl font-bold font-mono">{agent.inventory}</div>
          <div className="text-xs text-muted-foreground">Inventory</div>
        </div>
        <div>
          <div className="text-2xl font-bold font-mono">{agent.capacity}</div>
          <div className="text-xs text-muted-foreground">Capacity</div>
        </div>
        <div>
          <div className="text-2xl font-bold font-mono">
            {(agent.fill_rate * 100).toFixed(0)}%
          </div>
          <div className="text-xs text-muted-foreground">Fill Rate</div>
        </div>
      </div>

      {/* Financials */}
      {(agent.revenue > 0 || agent.costs > 0) && (
        <>
          <Separator />
          <div>
            <h3 className="text-sm font-medium mb-2">Financials</h3>
            <div className="grid grid-cols-3 gap-3 text-center">
              <div>
                <div className="text-lg font-bold font-mono text-green-500">
                  ${(agent.revenue / 1000).toFixed(1)}k
                </div>
                <div className="text-xs text-muted-foreground">Revenue</div>
              </div>
              <div>
                <div className="text-lg font-bold font-mono text-red-400">
                  ${(agent.costs / 1000).toFixed(1)}k
                </div>
                <div className="text-xs text-muted-foreground">Costs</div>
              </div>
              <div>
                <div
                  className={`text-lg font-bold font-mono ${agent.profit >= 0 ? "text-green-500" : "text-red-400"}`}
                >
                  {agent.profit >= 0 ? "+" : ""}
                  ${(agent.profit / 1000).toFixed(1)}k
                </div>
                <div className="text-xs text-muted-foreground">Profit</div>
              </div>
            </div>
            {agent.effective_quarterly_need > 0 && (
              <div className="text-xs text-muted-foreground text-center mt-1">
                Quarterly need: {agent.effective_quarterly_need} units
              </div>
            )}
          </div>
        </>
      )}

      {decision?.reasoning && (
        <>
          <Separator />
          <div>
            <h3 className="text-sm font-medium mb-1">Reasoning</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {decision.reasoning}
            </p>
          </div>
        </>
      )}

      {decision?.strategy_shift && (
        <div className="rounded-md bg-muted/50 border border-border p-2 text-sm">
          <span className="font-medium">Strategy Shift: </span>
          {decision.strategy_shift}
        </div>
      )}

      {/* Allocations / Orders */}
      {isSupplier && decision?.allocations && (
        <>
          <Separator />
          <div>
            <h3 className="text-sm font-medium mb-2">
              Allocations (Price: ${decision.price_offered}/unit)
            </h3>
            <div className="space-y-1">
              {Object.entries(decision.allocations).map(([name, units]) => (
                <div
                  key={name}
                  className="flex justify-between text-sm text-muted-foreground"
                >
                  <span>{name}</span>
                  <span className="font-mono">{units} units</span>
                </div>
              ))}
              {(decision.held_in_reserve ?? 0) > 0 && (
                <div className="flex justify-between text-sm text-amber-500">
                  <span>Held in reserve</span>
                  <span className="font-mono">
                    {decision.held_in_reserve} units
                  </span>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {isBuyer && decision?.orders && (
        <>
          <Separator />
          <div>
            <h3 className="text-sm font-medium mb-2">
              Orders (Max price: ${decision.max_price_willing_to_pay}/unit)
            </h3>
            <div className="space-y-1">
              {Object.entries(decision.orders).map(([name, units]) => (
                <div
                  key={name}
                  className="flex justify-between text-sm text-muted-foreground"
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
          </div>
        </>
      )}

      {/* Trust scores */}
      {agent.trust_scores && Object.keys(agent.trust_scores).length > 0 && (
        <>
          <Separator />
          <div>
            <h3 className="text-sm font-medium mb-2">Trust Scores</h3>
            <div className="space-y-1.5">
              {Object.entries(agent.trust_scores).map(([name, score]) => (
                <TrustBar key={name} name={name} score={score} />
              ))}
            </div>
          </div>
        </>
      )}

      {/* Decision history */}
      {agent.decision_history.length > 0 && (
        <>
          <Separator />
          <div>
            <h3 className="text-sm font-medium mb-2">Recent History</h3>
            <div className="space-y-2">
              {agent.decision_history.map((dec, i) => (
                <Card key={i} className="bg-muted/30">
                  <CardContent className="p-2 text-xs space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-medium">
                        Round {agent.decision_history.length - agent.decision_history.length + i + 1}
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
          </div>
        </>
      )}
    </div>
  );
}
