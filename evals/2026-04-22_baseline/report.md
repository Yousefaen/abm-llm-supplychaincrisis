# 2026-04-22_baseline — baseline

_Generated_: 2026-04-25T22:26:56-04:00  
_Branch_: `main`  _Commit_: `9fc5f60`

_Config_: seed=42, temperature=1.0, rounds=10, concurrency=5, persona_variant=`hand-crafted`

_Summary_: wall-clock 832.2s, cost $2.3583, errors 3, rounds 10/10

**Notes:** Original eval baseline — before scenario prompt rewrite. Documented in evals/run_2026-04-22.md.

## 1. Emergence

### Order totals per OEM (units)

| Round | Demand× | ToyotaMotors | FordAuto | VolkswagenAG |
|---|---|---|---|---|
| 1 | 0.60 | 321 | 265 | 423 |
| 2 | 0.50 | 267 | 238 | 574 |
| 3 | 0.80 | 400 | 113 | 968 |
| 4 | 1.10 | 545 | 194 | 1490 |
| 5 | 1.25 | 770 | 179 | 1814 |
| 6 | 1.20 | 992 | 210 | 1062 |
| 7 | 1.15 | 827 | 140 | 414 |
| 8 | 1.10 | 410 | 140 | 548 |
| 9 | 0.95 | 325 | 98 | 423 |
| 10 | 0.75 | 216 | 110 | 155 |

### Bullwhip — stdev of order totals within each tier

| Round | OEM σ | Tier-1 σ | Designer σ |
|---|---|---|---|
| 1 | 65.4 | 50.0 | 98.5 |
| 2 | 152.0 | 157.5 | 136.0 |
| 3 | 355.3 | 34.0 | 217.0 |
| 4 | 547.3 | 0.5 | 97.5 |
| 5 | 676.0 | 677.0 | 39.5 |
| 6 | 386.2 | 215.5 | 33.0 |
| 7 | 282.4 | 213.5 | 266.0 |
| 8 | 169.4 | 97.5 | 37.0 |
| 9 | 136.1 | 8.5 | 100.0 |
| 10 | 43.4 | 47.5 | 56.0 |

### Fill rate by tier (1.0 = perfect supply)

| Round | OEM | Tier-1 | Designer | Foundry |
|---|---|---|---|---|
| 1 | 0.70 | 1.00 | 1.00 | 1.00 |
| 2 | 0.70 | 1.00 | 1.00 | 1.00 |
| 3 | 0.50 | 1.00 | 1.00 | 1.00 |
| 4 | 0.39 | 1.00 | 1.00 | 1.00 |
| 5 | 0.28 | 1.00 | 1.00 | 1.00 |
| 6 | 0.29 | 1.00 | 1.00 | 1.00 |
| 7 | 0.31 | 1.00 | 1.00 | 1.00 |
| 8 | 0.35 | 1.00 | 1.00 | 1.00 |
| 9 | 0.35 | 1.00 | 1.00 | 1.00 |
| 10 | 0.01 | 1.00 | 1.00 | 1.00 |

### Average price by tier ($/unit)

| Round | Foundry | Designer | Tier-1 |
|---|---|---|---|
| 1 | 10.50 | 28.25 | 60.00 |
| 2 | 12.00 | 43.25 | 65.25 |
| 3 | 14.50 | 66.40 | 77.25 |
| 4 | 15.50 | 70.00 | 89.75 |
| 5 | 14.50 | 79.25 | 95.00 |
| 6 | 16.00 | 90.25 | 98.00 |
| 7 | 19.75 | 98.00 | 98.00 |
| 8 | 30.00 | 105.00 | 90.00 |
| 9 | 42.00 | 91.50 | 88.50 |
| 10 | 32.00 | 88.50 | 82.00 |

### Cumulative profit at end of run ($)

| Agent | Profit |
|---|---|
| BoschAuto | 284,544 |
| ContiParts | 218,568 |
| ToyotaMotors | 67,182 |
| VolkswagenAG | 55,278 |
| FordAuto | 13,028 |
| KoreaSilicon | -4,473 |
| TaiwanSemi | -6,954 |
| EuroChip | -8,042 |
| AmeriSemi | -17,594 |

## 2. Behavior

### Crisis-vocabulary density per round (hits / total LLM texts)

| Round | Demand× | Hits/Total | % |
|---|---|---|---|
| 1 | 0.60 | 10/95 | 11% |
| 2 | 0.50 | 21/58 | 36% |
| 3 | 0.80 | 40/122 | 33% |
| 4 | 1.10 | 48/122 | 39% |
| 5 | 1.25 | 42/58 | 72% |
| 6 | 1.20 | 30/58 | 52% |
| 7 | 1.15 | 48/122 | 39% |
| 8 | 1.10 | 59/122 | 48% |
| 9 | 0.95 | 63/122 | 52% |
| 10 | 0.75 | 38/122 | 31% |

### Mean affect intensity per round

| Round | Fear | Stress | Panicked+Anxious |
|---|---|---|---|
| 1 | 0.23 | 0.57 | 0/9 |
| 2 | 0.31 | 0.70 | 1/9 |
| 3 | 0.27 | 0.74 | 1/9 |
| 4 | 0.40 | 0.85 | 3/9 |
| 5 | 0.60 | 0.90 | 5/9 |
| 6 | 0.70 | 0.90 | 5/9 |
| 7 | 0.78 | 0.90 | 6/9 |
| 8 | 0.78 | 0.90 | 6/9 |
| 9 | 0.75 | 0.90 | 5/9 |
| 10 | 0.70 | 0.90 | 5/9 |

### Signals emitted per round (by type)

| Round | information | loyalty_pledge | price_warning | request | threat | Total |
|---|---|---|---|---|---|---|
| 1 | 6 | 7 | 0 | 5 | 0 | 18 |
| 2 | 8 | 6 | 0 | 4 | 0 | 18 |
| 3 | 6 | 7 | 4 | 1 | 0 | 18 |
| 4 | 3 | 9 | 4 | 2 | 0 | 18 |
| 5 | 6 | 8 | 2 | 2 | 0 | 18 |
| 6 | 7 | 7 | 4 | 0 | 0 | 18 |
| 7 | 7 | 7 | 2 | 2 | 0 | 18 |
| 8 | 8 | 8 | 0 | 1 | 1 | 18 |
| 9 | 9 | 1 | 7 | 0 | 1 | 18 |
| 10 | 9 | 7 | 1 | 1 | 0 | 18 |

### First explicit crisis/shortage/shock/emergency utterance

- **R1**, EuroChip (buyer): _COVID-19 has collapsed automotive demand 40%, but my quarterly need remains ~360 units to serve BoschAuto (235) and ContiParts (176). I'm ordering 400 total units across two trusted foundries who've j_


## 3. Engineering

### Per-round wall-clock + cost

| Round | Wall-clock | Cost | Events | Errors |
|---|---|---|---|---|
| 1 | 56.0s | $0.1013 | 31 | 0 |
| 2 | 70.4s | $0.1362 | 31 | 0 |
| 3 | 92.0s | $0.2557 | 40 | 0 |
| 4 | 89.2s | $0.2835 | 40 | 0 |
| 5 | 74.9s | $0.1756 | 31 | 0 |
| 6 | 81.0s | $0.1807 | 31 | 1 |
| 7 | 99.7s | $0.3010 | 40 | 2 |
| 8 | 87.8s | $0.3063 | 40 | 2 |
| 9 | 93.7s | $0.3137 | 40 | 3 |
| 10 | 87.4s | $0.3042 | 40 | 3 |
