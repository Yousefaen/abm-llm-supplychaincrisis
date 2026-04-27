# Comparison — `2026-04-22_baseline` vs `2026-04-22_scenario-rewrite`

- **A** (2026-04-22_baseline): baseline  persona=`hand-crafted`  commit=`9fc5f60`
- **B** (2026-04-22_scenario-rewrite): scenario-rewrite  persona=`hand-crafted`  commit=`7305d0a`

## Meta

| Metric | A | B |
|---|---|---|
| wall-clock (s) | 832.2 | 808.6 |
| total cost ($) | 2.3583 | 2.2268 |
| errors | 3 | 5 |

## Fill rates by tier

| Round | Tier | A | B | Δ |
|---|---|---|---|---|
| 1 | OEM | 0.70 | 0.86 | +0.16 |
| 1 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 1 | Designer | 1.00 | 1.00 | +0.00 |
| 1 | Foundry | 1.00 | 1.00 | +0.00 |
| 2 | OEM | 0.70 | 0.69 | -0.01 |
| 2 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 2 | Designer | 1.00 | 1.00 | +0.00 |
| 2 | Foundry | 1.00 | 1.00 | +0.00 |
| 3 | OEM | 0.50 | 0.63 | +0.13 |
| 3 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 3 | Designer | 1.00 | 1.00 | +0.00 |
| 3 | Foundry | 1.00 | 1.00 | +0.00 |
| 4 | OEM | 0.39 | 0.55 | +0.15 |
| 4 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 4 | Designer | 1.00 | 1.00 | +0.00 |
| 4 | Foundry | 1.00 | 1.00 | +0.00 |
| 5 | OEM | 0.28 | 0.46 | +0.18 |
| 5 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 5 | Designer | 1.00 | 1.00 | +0.00 |
| 5 | Foundry | 1.00 | 1.00 | +0.00 |
| 6 | OEM | 0.29 | 0.43 | +0.14 |
| 6 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 6 | Designer | 1.00 | 1.00 | +0.00 |
| 6 | Foundry | 1.00 | 1.00 | +0.00 |
| 7 | OEM | 0.31 | 0.71 | +0.40 |
| 7 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 7 | Designer | 1.00 | 1.00 | +0.00 |
| 7 | Foundry | 1.00 | 1.00 | +0.00 |
| 8 | OEM | 0.35 | 0.53 | +0.18 |
| 8 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 8 | Designer | 1.00 | 1.00 | +0.00 |
| 8 | Foundry | 1.00 | 1.00 | +0.00 |
| 9 | OEM | 0.35 | 0.21 | -0.14 |
| 9 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 9 | Designer | 1.00 | 1.00 | +0.00 |
| 9 | Foundry | 1.00 | 1.00 | +0.00 |
| 10 | OEM | 0.01 | 0.01 | -0.00 |
| 10 | Tier-1 | 1.00 | 1.00 | +0.00 |
| 10 | Designer | 1.00 | 1.00 | +0.00 |
| 10 | Foundry | 1.00 | 1.00 | +0.00 |

## Prices by tier ($/unit)

| Round | Tier | A | B | Δ |
|---|---|---|---|---|
| 1 | Foundry | 10.50 | 11.50 | +1.00 |
| 1 | Designer | 28.25 | 27.50 | -0.75 |
| 1 | Tier-1 | 60.00 | 51.00 | -9.00 |
| 2 | Foundry | 12.00 | 12.35 | +0.35 |
| 2 | Designer | 43.25 | 30.00 | -13.25 |
| 2 | Tier-1 | 65.25 | 55.00 | -10.25 |
| 3 | Foundry | 14.50 | 12.65 | -1.85 |
| 3 | Designer | 66.40 | 66.25 | -0.15 |
| 3 | Tier-1 | 77.25 | 63.00 | -14.25 |
| 4 | Foundry | 15.50 | 14.50 | -1.00 |
| 4 | Designer | 70.00 | 70.25 | +0.25 |
| 4 | Tier-1 | 89.75 | 70.00 | -19.75 |
| 5 | Foundry | 14.50 | 16.50 | +2.00 |
| 5 | Designer | 79.25 | 75.25 | -4.00 |
| 5 | Tier-1 | 95.00 | 78.00 | -17.00 |
| 6 | Foundry | 16.00 | 17.50 | +1.50 |
| 6 | Designer | 90.25 | 86.50 | -3.75 |
| 6 | Tier-1 | 98.00 | 81.00 | -17.00 |
| 7 | Foundry | 19.75 | 34.75 | +15.00 |
| 7 | Designer | 98.00 | 88.50 | -9.50 |
| 7 | Tier-1 | 98.00 | 87.50 | -10.50 |
| 8 | Foundry | 30.00 | 39.25 | +9.25 |
| 8 | Designer | 105.00 | 95.00 | -10.00 |
| 8 | Tier-1 | 90.00 | 86.00 | -4.00 |
| 9 | Foundry | 42.00 | 50.25 | +8.25 |
| 9 | Designer | 91.50 | 109.00 | +17.50 |
| 9 | Tier-1 | 88.50 | 105.00 | +16.50 |
| 10 | Foundry | 32.00 | 60.25 | +28.25 |
| 10 | Designer | 88.50 | 114.50 | +26.00 |
| 10 | Tier-1 | 82.00 | 100.00 | +18.00 |

