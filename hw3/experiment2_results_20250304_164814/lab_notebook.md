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
- Machine 3: 5 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 2
- Ending Clock Value: 234
- Max Jump: 1
- Average Jump: 0.92

Machine 2:
- Starting Clock Value: 2
- Ending Clock Value: 232
- Max Jump: 8
- Average Jump: 1.26

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 295
- Max Jump: 1
- Average Jump: 0.92

**Event Distribution:**

Machine 1:
- Total Events: 252
- Internal Events: 169 (67.1%)
- Send Events: 82 (32.5%)
- Receive Events: 1 (0.4%)

Machine 2:
- Total Events: 184
- Internal Events: 93 (50.5%)
- Send Events: 51 (27.7%)
- Receive Events: 40 (21.7%)

Machine 3:
- Total Events: 320
- Internal Events: 165 (51.6%)
- Send Events: 91 (28.4%)
- Receive Events: 64 (20.0%)

**Queue Analysis:**

Machine 1:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
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

- Machine 1: 3 ticks/second
- Machine 2: 4 ticks/second
- Machine 3: 4 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 1
- Ending Clock Value: 178
- Max Jump: 1
- Average Jump: 0.91

Machine 2:
- Starting Clock Value: 2
- Ending Clock Value: 236
- Max Jump: 1
- Average Jump: 0.95

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 237
- Max Jump: 1
- Average Jump: 0.94

**Event Distribution:**

Machine 1:
- Total Events: 195
- Internal Events: 116 (59.5%)
- Send Events: 79 (40.5%)
- Receive Events: 0 (0.0%)

Machine 2:
- Total Events: 248
- Internal Events: 150 (60.5%)
- Send Events: 54 (21.8%)
- Receive Events: 44 (17.7%)

Machine 3:
- Total Events: 253
- Internal Events: 127 (50.2%)
- Send Events: 66 (26.1%)
- Receive Events: 60 (23.7%)

**Queue Analysis:**

Machine 2:
- Max Queue Length: 2.0
- Average Queue Length: 0.09
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
- Machine 3: 5 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 1
- Ending Clock Value: 119
- Max Jump: 1
- Average Jump: 0.94

Machine 2:
- Starting Clock Value: 2
- Ending Clock Value: 118
- Max Jump: 8
- Average Jump: 1.81

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 295
- Max Jump: 1
- Average Jump: 0.92

**Event Distribution:**

Machine 1:
- Total Events: 127
- Internal Events: 83 (65.4%)
- Send Events: 44 (34.6%)
- Receive Events: 0 (0.0%)

Machine 2:
- Total Events: 65
- Internal Events: 26 (40.0%)
- Send Events: 16 (24.6%)
- Receive Events: 23 (35.4%)

Machine 3:
- Total Events: 322
- Internal Events: 193 (59.9%)
- Send Events: 100 (31.1%)
- Receive Events: 29 (9.0%)

**Queue Analysis:**

Machine 2:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
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

- Machine 1: 3 ticks/second
- Machine 2: 4 ticks/second
- Machine 3: 4 ticks/second

**Logical Clock Analysis:**

Machine 1:
- Starting Clock Value: 3
- Ending Clock Value: 180
- Max Jump: 1
- Average Jump: 0.89

Machine 2:
- Starting Clock Value: 5
- Ending Clock Value: 238
- Max Jump: 1
- Average Jump: 0.90

Machine 3:
- Starting Clock Value: 1
- Ending Clock Value: 239
- Max Jump: 2
- Average Jump: 0.94

**Event Distribution:**

Machine 1:
- Total Events: 199
- Internal Events: 121 (60.8%)
- Send Events: 77 (38.7%)
- Receive Events: 1 (0.5%)

Machine 2:
- Total Events: 260
- Internal Events: 130 (50.0%)
- Send Events: 92 (35.4%)
- Receive Events: 38 (14.6%)

Machine 3:
- Total Events: 254
- Internal Events: 109 (42.9%)
- Send Events: 60 (23.6%)
- Receive Events: 85 (33.5%)

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
- Average Queue Length: 0.12
- Median Queue Length: 0.00

## Comparative Analysis

This section compares results across different configurations.

### Event Distribution Comparison

