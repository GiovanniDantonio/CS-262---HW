# Lab Notebook: Experiment 1

## Experimental Setup

- Number of runs: 5
- Duration per run: 60 seconds
- Three virtual machines with varying clock rates

## Observations

### Run 1

#### Clock Rates

- Machine 1: 2 ticks/second
- Machine 2: 4 ticks/second
- Machine 3: 2 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 120
- Max Jump: 3
- Average Jump: 0.91

**Machine 2:**
- Starting Clock Value: 2
- Ending Clock Value: 236
- Max Jump: 6
- Average Jump: 1.09

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 234
- Max Jump: 14
- Average Jump: 2.31

#### Clock Drift Analysis

Maximum drift between logical clocks: 116 units

- Machine 1 final clock: 120
- Machine 2 final clock: 236
- Machine 3 final clock: 234

#### Queue Analysis

**Machine 2:**
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00

**Machine 3:**
- Max Queue Length: 2.0
- Average Queue Length: 0.18
- Median Queue Length: 0.00

### Run 2

#### Clock Rates

- Machine 1: 4 ticks/second
- Machine 2: 6 ticks/second
- Machine 3: 2 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 236
- Max Jump: 6
- Average Jump: 0.94

**Machine 2:**
- Starting Clock Value: 1
- Ending Clock Value: 350
- Max Jump: 10
- Average Jump: 1.12

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 346
- Max Jump: 16
- Average Jump: 3.19

#### Clock Drift Analysis

Maximum drift between logical clocks: 114 units

- Machine 1 final clock: 236
- Machine 2 final clock: 350
- Machine 3 final clock: 346

#### Queue Analysis

**Machine 2:**
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00

**Machine 3:**
- Max Queue Length: 5.0
- Average Queue Length: 1.07
- Median Queue Length: 1.00

### Run 3

#### Clock Rates

- Machine 1: 6 ticks/second
- Machine 2: 6 ticks/second
- Machine 3: 1 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 352
- Max Jump: 11
- Average Jump: 0.92

**Machine 2:**
- Starting Clock Value: 3
- Ending Clock Value: 353
- Max Jump: 8
- Average Jump: 1.07

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 182
- Max Jump: 17
- Average Jump: 3.07

#### Clock Drift Analysis

Maximum drift between logical clocks: 171 units

- Machine 1 final clock: 352
- Machine 2 final clock: 353
- Machine 3 final clock: 182

#### Queue Analysis

**Machine 2:**
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00

**Machine 3:**
- Max Queue Length: 59.0
- Average Queue Length: 27.17
- Median Queue Length: 27.00

### Run 4

#### Clock Rates

- Machine 1: 3 ticks/second
- Machine 2: 3 ticks/second
- Machine 3: 1 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 178
- Max Jump: 5
- Average Jump: 0.93

**Machine 2:**
- Starting Clock Value: 1
- Ending Clock Value: 179
- Max Jump: 5
- Average Jump: 1.12

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 168
- Max Jump: 14
- Average Jump: 2.88

#### Clock Drift Analysis

Maximum drift between logical clocks: 11 units

- Machine 1 final clock: 178
- Machine 2 final clock: 179
- Machine 3 final clock: 168

#### Queue Analysis

**Machine 2:**
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00

**Machine 3:**
- Max Queue Length: 7.0
- Average Queue Length: 2.79
- Median Queue Length: 3.00

### Run 5

#### Clock Rates

- Machine 1: 6 ticks/second
- Machine 2: 3 ticks/second
- Machine 3: 4 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 320
- Max Jump: 11
- Average Jump: 0.92

**Machine 2:**
- Starting Clock Value: 2
- Ending Clock Value: 318
- Max Jump: 11
- Average Jump: 2.12

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 315
- Max Jump: 13
- Average Jump: 1.76

#### Clock Drift Analysis

Maximum drift between logical clocks: 5 units

- Machine 1 final clock: 320
- Machine 2 final clock: 318
- Machine 3 final clock: 315

#### Queue Analysis

**Machine 2:**
- Max Queue Length: 3.0
- Average Queue Length: 0.23
- Median Queue Length: 0.00

**Machine 3:**
- Max Queue Length: 1.0
- Average Queue Length: 0.12
- Median Queue Length: 0.00

## Cross-Run Analysis

This section analyzes patterns and observations across all experimental runs.

### Logical Clock Jump Analysis

Average and maximum jumps by machine across runs:

| Run | Machine 1 Avg | Machine 1 Max | Machine 2 Avg | Machine 2 Max | Machine 3 Avg | Machine 3 Max |
| --- | --- | --- | --- | --- | --- | --- |
| Run 1 | 0.91 | 3 | 1.09 | 6 | 2.31 | 14 |
| Run 2 | 0.94 | 6 | 1.12 | 10 | 3.19 | 16 |
| Run 3 | 0.92 | 11 | 1.07 | 8 | 3.07 | 17 |
| Run 4 | 0.93 | 5 | 1.12 | 5 | 2.88 | 14 |
| Run 5 | 0.92 | 11 | 2.12 | 11 | 1.76 | 13 |

### Clock Drift Analysis

Drift between machines' logical clocks at the end of each run:

| Run | Max Drift | Machine 1 Final | Machine 2 Final | Machine 3 Final |
| --- | --- | --- | --- | --- |
| Run 1 | 116 | 120 | 236 | 234 |
| Run 2 | 114 | 236 | 350 | 346 |
| Run 3 | 171 | 352 | 353 | 182 |
| Run 4 | 11 | 178 | 179 | 168 |
| Run 5 | 5 | 320 | 318 | 315 |

## Summary Reflections

*This section should be filled in with reflections on the experimental results.*


