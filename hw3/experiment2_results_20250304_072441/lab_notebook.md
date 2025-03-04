# Lab Notebook: Experiment 2

## Experimental Setup

- Duration per configuration: 60 seconds
- Four configurations tested:
  1. Baseline (default parameters)
  2. Smaller variation in clock cycles
  3. Smaller probability of internal events
  4. Both modifications combined

## Observations

### Configuration: baseline

**Parameters:**
- Clock Rate Range: 1-6 ticks/second
- Internal Event Probability: 0.8

**Actual Clock Rates:**

- Machine 1: 3 ticks/second
- Machine 2: 5 ticks/second
- Machine 3: 6 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 2
- Ending Clock Value: 363
- Max Jump: 9
- Average Jump: 1.93

Machine 2:
- Starting Clock Value: 1
- Ending Clock Value: 364
- Max Jump: 5
- Average Jump: 1.17

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 365
- Max Jump: 2
- Average Jump: 0.96

**Event Distribution:**

Machine 1:
- Total Events: 188
- Internal Events: 50 (26.6%)
- Send Events: 43 (22.9%)
- Receive Events: 95 (50.5%)

Machine 2:
- Total Events: 312
- Internal Events: 155 (49.7%)
- Send Events: 83 (26.6%)
- Receive Events: 74 (23.7%)

