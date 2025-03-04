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

- Machine 1: 6 ticks/second
- Machine 2: 1 ticks/second
- Machine 3: 2 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 1
- Ending Clock Value: 346
- Max Jump: 1
- Average Jump: 0.91

Machine 2:
- Starting Clock Value: 3
- Ending Clock Value: 273
- Max Jump: 17
- Average Jump: 4.58

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 347
- Max Jump: 12
- Average Jump: 2.91

**Event Distribution:**

Machine 1:
- Total Events: 381
- Internal Events: 231 (60.6%)
- Send Events: 146 (38.3%)
- Receive Events: 4 (1.0%)

Machine 2:
- Total Events: 60
- Internal Events: 0 (0.0%)
- Send Events: 0 (0.0%)
- Receive Events: 60 (100.0%)

Machine 3:
- Total Events: 120
- Internal Events: 29 (24.2%)
- Send Events: 9 (7.5%)
- Receive Events: 82 (68.3%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 15
- Average Queue Length: 9.42
- Median Queue Length: 10.50

Machine 3:
- Max Queue Length: 3.0
- Average Queue Length: 0.61
- Median Queue Length: 0.00

### Configuration: smaller_clock_variation

**Parameters:**
- Clock Rate Range: 3-4 ticks/second
- Internal Event Probability: 0.8

**Actual Clock Rates:**

- Machine 1: 3 ticks/second
- Machine 2: 3 ticks/second
- Machine 3: 3 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 1
- Ending Clock Value: 204
- Max Jump: 3
- Average Jump: 1.06

Machine 2:
- Starting Clock Value: 1
- Ending Clock Value: 203
- Max Jump: 3
- Average Jump: 1.06

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 205
- Max Jump: 3
- Average Jump: 1.07

**Event Distribution:**

Machine 1:
- Total Events: 192
- Internal Events: 84 (43.8%)
- Send Events: 61 (31.8%)
- Receive Events: 47 (24.5%)

Machine 2:
- Total Events: 191
- Internal Events: 88 (46.1%)
- Send Events: 56 (29.3%)
- Receive Events: 47 (24.6%)

Machine 3:
- Total Events: 192
- Internal Events: 80 (41.7%)
- Send Events: 45 (23.4%)
- Receive Events: 67 (34.9%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 1.0
- Average Queue Length: 0.02
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 1.0
- Average Queue Length: 0.06
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 1.0
- Average Queue Length: 0.09
- Median Queue Length: 0.00

### Configuration: smaller_internal_prob

**Parameters:**
- Clock Rate Range: 1-6 ticks/second
- Internal Event Probability: 0.4

**Actual Clock Rates:**

- Machine 1: 3 ticks/second
- Machine 2: 2 ticks/second
- Machine 3: 4 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 1
- Ending Clock Value: 237
- Max Jump: 11
- Average Jump: 1.21

Machine 2:
- Starting Clock Value: 1
- Ending Clock Value: 236
- Max Jump: 9
- Average Jump: 1.90

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 242
- Max Jump: 2
- Average Jump: 0.95

**Event Distribution:**

Machine 1:
- Total Events: 196
- Internal Events: 86 (43.9%)
- Send Events: 62 (31.6%)
- Receive Events: 48 (24.5%)

Machine 2:
- Total Events: 125
- Internal Events: 27 (21.6%)
- Send Events: 24 (19.2%)
- Receive Events: 74 (59.2%)

Machine 3:
- Total Events: 255
- Internal Events: 136 (53.3%)
- Send Events: 78 (30.6%)
- Receive Events: 41 (16.1%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 1.0
- Average Queue Length: 0.02
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 2.0
- Average Queue Length: 0.27
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 1.0
- Average Queue Length: 0.02
- Median Queue Length: 0.00

### Configuration: both_modifications

**Parameters:**
- Clock Rate Range: 3-4 ticks/second
- Internal Event Probability: 0.4

**Actual Clock Rates:**

- Machine 1: 3 ticks/second
- Machine 2: 4 ticks/second
- Machine 3: 4 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 1
- Ending Clock Value: 258
- Max Jump: 6
- Average Jump: 1.37

Machine 2:
- Starting Clock Value: 1
- Ending Clock Value: 258
- Max Jump: 4
- Average Jump: 1.01

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 258
- Max Jump: 3
- Average Jump: 1.02

**Event Distribution:**

Machine 1:
- Total Events: 188
- Internal Events: 67 (35.6%)
- Send Events: 40 (21.3%)
- Receive Events: 81 (43.1%)

Machine 2:
- Total Events: 256
- Internal Events: 118 (46.1%)
- Send Events: 83 (32.4%)
- Receive Events: 55 (21.5%)

Machine 3:
- Total Events: 252
- Internal Events: 124 (49.2%)
- Send Events: 71 (28.2%)
- Receive Events: 57 (22.6%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 2.0
- Average Queue Length: 0.14
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
| baseline | Machine 1 | 381 | 231 (60.6%) | 146 (38.3%) | 4 (1.0%) |
| baseline | Machine 2 | 60 | 0 (0.0%) | 0 (0.0%) | 60 (100.0%) |
| baseline | Machine 3 | 120 | 29 (24.2%) | 9 (7.5%) | 82 (68.3%) |
| smaller_clock_variation | Machine 1 | 192 | 84 (43.8%) | 61 (31.8%) | 47 (24.5%) |
| smaller_clock_variation | Machine 2 | 191 | 88 (46.1%) | 56 (29.3%) | 47 (24.6%) |
| smaller_clock_variation | Machine 3 | 192 | 80 (41.7%) | 45 (23.4%) | 67 (34.9%) |
| smaller_internal_prob | Machine 1 | 196 | 86 (43.9%) | 62 (31.6%) | 48 (24.5%) |
| smaller_internal_prob | Machine 2 | 125 | 27 (21.6%) | 24 (19.2%) | 74 (59.2%) |
| smaller_internal_prob | Machine 3 | 255 | 136 (53.3%) | 78 (30.6%) | 41 (16.1%) |
| both_modifications | Machine 1 | 188 | 67 (35.6%) | 40 (21.3%) | 81 (43.1%) |
| both_modifications | Machine 2 | 256 | 118 (46.1%) | 83 (32.4%) | 55 (21.5%) |
| both_modifications | Machine 3 | 252 | 124 (49.2%) | 71 (28.2%) | 57 (22.6%) |

### Logical Clock Jump Comparison

| Configuration | Machine | Starting Value | Ending Value | Max Jump | Avg Jump |
| --- | --- | --- | --- | --- | --- |
| baseline | Machine 1 | 1 | 346 | 1 | 0.91 |
| baseline | Machine 2 | 3 | 273 | 17 | 4.58 |
| baseline | Machine 3 | 1 | 347 | 12 | 2.91 |
| smaller_clock_variation | Machine 1 | 1 | 204 | 3 | 1.06 |
| smaller_clock_variation | Machine 2 | 1 | 203 | 3 | 1.06 |
| smaller_clock_variation | Machine 3 | 1 | 205 | 3 | 1.07 |
| smaller_internal_prob | Machine 1 | 1 | 237 | 11 | 1.21 |
| smaller_internal_prob | Machine 2 | 1 | 236 | 9 | 1.90 |
| smaller_internal_prob | Machine 3 | 1 | 242 | 2 | 0.95 |
| both_modifications | Machine 1 | 1 | 258 | 6 | 1.37 |
| both_modifications | Machine 2 | 1 | 258 | 4 | 1.01 |
| both_modifications | Machine 3 | 1 | 258 | 3 | 1.02 |

### Queue Length Comparison

| Configuration | Machine | Max Queue | Avg Queue | Median Queue |
| --- | --- | --- | --- | --- |
| baseline | Machine 1 | 0.0 | 0.00 | 0.00 |
| baseline | Machine 2 | 15 | 9.42 | 10.50 |
| baseline | Machine 3 | 3.0 | 0.61 | 0.00 |
| smaller_clock_variation | Machine 1 | 1.0 | 0.02 | 0.00 |
| smaller_clock_variation | Machine 2 | 1.0 | 0.06 | 0.00 |
| smaller_clock_variation | Machine 3 | 1.0 | 0.09 | 0.00 |
| smaller_internal_prob | Machine 1 | 1.0 | 0.02 | 0.00 |
| smaller_internal_prob | Machine 2 | 2.0 | 0.27 | 0.00 |
| smaller_internal_prob | Machine 3 | 1.0 | 0.02 | 0.00 |
| both_modifications | Machine 1 | 2.0 | 0.14 | 0.00 |
| both_modifications | Machine 2 | 1.0 | 0.07 | 0.00 |
| both_modifications | Machine 3 | 0.0 | 0.00 | 0.00 |

### Clock Drift Comparison

| Configuration | Max Drift | Machine 1 Final | Machine 2 Final | Machine 3 Final |
| --- | --- | --- | --- | --- |
| baseline | 74 | 346 | 273 | 347 |
| smaller_clock_variation | 2 | 204 | 203 | 205 |
| smaller_internal_prob | 6 | 237 | 236 | 242 |
| both_modifications | 0 | 258 | 258 | 258 |

