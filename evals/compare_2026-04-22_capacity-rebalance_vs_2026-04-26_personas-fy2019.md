# Comparison — `2026-04-22_capacity-rebalance` vs `2026-04-26_personas-fy2019`

- **A** (2026-04-22_capacity-rebalance): capacity-rebalance  persona=`hand-crafted`  commit=`a853e9d`
- **B** (2026-04-26_personas-fy2019): personas-fy2019  persona=`auto-fy2019`  commit=`eb07796`

## Meta

| Metric | A | B |
|---|---|---|
| wall-clock (s) | 796.3 | 780.5 |
| total cost ($) | 2.1936 | 2.2090 |
| errors | 2 | 1 |

## Fill rates by tier

| Round | Tier | A | B | Δ |
|---|---|---|---|---|
| 1 | OEM | 0.79 | 0.87 | +0.08 |
| 1 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 1 | Designer | 1.00 | 1.00 | +0.00 |
| 1 | Foundry | 1.00 | 1.00 | +0.00 |
| 2 | OEM | 0.76 | 0.66 | -0.10 |
| 2 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 2 | Designer | 1.00 | 1.00 | +0.00 |
| 2 | Foundry | 1.00 | 1.00 | +0.00 |
| 3 | OEM | 0.59 | 0.63 | +0.04 |
| 3 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 3 | Designer | 1.00 | 1.00 | +0.00 |
| 3 | Foundry | 1.00 | 1.00 | +0.00 |
| 4 | OEM | 0.39 | 0.53 | +0.13 |
| 4 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 4 | Designer | 1.00 | 1.00 | +0.00 |
| 4 | Foundry | 1.00 | 1.00 | +0.00 |
| 5 | OEM | 0.34 | 0.36 | +0.03 |
| 5 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 5 | Designer | 1.00 | 1.00 | +0.00 |
| 5 | Foundry | 1.00 | 1.00 | +0.00 |
| 6 | OEM | 0.19 | 0.42 | +0.23 |
| 6 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 6 | Designer | 1.00 | 1.00 | +0.00 |
| 6 | Foundry | 1.00 | 1.00 | +0.00 |
| 7 | OEM | 0.41 | 0.54 | +0.13 |
| 7 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 7 | Designer | 1.00 | 1.00 | +0.00 |
| 7 | Foundry | 1.00 | 1.00 | +0.00 |
| 8 | OEM | 0.00 | 0.29 | +0.29 |
| 8 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 8 | Designer | 1.00 | 1.00 | +0.00 |
| 8 | Foundry | 1.00 | 1.00 | +0.00 |
| 9 | OEM | 0.00 | 0.07 | +0.07 |
| 9 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 9 | Designer | 1.00 | 1.00 | +0.00 |
| 9 | Foundry | 1.00 | 1.00 | +0.00 |
| 10 | OEM | 0.75 | 0.31 | -0.44 |
| 10 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 10 | Designer | 1.00 | 1.00 | +0.00 |
| 10 | Foundry | 1.00 | 1.00 | +0.00 |

## Prices by tier ($/unit)

| Round | Tier | A | B | Δ |
|---|---|---|---|---|
| 1 | Foundry | 11.25 | 11.25 | +0.00 |
| 1 | Designer | 25.75 | 25.25 | -0.50 |
| 1 | Tier-1 | 60.00 | 62.25 | +2.25 |
| 2 | Foundry | 11.75 | 11.75 | +0.00 |
| 2 | Designer | 26.75 | 26.25 | -0.50 |
| 2 | Tier-1 | 65.25 | 67.00 | +1.75 |
| 3 | Foundry | 27.25 | 13.50 | -13.75 |
| 3 | Designer | 34.75 | 35.00 | +0.25 |
| 3 | Tier-1 | 69.50 | 71.00 | +1.50 |
| 4 | Foundry | 32.25 | 13.50 | -18.75 |
| 4 | Designer | 38.25 | 38.00 | -0.25 |
| 4 | Tier-1 | 73.50 | 76.00 | +2.50 |
| 5 | Foundry | 33.40 | 16.50 | -16.90 |
| 5 | Designer | 48.75 | 41.00 | -7.75 |
| 5 | Tier-1 | 83.50 | 93.00 | +9.50 |
| 6 | Foundry | 35.75 | 18.50 | -17.25 |
| 6 | Designer | 54.00 | 50.00 | -4.00 |
| 6 | Tier-1 | 90.25 | 98.75 | +8.50 |
| 7 | Foundry | 41.00 | 17.50 | -23.50 |
| 7 | Designer | 87.25 | 63.25 | -24.00 |
| 7 | Tier-1 | 90.25 | 109.00 | +18.75 |
| 8 | Foundry | 50.00 | 20.50 | -29.50 |
| 8 | Designer | 106.50 | 77.25 | -29.25 |
| 8 | Tier-1 | 100.25 | 116.00 | +15.75 |
| 9 | Foundry | 57.00 | 25.50 | -31.50 |
| 9 | Designer | 106.50 | 84.75 | -21.75 |
| 9 | Tier-1 | 111.75 | 128.00 | +16.25 |
| 10 | Foundry | 63.50 | 25.50 | -38.00 |
| 10 | Designer | 108.50 | 91.50 | -17.00 |
| 10 | Tier-1 | 128.25 | 122.50 | -5.75 |

