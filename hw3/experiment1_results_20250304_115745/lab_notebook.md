# Lab Notebook: Experiment 1

## Experimental Setup

- Number of runs: 5
- Duration per run: 60 seconds
- Three virtual machines with varying clock rates

## Observations

### Run 1

#### Clock Rates

- Machine 1: 3 ticks/second
- Machine 2: 4 ticks/second
- Machine 3: 5 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 296
- Max Jump: 11
- Average Jump: 1.70

**Machine 2:**
- Starting Clock Value: 1
- Ending Clock Value: 296
- Max Jump: 9
- Average Jump: 1.26

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 298
- Max Jump: 2
- Average Jump: 1.01

#### Clock Drift Analysis

Maximum drift between logical clocks: 2 units

- Machine 1 final clock: 296
- Machine 2 final clock: 296
- Machine 3 final clock: 298

#### Queue Analysis

Machine 1:
- Max Queue Length: 1.0
- Average Queue Length: 0.12
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 1.0
- Average Queue Length: 0.03
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 1.0
- Average Queue Length: 0.02
- Median Queue Length: 0.00

### Run 2

#### Clock Rates

- Machine 1: 1 ticks/second
- Machine 2: 1 ticks/second
- Machine 3: 6 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 327
- Max Jump: 28
- Average Jump: 5.53

**Machine 2:**
- Starting Clock Value: 1
- Ending Clock Value: 339
- Max Jump: 32
- Average Jump: 5.73

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 352
- Max Jump: 1
- Average Jump: 1.00

#### Clock Drift Analysis

Maximum drift between logical clocks: 25 units

- Machine 1 final clock: 327
- Machine 2 final clock: 339
- Machine 3 final clock: 352

#### Queue Analysis

Machine 1:
- Max Queue Length: 6.0
- Average Queue Length: 2.23
- Median Queue Length: 2.00

Machine 2:
- Max Queue Length: 3.0
- Average Queue Length: 0.77
- Median Queue Length: 1.00

Machine 3:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

### Run 3

#### Clock Rates

- Machine 1: 6 ticks/second
- Machine 2: 1 ticks/second
- Machine 3: 5 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 353
- Max Jump: 2
- Average Jump: 1.01

**Machine 2:**
- Starting Clock Value: 1
- Ending Clock Value: 339
- Max Jump: 24
- Average Jump: 5.73

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 350
- Max Jump: 7
- Average Jump: 1.19

#### Clock Drift Analysis

Maximum drift between logical clocks: 14 units

- Machine 1 final clock: 353
- Machine 2 final clock: 339
- Machine 3 final clock: 350

#### Queue Analysis

Machine 1:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

Machine 2:
- Max Queue Length: 10.0
- Average Queue Length: 3.91
- Median Queue Length: 3.00

Machine 3:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

### Run 4

#### Clock Rates

- Machine 1: 5 ticks/second
- Machine 2: 1 ticks/second
- Machine 3: 5 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 3
- Ending Clock Value: 305
- Max Jump: 3
- Average Jump: 1.03

**Machine 2:**
- Starting Clock Value: 1
- Ending Clock Value: 303
- Max Jump: 31
- Average Jump: 5.12

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 305
- Max Jump: 2
- Average Jump: 1.04

#### Clock Drift Analysis

Maximum drift between logical clocks: 2 units

- Machine 1 final clock: 305
- Machine 2 final clock: 303
- Machine 3 final clock: 305

#### Queue Analysis

Machine 1:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

Machine 2:
- Max Queue Length: 7.0
- Average Queue Length: 2.30
- Median Queue Length: 2.00

Machine 3:
- Max Queue Length: 1.0
- Average Queue Length: 0.07
- Median Queue Length: 0.00

### Run 5

#### Clock Rates

- Machine 1: 2 ticks/second
- Machine 2: 6 ticks/second
- Machine 3: 3 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 344
- Max Jump: 21
- Average Jump: 2.91

**Machine 2:**
- Starting Clock Value: 2
- Ending Clock Value: 349
- Max Jump: 1
- Average Jump: 1.00

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 349
- Max Jump: 16
- Average Jump: 1.97

#### Clock Drift Analysis

Maximum drift between logical clocks: 5 units

- Machine 1 final clock: 344
- Machine 2 final clock: 349
- Machine 3 final clock: 349

#### Queue Analysis

Machine 1:
- Max Queue Length: 2.0
- Average Queue Length: 0.18
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

Machine 3:
- Max Queue Length: 1.0
- Average Queue Length: 0.15
- Median Queue Length: 0.00

## Cross-Run Analysis

This section analyzes patterns and observations across all experimental runs.

### Logical Clock Jump Analysis

Average and maximum jumps by machine across runs:

| Run | Machine 1 Avg | Machine 1 Max | Machine 2 Avg | Machine 2 Max | Machine 3 Avg | Machine 3 Max |
| --- | --- | --- | --- | --- | --- | --- |
| Run 1 | 1.70 | 11 | 1.26 | 9 | 1.01 | 2 |
| Run 2 | 5.53 | 28 | 5.73 | 32 | 1.00 | 1 |
| Run 3 | 1.01 | 2 | 5.73 | 24 | 1.19 | 7 |
| Run 4 | 1.03 | 3 | 5.12 | 31 | 1.04 | 2 |
| Run 5 | 2.91 | 21 | 1.00 | 1 | 1.97 | 16 |

### Clock Drift Analysis

Drift between machines' logical clocks at the end of each run:

| Run | Max Drift | Machine 1 Final | Machine 2 Final | Machine 3 Final |
| --- | --- | --- | --- | --- |
| Run 1 | 2 | 296 | 296 | 298 |
| Run 2 | 25 | 327 | 339 | 352 |
| Run 3 | 14 | 353 | 339 | 350 |
| Run 4 | 2 | 305 | 303 | 305 |
| Run 5 | 5 | 344 | 349 | 349 |

