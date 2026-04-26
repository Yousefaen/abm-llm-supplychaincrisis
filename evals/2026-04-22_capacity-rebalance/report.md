# 2026-04-22_capacity-rebalance — capacity-rebalance

_Generated_: 2026-04-25T22:26:57-04:00  
_Branch_: `main`  _Commit_: `a853e9d`

_Config_: seed=42, temperature=1.0, rounds=10, concurrency=5, persona_variant=`hand-crafted`

_Summary_: wall-clock 796.3s, cost $2.1936, errors 2, rounds 10/10

**Notes:** After rebalancing AGENT_SPECS capacities to approximate real auto-semi ratios. Pair with 2026-04-22_scenario-rewrite.

## 1. Emergence

### Order totals per OEM (units)

| Round | Demand× | ToyotaMotors | FordAuto | VolkswagenAG |
|---|---|---|---|---|
| 1 | 0.60 | 321 | 136 | 423 |
| 2 | 0.50 | 394 | 160 | 750 |
| 3 | 0.80 | 612 | 194 | 833 |
| 4 | 1.10 | 614 | 271 | 795 |
| 5 | 1.25 | 604 | 336 | 320 |
| 6 | 1.20 | 340 | 361 | 191 |
| 7 | 1.15 | 123 | 136 | 37 |
| 8 | 1.10 | 61 | 64 | 11 |
| 9 | 0.95 | 157 | 86 | 7 |
| 10 | 0.75 | 39 | 66 | 0 |

### Bullwhip — stdev of order totals within each tier

| Round | OEM σ | Tier-1 σ | Designer σ |
|---|---|---|---|
| 1 | 118.8 | 28.5 | 61.5 |
| 2 | 242.6 | 65.0 | 292.0 |
| 3 | 265.0 | 272.0 | 299.0 |
| 4 | 217.3 | 357.0 | 138.0 |
| 5 | 130.3 | 333.0 | 31.0 |
| 6 | 75.7 | 155.5 | 63.5 |
| 7 | 43.9 | 22.5 | 66.0 |
| 8 | 24.3 | 40.0 | 15.5 |
| 9 | 61.3 | 73.0 | 5.0 |
| 10 | 27.1 | 40.5 | 74.0 |

### Fill rate by tier (1.0 = perfect supply)

| Round | OEM | Tier-1 | Designer | Foundry |
|---|---|---|---|---|
| 1 | 0.79 | 1.00 | 1.00 | 1.00 |
| 2 | 0.76 | 1.00 | 1.00 | 1.00 |
| 3 | 0.59 | 1.00 | 1.00 | 1.00 |
| 4 | 0.39 | 1.00 | 1.00 | 1.00 |
| 5 | 0.34 | 1.00 | 1.00 | 1.00 |
| 6 | 0.19 | 1.00 | 1.00 | 1.00 |
| 7 | 0.41 | 1.00 | 1.00 | 1.00 |
| 8 | 0.00 | 1.00 | 1.00 | 1.00 |
| 9 | 0.00 | 1.00 | 1.00 | 1.00 |
| 10 | 0.75 | 1.00 | 1.00 | 1.00 |

### Average price by tier ($/unit)

| Round | Foundry | Designer | Tier-1 |
|---|---|---|---|
| 1 | 11.25 | 25.75 | 60.00 |
| 2 | 11.75 | 26.75 | 65.25 |
| 3 | 27.25 | 34.75 | 69.50 |
| 4 | 32.25 | 38.25 | 73.50 |
| 5 | 33.40 | 48.75 | 83.50 |
| 6 | 35.75 | 54.00 | 90.25 |
| 7 | 41.00 | 87.25 | 90.25 |
| 8 | 50.00 | 106.50 | 100.25 |
| 9 | 57.00 | 106.50 | 111.75 |
| 10 | 63.50 | 108.50 | 128.25 |

### Cumulative profit at end of run ($)

| Agent | Profit |
|---|---|
| ContiParts | 135,935 |
| BoschAuto | 126,491 |
| ToyotaMotors | 74,370 |
| VolkswagenAG | 44,454 |
| FordAuto | 26,130 |
| TaiwanSemi | -3,318 |
| AmeriSemi | -6,714 |
| EuroChip | -9,908 |
| KoreaSilicon | -19,467 |

## 2. Behavior

### Crisis-vocabulary density per round (hits / total LLM texts)

| Round | Demand× | Hits/Total | % |
|---|---|---|---|
| 1 | 0.60 | 21/95 | 22% |
| 2 | 0.50 | 17/58 | 29% |
| 3 | 0.80 | 26/121 | 21% |
| 4 | 1.10 | 31/122 | 25% |
| 5 | 1.25 | 45/58 | 78% |
| 6 | 1.20 | 25/58 | 43% |
| 7 | 1.15 | 52/122 | 43% |
| 8 | 1.10 | 56/122 | 46% |
| 9 | 0.95 | 76/122 | 62% |
| 10 | 0.75 | 46/122 | 38% |

### Mean affect intensity per round

| Round | Fear | Stress | Panicked+Anxious |
|---|---|---|---|
| 1 | 0.22 | 0.55 | 1/9 |
| 2 | 0.29 | 0.69 | 1/9 |
| 3 | 0.25 | 0.72 | 1/9 |
| 4 | 0.30 | 0.80 | 2/9 |
| 5 | 0.46 | 0.90 | 5/9 |
| 6 | 0.43 | 0.90 | 2/9 |
| 7 | 0.57 | 0.90 | 5/9 |
| 8 | 0.51 | 0.84 | 5/9 |
| 9 | 0.61 | 0.90 | 5/9 |
| 10 | 0.55 | 0.90 | 3/9 |

### Signals emitted per round (by type)

| Round | information | loyalty_pledge | price_warning | request | threat | Total |
|---|---|---|---|---|---|---|
| 1 | 9 | 4 | 1 | 4 | 0 | 18 |
| 2 | 9 | 3 | 0 | 6 | 0 | 18 |
| 3 | 7 | 6 | 4 | 1 | 0 | 18 |
| 4 | 7 | 8 | 2 | 1 | 0 | 18 |
| 5 | 6 | 6 | 4 | 2 | 0 | 18 |
| 6 | 6 | 9 | 1 | 2 | 0 | 18 |
| 7 | 4 | 6 | 4 | 3 | 1 | 18 |
| 8 | 8 | 7 | 2 | 1 | 0 | 18 |
| 9 | 5 | 7 | 3 | 2 | 1 | 18 |
| 10 | 10 | 4 | 4 | 0 | 0 | 18 |

### First explicit crisis/shortage/shock/emergency utterance

- **R1**, BoschAuto (signal): _COVID-19 lockdowns across Europe and North America are creating severe demand uncertainty. Automotive assembly plants shutting down globally—this is a demand destruction event, not a supply shortage. _


## 3. Engineering

### Per-round wall-clock + cost

| Round | Wall-clock | Cost | Events | Errors |
|---|---|---|---|---|
| 1 | 50.0s | $0.0949 | 31 | 0 |
| 2 | 57.6s | $0.1221 | 31 | 0 |
| 3 | 79.1s | $0.2309 | 39 | 0 |
| 4 | 89.7s | $0.2550 | 40 | 0 |
| 5 | 69.6s | $0.1614 | 31 | 0 |
| 6 | 70.0s | $0.1696 | 31 | 1 |
| 7 | 86.7s | $0.2801 | 40 | 2 |
| 8 | 103.9s | $0.3008 | 40 | 2 |
| 9 | 95.7s | $0.2941 | 40 | 2 |
| 10 | 94.1s | $0.2848 | 40 | 2 |