## Bullwhip — stdev of OEM order totals

| Round | A | B | Δ |
|---|---|---|---|
| 1 | 118.8 | 121.0 | +2.3 |
| 2 | 242.6 | 296.4 | +53.8 |
| 3 | 265.0 | 438.5 | +173.5 |
| 4 | 217.3 | 423.3 | +206.0 |
| 5 | 130.3 | 191.1 | +60.8 |
| 6 | 75.7 | 66.6 | -9.0 |
| 7 | 43.9 | 62.7 | +18.8 |
| 8 | 24.3 | 81.4 | +57.1 |
| 9 | 61.3 | 58.9 | -2.3 |
| 10 | 27.1 | 36.1 | +9.0 |

## Emotional state — panicked+anxious / total

| Round | A | B |
|---|---|---|
| 1 | 1/9 | 1/9 |
| 2 | 1/9 | 1/9 |
| 3 | 1/9 | 1/9 |
| 4 | 2/9 | 1/9 |
| 5 | 5/9 | 3/9 |
| 6 | 2/9 | 1/9 |
| 7 | 5/9 | 5/9 |
| 8 | 5/9 | 4/9 |
| 9 | 5/9 | 5/9 |
| 10 | 3/9 | 4/9 |

## Crisis-vocabulary density (hits / total LLM texts)

| Round | A | B |
|---|---|---|
| 1 | 21/95 (22%) | 17/95 (18%) |
| 2 | 17/58 (29%) | 24/58 (41%) |
| 3 | 26/121 (21%) | 22/122 (18%) |
| 4 | 31/122 (25%) | 18/122 (15%) |
| 5 | 45/58 (78%) | 39/58 (67%) |
| 6 | 25/58 (43%) | 25/58 (43%) |
| 7 | 52/122 (43%) | 55/122 (45%) |
| 8 | 56/122 (46%) | 54/122 (44%) |
| 9 | 76/122 (62%) | 71/122 (58%) |
| 10 | 46/122 (38%) | 45/120 (38%) |

## Cumulative profit at end of run ($)

| Agent | A | B | Δ |
|---|---|---|---|
| ToyotaMotors | 74,370 | 63,518 | -10,852 |
| FordAuto | 26,130 | 22,448 | -3,682 |
| VolkswagenAG | 44,454 | 39,402 | -5,052 |
| BoschAuto | 126,491 | 183,074 | +56,583 |
| ContiParts | 135,935 | 231,282 | +95,347 |
| EuroChip | -9,908 | -12,466 | -2,558 |
| AmeriSemi | -6,714 | -3,783 | +2,932 |
| TaiwanSemi | -3,318 | -4,789 | -1,471 |
| KoreaSilicon | -19,467 | -2,142 | +17,325 |

## First explicit crisis utterance

- **A R1** BoschAuto (signal): _COVID-19 lockdowns across Europe and North America are creating severe demand uncertainty. Automotive assembly plants shutting down globally—this is a demand destruction event, not a supply shortage. _

- **B R1** VolkswagenAG (signal): _VW remains committed to our partnership through this crisis. We're maintaining current order volumes and won't panic-buy; we expect the same stable approach from you as we weather this together._

