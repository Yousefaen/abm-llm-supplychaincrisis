@AGENTS.md

# Supply-Chain ABM (chip-shortage simulation)

## What this is

An agent-based model of the 2020-2022 auto/semiconductor supply-chain crisis. Nine LLM-driven agents play C-suite roles across a four-tier supply chain (foundry → chip designer → Tier-1 supplier → OEM) over ten quarterly rounds (Q1 2020 → Q2 2022). Real-world events (COVID, Texas storm, Renesas fire, CHIPS Act, Russia-Ukraine, etc.) are surfaced as **news triggers only** — supply-chain consequences (panic-buying, hoarding, allocation rationing, price spikes, lead-time blow-out) must **emerge** from agent behavior, not be announced in the prompt.

The architectural test: can LLM agents *recognize* and *adapt to* a crisis without being told one is happening? Comparable LLM-ABMs (e.g. MiroFish) stop at plausibility; this project tries for post-hoc external validity by correlating emergent stress signals against the real NY Fed GSCPI for the same calendar window.

This is a research prototype, not a production system. There is no end user, no SLAs, and no traditional unit-test suite (one affect-state test in `test_affect.py`).

## Stack and layout

- **Backend** — Python 3.12, [Mesa 3.5](https://mesa.readthedocs.io/) ABM framework, FastAPI server. LLM calls via the `anthropic` Python SDK. Default model: Claude Haiku 4.5 (`claude-haiku-4-5-20251001`); persona generation uses Sonnet 4 (`claude-sonnet-4-20250514`).
- **Frontend** — Next.js 16 (App Router), React 19, Tailwind 4, shadcn-ui, d3, recharts. RTS-style live/replay UI with scrubber, activity feed, inspect panel, findings overlay.
- **Deployment** — Backend on Railway (Dockerfile), frontend on Vercel. Health check at `/api/state`.
- **Models** — Haiku for agent decisions (latency + cost), Sonnet for one-shot persona generation from filings.

```
backend/
  agents.py             -- agent classes, AGENT_SPECS, hand-curated PERSONAS
  affect.py             -- multi-dim emotion + per-partner grudge state
  memory.py             -- Stanford-style memory stream + reflection
  market_data.py        -- exogenous news vs. endogenous emergent observables
  scenarios.py          -- 10 round events + DEMAND_MULTIPLIERS + CAPACITY_SHOCKS
  model.py              -- Mesa SupplyChainModel, parallel LLM dispatch, DataCollector
  server.py             -- FastAPI wrapper (/api/reset, /api/step, SSE stream)
  persona_builder.py    -- Sonnet-driven persona generation from a filing
  persona_sources.py    -- per-agent EDGAR / IR-PDF source map
  fetch_filings.py      -- SEC EDGAR + IR-PDF fetchers w/ on-disk cache
  build_personas.py     -- end-to-end pipeline (fetch + generate, all agents)
  _eval_run.py          -- headless 10-round driver, captures full state
  _eval_registry.py     -- experiment IDs, paths, meta schema
  _eval_report.py       -- per-run markdown report + index regeneration
  _eval_compare.py      -- pair-wise experiment diff
  _eval_pmi.py          -- GSCPI / sim-stress correlation harness
  _eval_analyze.py      -- ad-hoc stats helpers used by report.py
  personas_cache/       -- cached filings (docs/) + generated personas (personas/)
  data/                 -- external CSVs (e.g. fred_gscpi.csv — drop manually)

src/app/                -- Next.js app router
  page.tsx              -- main live/replay view
  analytics/            -- per-experiment analytics view
  components/           -- TopBar, Scrubber, SupplyChainGraph, InspectPanel,
                           ActivityFeed, FindingsOverlay, etc.
  lib/useSimulation.ts  -- hook wrapping /api endpoints + SSE

evals/<experiment_id>/  -- meta.json, run.json.gz, report.md per run
evals/index.md          -- auto-regenerated ledger
```

## Agent topology

Nine agents, four tiers, deterministic upstream/downstream wiring (see `AGENT_SPECS` in `backend/agents.py`):

| Tier | Agent ID | Maps to | Initial capacity | Initial inventory | Quarterly need |
|---|---|---|---|---|---|
| Foundry | `TaiwanSemi` | TSMC | 800 | 0 | — |
| Foundry | `KoreaSilicon` | Samsung | 450 | 0 | — |
| Chip designer | `EuroChip` | Infineon | 500 | 200 | 600 |
| Chip designer | `AmeriSemi` | NXP / TI | 550 | 150 | 650 |
| Tier-1 | `BoschAuto` | Bosch | 600 | 50 | 500 |
| Tier-1 | `ContiParts` | Continental | 500 | 40 | 450 |
| OEM | `ToyotaMotors` | Toyota | — | 300 | 400 |
| OEM | `FordAuto` | Ford | — | 30 | 180 |
| OEM | `VolkswagenAG` | VW | — | 60 | 450 |

OEM `quarterly_need` ratios reflect real 2019 unit production (Toyota:Ford:VW ≈ 40:17:43). Toyota's outsized starting inventory encodes its post-Fukushima reserve doctrine.

## Scenario calendar

Ten rounds, one quarter each:

| Round | Quarter | Trigger event |
|---|---|---|
| 1 | 2020 Q1 | COVID-19 begins; lockdowns, auto plant shutdowns |
| 2 | 2020 Q2 | Lockdowns deepen; consumer-electronics surge |
| 3 | 2020 Q3 | China rebounds; Western reopenings |
| 4 | 2020 Q4 | Pent-up demand + stimulus + vaccine rollout |
| 5 | 2021 Q1 | Texas storm + Suez Canal blockage |
| 6 | 2021 Q2 | EU Chips Act framework; OEMs eye direct foundry deals |
| 7 | 2021 Q3 | Renesas Naka fab fire (capacity shock to KoreaSilicon analog) |
| 8 | 2021 Q4 | US CHIPS Act passes Senate; TSMC/Samsung US fab announcements |
| 9 | 2022 Q1 | Russia invades Ukraine; neon-gas supply uncertainty |
| 10 | 2022 Q2 | CHIPS and Science Act signed; consumer-electronics demand fades |

Mechanical forcings live alongside the narrative in `scenarios.py`: `DEMAND_MULTIPLIERS` (per-round demand multiplier on OEM `quarterly_need`), `CAPACITY_SHOCKS` (per-round multiplier on a specific agent's capacity), and `EVENT_EMOTIONAL_VALENCE` (per-round affect deltas applied to all agents). These set the quantitative stakes; the prompt only contains the trigger narrative.

## Key subsystems

- **Personas** (`agents.py:_HARDCODED_PERSONAS` + `persona_builder.py`) — each agent's system prompt has a fixed three-section schema: opening paragraph (role + 2-3 ALL-CAPS personality traits + behavioral tells), `INTERNAL DYNAMICS` (3 stakeholder/board tensions), `YOUR KPIs` (4 numbered KPIs with concrete thresholds). The hand-curated set is the default; an auto-generated FY2019 variant is built from SEC 10-K/20-F filings (Toyota, Ford, TSMC, NXP) and annual-report PDFs (Samsung, Infineon, Continental, Bosch, VW). Selected at process startup via `PERSONA_VARIANT` env var.

- **Memory stream** (`memory.py`) — Stanford generative-agents architecture (Park et al., 2023) adapted for procurement. Categories: `transaction`, `market`, `partner_behavior`, `own_decision`, `consequence`, `reflection`. Tag-based relevance + recency-decay (per-category half-lives) + rule-based importance. No embeddings; scale is small enough (9 agents × 10 rounds) that string-match relevance suffices. Reflection is LLM-generated.

- **Affect / emotion** (`affect.py`) — multi-dimensional affect state replacing the legacy single-string emotional state. Dimensional core (valence/arousal) + 6 specific emotions (fear, anger, trust_joy, pride, shame, greed) at intensity 0..1 + slow physiological traits (stress, fatigue, morale) + per-partner `grudge` accumulator. Persona-seeded baselines per agent. Drives prompt brief, signal contagion, and post-hoc panic-fraction metrics in the eval harness.

- **Market environment** (`market_data.py`) — distinguishes **exogenous** news (what the world tells the agent) from **endogenous** observables (industry-avg fill rate, sentiment, hoarding totals — derived from agent state). Crucially, *outcome* metrics like utilization %, lead-time weeks, and chip spot prices are retained on the dataclass for post-hoc ground-truthing but **never surfaced to the prompt** — including them as inputs would cause agents to role-play the crisis instead of producing it.

- **Experiment registry** (`_eval_*.py`) — experiment IDs of the form `<YYYY-MM-DD>_<slug>`. Each run writes `evals/<id>/{meta.json, run.json.gz, report.md}` and updates `evals/index.md`. Comparison reports are written as `evals/compare_<a>_vs_<b>.md`.

- **External validity** (`_eval_pmi.py`) — correlates three sim emergent stress signals (`1 − fill_rate` on non-foundry tiers; price index; panic+anxious agent fraction) and a composite-z against the **NY Fed Global Supply Chain Pressure Index (GSCPI)** for the aligned 2020Q1-2022Q2 window. GSCPI CSV must be downloaded manually to `backend/data/fred_gscpi.csv` (FRED blocks programmatic fetch).

- **Concurrent LLM dispatch** (`model.py`) — phase-parallel agent calls capped at `PHASE_CONCURRENCY=5` (env-tunable). A `_cost_lock` serializes the cost accumulator since `+=` on a float is not atomic.

## Conventions and gotchas

- **Scenario events surface TRIGGERS only.** If you find yourself wanting to write "foundries running at 100%" or "panic-buying widespread" into the round prompt, stop — that defeats the architectural test. Add the forcing in `DEMAND_MULTIPLIERS` / `CAPACITY_SHOCKS` instead.
- **Agent IDs are validated against `^[A-Za-z0-9_]{1,64}$`.** They appear verbatim in prompts and JSON keys; the validator is defensive against future user-editable persona flows.
- **LLM JSON parsing is resilient** (`agents.py:parse_llm_json`) — strips ` ```json ` fences, handles trailing commas, falls back to regex extraction. Don't tighten it without checking why the leniency is there.
- **Cost accumulator uses a threading lock** because of the parallel dispatch above. Don't bypass it.
- **`Mesa 3.5` quirk** — instance `step()` returns `None`; use `model.advance_quarter()` from the API/eval driver.
- **Default seed 42, default temperature 1.0.** Same defaults across `_eval_run.py` and the FastAPI default model.
- **Persona variant selection is process-wide** — set `PERSONA_VARIANT` env var before backend startup; it's read once at module import.
- **Toyota's 300-unit starting inventory is intentional** — encodes the post-Fukushima reserve doctrine that sets up the calm-Toyota-vs-panicked-Ford-and-VW emergence.

## What this is NOT

- Not a forecasting model. The output is *behavioral plausibility under crisis*, not point predictions.
- Not a production system. Single-process FastAPI, in-memory model state, no auth, no multi-tenant.
- Not unit-test driven. Validation is integration-level: run an experiment, render a report, check emergent metrics correlate with reality.
- Not a polished product. Hobby-tier Vercel + Railway, hand-run experiments, no CI gates beyond `next build`.
- Not optimized for cost. Each 10-round eval run costs ~$2 in Anthropic spend; persona generation adds ~$1 one-time per agent.

## Commands

```
# Frontend
npm run dev                                          # Next.js dev server, :3000
npm run build                                        # production build

# Backend (local dev)
cd backend && uvicorn server:app --reload --port 8010

# One-off experiments
python backend/_eval_run.py --label foo              # 10 rounds, hand-crafted personas
python backend/_eval_run.py --label foo \
       --persona-variant auto-fy2019 --seed 42      # auto-personas from FY2019 filings
python backend/_eval_run.py --rounds 3 --label smoke # quick smoke test

# Reporting / comparison
python backend/_eval_report.py <experiment_id>       # regenerate per-run report
python backend/_eval_report.py index                 # regenerate evals/index.md
python backend/_eval_compare.py <id_a> <id_b>        # pair-wise diff
python backend/_eval_pmi.py <experiment_id>          # GSCPI correlation

# Persona generation (one-time, per filing year)
python backend/build_personas.py --fy 2019           # all 9 agents, FY2019
python backend/build_personas.py --fy 2019 BoschAuto # single agent
```

## Generative-agents architecture

See the long-form notes in `~/.claude/projects/.../memory/project_generative_agents.md` (auto-memory). Memory + reflection + planning + signaling layers are all wired; the doc covers what was kept vs. adapted vs. cut from Park et al.

## Live project state

For current branch state, open threads, and recent decisions, see [`docs/CURRENT_WORK.md`](docs/CURRENT_WORK.md). That file is updated frequently; this one stays stable.
