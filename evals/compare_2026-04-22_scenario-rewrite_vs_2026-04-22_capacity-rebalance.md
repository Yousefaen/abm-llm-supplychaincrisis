# Comparison — `2026-04-22_scenario-rewrite` vs `2026-04-22_capacity-rebalance`

- **A** (2026-04-22_scenario-rewrite): scenario-rewrite  persona=`hand-crafted`  commit=`7305d0a`
- **B** (2026-04-22_capacity-rebalance): capacity-rebalance  persona=`hand-crafted`  commit=`a853e9d`

## Meta

| Metric | A | B |
|---|---|---|
| wall-clock (s) | 808.6 | 796.3 |
| total cost ($) | 2.2268 | 2.1936 |
| errors | 5 | 2 |

## Fill rates by tier

| Round | Tier | A | B | Δ |
|---|---|---|---|---|
| 1 | OEM | 0.86 | 0.79 | -0.07 |
| 1 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 1 | Designer | 1.00 | 1.00 | +0.00 |
| 1 | Foundry | 1.00 | 1.00 | +0.00 |
| 2 | OEM | 0.69 | 0.76 | +0.07 |
| 2 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 2 | Designer | 1.00 | 1.00 | +0.00 |
| 2 | Foundry | 1.00 | 1.00 | +0.00 |
| 3 | OEM | 0.63 | 0.59 | -0.04 |
| 3 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 3 | Designer | 1.00 | 1.00 | +0.00 |
| 3 | Foundry | 1.00 | 1.00 | +0.00 |
| 4 | OEM | 0.55 | 0.39 | -0.16 |
| 4 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 4 | Designer | 1.00 | 1.00 | +0.00 |
| 4 | Foundry | 1.00 | 1.00 | +0.00 |
| 5 | OEM | 0.46 | 0.34 | -0.12 |
| 5 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 5 | Designer | 1.00 | 1.00 | +0.00 |
| 5 | Foundry | 1.00 | 1.00 | +0.00 |
| 6 | OEM | 0.43 | 0.19 | -0.24 |
| 6 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 6 | Designer | 1.00 | 1.00 | +0.00 |
| 6 | Foundry | 1.00 | 1.00 | +0.00 |
| 7 | OEM | 0.71 | 0.41 | -0.30 |
| 7 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 7 | Designer | 1.00 | 1.00 | +0.00 |
| 7 | Foundry | 1.00 | 1.00 | +0.00 |
| 8 | OEM | 0.53 | 0.00 | -0.53 |
| 8 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 8 | Designer | 1.00 | 1.00 | +0.00 |
| 8 | Foundry | 1.00 | 1.00 | +0.00 |
| 9 | OEM | 0.21 | 0.00 | -0.21 |
| 9 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 9 | Designer | 1.00 | 1.00 | +0.00 |
| 9 | Foundry | 1.00 | 1.00 | +0.00 |
| 10 | OEM | 0.01 | 0.75 | +0.74 |
| 10 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 10 | Designer | 1.00 | 1.00 | +0.00 |
| 10 | Foundry | 1.00 | 1.00 | +0.00 |

## Prices by tier ($/unit)

| Round | Tier | A | B | Δ |
|---|---|---|---|---|
| 1 | Foundry | 11.50 | 11.25 | -0.25 |
| 1 | Designer | 27.50 | 25.75 | -1.75 |
| 1 | Tier-1 | 51.00 | 60.00 | +9.00 |
| 2 | Foundry | 12.35 | 11.75 | -0.60 |
| 2 | Designer | 30.00 | 26.75 | -3.25 |
| 2 | Tier-1 | 55.00 | 65.25 | +10.25 |
| 3 | Foundry | 12.65 | 27.25 | +14.60 |
| 3 | Designer | 66.25 | 34.75 | -31.50 |
| 3 | Tier-1 | 63.00 | 69.50 | +6.50 |
| 4 | Foundry | 14.50 | 32.25 | +17.75 |
| 4 | Designer | 70.25 | 38.25 | -32.00 |
| 4 | Tier-1 | 70.00 | 73.50 | +3.50 |
| 5 | Foundry | 16.50 | 33.40 | +16.90 |
| 5 | Designer | 75.25 | 48.75 | -26.50 |
| 5 | Tier-1 | 78.00 | 83.50 | +5.50 |
| 6 | Foundry | 17.50 | 35.75 | +18.25 |
| 6 | Designer | 86.50 | 54.00 | -32.50 |
| 6 | Tier-1 | 81.00 | 90.25 | +9.25 |
| 7 | Foundry | 34.75 | 41.00 | +6.25 |
| 7 | Designer | 88.50 | 87.25 | -1.25 |
| 7 | Tier-1 | 87.50 | 90.25 | +2.75 |
| 8 | Foundry | 39.25 | 50.00 | +10.75 |
| 8 | Designer | 95.00 | 106.50 | +11.50 |
| 8 | Tier-1 | 86.00 | 100.25 | +14.25 |
| 9 | Foundry | 50.25 | 57.00 | +6.75 |
| 9 | Designer | 109.00 | 106.50 | -2.50 |
| 9 | Tier-1 | 105.00 | 111.75 | +6.75 |
| 10 | Foundry | 60.25 | 63.50 | +3.25 |
| 10 | Designer | 114.50 | 108.50 | -6.00 |
| 10 | Tier-1 | 100.00 | 128.25 | +28.25 |

