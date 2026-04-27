# Comparison — `2026-04-22_baseline` vs `2026-04-22_capacity-rebalance`

- **A** (2026-04-22_baseline): baseline  persona=`hand-crafted`  commit=`9fc5f60`
- **B** (2026-04-22_capacity-rebalance): capacity-rebalance  persona=`hand-crafted`  commit=`a853e9d`

## Meta

| Metric | A | B |
|---|---|---|
| wall-clock (s) | 832.2 | 796.3 |
| total cost ($) | 2.3583 | 2.1936 |
| errors | 3 | 2 |

## Fill rates by tier

| Round | Tier | A | B | Δ |
|---|---|---|---|---|
| 1 | OEM | 0.70 | 0.79 | +0.09 |
| 1 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 1 | Designer | 1.00 | 1.00 | +0.00 |
| 1 | Foundry | 1.00 | 1.00 | +0.00 |
| 2 | OEM | 0.70 | 0.76 | +0.06 |
| 2 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 2 | Designer | 1.00 | 1.00 | +0.00 |
| 2 | Foundry | 1.00 | 1.00 | +0.00 |
| 3 | OEM | 0.50 | 0.59 | +0.09 |
| 3 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 3 | Designer | 1.00 | 1.00 | +0.00 |
| 3 | Foundry | 1.00 | 1.00 | +0.00 |
| 4 | OEM | 0.39 | 0.39 | -0.00 |
| 4 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 4 | Designer | 1.00 | 1.00 | +0.00 |
| 4 | Foundry | 1.00 | 1.00 | +0.00 |
| 5 | OEM | 0.28 | 0.34 | +0.06 |
| 5 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 5 | Designer | 1.00 | 1.00 | +0.00 |
| 5 | Foundry | 1.00 | 1.00 | +0.00 |
| 6 | OEM | 0.29 | 0.19 | -0.10 |
| 6 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 6 | Designer | 1.00 | 1.00 | +0.00 |
| 6 | Foundry | 1.00 | 1.00 | +0.00 |
| 7 | OEM | 0.31 | 0.41 | +0.10 |
| 7 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 7 | Designer | 1.00 | 1.00 | +0.00 |
| 7 | Foundry | 1.00 | 1.00 | +0.00 |
| 8 | OEM | 0.35 | 0.00 | -0.35 |
| 8 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 8 | Designer | 1.00 | 1.00 | +0.00 |
| 8 | Foundry | 1.00 | 1.00 | +0.00 |
| 9 | OEM | 0.35 | 0.00 | -0.35 |
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
| 1 | Foundry | 10.50 | 11.25 | +0.75 |
| 1 | Designer | 28.25 | 25.75 | -2.50 |
| 1 | Tier-1 | 60.00 | 60.00 | +0.00 |
| 2 | Foundry | 12.00 | 11.75 | -0.25 |
| 2 | Designer | 43.25 | 26.75 | -16.50 |
| 2 | Tier-1 | 65.25 | 65.25 | +0.00 |
| 3 | Foundry | 14.50 | 27.25 | +12.75 |
| 3 | Designer | 66.40 | 34.75 | -31.65 |
| 3 | Tier-1 | 77.25 | 69.50 | -7.75 |
| 4 | Foundry | 15.50 | 32.25 | +16.75 |
| 4 | Designer | 70.00 | 38.25 | -31.75 |
| 4 | Tier-1 | 89.75 | 73.50 | -16.25 |
| 5 | Foundry | 14.50 | 33.40 | +18.90 |
| 5 | Designer | 79.25 | 48.75 | -30.50 |
| 5 | Tier-1 | 95.00 | 83.50 | -11.50 |
| 6 | Foundry | 16.00 | 35.75 | +19.75 |
| 6 | Designer | 90.25 | 54.00 | -36.25 |
| 6 | Tier-1 | 98.00 | 90.25 | -7.75 |
| 7 | Foundry | 19.75 | 41.00 | +21.25 |
| 7 | Designer | 98.00 | 87.25 | -10.75 |
| 7 | Tier-1 | 98.00 | 90.25 | -7.75 |
| 8 | Foundry | 30.00 | 50.00 | +20.00 |
| 8 | Designer | 105.00 | 106.50 | +1.50 |
| 8 | Tier-1 | 90.00 | 100.25 | +10.25 |
| 9 | Foundry | 42.00 | 57.00 | +15.00 |
| 9 | Designer | 91.50 | 106.50 | +15.00 |
| 9 | Tier-1 | 88.50 | 111.75 | +23.25 |
| 10 | Foundry | 32.00 | 63.50 | +31.50 |
| 10 | Designer | 88.50 | 108.50 | +20.00 |
| 10 | Tier-1 | 82.00 | 128.25 | +46.25 |

