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

- Machine 1: 4 ticks/second
- Machine 2: 3 ticks/second
- Machine 3: 6 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 2
- Ending Clock Value: 356
- Max Jump: 10
- Average Jump: 1.38

Machine 2:
- Starting Clock Value: 3
- Ending Clock Value: 351
- Max Jump: 12
- Average Jump: 1.91

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 356
- Max Jump: 2
- Average Jump: 0.94

**Event Distribution:**

Machine 1:
- Total Events: 258
- Internal Events: 107 (41.5%)
- Send Events: 75 (29.1%)
- Receive Events: 76 (29.5%)

Machine 2:
- Total Events: 183
- Internal Events: 57 (31.1%)
- Send Events: 36 (19.7%)
- Receive Events: 90 (49.2%)

Machine 3:
- Total Events: 377
- Internal Events: 212 (56.2%)
- Send Events: 111 (29.4%)
- Receive Events: 54 (14.3%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 1.0
- Average Queue Length: 0.12
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 2.0
- Average Queue Length: 0.22
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00

### Configuration: smaller_clock_variation

**Parameters:**
- Clock Rate Range: 3-4 ticks/second
- Internal Event Probability: 0.8

**Actual Clock Rates:**

- Machine 1: 4 ticks/second
- Machine 2: 3 ticks/second
- Machine 3: 4 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 1
- Ending Clock Value: 250
- Max Jump: 3
- Average Jump: 1.03

Machine 2:
- Starting Clock Value: 1
- Ending Clock Value: 249
- Max Jump: 9
- Average Jump: 1.35

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 250
- Max Jump: 2
- Average Jump: 1.00

**Event Distribution:**

Machine 1:
- Total Events: 243
- Internal Events: 122 (50.2%)
- Send Events: 62 (25.5%)
- Receive Events: 59 (24.3%)

Machine 2:
- Total Events: 185
- Internal Events: 77 (41.6%)
- Send Events: 43 (23.2%)
- Receive Events: 65 (35.1%)

Machine 3:
- Total Events: 249
- Internal Events: 117 (47.0%)
- Send Events: 77 (30.9%)
- Receive Events: 55 (22.1%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 1.0
- Average Queue Length: 0.05
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 2.0
- Average Queue Length: 0.26
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 1.0
- Average Queue Length: 0.07
- Median Queue Length: 0.00

### Configuration: smaller_internal_prob

**Parameters:**
- Clock Rate Range: 1-6 ticks/second
- Internal Event Probability: 0.4

**Actual Clock Rates:**

- Machine 1: 1 ticks/second
- Machine 2: 1 ticks/second
- Machine 3: 1 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 1
- Ending Clock Value: 67
- Max Jump: 2
- Average Jump: 1.02

Machine 2:
- Starting Clock Value: 1
- Ending Clock Value: 67
- Max Jump: 2
- Average Jump: 1.06

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 66
- Max Jump: 2
- Average Jump: 1.03

**Event Distribution:**

Machine 1:
- Total Events: 66
- Internal Events: 33 (50.0%)
- Send Events: 23 (34.8%)
- Receive Events: 10 (15.2%)

Machine 2:
- Total Events: 63
- Internal Events: 30 (47.6%)
- Send Events: 10 (15.9%)
- Receive Events: 23 (36.5%)

Machine 3:
- Total Events: 64
- Internal Events: 32 (50.0%)
- Send Events: 16 (25.0%)
- Receive Events: 16 (25.0%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 1.0
- Average Queue Length: 0.04
- Median Queue Length: 0.00

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
- Ending Clock Value: 253
- Max Jump: 3
- Average Jump: 1.00

Machine 2:
- Starting Clock Value: 2
- Ending Clock Value: 251
- Max Jump: 4
- Average Jump: 1.31

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 252
- Max Jump: 2
- Average Jump: 1.01

**Event Distribution:**

Machine 1:
- Total Events: 254
- Internal Events: 125 (49.2%)
- Send Events: 79 (31.1%)
- Receive Events: 50 (19.7%)

Machine 2:
- Total Events: 191
- Internal Events: 63 (33.0%)
- Send Events: 55 (28.8%)
- Receive Events: 73 (38.2%)

Machine 3:
- Total Events: 250
- Internal Events: 118 (47.2%)
- Send Events: 61 (24.4%)
- Receive Events: 71 (28.4%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 2.0
- Average Queue Length: 0.19
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 1.0
- Average Queue Length: 0.07
- Median Queue Length: 0.00

## Comparative Analysis

This section compares results across different configurations.

### Event Distribution Comparison

| Configuration | Machine | Total Events | Internal Events (%) | Send Events (%) | Receive Events (%) |
| --- | --- | --- | --- | --- | --- |
| baseline | Machine 1 | 258 | 107 (41.5%) | 75 (29.1%) | 76 (29.5%) |
| baseline | Machine 2 | 183 | 57 (31.1%) | 36 (19.7%) | 90 (49.2%) |
| baseline | Machine 3 | 377 | 212 (56.2%) | 111 (29.4%) | 54 (14.3%) |
| smaller_clock_variation | Machine 1 | 243 | 122 (50.2%) | 62 (25.5%) | 59 (24.3%) |
| smaller_clock_variation | Machine 2 | 185 | 77 (41.6%) | 43 (23.2%) | 65 (35.1%) |
| smaller_clock_variation | Machine 3 | 249 | 117 (47.0%) | 77 (30.9%) | 55 (22.1%) |
| smaller_internal_prob | Machine 1 | 66 | 33 (50.0%) | 23 (34.8%) | 10 (15.2%) |
| smaller_internal_prob | Machine 2 | 63 | 30 (47.6%) | 10 (15.9%) | 23 (36.5%) |
| smaller_internal_prob | Machine 3 | 64 | 32 (50.0%) | 16 (25.0%) | 16 (25.0%) |
| both_modifications | Machine 1 | 254 | 125 (49.2%) | 79 (31.1%) | 50 (19.7%) |
| both_modifications | Machine 2 | 191 | 63 (33.0%) | 55 (28.8%) | 73 (38.2%) |
| both_modifications | Machine 3 | 250 | 118 (47.2%) | 61 (24.4%) | 71 (28.4%) |

### Logical Clock Jump Comparison

| Configuration | Machine | Starting Value | Ending Value | Max Jump | Avg Jump |
| --- | --- | --- | --- | --- | --- |
| baseline | Machine 1 | 2 | 356 | 10 | 1.38 |
| baseline | Machine 2 | 3 | 351 | 12 | 1.91 |
| baseline | Machine 3 | 1 | 356 | 2 | 0.94 |
| smaller_clock_variation | Machine 1 | 1 | 250 | 3 | 1.03 |
| smaller_clock_variation | Machine 2 | 1 | 249 | 9 | 1.35 |
| smaller_clock_variation | Machine 3 | 1 | 250 | 2 | 1.00 |
| smaller_internal_prob | Machine 1 | 1 | 67 | 2 | 1.02 |
| smaller_internal_prob | Machine 2 | 1 | 67 | 2 | 1.06 |
| smaller_internal_prob | Machine 3 | 1 | 66 | 2 | 1.03 |
| both_modifications | Machine 1 | 1 | 253 | 3 | 1.00 |
| both_modifications | Machine 2 | 2 | 251 | 4 | 1.31 |
| both_modifications | Machine 3 | 1 | 252 | 2 | 1.01 |

### Queue Length Comparison

| Configuration | Machine | Max Queue | Avg Queue | Median Queue |
| --- | --- | --- | --- | --- |
| baseline | Machine 1 | 1.0 | 0.12 | 0.00 |
| baseline | Machine 2 | 2.0 | 0.22 | 0.00 |
| baseline | Machine 3 | 0.0 | 0.00 | 0.00 |
| smaller_clock_variation | Machine 1 | 1.0 | 0.05 | 0.00 |
| smaller_clock_variation | Machine 2 | 2.0 | 0.26 | 0.00 |
| smaller_clock_variation | Machine 3 | 1.0 | 0.07 | 0.00 |
| smaller_internal_prob | Machine 1 | 0.0 | 0.00 | 0.00 |
| smaller_internal_prob | Machine 2 | 1.0 | 0.04 | 0.00 |
| smaller_internal_prob | Machine 3 | 0.0 | 0.00 | 0.00 |
| both_modifications | Machine 1 | 0.0 | 0.00 | 0.00 |
| both_modifications | Machine 2 | 2.0 | 0.19 | 0.00 |
| both_modifications | Machine 3 | 1.0 | 0.07 | 0.00 |

### Clock Drift Comparison

| Configuration | Max Drift | Machine 1 Final | Machine 2 Final | Machine 3 Final |
| --- | --- | --- | --- | --- |
| baseline | 5 | 356 | 351 | 356 |
| smaller_clock_variation | 1 | 250 | 249 | 250 |
| smaller_internal_prob | 1 | 67 | 67 | 66 |
| both_modifications | 2 | 253 | 251 | 252 |

