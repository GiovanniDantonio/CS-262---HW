# Lab Notebook: Experiment 1

## Experimental Setup

- Number of runs: 5
- Duration per run: 60 seconds
- Three virtual machines with varying clock rates

## Observations

### Run 1

#### Clock Rates

- Machine 1: 4 ticks/second
- Machine 2: 2 ticks/second
- Machine 3: 6 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 5
- Ending Clock Value: 345
- Max Jump: 13
- Average Jump: 1.47

**Machine 2:**
- Starting Clock Value: 3
- Ending Clock Value: 345
- Max Jump: 19
- Average Jump: 2.90

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 353
- Max Jump: 1
- Average Jump: 1.00

#### Clock Drift Analysis

Maximum drift between logical clocks: 8 units

- Machine 1 final clock: 345
- Machine 2 final clock: 345
- Machine 3 final clock: 353

#### Queue Analysis

Machine 1:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

Machine 2:
- Max Queue Length: 1.0
- Average Queue Length: 0.16
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

### Run 2

#### Clock Rates

- Machine 1: 6 ticks/second
- Machine 2: 6 ticks/second
- Machine 3: 1 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 364
- Max Jump: 2
- Average Jump: 1.03

**Machine 2:**
- Starting Clock Value: 1
- Ending Clock Value: 364
- Max Jump: 4
- Average Jump: 1.04

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 323
- Max Jump: 28
- Average Jump: 5.46

#### Clock Drift Analysis

Maximum drift between logical clocks: 41 units

- Machine 1 final clock: 364
- Machine 2 final clock: 364
- Machine 3 final clock: 323

#### Queue Analysis

Machine 1:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

Machine 2:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

Machine 3:
- Max Queue Length: 10.0
- Average Queue Length: 3.38
- Median Queue Length: 3.00

### Run 3

#### Clock Rates

- Machine 1: 5 ticks/second
- Machine 2: 4 ticks/second
- Machine 3: 2 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 296
- Max Jump: 2
- Average Jump: 1.01

**Machine 2:**
- Starting Clock Value: 1
- Ending Clock Value: 294
- Max Jump: 6
- Average Jump: 1.25

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 287
- Max Jump: 22
- Average Jump: 2.40

#### Clock Drift Analysis

Maximum drift between logical clocks: 9 units

- Machine 1 final clock: 296
- Machine 2 final clock: 294
- Machine 3 final clock: 287

#### Queue Analysis

Machine 1:
- Max Queue Length: 1.0
- Average Queue Length: 0.09
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 1.0
- Average Queue Length: 0.10
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 2.0
- Average Queue Length: 0.17
- Median Queue Length: 0.00

### Run 4

#### Clock Rates

- Machine 1: 2 ticks/second
- Machine 2: 3 ticks/second
- Machine 3: 5 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 280
- Max Jump: 11
- Average Jump: 2.36

**Machine 2:**
- Starting Clock Value: 1
- Ending Clock Value: 292
- Max Jump: 20
- Average Jump: 1.65

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 295
- Max Jump: 1
- Average Jump: 1.00

#### Clock Drift Analysis

Maximum drift between logical clocks: 15 units

- Machine 1 final clock: 280
- Machine 2 final clock: 292
- Machine 3 final clock: 295

#### Queue Analysis

Machine 1:
- Max Queue Length: 2.0
- Average Queue Length: 0.25
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 1.0
- Average Queue Length: 0.19
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

### Run 5

#### Clock Rates

- Machine 1: 3 ticks/second
- Machine 2: 4 ticks/second
- Machine 3: 4 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 241
- Max Jump: 9
- Average Jump: 1.36

**Machine 2:**
- Starting Clock Value: 1
- Ending Clock Value: 249
- Max Jump: 2
- Average Jump: 1.06

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 249
- Max Jump: 2
- Average Jump: 1.05

#### Clock Drift Analysis

Maximum drift between logical clocks: 8 units

- Machine 1 final clock: 241
- Machine 2 final clock: 249
- Machine 3 final clock: 249

#### Queue Analysis

Machine 1:
- Max Queue Length: 1.0
- Average Queue Length: 0.11
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 1.0
- Average Queue Length: 0.03
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

## Cross-Run Analysis

This section analyzes patterns and observations across all experimental runs.

### Logical Clock Jump Analysis

Average and maximum jumps by machine across runs:

| Run | Machine 1 Avg | Machine 1 Max | Machine 2 Avg | Machine 2 Max | Machine 3 Avg | Machine 3 Max |
| --- | --- | --- | --- | --- | --- | --- |
| Run 1 | 1.47 | 13 | 2.90 | 19 | 1.00 | 1 |
| Run 2 | 1.03 | 2 | 1.04 | 4 | 5.46 | 28 |
| Run 3 | 1.01 | 2 | 1.25 | 6 | 2.40 | 22 |
| Run 4 | 2.36 | 11 | 1.65 | 20 | 1.00 | 1 |
| Run 5 | 1.36 | 9 | 1.06 | 2 | 1.05 | 2 |

### Clock Drift Analysis

Drift between machines' logical clocks at the end of each run:

| Run | Max Drift | Machine 1 Final | Machine 2 Final | Machine 3 Final |
| --- | --- | --- | --- | --- |
| Run 1 | 8 | 345 | 345 | 353 |
| Run 2 | 41 | 364 | 364 | 323 |
| Run 3 | 9 | 296 | 294 | 287 |
| Run 4 | 15 | 280 | 292 | 295 |
| Run 5 | 8 | 241 | 249 | 249 |