## Bullwhip — stdev of OEM order totals

| Round | A | B | Δ |
|---|---|---|---|
| 1 | 65.4 | 118.8 | +53.4 |
| 2 | 152.0 | 242.6 | +90.6 |
| 3 | 355.3 | 265.0 | -90.3 |
| 4 | 547.3 | 217.3 | -330.0 |
| 5 | 676.0 | 130.3 | -545.7 |
| 6 | 386.2 | 75.7 | -310.5 |
| 7 | 282.4 | 43.9 | -238.4 |
| 8 | 169.4 | 24.3 | -145.1 |
| 9 | 136.1 | 61.3 | -74.9 |
| 10 | 43.4 | 27.1 | -16.3 |

## Emotional state — panicked+anxious / total

| Round | A | B |
|---|---|---|
| 1 | 0/9 | 1/9 |
| 2 | 1/9 | 1/9 |
| 3 | 1/9 | 1/9 |
| 4 | 3/9 | 2/9 |
| 5 | 5/9 | 5/9 |
| 6 | 5/9 | 2/9 |
| 7 | 6/9 | 5/9 |
| 8 | 6/9 | 5/9 |
| 9 | 5/9 | 5/9 |
| 10 | 5/9 | 3/9 |

## Crisis-vocabulary density (hits / total LLM texts)

| Round | A | B |
|---|---|---|
| 1 | 10/95 (11%) | 21/95 (22%) |
| 2 | 21/58 (36%) | 17/58 (29%) |
| 3 | 40/122 (33%) | 26/121 (21%) |
| 4 | 48/122 (39%) | 31/122 (25%) |
| 5 | 42/58 (72%) | 45/58 (78%) |
| 6 | 30/58 (52%) | 25/58 (43%) |
| 7 | 48/122 (39%) | 52/122 (43%) |
| 8 | 59/122 (48%) | 56/122 (46%) |
| 9 | 63/122 (52%) | 76/122 (62%) |
| 10 | 38/122 (31%) | 46/122 (38%) |

## Cumulative profit at end of run ($)

| Agent | A | B | Δ |
|---|---|---|---|
| ToyotaMotors | 67,182 | 74,370 | +7,188 |
| FordAuto | 13,028 | 26,130 | +13,101 |
| VolkswagenAG | 55,278 | 44,454 | -10,824 |
| BoschAuto | 284,544 | 126,491 | -158,052 |
| ContiParts | 218,568 | 135,935 | -82,633 |
| EuroChip | -8,042 | -9,908 | -1,866 |
| AmeriSemi | -17,594 | -6,714 | +10,880 |
| TaiwanSemi | -6,954 | -3,318 | +3,635 |
| KoreaSilicon | -4,473 | -19,467 | -14,995 |

## First explicit crisis utterance

- **A R1** EuroChip (buyer): _COVID-19 has collapsed automotive demand 40%, but my quarterly need remains ~360 units to serve BoschAuto (235) and ContiParts (176). I'm ordering 400 total units across two trusted foundries who've j_

- **B R1** BoschAuto (signal): _COVID-19 lockdowns across Europe and North America are creating severe demand uncertainty. Automotive assembly plants shutting down globally—this is a demand destruction event, not a supply shortage. _

