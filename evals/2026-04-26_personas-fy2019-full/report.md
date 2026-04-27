# 2026-04-26_personas-fy2019-full — personas-fy2019-full

_Generated_: 2026-04-26T14:27:51-04:00  
_Branch_: `feat/auto-persona-edgar`  _Commit_: `b3cdde2`

_Config_: seed=42, temperature=1.0, rounds=10, concurrency=5, persona_variant=`auto-fy2019`

_Summary_: wall-clock 844.1s, cost $2.2876, errors 2, rounds 10/10

**Notes:** Full-coverage auto-FY2019 personas: all 9 agents now load from personas_cache (4 from EDGAR + 5 from IR-website PDFs). Pair with 2026-04-22_capacity-rebalance to isolate persona-source contribution under complete coverage. Compare also with 2026-04-26_personas-fy2019 (partial 4/9 coverage) to see what additional cleanup the IR-sourced personas contribute.

## 1. Emergence

### Order totals per OEM (units)

| Round | Demand× | ToyotaMotors | FordAuto | VolkswagenAG |
|---|---|---|---|---|
| 1 | 0.60 | 344 | 136 | 381 |
| 2 | 0.50 | 394 | 131 | 421 |
| 3 | 0.80 | 493 | 184 | 773 |
| 4 | 1.10 | 764 | 251 | 648 |
| 5 | 1.25 | 768 | 279 | 344 |
| 6 | 1.20 | 813 | 289 | 197 |
| 7 | 1.15 | 829 | 296 | 163 |
| 8 | 1.10 | 468 | 377 | 152 |
| 9 | 0.95 | 266 | 116 | 103 |
| 10 | 0.75 | 220 | 107 | 95 |

### Bullwhip — stdev of order totals within each tier

| Round | OEM σ | Tier-1 σ | Designer σ |
|---|---|---|---|
| 1 | 107.8 | 39.0 | 32.0 |
| 2 | 130.8 | 225.5 | 81.5 |
| 3 | 240.6 | 32.0 | 46.5 |
| 4 | 219.7 | 249.5 | 52.5 |
| 5 | 216.8 | 189.0 | 294.0 |
| 6 | 271.3 | 49.0 | 86.5 |
| 7 | 287.8 | 51.0 | 9.5 |
| 8 | 132.8 | 190.5 | 73.5 |
| 9 | 74.0 | 226.0 | 176.0 |
| 10 | 56.3 | 35.5 | 157.5 |

### Fill rate by tier (1.0 = perfect supply)

| Round | OEM | Tier-1 | Designer | Foundry |
|---|---|---|---|---|
| 1 | 0.68 | 1.00 | 1.00 | 1.00 |
| 2 | 0.67 | 1.00 | 1.00 | 1.00 |
| 3 | 0.71 | 1.00 | 1.00 | 1.00 |
| 4 | 0.62 | 1.00 | 1.00 | 1.00 |
| 5 | 0.45 | 1.00 | 1.00 | 1.00 |
| 6 | 0.45 | 1.00 | 1.00 | 1.00 |
| 7 | 0.36 | 1.00 | 1.00 | 1.00 |
| 8 | 0.41 | 1.00 | 1.00 | 1.00 |
| 9 | 0.88 | 1.00 | 1.00 | 1.00 |
| 10 | 0.07 | 1.00 | 1.00 | 1.00 |

### Average price by tier ($/unit)

| Round | Foundry | Designer | Tier-1 |
|---|---|---|---|
| 1 | 10.75 | 26.50 | 65.00 |
| 2 | 10.75 | 28.50 | 65.00 |
| 3 | 12.50 | 37.00 | 67.75 |
| 4 | 14.00 | 53.25 | 76.00 |
| 5 | 16.00 | 60.25 | 81.25 |
| 6 | 17.50 | 62.00 | 78.25 |
| 7 | 21.50 | 88.00 | 85.00 |
| 8 | 25.25 | 78.50 | 87.00 |
| 9 | 29.25 | 84.50 | 91.75 |
| 10 | 43.50 | 79.00 | 91.75 |

