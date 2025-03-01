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
- Machine 2: 5 ticks/second
- Machine 3: 6 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 1
- Ending Clock Value: 352
- Max Jump: 9
- Average Jump: 0.93

Machine 2:
- Starting Clock Value: 1
- Ending Clock Value: 353
- Max Jump: 9
- Average Jump: 1.29

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 353
- Max Jump: 9
- Average Jump: 1.28

**Event Distribution:**

Machine 1:
- Total Events: 378
- Internal Events: 260 (68.8%)
- Send Events: 118 (31.2%)
- Receive Events: 0 (0.0%)

Machine 2:
- Total Events: 273
- Internal Events: 172 (63.0%)
- Send Events: 44 (16.1%)
- Receive Events: 57 (20.9%)

Machine 3:
- Total Events: 277
- Internal Events: 172 (62.1%)
- Send Events: 0 (0.0%)
- Receive Events: 105 (37.9%)

**Queue Analysis:**

Machine 2:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 1.0
- Average Queue Length: 0.10
- Median Queue Length: 0.00

### Configuration: smaller_clock_variation

**Parameters:**
- Clock Rate Range: 3-4 ticks/second
- Internal Event Probability: 0.8

**Actual Clock Rates:**

- Machine 1: 3 ticks/second
- Machine 2: 3 ticks/second
- Machine 3: 4 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 1
- Ending Clock Value: 178
- Max Jump: 5
- Average Jump: 0.90

Machine 2:
- Starting Clock Value: 3
- Ending Clock Value: 179
- Max Jump: 5
- Average Jump: 1.07

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 237
- Max Jump: 6
- Average Jump: 1.26

**Event Distribution:**

Machine 1:
- Total Events: 197
- Internal Events: 123 (62.4%)
- Send Events: 74 (37.6%)
- Receive Events: 0 (0.0%)

Machine 2:
- Total Events: 165
- Internal Events: 104 (63.0%)
- Send Events: 22 (13.3%)
- Receive Events: 39 (23.6%)

Machine 3:
- Total Events: 189
- Internal Events: 132 (69.8%)
- Send Events: 0 (0.0%)
- Receive Events: 57 (30.2%)

**Queue Analysis:**

Machine 2:
- Max Queue Length: 1.0
- Average Queue Length: 0.03
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

- Machine 1: 6 ticks/second
- Machine 2: 5 ticks/second
- Machine 3: 5 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 1
- Ending Clock Value: 351
- Max Jump: 10
- Average Jump: 0.91

Machine 2:
- Starting Clock Value: 1
- Ending Clock Value: 349
- Max Jump: 8
- Average Jump: 1.34

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 350
- Max Jump: 11
- Average Jump: 1.45

**Event Distribution:**

Machine 1:
- Total Events: 386
- Internal Events: 233 (60.4%)
- Send Events: 153 (39.6%)
- Receive Events: 0 (0.0%)

Machine 2:
- Total Events: 261
- Internal Events: 154 (59.0%)
- Send Events: 36 (13.8%)
- Receive Events: 71 (27.2%)

Machine 3:
- Total Events: 241
- Internal Events: 123 (51.0%)
- Send Events: 0 (0.0%)
- Receive Events: 118 (49.0%)

**Queue Analysis:**

Machine 2:
- Max Queue Length: 1.0
- Average Queue Length: 0.08
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 2.0
- Average Queue Length: 0.19
- Median Queue Length: 0.00

### Configuration: both_modifications

**Parameters:**
- Clock Rate Range: 3-4 ticks/second
- Internal Event Probability: 0.4

**Actual Clock Rates:**

- Machine 1: 4 ticks/second
- Machine 2: 4 ticks/second
- Machine 3: 3 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 1
- Ending Clock Value: 236
- Max Jump: 6
- Average Jump: 0.89

Machine 2:
- Starting Clock Value: 1
- Ending Clock Value: 236
- Max Jump: 6
- Average Jump: 1.11

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 236
- Max Jump: 7
- Average Jump: 1.53

**Event Distribution:**

Machine 1:
- Total Events: 264
- Internal Events: 159 (60.2%)
- Send Events: 105 (39.8%)
- Receive Events: 0 (0.0%)

Machine 2:
- Total Events: 213
- Internal Events: 122 (57.3%)
- Send Events: 40 (18.8%)
- Receive Events: 51 (23.9%)

Machine 3:
- Total Events: 155
- Internal Events: 61 (39.4%)
- Send Events: 0 (0.0%)
- Receive Events: 94 (60.6%)

