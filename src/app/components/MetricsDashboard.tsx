"use client";

import { useMemo } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Badge } from "@/components/ui/badge";
import type { AgentState, EmotionalState, HistoryRound, Tier } from "../lib/types";
import {
  AGENT_IDS,
  EMOTIONAL_COLORS,
  TIER_COLORS,
  TIER_LABELS,
} from "../lib/types";

interface Props {
  history: HistoryRound[];
  agents: Record<string, AgentState>;
}

const AGENT_LINE_COLORS: Record<string, string> = {
  TaiwanSemi: "#8b5cf6",
  KoreaSilicon: "#a78bfa",
  EuroChip: "#3b82f6",
  AmeriSemi: "#60a5fa",
  BoschAuto: "#22c55e",
  ContiParts: "#4ade80",
  ToyotaMotors: "#f97316",
  FordAuto: "#fb923c",
  VolkswagenAG: "#fdba74",
};

export default function MetricsDashboard({ history, agents }: Props) {
  // --- Fill Rate data ---
  const fillRateData = useMemo(() => {
    return history.map((round) => {
      const entry: Record<string, number | string> = { round: `R${round.round}` };
      for (const id of AGENT_IDS) {
        entry[id] = round.agents[id]?.fill_rate ?? 1;
      }
      return entry;
    });
  }, [history]);

  // --- Hoarding Index data ---
  const hoardingData = useMemo(() => {
    return history.map((round) => {
      const entry: Record<string, number | string> = { round: `R${round.round}` };
      for (const id of AGENT_IDS) {
        const dec = round.agents[id]?.decision;
        entry[id] = dec?.held_in_reserve ?? 0;
      }
      return entry;
    });
  }, [history]);

  // --- Price Index data ---
  const priceData = useMemo(() => {
    return history.map((round) => {
      const entry: Record<string, number | string> = { round: `R${round.round}` };
      const tierPrices: Record<string, number[]> = {
        foundry: [],
        chipDesigner: [],
        tier1Supplier: [],
      };
      for (const [aid, data] of Object.entries(round.agents)) {
        const tier = agents[aid]?.tier;
        if (tier && tierPrices[tier]) {
          tierPrices[tier].push(data.current_price ?? 0);
        }
      }
      for (const [tier, prices] of Object.entries(tierPrices)) {
        entry[tier] =
          prices.length > 0
            ? Math.round((prices.reduce((a, b) => a + b, 0) / prices.length) * 100) / 100
            : 0;
      }
      return entry;
    });
  }, [history, agents]);

  // --- Emotional Timeline data ---
  const emotionalData = useMemo(() => {
    return history.map((round) => {
      const entry: Record<string, string | number> = { round: `R${round.round}` };
      for (const id of AGENT_IDS) {
        entry[id] = round.agents[id]?.emotional_state ?? "confident";
      }
      return entry;
    });
  }, [history]);

  // --- Profit data ---
  const profitData = useMemo(() => {
    return history.map((round) => {
      const entry: Record<string, number | string> = { round: `R${round.round}` };
      for (const id of AGENT_IDS) {
        const agentData = agents[id];
        if (agentData) {
          entry[id] = agentData.profit ?? 0;
        }
      }
      return entry;
    });
  }, [history, agents]);

  // --- Financial scorecard (current snapshot) ---
  const scorecardData = useMemo(() => {
    return AGENT_IDS
      .filter((id) => agents[id])
      .map((id) => ({
        name: id,
        tier: agents[id].tier,
        revenue: agents[id].revenue ?? 0,
        costs: agents[id].costs ?? 0,
        profit: agents[id].profit ?? 0,
        inventory: agents[id].inventory,
        fillRate: agents[id].fill_rate,
      }))
      .sort((a, b) => b.profit - a.profit);
  }, [agents]);

  // --- Bullwhip data ---
  const bullwhipData = useMemo(() => {
    if (history.length < 2) return [];
    const tiers: { name: string; agents: string[] }[] = [
      { name: "OEM", agents: ["ToyotaMotors", "FordAuto", "VolkswagenAG"] },
      { name: "Tier-1", agents: ["BoschAuto", "ContiParts"] },
      { name: "Chip Designer", agents: ["EuroChip", "AmeriSemi"] },
    ];

    return tiers.map(({ name, agents: tierAgents }) => {
      const orderSeries: number[] = history.map((round) => {
        let total = 0;
        for (const aid of tierAgents) {
          const dec = round.agents[aid]?.decision;
          if (dec?.orders) {
            total += Object.values(dec.orders).reduce(
              (a: number, b: unknown) => a + Number(b),
              0
            );
          }
        }
        return total;
      });
      const mean = orderSeries.reduce((a, b) => a + b, 0) / Math.max(orderSeries.length, 1);
      const variance =
        orderSeries.reduce((a, b) => a + (b - mean) ** 2, 0) /
        Math.max(orderSeries.length, 1);
      return { tier: name, variance: Math.round(variance) };
    });
  }, [history]);

  if (history.length === 0) {
    return (
      <div className="flex items-center justify-center h-full p-6 text-muted-foreground text-sm">
        Run at least one round to see metrics
      </div>
    );
  }

  return (
    <Tabs defaultValue="fillRate" className="h-full flex flex-col">
      <TabsList className="mx-3 mt-2 shrink-0">
        <TabsTrigger value="fillRate" className="text-xs">
          Fill Rate
        </TabsTrigger>
        <TabsTrigger value="hoarding" className="text-xs">
          Hoarding
        </TabsTrigger>
        <TabsTrigger value="price" className="text-xs">
          Price
        </TabsTrigger>
        <TabsTrigger value="trust" className="text-xs">
          Trust
        </TabsTrigger>
        <TabsTrigger value="emotions" className="text-xs">
          Emotions
        </TabsTrigger>
        <TabsTrigger value="bullwhip" className="text-xs">
          Bullwhip
        </TabsTrigger>
        <TabsTrigger value="scorecard" className="text-xs">
          Scorecard
        </TabsTrigger>
        <TabsTrigger value="minds" className="text-xs">
          Minds
        </TabsTrigger>
      </TabsList>

      {/* Fill Rate */}
      <TabsContent value="fillRate" className="flex-1 p-3 pt-1">
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={fillRateData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="round" tick={{ fontSize: 10 }} stroke="#888" />
            <YAxis domain={[0, 1.1]} tick={{ fontSize: 10 }} stroke="#888" />
            <Tooltip
              contentStyle={{ backgroundColor: "#1a1a2e", border: "1px solid #333", fontSize: 11 }}
            />
            <Legend wrapperStyle={{ fontSize: 10 }} />
            {AGENT_IDS.map((id) => (
              <Line
                key={id}
                type="monotone"
                dataKey={id}
                stroke={AGENT_LINE_COLORS[id]}
                strokeWidth={1.5}
                dot={{ r: 2 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </TabsContent>

      {/* Hoarding */}
      <TabsContent value="hoarding" className="flex-1 p-3 pt-1">
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={hoardingData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="round" tick={{ fontSize: 10 }} stroke="#888" />
            <YAxis tick={{ fontSize: 10 }} stroke="#888" />
            <Tooltip
              contentStyle={{ backgroundColor: "#1a1a2e", border: "1px solid #333", fontSize: 11 }}
            />
            <Legend wrapperStyle={{ fontSize: 10 }} />
            {AGENT_IDS.map((id) => (
              <Area
                key={id}
                type="monotone"
                dataKey={id}
                stackId="1"
                stroke={AGENT_LINE_COLORS[id]}
                fill={AGENT_LINE_COLORS[id]}
                fillOpacity={0.5}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </TabsContent>

      {/* Price Index */}
      <TabsContent value="price" className="flex-1 p-3 pt-1">
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={priceData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="round" tick={{ fontSize: 10 }} stroke="#888" />
            <YAxis tick={{ fontSize: 10 }} stroke="#888" />
            <Tooltip
              contentStyle={{ backgroundColor: "#1a1a2e", border: "1px solid #333", fontSize: 11 }}
            />
            <Legend wrapperStyle={{ fontSize: 10 }} />
            {(["foundry", "chipDesigner", "tier1Supplier"] as Tier[]).map(
              (tier) => (
                <Line
                  key={tier}
                  type="monotone"
                  dataKey={tier}
                  name={TIER_LABELS[tier]}
                  stroke={TIER_COLORS[tier]}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              )
            )}
          </LineChart>
        </ResponsiveContainer>
      </TabsContent>

      {/* Trust Heatmap */}
      <TabsContent value="trust" className="flex-1 p-3 pt-1 overflow-auto">
        <TrustHeatmap agents={agents} />
      </TabsContent>

      {/* Emotional Timeline */}
      <TabsContent value="emotions" className="flex-1 p-3 pt-1 overflow-auto">
        <EmotionalTimeline data={emotionalData} />
      </TabsContent>

      {/* Bullwhip */}
      <TabsContent value="bullwhip" className="flex-1 p-3 pt-1">
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={bullwhipData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="tier" tick={{ fontSize: 10 }} stroke="#888" />
            <YAxis tick={{ fontSize: 10 }} stroke="#888" />
            <Tooltip
              contentStyle={{ backgroundColor: "#1a1a2e", border: "1px solid #333", fontSize: 11 }}
            />
            <Bar dataKey="variance" fill="#8b5cf6" name="Order Variance" />
          </BarChart>
        </ResponsiveContainer>
      </TabsContent>

      {/* Financial Scorecard */}
      <TabsContent value="scorecard" className="flex-1 p-3 pt-1 overflow-auto">
        <FinancialScorecard data={scorecardData} />
      </TabsContent>

      {/* Agent Minds */}
      <TabsContent value="minds" className="flex-1 p-3 pt-1 overflow-auto">
        <AgentMinds agents={agents} />
      </TabsContent>
    </Tabs>
  );
}

// --- Trust Heatmap sub-component ---
function TrustHeatmap({ agents }: { agents: Record<string, AgentState> }) {
  const agentIds = AGENT_IDS.filter((id) => agents[id]);

  if (agentIds.length === 0) {
    return <div className="text-xs text-muted-foreground">No data</div>;
  }

  return (
    <div className="overflow-auto">
      <table className="text-xs border-collapse">
        <thead>
          <tr>
            <th className="p-1" />
            {agentIds.map((id) => (
              <th
                key={id}
                className="p-1 font-normal text-muted-foreground -rotate-45 origin-left whitespace-nowrap"
              >
                {id}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {agentIds.map((rowId) => (
            <tr key={rowId}>
              <td className="p-1 font-medium whitespace-nowrap pr-2">
                {rowId}
              </td>
              {agentIds.map((colId) => {
                const score = agents[rowId]?.trust_scores?.[colId];
                if (score === undefined) {
                  return (
                    <td key={colId} className="p-1">
                      <div className="w-6 h-6 rounded bg-muted/20" />
                    </td>
                  );
                }
                const intensity = score / 10;
                const r = Math.round(239 * (1 - intensity) + 34 * intensity);
                const g = Math.round(68 * (1 - intensity) + 197 * intensity);
                const b = Math.round(68 * (1 - intensity) + 94 * intensity);
                return (
                  <td key={colId} className="p-0.5">
                    <div
                      className="w-6 h-6 rounded flex items-center justify-center text-[9px] font-mono"
                      style={{ backgroundColor: `rgb(${r},${g},${b})` }}
                      title={`${rowId} → ${colId}: ${score}`}
                    >
                      {score}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// --- Emotional Timeline sub-component ---
function EmotionalTimeline({
  data,
}: {
  data: Record<string, string | number>[];
}) {
  if (data.length === 0) return null;

  return (
    <div className="overflow-auto">
      <div className="grid gap-1" style={{ gridTemplateColumns: `120px repeat(${data.length}, 1fr)` }}>
        {/* Header row */}
        <div className="text-xs text-muted-foreground" />
        {data.map((d) => (
          <div
            key={String(d.round)}
            className="text-[10px] text-muted-foreground text-center"
          >
            {d.round}
          </div>
        ))}

        {/* Agent rows */}
        {AGENT_IDS.map((id) => (
          <>
            <div key={`${id}-label`} className="text-xs font-medium truncate pr-2">
              {id}
            </div>
            {data.map((d, i) => {
              const emotion = (d[id] as EmotionalState) ?? "confident";
              return (
                <div
                  key={`${id}-${i}`}
                  className="h-5 rounded-sm"
                  style={{
                    backgroundColor: EMOTIONAL_COLORS[emotion] ?? "#888",
                    opacity: 0.8,
                  }}
                  title={`${id} R${d.round}: ${emotion}`}
                />
              );
            })}
          </>
        ))}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-2 mt-2">
        {(Object.entries(EMOTIONAL_COLORS) as [EmotionalState, string][]).map(
          ([emotion, color]) => (
            <div key={emotion} className="flex items-center gap-1 text-[10px]">
              <div
                className="w-2.5 h-2.5 rounded-sm"
                style={{ backgroundColor: color }}
              />
              {emotion}
            </div>
          )
        )}
      </div>
    </div>
  );
}

// --- Financial Scorecard sub-component ---
function FinancialScorecard({
  data,
}: {
  data: {
    name: string;
    tier: string;
    revenue: number;
    costs: number;
    profit: number;
    inventory: number;
    fillRate: number;
  }[];
}) {
  if (data.length === 0) {
    return <div className="text-xs text-muted-foreground">No data</div>;
  }

  const fmt = (n: number) => {
    if (Math.abs(n) >= 1000) return `${(n / 1000).toFixed(1)}k`;
    return n.toFixed(0);
  };

  return (
    <div className="overflow-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="text-muted-foreground">
            <th className="text-left p-1 font-medium">Agent</th>
            <th className="text-left p-1 font-medium">Tier</th>
            <th className="text-right p-1 font-medium">Revenue</th>
            <th className="text-right p-1 font-medium">Costs</th>
            <th className="text-right p-1 font-medium">Profit</th>
            <th className="text-right p-1 font-medium">Inv</th>
            <th className="text-right p-1 font-medium">Fill%</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr
              key={row.name}
              className={i === 0 ? "bg-green-500/10" : ""}
            >
              <td className="p-1 font-medium whitespace-nowrap">
                {i === 0 && <span className="mr-1">&#9733;</span>}
                {row.name}
              </td>
              <td className="p-1 text-muted-foreground">
                {TIER_LABELS[row.tier as Tier] ?? row.tier}
              </td>
              <td className="p-1 text-right font-mono text-green-500">
                ${fmt(row.revenue)}
              </td>
              <td className="p-1 text-right font-mono text-red-400">
                ${fmt(row.costs)}
              </td>
              <td
                className={`p-1 text-right font-mono font-semibold ${
                  row.profit >= 0 ? "text-green-500" : "text-red-400"
                }`}
              >
                {row.profit >= 0 ? "+" : ""}${fmt(row.profit)}
              </td>
              <td className="p-1 text-right font-mono">{row.inventory}</td>
              <td className="p-1 text-right font-mono">
                {(row.fillRate * 100).toFixed(0)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// --- Agent Minds sub-component ---
function AgentMinds({ agents }: { agents: Record<string, AgentState> }) {
  const agentList = AGENT_IDS.filter((id) => agents[id]);

  if (agentList.length === 0) {
    return <div className="text-xs text-muted-foreground">No data</div>;
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
      {agentList.map((id) => {
        const agent = agents[id];
        const reflections = agent.reflections ?? [];
        const plan = agent.current_plan;
        const hasContent = reflections.length > 0 || plan;

        return (
          <div
            key={id}
            className="rounded-md border border-border/50 bg-muted/20 p-2 space-y-1.5"
          >
            {/* Header */}
            <div className="flex items-center gap-1.5">
              <div
                className="w-2 h-2 rounded-full shrink-0"
                style={{
                  backgroundColor: TIER_COLORS[agent.tier] ?? "#888",
                }}
              />
              <span className="text-xs font-semibold truncate">{id}</span>
              <Badge
                variant="outline"
                className="ml-auto text-[9px] px-1 py-0 shrink-0"
                style={{
                  borderColor:
                    EMOTIONAL_COLORS[agent.emotional_state] ?? "#888",
                  color: EMOTIONAL_COLORS[agent.emotional_state] ?? "#888",
                }}
              >
                {agent.emotional_state}
              </Badge>
            </div>

            {/* Plan summary (one line) */}
            {plan && (
              <div className="text-[10px] text-emerald-400/80 truncate">
                {plan.invalidated ? "Plan invalidated" : plan.goals[0] ?? ""}
              </div>
            )}

            {/* Reflections */}
            {reflections.length > 0 ? (
              <div className="space-y-1">
                {reflections.slice(0, 3).map((r, i) => (
                  <p
                    key={i}
                    className="text-[10px] text-muted-foreground italic leading-snug"
                  >
                    {r.length > 120 ? r.slice(0, 120) + "..." : r}
                  </p>
                ))}
              </div>
            ) : (
              !hasContent && (
                <p className="text-[10px] text-muted-foreground/50">
                  No reflections yet
                </p>
              )
            )}
          </div>
        );
      })}
    </div>
  );
}
