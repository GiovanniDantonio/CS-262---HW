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

- Machine 1: 1 ticks/second
- Machine 2: 5 ticks/second
- Machine 3: 5 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 1
- Ending Clock Value: 190
- Max Jump: 13
- Average Jump: 3.15

Machine 2:
- Starting Clock Value: 2
- Ending Clock Value: 317
- Max Jump: 3
- Average Jump: 1.01

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 318
- Max Jump: 2
- Average Jump: 0.99

**Event Distribution:**

Machine 1:
- Total Events: 61
- Internal Events: 2 (3.3%)
- Send Events: 2 (3.3%)
- Receive Events: 57 (93.4%)

Machine 2:
- Total Events: 314
- Internal Events: 169 (53.8%)
- Send Events: 98 (31.2%)
- Receive Events: 47 (15.0%)

Machine 3:
- Total Events: 320
- Internal Events: 170 (53.1%)
- Send Events: 95 (29.7%)
- Receive Events: 55 (17.2%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 36.0
- Average Queue Length: 18.56
- Median Queue Length: 21.00

Machine 2:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
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

- Machine 1: 3 ticks/second
- Machine 2: 4 ticks/second
- Machine 3: 4 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 1
- Ending Clock Value: 251
- Max Jump: 6
- Average Jump: 1.33

Machine 2:
- Starting Clock Value: 1
- Ending Clock Value: 252
- Max Jump: 3
- Average Jump: 1.00

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 252
- Max Jump: 2
- Average Jump: 1.00

**Event Distribution:**

Machine 1:
- Total Events: 189
- Internal Events: 67 (35.4%)
- Send Events: 52 (27.5%)
- Receive Events: 70 (37.0%)

Machine 2:
- Total Events: 252
- Internal Events: 132 (52.4%)
- Send Events: 67 (26.6%)
- Receive Events: 53 (21.0%)

Machine 3:
- Total Events: 252
- Internal Events: 126 (50.0%)
- Send Events: 65 (25.8%)
- Receive Events: 61 (24.2%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 2.0
- Average Queue Length: 0.29
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 1.0
- Average Queue Length: 0.06
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 1.0
- Average Queue Length: 0.02
- Median Queue Length: 0.00

### Configuration: smaller_internal_prob

**Parameters:**
- Clock Rate Range: 1-6 ticks/second
- Internal Event Probability: 0.1

**Actual Clock Rates:**

- Machine 1: 2 ticks/second
- Machine 2: 1 ticks/second
- Machine 3: 3 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 1
- Ending Clock Value: 178
- Max Jump: 13
- Average Jump: 1.42

Machine 2:
- Starting Clock Value: 1
- Ending Clock Value: 177
- Max Jump: 12
- Average Jump: 2.98

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 179
- Max Jump: 2
- Average Jump: 0.96

**Event Distribution:**

Machine 1:
- Total Events: 126
- Internal Events: 59 (46.8%)
- Send Events: 35 (27.8%)
- Receive Events: 32 (25.4%)

Machine 2:
- Total Events: 60
- Internal Events: 9 (15.0%)
- Send Events: 3 (5.0%)
- Receive Events: 48 (80.0%)

Machine 3:
- Total Events: 187
- Internal Events: 105 (56.1%)
- Send Events: 62 (33.2%)
- Receive Events: 20 (10.7%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 2.0
- Average Queue Length: 0.28
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 4.0
- Average Queue Length: 1.25
- Median Queue Length: 1.00

Machine 3:
- Max Queue Length: 1.0
- Average Queue Length: 0.05
- Median Queue Length: 0.00

### Configuration: both_modifications

**Parameters:**
- Clock Rate Range: 3-4 ticks/second
- Internal Event Probability: 0.4

**Actual Clock Rates:**

- Machine 1: 3 ticks/second
- Machine 2: 3 ticks/second
- Machine 3: 3 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 1
- Ending Clock Value: 197
- Max Jump: 3
- Average Jump: 1.02

Machine 2:
- Starting Clock Value: 1
- Ending Clock Value: 197
- Max Jump: 4
- Average Jump: 1.05

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 197
- Max Jump: 2
- Average Jump: 1.05

**Event Distribution:**

Machine 1:
- Total Events: 193
- Internal Events: 90 (46.6%)
- Send Events: 60 (31.1%)
- Receive Events: 43 (22.3%)

Machine 2:
- Total Events: 188
- Internal Events: 93 (49.5%)
- Send Events: 49 (26.1%)
- Receive Events: 46 (24.5%)

Machine 3:
- Total Events: 187
- Internal Events: 92 (49.2%)
- Send Events: 38 (20.3%)
- Receive Events: 57 (30.5%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 1.0
- Average Queue Length: 0.02
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 1.0
- Average Queue Length: 0.20
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 2.0
- Average Queue Length: 0.12
- Median Queue Length: 0.00

## Comparative Analysis

This section compares results across different configurations.

### Event Distribution Comparison

| Configuration | Machine | Total Events | Internal Events (%) | Send Events (%) | Receive Events (%) |
| --- | --- | --- | --- | --- | --- |
| baseline | Machine 1 | 61 | 2 (3.3%) | 2 (3.3%) | 57 (93.4%) |
| baseline | Machine 2 | 314 | 169 (53.8%) | 98 (31.2%) | 47 (15.0%) |
| baseline | Machine 3 | 320 | 170 (53.1%) | 95 (29.7%) | 55 (17.2%) |
| smaller_clock_variation | Machine 1 | 189 | 67 (35.4%) | 52 (27.5%) | 70 (37.0%) |
| smaller_clock_variation | Machine 2 | 252 | 132 (52.4%) | 67 (26.6%) | 53 (21.0%) |
| smaller_clock_variation | Machine 3 | 252 | 126 (50.0%) | 65 (25.8%) | 61 (24.2%) |
| smaller_internal_prob | Machine 1 | 126 | 59 (46.8%) | 35 (27.8%) | 32 (25.4%) |
| smaller_internal_prob | Machine 2 | 60 | 9 (15.0%) | 3 (5.0%) | 48 (80.0%) |
| smaller_internal_prob | Machine 3 | 187 | 105 (56.1%) | 62 (33.2%) | 20 (10.7%) |
| both_modifications | Machine 1 | 193 | 90 (46.6%) | 60 (31.1%) | 43 (22.3%) |
| both_modifications | Machine 2 | 188 | 93 (49.5%) | 49 (26.1%) | 46 (24.5%) |
| both_modifications | Machine 3 | 187 | 92 (49.2%) | 38 (20.3%) | 57 (30.5%) |

### Logical Clock Jump Comparison

| Configuration | Machine | Starting Value | Ending Value | Max Jump | Avg Jump |
| --- | --- | --- | --- | --- | --- |
| baseline | Machine 1 | 1 | 190 | 13 | 3.15 |
| baseline | Machine 2 | 2 | 317 | 3 | 1.01 |
| baseline | Machine 3 | 1 | 318 | 2 | 0.99 |
| smaller_clock_variation | Machine 1 | 1 | 251 | 6 | 1.33 |
| smaller_clock_variation | Machine 2 | 1 | 252 | 3 | 1.00 |
| smaller_clock_variation | Machine 3 | 1 | 252 | 2 | 1.00 |
| smaller_internal_prob | Machine 1 | 1 | 178 | 13 | 1.42 |
| smaller_internal_prob | Machine 2 | 1 | 177 | 12 | 2.98 |
| smaller_internal_prob | Machine 3 | 1 | 179 | 2 | 0.96 |
| both_modifications | Machine 1 | 1 | 197 | 3 | 1.02 |
| both_modifications | Machine 2 | 1 | 197 | 4 | 1.05 |
| both_modifications | Machine 3 | 1 | 197 | 2 | 1.05 |

### Queue Length Comparison

| Configuration | Machine | Max Queue | Avg Queue | Median Queue |
| --- | --- | --- | --- | --- |
| baseline | Machine 1 | 36.0 | 18.56 | 21.00 |
| baseline | Machine 2 | 0.0 | 0.00 | 0.00 |
| baseline | Machine 3 | 0.0 | 0.00 | 0.00 |
| smaller_clock_variation | Machine 1 | 2.0 | 0.29 | 0.00 |
| smaller_clock_variation | Machine 2 | 1.0 | 0.06 | 0.00 |
| smaller_clock_variation | Machine 3 | 1.0 | 0.02 | 0.00 |
| smaller_internal_prob | Machine 1 | 2.0 | 0.28 | 0.00 |
| smaller_internal_prob | Machine 2 | 4.0 | 1.25 | 1.00 |
| smaller_internal_prob | Machine 3 | 1.0 | 0.05 | 0.00 |
| both_modifications | Machine 1 | 1.0 | 0.02 | 0.00 |
| both_modifications | Machine 2 | 1.0 | 0.20 | 0.00 |
| both_modifications | Machine 3 | 2.0 | 0.12 | 0.00 |

### Clock Drift Comparison

| Configuration | Max Drift | Machine 1 Final | Machine 2 Final | Machine 3 Final |
| --- | --- | --- | --- | --- |
| baseline | 128 | 190 | 317 | 318 |
| smaller_clock_variation | 1 | 251 | 252 | 252 |
| smaller_internal_prob | 2 | 178 | 177 | 179 |
| both_modifications | 0 | 197 | 197 | 197 |

