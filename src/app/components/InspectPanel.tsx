"use client";

import { FileText, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import type {
  AgentId,
  AgentSignal,
  AgentState,
  MemoryRecord,
} from "../lib/types";
import { EMOTIONAL_COLORS, PERSONA_SOURCES, TIER_LABELS } from "../lib/types";

interface Props {
  agent: AgentState;
  currentRound: number;
  onClose: () => void;
}

// Document-style agent view. The agent's reasoning, memories, and
// reflections are treated as reading material (serif), not as dashboard
// widgets. The top strip carries structural metadata; everything below
// is a chapter.
export default function InspectPanel({ agent, currentRound, onClose }: Props) {
  const decision = agent.current_decision;
  const memories = agent.memories ?? [];
  const reflections = agent.reflections ?? [];
  const signalsSent = agent.signals_sent ?? [];
  const signalsReceived = agent.signals_received ?? [];
  const plan = agent.current_plan ?? null;

  const emotionColor = EMOTIONAL_COLORS[agent.emotional_state] ?? "#888";
  const profit = agent.profit ?? 0;

  return (
    <article className="h-full overflow-y-auto bg-background">
      {/* Hairline close affordance, top right */}
      <div className="sticky top-0 z-10 flex items-center justify-between px-6 md:px-10 py-3 bg-background/90 backdrop-blur-sm border-b border-border">
        <span className="text-[11px] uppercase tracking-widest text-muted-foreground font-mono">
          round {currentRound} · agent inspect
        </span>
        <Button
          variant="ghost"
          size="icon"
          onClick={onClose}
          title="Close (Esc)"
          className="h-7 w-7"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="max-w-3xl mx-auto px-6 md:px-10 py-8 md:py-12">
        {/* Title block */}
        <header className="mb-8">
          <p className="text-xs uppercase tracking-widest text-muted-foreground font-mono mb-2">
            {TIER_LABELS[agent.tier]}
          </p>
          <h1 className="font-serif text-4xl md:text-5xl leading-tight tracking-tight">
            {agent.display_name}
          </h1>
          {/* Persona provenance — names the public document the system
              prompt was generated from, so a viewer can trace any agent
              behavior back to a verifiable source. */}
          {(() => {
            const src = PERSONA_SOURCES[agent.agent_id as AgentId];
            if (!src) return null;
            return (
              <p className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground italic font-serif">
                <FileText className="h-3 w-3 shrink-0" aria-hidden />
                <span>
                  Persona generated from {src.company}'s FY{src.fiscalYear}{" "}
                  {src.document}
                  <span className="ml-1.5 text-[10px] not-italic font-mono uppercase tracking-wider opacity-70">
                    {src.origin}
                  </span>
                </span>
              </p>
            );
          })()}
          <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
            <span className="flex items-center gap-1.5">
              <span
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: emotionColor }}
              />
              <span className="font-serif italic">
                {agent.emotional_state}
              </span>
            </span>
            <Metric label="inventory" value={agent.inventory.toLocaleString()} />
            <Metric label="capacity" value={agent.capacity.toLocaleString()} />
            <Metric
              label="price"
              value={`$${agent.current_price.toFixed(2)}`}
            />
            <Metric
              label="fill"
              value={`${Math.round(agent.fill_rate * 100)}%`}
            />
            <Metric
              label="profit"
              value={`${profit >= 0 ? "+" : ""}$${Math.abs(profit).toFixed(0)}`}
              tone={profit < 0 ? "destructive" : "neutral"}
            />
          </div>
        </header>

        {/* Decision section */}
        {decision && <DecisionChapter decision={decision} />}

        {/* Reasoning prose */}
        {decision?.reasoning && (
          <Chapter title="Reasoning">
            <p className="font-serif text-lg leading-relaxed text-foreground/90">
              {decision.reasoning}
            </p>
          </Chapter>
        )}

        {/* Memories retrieved */}
        {memories.length > 0 && (
          <Chapter title="What it remembered">
            <ul className="space-y-2">
              {memories.slice(-8).reverse().map((m, i) => (
                <MemoryLine key={i} record={m} currentRound={currentRound} />
              ))}
            </ul>
          </Chapter>
        )}

        {/* Reflections */}
        {reflections.length > 0 && (
          <Chapter title="What it reflected">
            <ul className="space-y-3">
              {reflections.map((r, i) => (
                <li
                  key={i}
                  className="font-serif text-lg leading-relaxed text-foreground/90"
                >
                  {r}
                </li>
              ))}
            </ul>
          </Chapter>
        )}

        {/* Signals */}
        {(signalsSent.length > 0 || signalsReceived.length > 0) && (
          <Chapter title="Messages this round">
            <ul className="space-y-2">
              {signalsSent.map((s, i) => (
                <SignalLine key={`s${i}`} signal={s} direction="sent" />
              ))}
              {signalsReceived.map((s, i) => (
                <SignalLine key={`r${i}`} signal={s} direction="received" />
              ))}
            </ul>
          </Chapter>
        )}

        {/* Plan */}
        {plan && (
          <Chapter title="Current plan">
            <p className="text-xs font-mono text-muted-foreground mb-3">
              created round {plan.created_round} · horizon {plan.horizon}
              {plan.invalidated && (
                <span className="ml-2 text-destructive">invalidated</span>
              )}
            </p>
            <ul className="space-y-1 mb-3">
              {plan.goals.map((g, i) => (
                <li
                  key={i}
                  className="font-serif text-base leading-relaxed"
                >
                  — {g}
                </li>
              ))}
            </ul>
            {plan.risk_assessment && (
              <p className="font-serif italic text-sm text-muted-foreground">
                risk: {plan.risk_assessment}
              </p>
            )}
          </Chapter>
        )}

        {/* Trust map — compact */}
        {Object.keys(agent.trust_scores).length > 0 && (
          <Chapter title="Trust">
            <dl className="grid grid-cols-[max-content_1fr_max-content] gap-x-3 gap-y-1 text-sm">
              {Object.entries(agent.trust_scores).map(([partner, score]) => (
                <div key={partner} className="contents">
                  <dt className="font-mono text-muted-foreground">
                    {partner}
                  </dt>
                  <dd className="flex items-center">
                    <span className="h-px w-full bg-border relative">
                      <span
                        className="absolute top-[-3px] h-[7px] w-[2px] bg-primary"
                        style={{ left: `${(score / 10) * 100}%` }}
                      />
                    </span>
                  </dd>
                  <dd className="font-mono tabular-nums text-right w-8">
                    {score.toFixed(1)}
                  </dd>
                </div>
              ))}
            </dl>
          </Chapter>
        )}
      </div>
    </article>
  );
}

