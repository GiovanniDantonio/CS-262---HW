# Lab Notebook: Experiment 1

## Experimental Setup

- Number of runs: 5
- Duration per run: 60 seconds
- Three virtual machines with varying clock rates

## Observations

### Run 1

#### Clock Rates

- Machine 1: 6 ticks/second
- Machine 2: 2 ticks/second
- Machine 3: 1 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 352
- Max Jump: 1
- Average Jump: 0.91

**Machine 2:**
- Starting Clock Value: 2
- Ending Clock Value: 348
- Max Jump: 15
- Average Jump: 2.77

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 268
- Max Jump: 36
- Average Jump: 4.53

#### Clock Drift Analysis

Maximum drift between logical clocks: 84 units

- Machine 1 final clock: 352
- Machine 2 final clock: 348
- Machine 3 final clock: 268

#### Queue Analysis

Machine 1:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

Machine 2:
- Max Queue Length: 2.0
- Average Queue Length: 0.44
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 20.0
- Average Queue Length: 8.51
- Median Queue Length: 7.00

### Run 2

#### Clock Rates

- Machine 1: 6 ticks/second
- Machine 2: 4 ticks/second
- Machine 3: 1 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 352
- Max Jump: 2
- Average Jump: 0.94

**Machine 2:**
- Starting Clock Value: 1
- Ending Clock Value: 352
- Max Jump: 10
- Average Jump: 1.39

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 207
- Max Jump: 14
- Average Jump: 3.49

#### Clock Drift Analysis

Maximum drift between logical clocks: 145 units

- Machine 1 final clock: 352
- Machine 2 final clock: 352
- Machine 3 final clock: 207

#### Queue Analysis

Machine 1:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

Machine 2:
- Max Queue Length: 1.0
- Average Queue Length: 0.08
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 40.0
- Average Queue Length: 21.81
- Median Queue Length: 22.50

### Run 3

#### Clock Rates

- Machine 1: 1 ticks/second
- Machine 2: 4 ticks/second
- Machine 3: 3 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 2
- Ending Clock Value: 184
- Max Jump: 9
- Average Jump: 3.08

**Machine 2:**
- Starting Clock Value: 1
- Ending Clock Value: 238
- Max Jump: 2
- Average Jump: 0.93

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 238
- Max Jump: 10
- Average Jump: 1.23

#### Clock Drift Analysis

Maximum drift between logical clocks: 54 units

- Machine 1 final clock: 184
- Machine 2 final clock: 238
- Machine 3 final clock: 238

#### Queue Analysis

Machine 1:
- Max Queue Length: 14
- Average Queue Length: 6.57
- Median Queue Length: 5.00

Machine 2:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

Machine 3:
- Max Queue Length: 1.0
- Average Queue Length: 0.09
- Median Queue Length: 0.00

### Run 4

#### Clock Rates

- Machine 1: 2 ticks/second
- Machine 2: 3 ticks/second
- Machine 3: 4 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 238
- Max Jump: 7
- Average Jump: 1.96

**Machine 2:**
- Starting Clock Value: 2
- Ending Clock Value: 238
- Max Jump: 7
- Average Jump: 1.22

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 244
- Max Jump: 2
- Average Jump: 0.92

#### Clock Drift Analysis

Maximum drift between logical clocks: 6 units

- Machine 1 final clock: 238
- Machine 2 final clock: 238
- Machine 3 final clock: 244

#### Queue Analysis

Machine 1:
- Max Queue Length: 2.0
- Average Queue Length: 0.41
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 1.0
- Average Queue Length: 0.10
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

### Run 5

#### Clock Rates

- Machine 1: 5 ticks/second
- Machine 2: 3 ticks/second
- Machine 3: 2 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 2
- Ending Clock Value: 294
- Max Jump: 1
- Average Jump: 0.93

**Machine 2:**
- Starting Clock Value: 1
- Ending Clock Value: 287
- Max Jump: 11
- Average Jump: 1.55

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 287
- Max Jump: 16
- Average Jump: 2.38

#### Clock Drift Analysis

Maximum drift between logical clocks: 7 units

- Machine 1 final clock: 294
- Machine 2 final clock: 287
- Machine 3 final clock: 287

#### Queue Analysis

Machine 1:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

Machine 2:
- Max Queue Length: 2.0
- Average Queue Length: 0.19
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 2.0
- Average Queue Length: 0.35
- Median Queue Length: 0.00

## Cross-Run Analysis

This section analyzes patterns and observations across all experimental runs.

### Logical Clock Jump Analysis

Average and maximum jumps by machine across runs:

| Run | Machine 1 Avg | Machine 1 Max | Machine 2 Avg | Machine 2 Max | Machine 3 Avg | Machine 3 Max |
| --- | --- | --- | --- | --- | --- | --- |
| Run 1 | 0.91 | 1 | 2.77 | 15 | 4.53 | 36 |
| Run 2 | 0.94 | 2 | 1.39 | 10 | 3.49 | 14 |
| Run 3 | 3.08 | 9 | 0.93 | 2 | 1.23 | 10 |
| Run 4 | 1.96 | 7 | 1.22 | 7 | 0.92 | 2 |
| Run 5 | 0.93 | 1 | 1.55 | 11 | 2.38 | 16 |

### Clock Drift Analysis

Drift between machines' logical clocks at the end of each run:

| Run | Max Drift | Machine 1 Final | Machine 2 Final | Machine 3 Final |
| --- | --- | --- | --- | --- |
| Run 1 | 84 | 352 | 348 | 268 |
| Run 2 | 145 | 352 | 352 | 207 |
| Run 3 | 54 | 184 | 238 | 238 |
| Run 4 | 6 | 238 | 238 | 244 |
| Run 5 | 7 | 294 | 287 | 287 |