### Cumulative profit at end of run ($)

| Agent | Profit |
|---|---|
| ContiParts | 244,054 |
| BoschAuto | 189,998 |
| ToyotaMotors | 102,936 |
| FordAuto | 35,736 |
| VolkswagenAG | 33,526 |
| KoreaSilicon | -1,246 |
| TaiwanSemi | -4,950 |
| AmeriSemi | -7,807 |
| EuroChip | -11,233 |

## 2. Behavior

### Crisis-vocabulary density per round (hits / total LLM texts)

| Round | Demand× | Hits/Total | % |
|---|---|---|---|
| 1 | 0.60 | 24/95 | 25% |
| 2 | 0.50 | 14/58 | 24% |
| 3 | 0.80 | 22/122 | 18% |
| 4 | 1.10 | 18/122 | 15% |
| 5 | 1.25 | 41/58 | 71% |
| 6 | 1.20 | 24/58 | 41% |
| 7 | 1.15 | 58/122 | 48% |
| 8 | 1.10 | 61/122 | 50% |
| 9 | 0.95 | 83/122 | 68% |
| 10 | 0.75 | 46/122 | 38% |

### Mean affect intensity per round

| Round | Fear | Stress | Panicked+Anxious |
|---|---|---|---|
| 1 | 0.24 | 0.56 | 1/9 |
| 2 | 0.31 | 0.68 | 1/9 |
| 3 | 0.24 | 0.70 | 1/9 |
| 4 | 0.27 | 0.77 | 1/9 |
| 5 | 0.42 | 0.90 | 5/9 |
| 6 | 0.36 | 0.90 | 2/9 |
| 7 | 0.55 | 0.90 | 5/9 |
| 8 | 0.48 | 0.83 | 4/9 |
| 9 | 0.58 | 0.90 | 4/9 |
| 10 | 0.57 | 0.90 | 5/9 |

### Signals emitted per round (by type)

| Round | information | loyalty_pledge | price_warning | request | threat | Total |
|---|---|---|---|---|---|---|
| 1 | 8 | 5 | 0 | 5 | 0 | 18 |
| 2 | 8 | 7 | 0 | 3 | 0 | 18 |
| 3 | 9 | 7 | 1 | 1 | 0 | 18 |
| 4 | 7 | 7 | 3 | 1 | 0 | 18 |
| 5 | 8 | 6 | 3 | 1 | 0 | 18 |
| 6 | 8 | 8 | 0 | 2 | 0 | 18 |
| 7 | 10 | 5 | 1 | 1 | 1 | 18 |
| 8 | 8 | 6 | 1 | 2 | 1 | 18 |
| 9 | 8 | 7 | 0 | 1 | 2 | 18 |
| 10 | 9 | 7 | 2 | 0 | 0 | 18 |

### First explicit crisis/shortage/shock/emergency utterance

- **R1**, KoreaSilicon (signal): _Despite automotive sector disruption, Samsung Foundry maintains stable supply allocation for your critical applications. We're committed to supporting European OEMs through this crisis period._


## 3. Engineering

### Per-round wall-clock + cost

| Round | Wall-clock | Cost | Events | Errors |
|---|---|---|---|---|
| 1 | 53.2s | $0.0987 | 31 | 0 |
| 2 | 59.2s | $0.1263 | 31 | 0 |
| 3 | 89.6s | $0.2376 | 40 | 0 |
| 4 | 97.3s | $0.2703 | 40 | 0 |
| 5 | 82.1s | $0.1789 | 31 | 0 |
| 6 | 82.4s | $0.1803 | 31 | 2 |
| 7 | 97.6s | $0.2976 | 40 | 0 |
| 8 | 100.7s | $0.3079 | 40 | 0 |
| 9 | 95.2s | $0.3003 | 40 | 0 |
| 10 | 86.8s | $0.2898 | 40 | 0 |