## Bullwhip — stdev of OEM order totals

| Round | A | B | Δ |
|---|---|---|---|
| 1 | 81.7 | 118.8 | +37.1 |
| 2 | 299.0 | 242.6 | -56.4 |
| 3 | 119.0 | 265.0 | +146.0 |
| 4 | 131.0 | 217.3 | +86.3 |
| 5 | 56.0 | 130.3 | +74.3 |
| 6 | 106.6 | 75.7 | -30.9 |
| 7 | 60.4 | 43.9 | -16.5 |
| 8 | 177.6 | 24.3 | -153.3 |
| 9 | 236.7 | 61.3 | -175.5 |
| 10 | 36.6 | 27.1 | -9.5 |

## Emotional state — panicked+anxious / total

| Round | A | B |
|---|---|---|
| 1 | 1/9 | 1/9 |
| 2 | 1/9 | 1/9 |
| 3 | 1/9 | 1/9 |
| 4 | 1/9 | 2/9 |
| 5 | 4/9 | 5/9 |
| 6 | 1/9 | 2/9 |
| 7 | 5/9 | 5/9 |
| 8 | 3/9 | 5/9 |
| 9 | 5/9 | 5/9 |
| 10 | 5/9 | 3/9 |

## Crisis-vocabulary density (hits / total LLM texts)

| Round | A | B |
|---|---|---|
| 1 | 27/95 (28%) | 21/95 (22%) |
| 2 | 23/58 (40%) | 17/58 (29%) |
| 3 | 27/122 (22%) | 26/121 (21%) |
| 4 | 24/122 (20%) | 31/122 (25%) |
| 5 | 32/58 (55%) | 45/58 (78%) |
| 6 | 26/58 (45%) | 25/58 (43%) |
| 7 | 46/122 (38%) | 52/122 (43%) |
| 8 | 53/122 (43%) | 56/122 (46%) |
| 9 | 83/122 (68%) | 76/122 (62%) |
| 10 | 48/122 (39%) | 46/122 (38%) |

## Cumulative profit at end of run ($)

| Agent | A | B | Δ |
|---|---|---|---|
| ToyotaMotors | 88,526 | 74,370 | -14,156 |
| FordAuto | 75,853 | 26,130 | -49,724 |
| VolkswagenAG | 64,534 | 44,454 | -20,080 |
| BoschAuto | 251,822 | 126,491 | -125,331 |
| ContiParts | 222,015 | 135,935 | -86,080 |
| EuroChip | -9,022 | -9,908 | -886 |
| AmeriSemi | -9,973 | -6,714 | +3,258 |
| TaiwanSemi | -12,724 | -3,318 | +9,406 |
| KoreaSilicon | -3,679 | -19,467 | -15,788 |

## First explicit crisis utterance

- **A R1** FordAuto (signal): _In this crisis, Ford is doubling down on our partnership. We want preferential allocation from you, and in return, you'll have predictable volume commitments and long-term contracts once we stabilize._

- **B R1** BoschAuto (signal): _COVID-19 lockdowns across Europe and North America are creating severe demand uncertainty. Automotive assembly plants shutting down globally—this is a demand destruction event, not a supply shortage. _

