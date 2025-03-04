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
- Machine 2: 1 ticks/second
- Machine 3: 2 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 2
- Ending Clock Value: 238
- Max Jump: 1
- Average Jump: 0.92

Machine 2:
- Starting Clock Value: 2
- Ending Clock Value: 236
- Max Jump: 16
- Average Jump: 3.97

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 237
- Max Jump: 9
- Average Jump: 1.83

**Event Distribution:**

Machine 1:
- Total Events: 257
- Internal Events: 174 (67.7%)
- Send Events: 82 (31.9%)
- Receive Events: 1 (0.4%)

Machine 2:
- Total Events: 60
- Internal Events: 17 (28.3%)
- Send Events: 2 (3.3%)
- Receive Events: 41 (68.3%)

Machine 3:
- Total Events: 130
- Internal Events: 54 (41.5%)
- Send Events: 35 (26.9%)
- Receive Events: 41 (31.5%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 2.0
- Average Queue Length: 0.46
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 1.0
- Average Queue Length: 0.15
- Median Queue Length: 0.00

### Configuration: smaller_clock_variation

**Parameters:**
- Clock Rate Range: 3-4 ticks/second
- Internal Event Probability: 0.8

**Actual Clock Rates:**

- Machine 1: 3 ticks/second
- Machine 2: 4 ticks/second
- Machine 3: 3 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 1
- Ending Clock Value: 177
- Max Jump: 1
- Average Jump: 0.89

Machine 2:
- Starting Clock Value: 1
- Ending Clock Value: 235
- Max Jump: 2
- Average Jump: 0.91

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 234
- Max Jump: 6
- Average Jump: 1.26

**Event Distribution:**

Machine 1:
- Total Events: 198
- Internal Events: 124 (62.6%)
- Send Events: 74 (37.4%)
- Receive Events: 0 (0.0%)

Machine 2:
- Total Events: 258
- Internal Events: 133 (51.6%)
- Send Events: 90 (34.9%)
- Receive Events: 35 (13.6%)

Machine 3:
- Total Events: 186
- Internal Events: 69 (37.1%)
- Send Events: 35 (18.8%)
- Receive Events: 82 (44.1%)

**Queue Analysis:**

Machine 2:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 2.0
- Average Queue Length: 0.28
- Median Queue Length: 0.00

### Configuration: smaller_internal_prob

**Parameters:**
- Clock Rate Range: 1-6 ticks/second
- Internal Event Probability: 0.1

**Actual Clock Rates:**

- Machine 1: 6 ticks/second
- Machine 2: 6 ticks/second
- Machine 3: 6 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 2
- Ending Clock Value: 352
- Max Jump: 1
- Average Jump: 0.90

Machine 2:
- Starting Clock Value: 1
- Ending Clock Value: 352
- Max Jump: 4
- Average Jump: 0.94

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 353
- Max Jump: 1
- Average Jump: 0.94

**Event Distribution:**

Machine 1:
- Total Events: 388
- Internal Events: 231 (59.5%)
- Send Events: 156 (40.2%)
- Receive Events: 1 (0.3%)

Machine 2:
- Total Events: 376
- Internal Events: 184 (48.9%)
- Send Events: 114 (30.3%)
- Receive Events: 78 (20.7%)

Machine 3:
- Total Events: 375
- Internal Events: 156 (41.6%)
- Send Events: 82 (21.9%)
- Receive Events: 137 (36.5%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 1.0
- Average Queue Length: 0.13
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
- Ending Clock Value: 236
- Max Jump: 1
- Average Jump: 0.90

Machine 2:
- Starting Clock Value: 2
- Ending Clock Value: 236
- Max Jump: 5
- Average Jump: 1.24

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 237
- Max Jump: 1
- Average Jump: 0.93

**Event Distribution:**

Machine 1:
- Total Events: 263
- Internal Events: 163 (62.0%)
- Send Events: 100 (38.0%)
- Receive Events: 0 (0.0%)

Machine 2:
- Total Events: 190
- Internal Events: 78 (41.1%)
- Send Events: 58 (30.5%)
- Receive Events: 54 (28.4%)

Machine 3:
- Total Events: 254
- Internal Events: 114 (44.9%)
- Send Events: 65 (25.6%)
- Receive Events: 75 (29.5%)

**Queue Analysis:**

Machine 2:
- Max Queue Length: 1.0
- Average Queue Length: 0.09
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 1.0
- Average Queue Length: 0.05
- Median Queue Length: 0.00

## Comparative Analysis

This section compares results across different configurations.

### Event Distribution Comparison

| Configuration | Machine | Total Events | Internal Events (%) | Send Events (%) | Receive Events (%) |
| --- | --- | --- | --- | --- | --- |
| baseline | Machine 1 | 257 | 174 (67.7%) | 82 (31.9%) | 1 (0.4%) |
| baseline | Machine 2 | 60 | 17 (28.3%) | 2 (3.3%) | 41 (68.3%) |
| baseline | Machine 3 | 130 | 54 (41.5%) | 35 (26.9%) | 41 (31.5%) |
| smaller_clock_variation | Machine 1 | 198 | 124 (62.6%) | 74 (37.4%) | 0 (0.0%) |
| smaller_clock_variation | Machine 2 | 258 | 133 (51.6%) | 90 (34.9%) | 35 (13.6%) |
| smaller_clock_variation | Machine 3 | 186 | 69 (37.1%) | 35 (18.8%) | 82 (44.1%) |
| smaller_internal_prob | Machine 1 | 388 | 231 (59.5%) | 156 (40.2%) | 1 (0.3%) |
| smaller_internal_prob | Machine 2 | 376 | 184 (48.9%) | 114 (30.3%) | 78 (20.7%) |
| smaller_internal_prob | Machine 3 | 375 | 156 (41.6%) | 82 (21.9%) | 137 (36.5%) |
| both_modifications | Machine 1 | 263 | 163 (62.0%) | 100 (38.0%) | 0 (0.0%) |
| both_modifications | Machine 2 | 190 | 78 (41.1%) | 58 (30.5%) | 54 (28.4%) |
| both_modifications | Machine 3 | 254 | 114 (44.9%) | 65 (25.6%) | 75 (29.5%) |

### Logical Clock Jump Comparison

| Configuration | Machine | Starting Value | Ending Value | Max Jump | Avg Jump |
| --- | --- | --- | --- | --- | --- |
| baseline | Machine 1 | 2 | 238 | 1 | 0.92 |
| baseline | Machine 2 | 2 | 236 | 16 | 3.97 |
| baseline | Machine 3 | 1 | 237 | 9 | 1.83 |
| smaller_clock_variation | Machine 1 | 1 | 177 | 1 | 0.89 |
| smaller_clock_variation | Machine 2 | 1 | 235 | 2 | 0.91 |
| smaller_clock_variation | Machine 3 | 1 | 234 | 6 | 1.26 |
| smaller_internal_prob | Machine 1 | 2 | 352 | 1 | 0.90 |
| smaller_internal_prob | Machine 2 | 1 | 352 | 4 | 0.94 |
| smaller_internal_prob | Machine 3 | 1 | 353 | 1 | 0.94 |
| both_modifications | Machine 1 | 1 | 236 | 1 | 0.90 |
| both_modifications | Machine 2 | 2 | 236 | 5 | 1.24 |
| both_modifications | Machine 3 | 1 | 237 | 1 | 0.93 |

### Queue Length Comparison

| Configuration | Machine | Max Queue | Avg Queue | Median Queue |
| --- | --- | --- | --- | --- |
| baseline | Machine 1 | 0.0 | 0.00 | 0.00 |
| baseline | Machine 2 | 2.0 | 0.46 | 0.00 |
| baseline | Machine 3 | 1.0 | 0.15 | 0.00 |
| smaller_clock_variation | Machine 2 | 0.0 | 0.00 | 0.00 |
| smaller_clock_variation | Machine 3 | 2.0 | 0.28 | 0.00 |
| smaller_internal_prob | Machine 1 | 0.0 | 0.00 | 0.00 |
| smaller_internal_prob | Machine 2 | 0.0 | 0.00 | 0.00 |
| smaller_internal_prob | Machine 3 | 1.0 | 0.13 | 0.00 |
| both_modifications | Machine 2 | 1.0 | 0.09 | 0.00 |
| both_modifications | Machine 3 | 1.0 | 0.05 | 0.00 |

### Clock Drift Comparison

| Configuration | Max Drift | Machine 1 Final | Machine 2 Final | Machine 3 Final |
| --- | --- | --- | --- | --- |
| baseline | 2 | 238 | 236 | 237 |
| smaller_clock_variation | 58 | 177 | 235 | 234 |
| smaller_internal_prob | 1 | 352 | 352 | 353 |
| both_modifications | 1 | 236 | 236 | 237 |