Machine 3:
- Total Events: 381
- Internal Events: 215 (56.4%)
- Send Events: 105 (27.6%)
- Receive Events: 61 (16.0%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 2.0
- Average Queue Length: 0.24
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 1.0
- Average Queue Length: 0.05
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 1.0
- Average Queue Length: 0.02
- Median Queue Length: 0.00

### Configuration: smaller_clock_variation

**Parameters:**
- Clock Rate Range: 3-4 ticks/second
- Internal Event Probability: 0.8

**Actual Clock Rates:**

- Machine 1: 4 ticks/second
- Machine 2: 3 ticks/second
- Machine 3: 3 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 2
- Ending Clock Value: 239
- Max Jump: 2
- Average Jump: 0.94

Machine 2:
- Starting Clock Value: 1
- Ending Clock Value: 239
- Max Jump: 7
- Average Jump: 1.27

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 237
- Max Jump: 6
- Average Jump: 1.30

**Event Distribution:**

Machine 1:
- Total Events: 254
- Internal Events: 136 (53.5%)
- Send Events: 72 (28.3%)
- Receive Events: 46 (18.1%)

Machine 2:
- Total Events: 189
- Internal Events: 90 (47.6%)
- Send Events: 52 (27.5%)
- Receive Events: 47 (24.9%)

Machine 3:
- Total Events: 183
- Internal Events: 88 (48.1%)
- Send Events: 32 (17.5%)
- Receive Events: 63 (34.4%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 1.0
- Average Queue Length: 0.04
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 1.0
- Average Queue Length: 0.06
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 2.0
- Average Queue Length: 0.22
- Median Queue Length: 0.00

### Configuration: smaller_internal_prob

**Parameters:**
- Clock Rate Range: 1-6 ticks/second
- Internal Event Probability: 0.4

**Actual Clock Rates:**

- Machine 1: 2 ticks/second
- Machine 2: 1 ticks/second
- Machine 3: 3 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 2
- Ending Clock Value: 178
- Max Jump: 5
- Average Jump: 1.38

Machine 2:
- Starting Clock Value: 2
- Ending Clock Value: 180
- Max Jump: 11
- Average Jump: 3.02

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 180
- Max Jump: 2
- Average Jump: 0.90

**Event Distribution:**

Machine 1:
- Total Events: 129
- Internal Events: 61 (47.3%)
- Send Events: 32 (24.8%)
- Receive Events: 36 (27.9%)

Machine 2:
- Total Events: 60
- Internal Events: 4 (6.7%)
- Send Events: 5 (8.3%)
- Receive Events: 51 (85.0%)

Machine 3:
- Total Events: 199
- Internal Events: 114 (57.3%)
- Send Events: 68 (34.2%)
- Receive Events: 17 (8.5%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 4.0
- Average Queue Length: 1.51
- Median Queue Length: 1.00

Machine 3:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00

### Configuration: both_modifications

**Parameters:**
- Clock Rate Range: 3-4 ticks/second
- Internal Event Probability: 0.4

**Actual Clock Rates:**

- Machine 1: 4 ticks/second
- Machine 2: 3 ticks/second
- Machine 3: 4 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 1
- Ending Clock Value: 254
- Max Jump: 3
- Average Jump: 0.99

Machine 2:
- Starting Clock Value: 3
- Ending Clock Value: 254
- Max Jump: 7
- Average Jump: 1.39

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 254
- Max Jump: 3
- Average Jump: 1.02

**Event Distribution:**

Machine 1:
- Total Events: 256
- Internal Events: 126 (49.2%)
- Send Events: 69 (27.0%)
- Receive Events: 61 (23.8%)

Machine 2:
- Total Events: 182
- Internal Events: 85 (46.7%)
- Send Events: 36 (19.8%)
- Receive Events: 61 (33.5%)

Machine 3:
- Total Events: 250
- Internal Events: 133 (53.2%)
- Send Events: 67 (26.8%)
- Receive Events: 50 (20.0%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 1.0
- Average Queue Length: 0.05
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 1.0
- Average Queue Length: 0.07
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00

## Comparative Analysis

This section compares results across different configurations.

### Event Distribution Comparison

| Configuration | Machine | Total Events | Internal Events (%) | Send Events (%) | Receive Events (%) |
| --- | --- | --- | --- | --- | --- |
| baseline | Machine 1 | 188 | 50 (26.6%) | 43 (22.9%) | 95 (50.5%) |
| baseline | Machine 2 | 312 | 155 (49.7%) | 83 (26.6%) | 74 (23.7%) |
| baseline | Machine 3 | 381 | 215 (56.4%) | 105 (27.6%) | 61 (16.0%) |
| smaller_clock_variation | Machine 1 | 254 | 136 (53.5%) | 72 (28.3%) | 46 (18.1%) |
| smaller_clock_variation | Machine 2 | 189 | 90 (47.6%) | 52 (27.5%) | 47 (24.9%) |
| smaller_clock_variation | Machine 3 | 183 | 88 (48.1%) | 32 (17.5%) | 63 (34.4%) |
| smaller_internal_prob | Machine 1 | 129 | 61 (47.3%) | 32 (24.8%) | 36 (27.9%) |
| smaller_internal_prob | Machine 2 | 60 | 4 (6.7%) | 5 (8.3%) | 51 (85.0%) |
| smaller_internal_prob | Machine 3 | 199 | 114 (57.3%) | 68 (34.2%) | 17 (8.5%) |
| both_modifications | Machine 1 | 256 | 126 (49.2%) | 69 (27.0%) | 61 (23.8%) |
| both_modifications | Machine 2 | 182 | 85 (46.7%) | 36 (19.8%) | 61 (33.5%) |
| both_modifications | Machine 3 | 250 | 133 (53.2%) | 67 (26.8%) | 50 (20.0%) |

### Logical Clock Jump Comparison

| Configuration | Machine | Starting Value | Ending Value | Max Jump | Avg Jump |
| --- | --- | --- | --- | --- | --- |
| baseline | Machine 1 | 2 | 363 | 9 | 1.93 |
| baseline | Machine 2 | 1 | 364 | 5 | 1.17 |
| baseline | Machine 3 | 1 | 365 | 2 | 0.96 |
| smaller_clock_variation | Machine 1 | 2 | 239 | 2 | 0.94 |
| smaller_clock_variation | Machine 2 | 1 | 239 | 7 | 1.27 |
| smaller_clock_variation | Machine 3 | 1 | 237 | 6 | 1.30 |
| smaller_internal_prob | Machine 1 | 2 | 178 | 5 | 1.38 |
| smaller_internal_prob | Machine 2 | 2 | 180 | 11 | 3.02 |
| smaller_internal_prob | Machine 3 | 1 | 180 | 2 | 0.90 |
| both_modifications | Machine 1 | 1 | 254 | 3 | 0.99 |
| both_modifications | Machine 2 | 3 | 254 | 7 | 1.39 |
| both_modifications | Machine 3 | 1 | 254 | 3 | 1.02 |

### Queue Length Comparison

| Configuration | Machine | Max Queue | Avg Queue | Median Queue |
| --- | --- | --- | --- | --- |
| baseline | Machine 1 | 2.0 | 0.24 | 0.00 |
| baseline | Machine 2 | 1.0 | 0.05 | 0.00 |
| baseline | Machine 3 | 1.0 | 0.02 | 0.00 |
| smaller_clock_variation | Machine 1 | 1.0 | 0.04 | 0.00 |
| smaller_clock_variation | Machine 2 | 1.0 | 0.06 | 0.00 |
| smaller_clock_variation | Machine 3 | 2.0 | 0.22 | 0.00 |
| smaller_internal_prob | Machine 1 | 0.0 | 0.00 | 0.00 |
| smaller_internal_prob | Machine 2 | 4.0 | 1.51 | 1.00 |
| smaller_internal_prob | Machine 3 | 0.0 | 0.00 | 0.00 |
| both_modifications | Machine 1 | 1.0 | 0.05 | 0.00 |
| both_modifications | Machine 2 | 1.0 | 0.07 | 0.00 |
| both_modifications | Machine 3 | 0.0 | 0.00 | 0.00 |

### Clock Drift Comparison

| Configuration | Max Drift | Machine 1 Final | Machine 2 Final | Machine 3 Final |
| --- | --- | --- | --- | --- |
| baseline | 2 | 363 | 364 | 365 |
| smaller_clock_variation | 2 | 239 | 239 | 237 |
| smaller_internal_prob | 2 | 178 | 180 | 180 |
| both_modifications | 0 | 254 | 254 | 254 |
