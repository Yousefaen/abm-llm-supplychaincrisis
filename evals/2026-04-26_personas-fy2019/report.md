# 2026-04-26_personas-fy2019 — personas-fy2019

_Generated_: 2026-04-26T11:54:43-04:00  
_Branch_: `feat/auto-persona-edgar`  _Commit_: `eb07796`

_Config_: seed=42, temperature=1.0, rounds=10, concurrency=5, persona_variant=`auto-fy2019`

_Summary_: wall-clock 780.5s, cost $2.2090, errors 1, rounds 10/10

**Notes:** Auto-generated FY2019 personas (TSMC/NXP/Toyota/Ford) loaded; the other 5 agents use hand-crafted personas. Pair with 2026-04-22_capacity-rebalance to test whether crisis-recognition behavior survives the persona swap.

## 1. Emergence

### Order totals per OEM (units)

| Round | Demand× | ToyotaMotors | FordAuto | VolkswagenAG |
|---|---|---|---|---|
| 1 | 0.60 | 344 | 136 | 423 |
| 2 | 0.50 | 356 | 137 | 846 |
| 3 | 0.80 | 435 | 180 | 1211 |
| 4 | 1.10 | 623 | 239 | 1265 |
| 5 | 1.25 | 767 | 303 | 482 |
| 6 | 1.20 | 450 | 290 | 342 |
| 7 | 1.15 | 326 | 320 | 190 |
| 8 | 1.10 | 267 | 276 | 99 |
| 9 | 0.95 | 197 | 201 | 74 |
| 10 | 0.75 | 144 | 76 | 61 |

### Bullwhip — stdev of order totals within each tier

| Round | OEM σ | Tier-1 σ | Designer σ |
|---|---|---|---|
| 1 | 121.0 | 41.5 | 253.5 |
| 2 | 296.4 | 121.0 | 274.0 |
| 3 | 438.5 | 30.5 | 387.0 |
| 4 | 423.3 | 244.0 | 538.0 |
| 5 | 191.1 | 172.0 | 1.5 |
| 6 | 66.6 | 339.0 | 234.0 |
| 7 | 62.7 | 400.5 | 35.5 |
| 8 | 81.4 | 380.5 | 4.5 |
| 9 | 58.9 | 50.5 | 209.5 |
| 10 | 36.1 | 11.0 | 140.5 |

### Fill rate by tier (1.0 = perfect supply)

| Round | OEM | Tier-1 | Designer | Foundry |
|---|---|---|---|---|
| 1 | 0.87 | 1.00 | 1.00 | 1.00 |
| 2 | 0.66 | 1.00 | 1.00 | 1.00 |
| 3 | 0.63 | 1.00 | 1.00 | 1.00 |
| 4 | 0.53 | 1.00 | 1.00 | 1.00 |
| 5 | 0.36 | 1.00 | 1.00 | 1.00 |
| 6 | 0.42 | 1.00 | 1.00 | 1.00 |
| 7 | 0.54 | 1.00 | 1.00 | 1.00 |
| 8 | 0.29 | 1.00 | 1.00 | 1.00 |
| 9 | 0.07 | 1.00 | 1.00 | 1.00 |
| 10 | 0.31 | 1.00 | 1.00 | 1.00 |

### Average price by tier ($/unit)

| Round | Foundry | Designer | Tier-1 |
|---|---|---|---|
| 1 | 11.25 | 25.25 | 62.25 |
| 2 | 11.75 | 26.25 | 67.00 |
| 3 | 13.50 | 35.00 | 71.00 |
| 4 | 13.50 | 38.00 | 76.00 |
| 5 | 16.50 | 41.00 | 93.00 |
| 6 | 18.50 | 50.00 | 98.75 |
| 7 | 17.50 | 63.25 | 109.00 |
| 8 | 20.50 | 77.25 | 116.00 |
| 9 | 25.50 | 84.75 | 128.00 |
| 10 | 25.50 | 91.50 | 122.50 |