| Configuration | Machine | Total Events | Internal Events (%) | Send Events (%) | Receive Events (%) |
| --- | --- | --- | --- | --- | --- |
| baseline | Machine 1 | 252 | 169 (67.1%) | 82 (32.5%) | 1 (0.4%) |
| baseline | Machine 2 | 184 | 93 (50.5%) | 51 (27.7%) | 40 (21.7%) |
| baseline | Machine 3 | 320 | 165 (51.6%) | 91 (28.4%) | 64 (20.0%) |
| smaller_clock_variation | Machine 1 | 195 | 116 (59.5%) | 79 (40.5%) | 0 (0.0%) |
| smaller_clock_variation | Machine 2 | 248 | 150 (60.5%) | 54 (21.8%) | 44 (17.7%) |
| smaller_clock_variation | Machine 3 | 253 | 127 (50.2%) | 66 (26.1%) | 60 (23.7%) |
| smaller_internal_prob | Machine 1 | 127 | 83 (65.4%) | 44 (34.6%) | 0 (0.0%) |
| smaller_internal_prob | Machine 2 | 65 | 26 (40.0%) | 16 (24.6%) | 23 (35.4%) |
| smaller_internal_prob | Machine 3 | 322 | 193 (59.9%) | 100 (31.1%) | 29 (9.0%) |
| both_modifications | Machine 1 | 199 | 121 (60.8%) | 77 (38.7%) | 1 (0.5%) |
| both_modifications | Machine 2 | 260 | 130 (50.0%) | 92 (35.4%) | 38 (14.6%) |
| both_modifications | Machine 3 | 254 | 109 (42.9%) | 60 (23.6%) | 85 (33.5%) |

### Logical Clock Jump Comparison

| Configuration | Machine | Starting Value | Ending Value | Max Jump | Avg Jump |
| --- | --- | --- | --- | --- | --- |
| baseline | Machine 1 | 2 | 234 | 1 | 0.92 |
| baseline | Machine 2 | 2 | 232 | 8 | 1.26 |
| baseline | Machine 3 | 1 | 295 | 1 | 0.92 |
| smaller_clock_variation | Machine 1 | 1 | 178 | 1 | 0.91 |
| smaller_clock_variation | Machine 2 | 2 | 236 | 1 | 0.95 |
| smaller_clock_variation | Machine 3 | 1 | 237 | 1 | 0.94 |
| smaller_internal_prob | Machine 1 | 1 | 119 | 1 | 0.94 |
| smaller_internal_prob | Machine 2 | 2 | 118 | 8 | 1.81 |
| smaller_internal_prob | Machine 3 | 1 | 295 | 1 | 0.92 |
| both_modifications | Machine 1 | 3 | 180 | 1 | 0.89 |
| both_modifications | Machine 2 | 5 | 238 | 1 | 0.90 |
| both_modifications | Machine 3 | 1 | 239 | 2 | 0.94 |

### Queue Length Comparison

| Configuration | Machine | Max Queue | Avg Queue | Median Queue |
| --- | --- | --- | --- | --- |
| baseline | Machine 1 | 0.0 | 0.00 | 0.00 |
| baseline | Machine 2 | 1.0 | 0.05 | 0.00 |
| baseline | Machine 3 | 1.0 | 0.02 | 0.00 |
| smaller_clock_variation | Machine 2 | 2.0 | 0.09 | 0.00 |
| smaller_clock_variation | Machine 3 | 1.0 | 0.02 | 0.00 |
| smaller_internal_prob | Machine 2 | 0.0 | 0.00 | 0.00 |
| smaller_internal_prob | Machine 3 | 0.0 | 0.00 | 0.00 |
| both_modifications | Machine 1 | 0.0 | 0.00 | 0.00 |
| both_modifications | Machine 2 | 0.0 | 0.00 | 0.00 |
| both_modifications | Machine 3 | 1.0 | 0.12 | 0.00 |

### Clock Drift Comparison

| Configuration | Max Drift | Machine 1 Final | Machine 2 Final | Machine 3 Final |
| --- | --- | --- | --- | --- |
| baseline | 63 | 234 | 232 | 295 |
| smaller_clock_variation | 59 | 178 | 236 | 237 |
| smaller_internal_prob | 177 | 119 | 118 | 295 |
| both_modifications | 59 | 180 | 238 | 239 |

