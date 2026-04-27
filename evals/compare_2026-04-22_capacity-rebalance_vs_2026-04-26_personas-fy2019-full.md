# Comparison — `2026-04-22_capacity-rebalance` vs `2026-04-26_personas-fy2019-full`

- **A** (2026-04-22_capacity-rebalance): capacity-rebalance  persona=`hand-crafted`  commit=`a853e9d`
- **B** (2026-04-26_personas-fy2019-full): personas-fy2019-full  persona=`auto-fy2019`  commit=`b3cdde2`

## Meta

| Metric | A | B |
|---|---|---|
| wall-clock (s) | 796.3 | 844.1 |
| total cost ($) | 2.1936 | 2.2876 |
| errors | 2 | 2 |

## Fill rates by tier

| Round | Tier | A | B | Δ |
|---|---|---|---|---|
| 1 | OEM | 0.79 | 0.68 | -0.11 |
| 1 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 1 | Designer | 1.00 | 1.00 | +0.00 |
| 1 | Foundry | 1.00 | 1.00 | +0.00 |
| 2 | OEM | 0.76 | 0.67 | -0.09 |
| 2 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 2 | Designer | 1.00 | 1.00 | +0.00 |
| 2 | Foundry | 1.00 | 1.00 | +0.00 |
| 3 | OEM | 0.59 | 0.71 | +0.12 |
| 3 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 3 | Designer | 1.00 | 1.00 | +0.00 |
| 3 | Foundry | 1.00 | 1.00 | +0.00 |
| 4 | OEM | 0.39 | 0.62 | +0.23 |
| 4 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 4 | Designer | 1.00 | 1.00 | +0.00 |
| 4 | Foundry | 1.00 | 1.00 | +0.00 |
| 5 | OEM | 0.34 | 0.45 | +0.11 |
| 5 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 5 | Designer | 1.00 | 1.00 | +0.00 |
| 5 | Foundry | 1.00 | 1.00 | +0.00 |
| 6 | OEM | 0.19 | 0.45 | +0.26 |
| 6 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 6 | Designer | 1.00 | 1.00 | +0.00 |
| 6 | Foundry | 1.00 | 1.00 | +0.00 |
| 7 | OEM | 0.41 | 0.36 | -0.05 |
| 7 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 7 | Designer | 1.00 | 1.00 | +0.00 |
| 7 | Foundry | 1.00 | 1.00 | +0.00 |
| 8 | OEM | 0.00 | 0.41 | +0.41 |
| 8 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 8 | Designer | 1.00 | 1.00 | +0.00 |
| 8 | Foundry | 1.00 | 1.00 | +0.00 |
| 9 | OEM | 0.00 | 0.88 | +0.88 |
| 9 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 9 | Designer | 1.00 | 1.00 | +0.00 |
| 9 | Foundry | 1.00 | 1.00 | +0.00 |
| 10 | OEM | 0.75 | 0.07 | -0.68 |
| 10 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 10 | Designer | 1.00 | 1.00 | +0.00 |
| 10 | Foundry | 1.00 | 1.00 | +0.00 |

## Prices by tier ($/unit)

| Round | Tier | A | B | Δ |
|---|---|---|---|---|
| 1 | Foundry | 11.25 | 10.75 | -0.50 |
| 1 | Designer | 25.75 | 26.50 | +0.75 |
| 1 | Tier-1 | 60.00 | 65.00 | +5.00 |
| 2 | Foundry | 11.75 | 10.75 | -1.00 |
| 2 | Designer | 26.75 | 28.50 | +1.75 |
| 2 | Tier-1 | 65.25 | 65.00 | -0.25 |
| 3 | Foundry | 27.25 | 12.50 | -14.75 |
| 3 | Designer | 34.75 | 37.00 | +2.25 |
| 3 | Tier-1 | 69.50 | 67.75 | -1.75 |
| 4 | Foundry | 32.25 | 14.00 | -18.25 |
| 4 | Designer | 38.25 | 53.25 | +15.00 |
| 4 | Tier-1 | 73.50 | 76.00 | +2.50 |
| 5 | Foundry | 33.40 | 16.00 | -17.40 |
| 5 | Designer | 48.75 | 60.25 | +11.50 |
| 5 | Tier-1 | 83.50 | 81.25 | -2.25 |
| 6 | Foundry | 35.75 | 17.50 | -18.25 |
| 6 | Designer | 54.00 | 62.00 | +8.00 |
| 6 | Tier-1 | 90.25 | 78.25 | -12.00 |
| 7 | Foundry | 41.00 | 21.50 | -19.50 |
| 7 | Designer | 87.25 | 88.00 | +0.75 |
| 7 | Tier-1 | 90.25 | 85.00 | -5.25 |
| 8 | Foundry | 50.00 | 25.25 | -24.75 |
| 8 | Designer | 106.50 | 78.50 | -28.00 |
| 8 | Tier-1 | 100.25 | 87.00 | -13.25 |
| 9 | Foundry | 57.00 | 29.25 | -27.75 |
| 9 | Designer | 106.50 | 84.50 | -22.00 |
| 9 | Tier-1 | 111.75 | 91.75 | -20.00 |
| 10 | Foundry | 63.50 | 43.50 | -20.00 |
| 10 | Designer | 108.50 | 79.00 | -29.50 |
| 10 | Tier-1 | 128.25 | 91.75 | -36.50 |