**Queue Analysis:**

Machine 2:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 2.0
- Average Queue Length: 0.20
- Median Queue Length: 0.00

## Comparative Analysis

This section compares results across different configurations.

### Event Distribution Comparison

| Configuration | Machine | Total Events | Internal Events (%) | Send Events (%) | Receive Events (%) |
| --- | --- | --- | --- | --- | --- |
| baseline | Machine 1 | 378 | 260 (68.8%) | 118 (31.2%) | 0 (0.0%) |
| baseline | Machine 2 | 273 | 172 (63.0%) | 44 (16.1%) | 57 (20.9%) |
| baseline | Machine 3 | 277 | 172 (62.1%) | 0 (0.0%) | 105 (37.9%) |
| smaller_clock_variation | Machine 1 | 197 | 123 (62.4%) | 74 (37.6%) | 0 (0.0%) |
| smaller_clock_variation | Machine 2 | 165 | 104 (63.0%) | 22 (13.3%) | 39 (23.6%) |
| smaller_clock_variation | Machine 3 | 189 | 132 (69.8%) | 0 (0.0%) | 57 (30.2%) |
| smaller_internal_prob | Machine 1 | 386 | 233 (60.4%) | 153 (39.6%) | 0 (0.0%) |
| smaller_internal_prob | Machine 2 | 261 | 154 (59.0%) | 36 (13.8%) | 71 (27.2%) |
| smaller_internal_prob | Machine 3 | 241 | 123 (51.0%) | 0 (0.0%) | 118 (49.0%) |
| both_modifications | Machine 1 | 264 | 159 (60.2%) | 105 (39.8%) | 0 (0.0%) |
| both_modifications | Machine 2 | 213 | 122 (57.3%) | 40 (18.8%) | 51 (23.9%) |
| both_modifications | Machine 3 | 155 | 61 (39.4%) | 0 (0.0%) | 94 (60.6%) |

### Logical Clock Jump Comparison

| Configuration | Machine | Starting Value | Ending Value | Max Jump | Avg Jump |
| --- | --- | --- | --- | --- | --- |
| baseline | Machine 1 | 1 | 352 | 9 | 0.93 |
| baseline | Machine 2 | 1 | 353 | 9 | 1.29 |
| baseline | Machine 3 | 1 | 353 | 9 | 1.28 |
| smaller_clock_variation | Machine 1 | 1 | 178 | 5 | 0.90 |
| smaller_clock_variation | Machine 2 | 3 | 179 | 5 | 1.07 |
| smaller_clock_variation | Machine 3 | 1 | 237 | 6 | 1.26 |
| smaller_internal_prob | Machine 1 | 1 | 351 | 10 | 0.91 |
| smaller_internal_prob | Machine 2 | 1 | 349 | 8 | 1.34 |
| smaller_internal_prob | Machine 3 | 1 | 350 | 11 | 1.45 |
| both_modifications | Machine 1 | 1 | 236 | 6 | 0.89 |
| both_modifications | Machine 2 | 1 | 236 | 6 | 1.11 |
| both_modifications | Machine 3 | 1 | 236 | 7 | 1.53 |

### Queue Length Comparison

| Configuration | Machine | Max Queue | Avg Queue | Median Queue |
| --- | --- | --- | --- | --- |
| baseline | Machine 2 | 0.0 | 0.00 | 0.00 |
| baseline | Machine 3 | 1.0 | 0.10 | 0.00 |
| smaller_clock_variation | Machine 2 | 1.0 | 0.03 | 0.00 |
| smaller_clock_variation | Machine 3 | 1.0 | 0.07 | 0.00 |
| smaller_internal_prob | Machine 2 | 1.0 | 0.08 | 0.00 |
| smaller_internal_prob | Machine 3 | 2.0 | 0.19 | 0.00 |
| both_modifications | Machine 2 | 0.0 | 0.00 | 0.00 |
| both_modifications | Machine 3 | 2.0 | 0.20 | 0.00 |

### Clock Drift Comparison

| Configuration | Max Drift | Machine 1 Final | Machine 2 Final | Machine 3 Final |
| --- | --- | --- | --- | --- |
| baseline | 1 | 352 | 353 | 353 |
| smaller_clock_variation | 59 | 178 | 179 | 237 |
| smaller_internal_prob | 2 | 351 | 349 | 350 |
| both_modifications | 0 | 236 | 236 | 236 |

## Summary Reflections

*This section should be filled in with reflections on how the different configurations affected the results.*

