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
- Machine 2: 6 ticks/second
- Machine 3: 4 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 2
- Ending Clock Value: 340
- Max Jump: 15
- Average Jump: 1.94

Machine 2:
- Starting Clock Value: 1
- Ending Clock Value: 351
- Max Jump: 2
- Average Jump: 1.01

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 350
- Max Jump: 10
- Average Jump: 1.49

**Event Distribution:**

Machine 1:
- Total Events: 175
- Internal Events: 106 (60.6%)
- Send Events: 19 (10.9%)
- Receive Events: 50 (28.6%)

Machine 2:
- Total Events: 349
- Internal Events: 252 (72.2%)
- Send Events: 63 (18.1%)
- Receive Events: 34 (9.7%)

Machine 3:
- Total Events: 236
- Internal Events: 144 (61.0%)
- Send Events: 47 (19.9%)
- Receive Events: 45 (19.1%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 1.0
- Average Queue Length: 0.08
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 1.0
- Average Queue Length: 0.03
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 1.0
- Average Queue Length: 0.04
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
- Starting Clock Value: 3
- Ending Clock Value: 235
- Max Jump: 8
- Average Jump: 1.32

Machine 2:
- Starting Clock Value: 1
- Ending Clock Value: 237
- Max Jump: 2
- Average Jump: 1.01

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 234
- Max Jump: 8
- Average Jump: 1.32

**Event Distribution:**

Machine 1:
- Total Events: 177
- Internal Events: 113 (63.8%)
- Send Events: 28 (15.8%)
- Receive Events: 36 (20.3%)

Machine 2:
- Total Events: 234
- Internal Events: 164 (70.1%)
- Send Events: 38 (16.2%)
- Receive Events: 32 (13.7%)

Machine 3:
- Total Events: 178
- Internal Events: 110 (61.8%)
- Send Events: 35 (19.7%)
- Receive Events: 33 (18.5%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 1.0
- Average Queue Length: 0.03
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 1.0
- Average Queue Length: 0.06
- Median Queue Length: 0.00

### Configuration: smaller_internal_prob

**Parameters:**
- Clock Rate Range: 1-6 ticks/second
- Internal Event Probability: 0.4

**Actual Clock Rates:**

- Machine 1: 5 ticks/second
- Machine 2: 1 ticks/second
- Machine 3: 6 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 1
- Ending Clock Value: 354
- Max Jump: 8
- Average Jump: 1.21

Machine 2:
- Starting Clock Value: 1
- Ending Clock Value: 299
- Max Jump: 22
- Average Jump: 5.05

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 356
- Max Jump: 2
- Average Jump: 1.01

**Event Distribution:**

Machine 1:
- Total Events: 293
- Internal Events: 209 (71.3%)
- Send Events: 52 (17.7%)
- Receive Events: 32 (10.9%)

Machine 2:
- Total Events: 60
- Internal Events: 2 (3.3%)
- Send Events: 0 (0.0%)
- Receive Events: 58 (96.7%)

Machine 3:
- Total Events: 352
- Internal Events: 267 (75.9%)
- Send Events: 67 (19.0%)
- Receive Events: 18 (5.1%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 11.0
- Average Queue Length: 3.59
- Median Queue Length: 2.00

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
- Machine 2: 4 ticks/second
- Machine 3: 4 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 1
- Ending Clock Value: 257
- Max Jump: 3
- Average Jump: 1.09

Machine 2:
- Starting Clock Value: 1
- Ending Clock Value: 256
- Max Jump: 3
- Average Jump: 1.09

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 256
- Max Jump: 4
- Average Jump: 1.09

**Event Distribution:**

Machine 1:
- Total Events: 236
- Internal Events: 155 (65.7%)
- Send Events: 35 (14.8%)
- Receive Events: 46 (19.5%)

Machine 2:
- Total Events: 234
- Internal Events: 149 (63.7%)
- Send Events: 46 (19.7%)
- Receive Events: 39 (16.7%)

Machine 3:
- Total Events: 236
- Internal Events: 158 (66.9%)
- Send Events: 41 (17.4%)
- Receive Events: 37 (15.7%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 1.0
- Average Queue Length: 0.11
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 1.0
- Average Queue Length: 0.03
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 1.0
- Average Queue Length: 0.08
- Median Queue Length: 0.00

## Comparative Analysis

This section compares results across different configurations.

### Event Distribution Comparison

| Configuration | Machine | Total Events | Internal Events (%) | Send Events (%) | Receive Events (%) |
| --- | --- | --- | --- | --- | --- |
| baseline | Machine 1 | 175 | 106 (60.6%) | 19 (10.9%) | 50 (28.6%) |
| baseline | Machine 2 | 349 | 252 (72.2%) | 63 (18.1%) | 34 (9.7%) |
| baseline | Machine 3 | 236 | 144 (61.0%) | 47 (19.9%) | 45 (19.1%) |
| smaller_clock_variation | Machine 1 | 177 | 113 (63.8%) | 28 (15.8%) | 36 (20.3%) |
| smaller_clock_variation | Machine 2 | 234 | 164 (70.1%) | 38 (16.2%) | 32 (13.7%) |
| smaller_clock_variation | Machine 3 | 178 | 110 (61.8%) | 35 (19.7%) | 33 (18.5%) |
| smaller_internal_prob | Machine 1 | 293 | 209 (71.3%) | 52 (17.7%) | 32 (10.9%) |
| smaller_internal_prob | Machine 2 | 60 | 2 (3.3%) | 0 (0.0%) | 58 (96.7%) |
| smaller_internal_prob | Machine 3 | 352 | 267 (75.9%) | 67 (19.0%) | 18 (5.1%) |
| both_modifications | Machine 1 | 236 | 155 (65.7%) | 35 (14.8%) | 46 (19.5%) |
| both_modifications | Machine 2 | 234 | 149 (63.7%) | 46 (19.7%) | 39 (16.7%) |
| both_modifications | Machine 3 | 236 | 158 (66.9%) | 41 (17.4%) | 37 (15.7%) |

### Logical Clock Jump Comparison

| Configuration | Machine | Starting Value | Ending Value | Max Jump | Avg Jump |
| --- | --- | --- | --- | --- | --- |
| baseline | Machine 1 | 2 | 340 | 15 | 1.94 |
| baseline | Machine 2 | 1 | 351 | 2 | 1.01 |
| baseline | Machine 3 | 1 | 350 | 10 | 1.49 |
| smaller_clock_variation | Machine 1 | 3 | 235 | 8 | 1.32 |
| smaller_clock_variation | Machine 2 | 1 | 237 | 2 | 1.01 |
| smaller_clock_variation | Machine 3 | 1 | 234 | 8 | 1.32 |
| smaller_internal_prob | Machine 1 | 1 | 354 | 8 | 1.21 |
| smaller_internal_prob | Machine 2 | 1 | 299 | 22 | 5.05 |
| smaller_internal_prob | Machine 3 | 1 | 356 | 2 | 1.01 |
| both_modifications | Machine 1 | 1 | 257 | 3 | 1.09 |
| both_modifications | Machine 2 | 1 | 256 | 3 | 1.09 |
| both_modifications | Machine 3 | 1 | 256 | 4 | 1.09 |

### Queue Length Comparison

| Configuration | Machine | Max Queue | Avg Queue | Median Queue |
| --- | --- | --- | --- | --- |
| baseline | Machine 1 | 1.0 | 0.08 | 0.00 |
| baseline | Machine 2 | 1.0 | 0.03 | 0.00 |
| baseline | Machine 3 | 1.0 | 0.04 | 0.00 |
| smaller_clock_variation | Machine 1 | 1.0 | 0.03 | 0.00 |
| smaller_clock_variation | Machine 2 | 0.0 | 0.00 | 0.00 |
| smaller_clock_variation | Machine 3 | 1.0 | 0.06 | 0.00 |
| smaller_internal_prob | Machine 1 | 0.0 | 0.00 | 0.00 |
| smaller_internal_prob | Machine 2 | 11.0 | 3.59 | 2.00 |
| smaller_internal_prob | Machine 3 | 0.0 | 0.00 | 0.00 |
| both_modifications | Machine 1 | 1.0 | 0.11 | 0.00 |
| both_modifications | Machine 2 | 1.0 | 0.03 | 0.00 |
| both_modifications | Machine 3 | 1.0 | 0.08 | 0.00 |

### Clock Drift Comparison

| Configuration | Max Drift | Machine 1 Final | Machine 2 Final | Machine 3 Final |
| --- | --- | --- | --- | --- |
| baseline | 11 | 340 | 351 | 350 |
| smaller_clock_variation | 3 | 235 | 237 | 234 |
| smaller_internal_prob | 57 | 354 | 299 | 356 |
| both_modifications | 1 | 257 | 256 | 256 |

