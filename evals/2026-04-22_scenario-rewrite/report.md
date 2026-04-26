# 2026-04-22_scenario-rewrite — scenario-rewrite

_Generated_: 2026-04-25T22:26:57-04:00  
_Branch_: `main`  _Commit_: `7305d0a`

_Config_: seed=42, temperature=1.0, rounds=10, concurrency=5, persona_variant=`hand-crafted`

_Summary_: wall-clock 808.6s, cost $2.2268, errors 5, rounds 10/10

**Notes:** After rewriting SCENARIO_EVENTS to remove outcome descriptions (narrative-leakage fix). Pair with 2026-04-22_baseline.

## 1. Emergence

### Order totals per OEM (units)

| Round | Demand× | ToyotaMotors | FordAuto | VolkswagenAG |
|---|---|---|---|---|
| 1 | 0.60 | 310 | 259 | 452 |
| 2 | 0.50 | 332 | 230 | 909 |
| 3 | 0.80 | 384 | 333 | 607 |
| 4 | 1.10 | 483 | 537 | 784 |
| 5 | 1.25 | 600 | 673 | 536 |
| 6 | 1.20 | 409 | 606 | 359 |
| 7 | 1.15 | 214 | 361 | 273 |
| 8 | 1.10 | 208 | 576 | 191 |
| 9 | 0.95 | 228 | 613 | 45 |
| 10 | 0.75 | 101 | 188 | 163 |

### Bullwhip — stdev of order totals within each tier

| Round | OEM σ | Tier-1 σ | Designer σ |
|---|---|---|---|
| 1 | 81.7 | 2.5 | 68.0 |
| 2 | 299.0 | 42.0 | 54.0 |
| 3 | 119.0 | 87.0 | 264.5 |
| 4 | 131.0 | 226.0 | 512.5 |
| 5 | 56.0 | 49.0 | 94.5 |
| 6 | 106.6 | 146.5 | 24.0 |
| 7 | 60.4 | 245.5 | 40.5 |
| 8 | 177.6 | 214.0 | 70.5 |
| 9 | 236.7 | 175.5 | 222.0 |
| 10 | 36.6 | 154.0 | 228.0 |

### Fill rate by tier (1.0 = perfect supply)

| Round | OEM | Tier-1 | Designer | Foundry |
|---|---|---|---|---|
| 1 | 0.86 | 1.00 | 1.00 | 1.00 |
| 2 | 0.69 | 1.00 | 1.00 | 1.00 |
| 3 | 0.63 | 1.00 | 1.00 | 1.00 |
| 4 | 0.55 | 1.00 | 1.00 | 1.00 |
| 5 | 0.46 | 1.00 | 1.00 | 1.00 |
| 6 | 0.43 | 1.00 | 1.00 | 1.00 |
| 7 | 0.71 | 1.00 | 1.00 | 1.00 |
| 8 | 0.53 | 1.00 | 1.00 | 1.00 |
| 9 | 0.21 | 1.00 | 1.00 | 1.00 |
| 10 | 0.01 | 1.00 | 1.00 | 1.00 |

### Average price by tier ($/unit)

| Round | Foundry | Designer | Tier-1 |
|---|---|---|---|
| 1 | 11.50 | 27.50 | 51.00 |
| 2 | 12.35 | 30.00 | 55.00 |
| 3 | 12.65 | 66.25 | 63.00 |
| 4 | 14.50 | 70.25 | 70.00 |
| 5 | 16.50 | 75.25 | 78.00 |
| 6 | 17.50 | 86.50 | 81.00 |
| 7 | 34.75 | 88.50 | 87.50 |
| 8 | 39.25 | 95.00 | 86.00 |
| 9 | 50.25 | 109.00 | 105.00 |
| 10 | 60.25 | 114.50 | 100.00 |

### Cumulative profit at end of run ($)

| Agent | Profit |
|---|---|
| BoschAuto | 251,822 |
| ContiParts | 222,015 |
| ToyotaMotors | 88,526 |
| FordAuto | 75,853 |
| VolkswagenAG | 64,534 |
| KoreaSilicon | -3,679 |
| EuroChip | -9,022 |
| AmeriSemi | -9,973 |
| TaiwanSemi | -12,724 |

## 2. Behavior

### Crisis-vocabulary density per round (hits / total LLM texts)

| Round | Demand× | Hits/Total | % |
|---|---|---|---|
| 1 | 0.60 | 27/95 | 28% |
| 2 | 0.50 | 23/58 | 40% |
| 3 | 0.80 | 27/122 | 22% |
| 4 | 1.10 | 24/122 | 20% |
| 5 | 1.25 | 32/58 | 55% |
| 6 | 1.20 | 26/58 | 45% |
| 7 | 1.15 | 46/122 | 38% |
| 8 | 1.10 | 53/122 | 43% |
| 9 | 0.95 | 83/122 | 68% |
| 10 | 0.75 | 48/122 | 39% |

### Mean affect intensity per round

| Round | Fear | Stress | Panicked+Anxious |
|---|---|---|---|
| 1 | 0.21 | 0.55 | 1/9 |
| 2 | 0.28 | 0.68 | 1/9 |
| 3 | 0.23 | 0.71 | 1/9 |
| 4 | 0.27 | 0.78 | 1/9 |
| 5 | 0.43 | 0.90 | 4/9 |
| 6 | 0.37 | 0.90 | 1/9 |
| 7 | 0.53 | 0.90 | 5/9 |
| 8 | 0.45 | 0.84 | 3/9 |
| 9 | 0.58 | 0.90 | 5/9 |
| 10 | 0.57 | 0.90 | 5/9 |

### Signals emitted per round (by type)

| Round | information | loyalty_pledge | price_warning | request | threat | Total |
|---|---|---|---|---|---|---|
| 1 | 8 | 7 | 0 | 3 | 0 | 18 |
| 2 | 9 | 6 | 0 | 3 | 0 | 18 |
| 3 | 8 | 6 | 2 | 2 | 0 | 18 |
| 4 | 6 | 7 | 2 | 3 | 0 | 18 |
| 5 | 6 | 7 | 4 | 1 | 0 | 18 |
| 6 | 9 | 6 | 1 | 1 | 1 | 18 |
| 7 | 9 | 6 | 1 | 1 | 1 | 18 |
| 8 | 9 | 7 | 2 | 0 | 0 | 18 |
| 9 | 7 | 4 | 4 | 2 | 1 | 18 |
| 10 | 9 | 3 | 5 | 1 | 0 | 18 |

### First explicit crisis/shortage/shock/emergency utterance

- **R1**, FordAuto (signal): _In this crisis, Ford is doubling down on our partnership. We want preferential allocation from you, and in return, you'll have predictable volume commitments and long-term contracts once we stabilize._


## 3. Engineering

### Per-round wall-clock + cost

| Round | Wall-clock | Cost | Events | Errors |
|---|---|---|---|---|
| 1 | 53.3s | $0.0937 | 31 | 0 |
| 2 | 67.3s | $0.1205 | 31 | 0 |
| 3 | 86.1s | $0.2331 | 40 | 0 |
| 4 | 77.7s | $0.2503 | 40 | 0 |
| 5 | 75.2s | $0.1648 | 31 | 0 |
| 6 | 67.6s | $0.1641 | 31 | 0 |
| 7 | 90.6s | $0.2851 | 40 | 1 |
| 8 | 100.5s | $0.3066 | 40 | 4 |
| 9 | 96.6s | $0.3036 | 40 | 4 |
| 10 | 93.7s | $0.3051 | 40 | 5 |
