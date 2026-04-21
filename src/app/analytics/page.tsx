"use client";

import Link from "next/link";
import { useEffect } from "react";
import { ArrowLeft } from "lucide-react";
import { useSimulation } from "../lib/useSimulation";
import MetricsDashboard from "../components/MetricsDashboard";
import EventLog from "../components/EventLog";

// Post-hoc analysis view. The main page is narrative; this page is
// quantitative. Phase 4 (benchmarks vs empirical data) will add the
// baseline comparison and scoring tables here.
export default function AnalyticsPage() {
  const { state, fetchState } = useSimulation();

  useEffect(() => {
    fetchState();
  }, [fetchState]);

  return (
    <main className="min-h-screen bg-background">
      {/* Thin header with back link */}
      <header className="flex items-center gap-4 px-4 h-12 border-b border-border bg-card/60 backdrop-blur-sm">
        <Link
          href="/"
          className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>back to simulation</span>
        </Link>
        <span className="mx-2 text-muted-foreground/40">·</span>
        <h1 className="font-serif text-xl leading-none tracking-tight">
          Analytics
        </h1>
        <span className="ml-auto text-xs text-muted-foreground font-mono tabular-nums">
          ${state.totalCost.toFixed(3)}
        </span>
      </header>

      <div className="max-w-6xl mx-auto px-4 md:px-8 py-8">
        <section className="mb-12">
          <h2 className="font-serif text-2xl mb-1 tracking-tight">
            Emergence metrics
          </h2>
          <p className="text-sm text-muted-foreground mb-6 font-serif italic">
            Fill rates, hoarding, trust, prices, bullwhip.
          </p>
          <div className="rounded-lg border border-border bg-card">
            <MetricsDashboard history={state.history} agents={state.agents} />
          </div>
        </section>

        <section>
          <h2 className="font-serif text-2xl mb-1 tracking-tight">
            Event log
          </h2>
          <p className="text-sm text-muted-foreground mb-6 font-serif italic">
            Every decision, signal, and consequence, round by round.
          </p>
          <div className="rounded-lg border border-border bg-card h-[60vh]">
            <EventLog
              history={state.history}
              agents={state.agents}
              currentRound={state.currentRound}
            />
          </div>
        </section>

        <section className="mt-12 pt-8 border-t border-border">
          <h2 className="font-serif text-2xl mb-1 tracking-tight">
            Benchmarks <span className="text-muted-foreground italic">(Phase 4)</span>
          </h2>
          <p className="text-sm text-muted-foreground mb-2 font-serif italic max-w-prose">
            Empirical validation against the 2020–2022 semiconductor crisis.
            Comparisons against rule-based, random, and memoryless-LLM baselines
            will land here once the data pipeline is wired.
          </p>
        </section>
      </div>
    </main>
  );
}