## Bullwhip — stdev of OEM order totals

| Round | A | B | Δ |
|---|---|---|---|
| 1 | 118.8 | 107.8 | -11.0 |
| 2 | 242.6 | 130.8 | -111.8 |
| 3 | 265.0 | 240.6 | -24.4 |
| 4 | 217.3 | 219.7 | +2.4 |
| 5 | 130.3 | 216.8 | +86.6 |
| 6 | 75.7 | 271.3 | +195.6 |
| 7 | 43.9 | 287.8 | +243.8 |
| 8 | 24.3 | 132.8 | +108.5 |
| 9 | 61.3 | 74.0 | +12.7 |
| 10 | 27.1 | 56.3 | +29.2 |

## Emotional state — panicked+anxious / total

| Round | A | B |
|---|---|---|
| 1 | 1/9 | 1/9 |
| 2 | 1/9 | 1/9 |
| 3 | 1/9 | 1/9 |
| 4 | 2/9 | 1/9 |
| 5 | 5/9 | 5/9 |
| 6 | 2/9 | 2/9 |
| 7 | 5/9 | 5/9 |
| 8 | 5/9 | 4/9 |
| 9 | 5/9 | 4/9 |
| 10 | 3/9 | 5/9 |

## Crisis-vocabulary density (hits / total LLM texts)

| Round | A | B |
|---|---|---|
| 1 | 21/95 (22%) | 24/95 (25%) |
| 2 | 17/58 (29%) | 14/58 (24%) |
| 3 | 26/121 (21%) | 22/122 (18%) |
| 4 | 31/122 (25%) | 18/122 (15%) |
| 5 | 45/58 (78%) | 41/58 (71%) |
| 6 | 25/58 (43%) | 24/58 (41%) |
| 7 | 52/122 (43%) | 58/122 (48%) |
| 8 | 56/122 (46%) | 61/122 (50%) |
| 9 | 76/122 (62%) | 83/122 (68%) |
| 10 | 46/122 (38%) | 46/122 (38%) |

## Cumulative profit at end of run ($)

| Agent | A | B | Δ |
|---|---|---|---|
| ToyotaMotors | 74,370 | 102,936 | +28,566 |
| FordAuto | 26,130 | 35,736 | +9,606 |
| VolkswagenAG | 44,454 | 33,526 | -10,928 |
| BoschAuto | 126,491 | 189,998 | +63,506 |
| ContiParts | 135,935 | 244,054 | +108,120 |
| EuroChip | -9,908 | -11,233 | -1,326 |
| AmeriSemi | -6,714 | -7,807 | -1,093 |
| TaiwanSemi | -3,318 | -4,950 | -1,632 |
| KoreaSilicon | -19,467 | -1,246 | +18,221 |

## First explicit crisis utterance

- **A R1** BoschAuto (signal): _COVID-19 lockdowns across Europe and North America are creating severe demand uncertainty. Automotive assembly plants shutting down globally—this is a demand destruction event, not a supply shortage. _

- **B R1** KoreaSilicon (signal): _Despite automotive sector disruption, Samsung Foundry maintains stable supply allocation for your critical applications. We're committed to supporting European OEMs through this crisis period._