function Metric({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: "neutral" | "destructive";
}) {
  return (
    <span className="flex items-baseline gap-1.5">
      <span className="text-[11px] uppercase tracking-wider text-muted-foreground font-mono">
        {label}
      </span>
      <span
        className={`font-mono tabular-nums ${tone === "destructive" ? "text-destructive" : "text-foreground"}`}
      >
        {value}
      </span>
    </span>
  );
}

function Chapter({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mt-10">
      <h2 className="text-[11px] uppercase tracking-widest text-muted-foreground font-mono mb-3">
        {title}
      </h2>
      {children}
    </section>
  );
}

function DecisionChapter({
  decision,
}: {
  decision: NonNullable<AgentState["current_decision"]>;
}) {
  const allocations = decision.allocations;
  const orders = decision.orders;
  const held = decision.held_in_reserve;
  const priceOffered = decision.price_offered;
  const maxWilling = decision.max_price_willing_to_pay;

  const hasSupplierFields =
    allocations || typeof held === "number" || typeof priceOffered === "number";
  const hasBuyerFields = orders || typeof maxWilling === "number";

  if (!hasSupplierFields && !hasBuyerFields) return null;

  return (
    <section className="mt-8 border-l-2 border-primary pl-5">
      <h2 className="text-[11px] uppercase tracking-widest text-muted-foreground font-mono mb-2">
        Decision
      </h2>
      {hasSupplierFields && (
        <div className="font-serif text-base leading-relaxed text-foreground/90">
          {allocations && Object.keys(allocations).length > 0 && (
            <p>
              Allocated{" "}
              {Object.entries(allocations)
                .filter(([, v]) => v > 0)
                .map(([partner, units], i, arr) => (
                  <span key={partner}>
                    <span className="font-mono tabular-nums">
                      {units.toLocaleString()}
                    </span>{" "}
                    to{" "}
                    <span className="font-sans text-foreground">{partner}</span>
                    {i < arr.length - 1 ? ", " : ""}
                  </span>
                ))}
              {typeof held === "number" && held > 0 && (
                <>
                  , held{" "}
                  <span className="font-mono tabular-nums">
                    {held.toLocaleString()}
                  </span>{" "}
                  in reserve
                </>
              )}
              .
            </p>
          )}
          {typeof priceOffered === "number" && (
            <p className="mt-1">
              Priced at{" "}
              <span className="font-mono tabular-nums">
                ${priceOffered.toFixed(2)}
              </span>{" "}
              per unit.
            </p>
          )}
        </div>
      )}
      {hasBuyerFields && (
        <div className="font-serif text-base leading-relaxed text-foreground/90">
          {orders && Object.keys(orders).length > 0 && (
            <p>
              Ordered{" "}
              {Object.entries(orders)
                .filter(([, v]) => v > 0)
                .map(([partner, units], i, arr) => (
                  <span key={partner}>
                    <span className="font-mono tabular-nums">
                      {units.toLocaleString()}
                    </span>{" "}
                    from{" "}
                    <span className="font-sans text-foreground">{partner}</span>
                    {i < arr.length - 1 ? ", " : ""}
                  </span>
                ))}
              .
            </p>
          )}
          {typeof maxWilling === "number" && (
            <p className="mt-1">
              Willing to pay up to{" "}
              <span className="font-mono tabular-nums">
                ${maxWilling.toFixed(2)}
              </span>{" "}
              per unit.
            </p>
          )}
        </div>
      )}
    </section>
  );
}

function MemoryLine({
  record,
  currentRound,
}: {
  record: MemoryRecord;
  currentRound: number;
}) {
  const ago = currentRound - record.round;
  const when =
    ago === 0
      ? "this round"
      : ago === 1
        ? "last round"
        : `${ago} rounds ago`;
  return (
    <li className="font-serif text-base leading-relaxed text-foreground/85">
      <span className="text-xs font-mono text-muted-foreground mr-2">
        [{record.category}]
      </span>
      {record.description}
      <span className="text-xs font-mono text-muted-foreground ml-2">
        · {when}
      </span>
    </li>
  );
}

function SignalLine({
  signal,
  direction,
}: {
  signal: AgentSignal;
  direction: "sent" | "received";
}) {
  const arrow = direction === "sent" ? "→" : "←";
  const other = direction === "sent" ? signal.recipient ?? "broadcast" : signal.sender;
  return (
    <li className="flex items-baseline gap-2 text-sm">
      <span className="text-muted-foreground font-mono">{arrow}</span>
      <span className="font-mono text-xs text-muted-foreground w-28 shrink-0 truncate">
        {other}
      </span>
      <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono w-20 shrink-0">
        {signal.signal_type}
      </span>
      <span className="font-serif italic text-foreground/85 leading-relaxed">
        “{signal.content}”
      </span>
    </li>
  );
}