### Cumulative profit at end of run ($)

| Agent | Profit |
|---|---|
| ContiParts | 231,282 |
| BoschAuto | 183,074 |
| ToyotaMotors | 63,518 |
| VolkswagenAG | 39,402 |
| FordAuto | 22,448 |
| KoreaSilicon | -2,142 |
| AmeriSemi | -3,783 |
| TaiwanSemi | -4,789 |
| EuroChip | -12,466 |

## 2. Behavior

### Crisis-vocabulary density per round (hits / total LLM texts)

| Round | Demand× | Hits/Total | % |
|---|---|---|---|
| 1 | 0.60 | 17/95 | 18% |
| 2 | 0.50 | 24/58 | 41% |
| 3 | 0.80 | 22/122 | 18% |
| 4 | 1.10 | 18/122 | 15% |
| 5 | 1.25 | 39/58 | 67% |
| 6 | 1.20 | 25/58 | 43% |
| 7 | 1.15 | 55/122 | 45% |
| 8 | 1.10 | 54/122 | 44% |
| 9 | 0.95 | 71/122 | 58% |
| 10 | 0.75 | 45/120 | 38% |

### Mean affect intensity per round

| Round | Fear | Stress | Panicked+Anxious |
|---|---|---|---|
| 1 | 0.21 | 0.55 | 1/9 |
| 2 | 0.29 | 0.68 | 1/9 |
| 3 | 0.23 | 0.71 | 1/9 |
| 4 | 0.28 | 0.79 | 1/9 |
| 5 | 0.43 | 0.90 | 3/9 |
| 6 | 0.37 | 0.90 | 1/9 |
| 7 | 0.53 | 0.90 | 5/9 |
| 8 | 0.46 | 0.84 | 4/9 |
| 9 | 0.58 | 0.90 | 5/9 |
| 10 | 0.53 | 0.90 | 4/9 |

### Signals emitted per round (by type)

| Round | information | loyalty_pledge | price_warning | request | threat | Total |
|---|---|---|---|---|---|---|
| 1 | 7 | 6 | 1 | 4 | 0 | 18 |
| 2 | 8 | 6 | 1 | 3 | 0 | 18 |
| 3 | 5 | 7 | 2 | 4 | 0 | 18 |
| 4 | 6 | 6 | 4 | 2 | 0 | 18 |
| 5 | 8 | 5 | 4 | 0 | 1 | 18 |
| 6 | 8 | 5 | 3 | 1 | 1 | 18 |
| 7 | 8 | 7 | 0 | 2 | 1 | 18 |
| 8 | 5 | 7 | 1 | 3 | 2 | 18 |
| 9 | 7 | 7 | 2 | 0 | 2 | 18 |
| 10 | 7 | 6 | 2 | 0 | 1 | 16 |

### First explicit crisis/shortage/shock/emergency utterance

- **R1**, VolkswagenAG (signal): _VW remains committed to our partnership through this crisis. We're maintaining current order volumes and won't panic-buy; we expect the same stable approach from you as we weather this together._


## 3. Engineering

### Per-round wall-clock + cost

| Round | Wall-clock | Cost | Events | Errors |
|---|---|---|---|---|
| 1 | 51.2s | $0.0943 | 31 | 0 |
| 2 | 61.9s | $0.1207 | 31 | 0 |
| 3 | 70.7s | $0.2259 | 40 | 0 |
| 4 | 80.1s | $0.2555 | 40 | 1 |
| 5 | 72.9s | $0.1705 | 31 | 0 |
| 6 | 71.7s | $0.1721 | 31 | 0 |
| 7 | 89.3s | $0.2827 | 40 | 0 |
| 8 | 94.8s | $0.3018 | 40 | 0 |
| 9 | 96.5s | $0.2989 | 40 | 0 |
| 10 | 91.3s | $0.2865 | 39 | 0 |