## Bullwhip — stdev of OEM order totals

| Round | A | B | Δ |
|---|---|---|---|
| 1 | 65.4 | 81.7 | +16.3 |
| 2 | 152.0 | 299.0 | +146.9 |
| 3 | 355.3 | 119.0 | -236.3 |
| 4 | 547.3 | 131.0 | -416.3 |
| 5 | 676.0 | 56.0 | -620.0 |
| 6 | 386.2 | 106.6 | -279.6 |
| 7 | 282.4 | 60.4 | -222.0 |
| 8 | 169.4 | 177.6 | +8.2 |
| 9 | 136.1 | 236.7 | +100.6 |
| 10 | 43.4 | 36.6 | -6.9 |

## Emotional state — panicked+anxious / total

| Round | A | B |
|---|---|---|
| 1 | 0/9 | 1/9 |
| 2 | 1/9 | 1/9 |
| 3 | 1/9 | 1/9 |
| 4 | 3/9 | 1/9 |
| 5 | 5/9 | 4/9 |
| 6 | 5/9 | 1/9 |
| 7 | 6/9 | 5/9 |
| 8 | 6/9 | 3/9 |
| 9 | 5/9 | 5/9 |
| 10 | 5/9 | 5/9 |

## Crisis-vocabulary density (hits / total LLM texts)

| Round | A | B |
|---|---|---|
| 1 | 10/95 (11%) | 27/95 (28%) |
| 2 | 21/58 (36%) | 23/58 (40%) |
| 3 | 40/122 (33%) | 27/122 (22%) |
| 4 | 48/122 (39%) | 24/122 (20%) |
| 5 | 42/58 (72%) | 32/58 (55%) |
| 6 | 30/58 (52%) | 26/58 (45%) |
| 7 | 48/122 (39%) | 46/122 (38%) |
| 8 | 59/122 (48%) | 53/122 (43%) |
| 9 | 63/122 (52%) | 83/122 (68%) |
| 10 | 38/122 (31%) | 48/122 (39%) |

## Cumulative profit at end of run ($)

| Agent | A | B | Δ |
|---|---|---|---|
| ToyotaMotors | 67,182 | 88,526 | +21,343 |
| FordAuto | 13,028 | 75,853 | +62,824 |
| VolkswagenAG | 55,278 | 64,534 | +9,256 |
| BoschAuto | 284,544 | 251,822 | -32,722 |
| ContiParts | 218,568 | 222,015 | +3,447 |
| EuroChip | -8,042 | -9,022 | -980 |
| AmeriSemi | -17,594 | -9,973 | +7,622 |
| TaiwanSemi | -6,954 | -12,724 | -5,770 |
| KoreaSilicon | -4,473 | -3,679 | +793 |

## First explicit crisis utterance

- **A R1** EuroChip (buyer): _COVID-19 has collapsed automotive demand 40%, but my quarterly need remains ~360 units to serve BoschAuto (235) and ContiParts (176). I'm ordering 400 total units across two trusted foundries who've j_

- **B R1** FordAuto (signal): _In this crisis, Ford is doubling down on our partnership. We want preferential allocation from you, and in return, you'll have predictable volume commitments and long-term contracts once we stabilize._

