# 2026-05-03_personas-fy2019-seed43 — personas-fy2019-seed43

_Generated_: 2026-05-03T14:29:06-04:00  
_Branch_: `feat/pmi-and-findings`  _Commit_: `08ae436`  _(dirty tree)_

_Config_: seed=43, temperature=1.0, rounds=10, concurrency=5, persona_variant=`auto-fy2019`

_Summary_: wall-clock 776.2s, cost $2.2295, errors 5, rounds 10/10

**Notes:** Seed 43 (different from 42 used in 2026-04-26_personas-fy2019-full). Same persona variant + scenario, different RNG seed. Used to test bullwhip robustness across seeds.

## 1. Emergence

### Order totals per OEM (units)

| Round | Demand× | ToyotaMotors | FordAuto | VolkswagenAG |
|---|---|---|---|---|
| 1 | 0.60 | 321 | 136 | 402 |
| 2 | 0.50 | 251 | 127 | 390 |
| 3 | 0.80 | 448 | 157 | 525 |
| 4 | 1.10 | 395 | 218 | 710 |
| 5 | 1.25 | 452 | 288 | 976 |
| 6 | 1.20 | 203 | 305 | 919 |
| 7 | 1.15 | 112 | 359 | 511 |
| 8 | 1.10 | 95 | 263 | 444 |
| 9 | 0.95 | 120 | 285 | 372 |
| 10 | 0.75 | 81 | 180 | 359 |

### Bullwhip — stdev of order totals within each tier

| Round | OEM σ | Tier-1 σ | Designer σ |
|---|---|---|---|
| 1 | 111.3 | 29.5 | 22.5 |
| 2 | 107.4 | 160.0 | 38.5 |
| 3 | 158.5 | 314.5 | 57.5 |
| 4 | 203.5 | 481.0 | 151.5 |
| 5 | 293.4 | 913.5 | 239.5 |
| 6 | 316.2 | 30.5 | 166.0 |
| 7 | 164.4 | 13.0 | 65.0 |
| 8 | 142.5 | 174.5 | 22.5 |
| 9 | 104.5 | 38.0 | 6.0 |
| 10 | 115.0 | 168.0 | 161.5 |

### Fill rate by tier (1.0 = perfect supply)

| Round | OEM | Tier-1 | Designer | Foundry |
|---|---|---|---|---|
| 1 | 0.75 | 1.00 | 1.00 | 1.00 |
| 2 | 0.70 | 1.00 | 1.00 | 1.00 |
| 3 | 0.70 | 1.00 | 1.00 | 1.00 |
| 4 | 0.78 | 1.00 | 1.00 | 1.00 |
| 5 | 0.48 | 1.00 | 1.00 | 1.00 |
| 6 | 0.57 | 1.00 | 1.00 | 1.00 |
| 7 | 0.82 | 1.00 | 1.00 | 1.00 |
| 8 | 0.66 | 1.00 | 1.00 | 1.00 |
| 9 | 0.63 | 1.00 | 1.00 | 1.00 |
| 10 | 0.58 | 1.00 | 1.00 | 1.00 |

### Average price by tier ($/unit)

| Round | Foundry | Designer | Tier-1 |
|---|---|---|---|
| 1 | 10.75 | 26.25 | 68.25 |
| 2 | 11.75 | 26.25 | 71.75 |
| 3 | 12.50 | 34.00 | 73.50 |
| 4 | 13.50 | 37.00 | 78.75 |
| 5 | 14.50 | 38.50 | 84.50 |
| 6 | 18.00 | 40.50 | 86.50 |
| 7 | 21.75 | 50.50 | 91.50 |
| 8 | 22.75 | 57.50 | 92.00 |
| 9 | 27.25 | 65.25 | 94.50 |
| 10 | 27.25 | 68.75 | 95.50 |

### Cumulative profit at end of run ($)

| Agent | Profit |
|---|---|
| BoschAuto | 320,442 |
| ContiParts | 267,520 |
| VolkswagenAG | 68,140 |
| ToyotaMotors | 49,826 |
| KoreaSilicon | -1,904 |
| TaiwanSemi | -2,349 |
| AmeriSemi | -5,737 |
| EuroChip | -8,403 |
| FordAuto | -21,408 |

## 2. Behavior

### Crisis-vocabulary density per round (hits / total LLM texts)

| Round | Demand× | Hits/Total | % |
|---|---|---|---|
| 1 | 0.60 | 27/95 | 28% |
| 2 | 0.50 | 18/58 | 31% |
| 3 | 0.80 | 21/122 | 17% |
| 4 | 1.10 | 25/122 | 20% |
| 5 | 1.25 | 44/58 | 76% |
| 6 | 1.20 | 21/58 | 36% |
| 7 | 1.15 | 45/122 | 37% |
| 8 | 1.10 | 55/121 | 45% |
| 9 | 0.95 | 78/121 | 64% |
| 10 | 0.75 | 53/120 | 44% |

### Mean affect intensity per round

| Round | Fear | Stress | Panicked+Anxious |
|---|---|---|---|
| 1 | 0.23 | 0.56 | 1/9 |
| 2 | 0.30 | 0.70 | 1/9 |
| 3 | 0.23 | 0.73 | 1/9 |
| 4 | 0.25 | 0.79 | 1/9 |
| 5 | 0.43 | 0.90 | 5/9 |
| 6 | 0.35 | 0.90 | 2/9 |
| 7 | 0.49 | 0.90 | 4/9 |
| 8 | 0.40 | 0.83 | 3/9 |
| 9 | 0.52 | 0.90 | 4/9 |
| 10 | 0.46 | 0.90 | 4/9 |

### Signals emitted per round (by type)

| Round | information | loyalty_pledge | price_warning | request | Total |
|---|---|---|---|---|---|
| 1 | 7 | 8 | 0 | 3 | 18 |
| 2 | 8 | 6 | 0 | 4 | 18 |
| 3 | 10 | 4 | 1 | 3 | 18 |
| 4 | 9 | 7 | 2 | 0 | 18 |
| 5 | 8 | 6 | 3 | 1 | 18 |
| 6 | 10 | 5 | 2 | 1 | 18 |
| 7 | 9 | 4 | 1 | 4 | 18 |
| 8 | 9 | 8 | 0 | 0 | 17 |
| 9 | 9 | 6 | 1 | 1 | 17 |
| 10 | 8 | 6 | 1 | 1 | 16 |

### First explicit crisis/shortage/shock/emergency utterance

- **R1**, KoreaSilicon (signal): _Automotive sector will recover—we're holding your 60% allocation stable and absorbing short-term margin pressure to ensure supply continuity through this crisis. Your partnership is foundational to ou_


## 3. Engineering

### Per-round wall-clock + cost

| Round | Wall-clock | Cost | Events | Errors |
|---|---|---|---|---|
| 1 | 48.0s | $0.0961 | 31 | 0 |
| 2 | 73.6s | $0.1294 | 31 | 0 |
| 3 | 75.8s | $0.2329 | 40 | 0 |
| 4 | 80.7s | $0.2614 | 40 | 0 |
| 5 | 71.2s | $0.1695 | 31 | 0 |
| 6 | 72.5s | $0.1702 | 31 | 1 |
| 7 | 91.5s | $0.2876 | 40 | 0 |
| 8 | 86.2s | $0.2962 | 40 | 0 |
| 9 | 91.5s | $0.2988 | 40 | 3 |
| 10 | 85.2s | $0.2874 | 39 | 1 |
