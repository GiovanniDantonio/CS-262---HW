# Lab Notebook: Experiment 1

## Experimental Setup

- Number of runs: 5
- Duration per run: 60 seconds
- Three virtual machines with varying clock rates

## Observations

### Run 1

#### Clock Rates

- Machine 1: 5 ticks/second
- Machine 2: 1 ticks/second
- Machine 3: 3 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 298
- Max Jump: 2
- Average Jump: 0.90

**Machine 2:**
- Starting Clock Value: 1
- Ending Clock Value: 181
- Max Jump: 12
- Average Jump: 3.05

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 294
- Max Jump: 12
- Average Jump: 1.53

#### Clock Drift Analysis

Maximum drift between logical clocks: 117 units

- Machine 1 final clock: 298
- Machine 2 final clock: 181
- Machine 3 final clock: 294

#### Queue Analysis

Machine 1:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

Machine 2:
- Max Queue Length: 24.0
- Average Queue Length: 15.47
- Median Queue Length: 17.00

Machine 3:
- Max Queue Length: 2.0
- Average Queue Length: 0.21
- Median Queue Length: 0.00

### Run 2

#### Clock Rates

- Machine 1: 5 ticks/second
- Machine 2: 5 ticks/second
- Machine 3: 5 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 328
- Max Jump: 3
- Average Jump: 1.06

**Machine 2:**
- Starting Clock Value: 1
- Ending Clock Value: 328
- Max Jump: 3
- Average Jump: 1.05

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 328
- Max Jump: 3
- Average Jump: 1.03

#### Clock Drift Analysis

Maximum drift between logical clocks: 0 units

- Machine 1 final clock: 328
- Machine 2 final clock: 328
- Machine 3 final clock: 328

#### Queue Analysis

Machine 1:
- Max Queue Length: 2.0
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

### Run 3

#### Clock Rates

- Machine 1: 1 ticks/second
- Machine 2: 5 ticks/second
- Machine 3: 4 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 2
- Ending Clock Value: 161
- Max Jump: 8
- Average Jump: 2.69

**Machine 2:**
- Starting Clock Value: 1
- Ending Clock Value: 302
- Max Jump: 4
- Average Jump: 0.96

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 302
- Max Jump: 6
- Average Jump: 1.18

#### Clock Drift Analysis

Maximum drift between logical clocks: 141 units

- Machine 1 final clock: 161
- Machine 2 final clock: 302
- Machine 3 final clock: 302

#### Queue Analysis

Machine 1:
- Max Queue Length: 39
- Average Queue Length: 23.05
- Median Queue Length: 27.00

Machine 2:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

Machine 3:
- Max Queue Length: 1.0
- Average Queue Length: 0.06
- Median Queue Length: 0.00

### Run 4

#### Clock Rates

- Machine 1: 6 ticks/second
- Machine 2: 1 ticks/second
- Machine 3: 1 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 351
- Max Jump: 1
- Average Jump: 0.93

**Machine 2:**
- Starting Clock Value: 4
- Ending Clock Value: 332
- Max Jump: 20
- Average Jump: 5.38

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 303
- Max Jump: 21
- Average Jump: 5.12

#### Clock Drift Analysis

Maximum drift between logical clocks: 48 units

- Machine 1 final clock: 351
- Machine 2 final clock: 332
- Machine 3 final clock: 303

#### Queue Analysis

Machine 1:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

Machine 2:
- Max Queue Length: 6.0
- Average Queue Length: 1.11
- Median Queue Length: 1.00

Machine 3:
- Max Queue Length: 9.0
- Average Queue Length: 3.84
- Median Queue Length: 3.00

### Run 5

#### Clock Rates

- Machine 1: 5 ticks/second
- Machine 2: 5 ticks/second
- Machine 3: 6 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 3
- Ending Clock Value: 372
- Max Jump: 6
- Average Jump: 1.21

**Machine 2:**
- Starting Clock Value: 3
- Ending Clock Value: 370
- Max Jump: 5
- Average Jump: 1.18

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 372
- Max Jump: 2
- Average Jump: 0.99

#### Clock Drift Analysis

Maximum drift between logical clocks: 2 units

- Machine 1 final clock: 372
- Machine 2 final clock: 370
- Machine 3 final clock: 372

#### Queue Analysis

Machine 1:
- Max Queue Length: 1.0
- Average Queue Length: 0.12
- Median Queue Length: 0.00

Machine 2:
- Max Queue Length: 1.0
- Average Queue Length: 0.08
- Median Queue Length: 0.00

Machine 3:
- Max Queue Length: 1.0
- Average Queue Length: 0.05
- Median Queue Length: 0.00

## Cross-Run Analysis

This section analyzes patterns and observations across all experimental runs.

### Logical Clock Jump Analysis

Average and maximum jumps by machine across runs:

| Run | Machine 1 Avg | Machine 1 Max | Machine 2 Avg | Machine 2 Max | Machine 3 Avg | Machine 3 Max |
| --- | --- | --- | --- | --- | --- | --- |
| Run 1 | 0.90 | 2 | 3.05 | 12 | 1.53 | 12 |
| Run 2 | 1.06 | 3 | 1.05 | 3 | 1.03 | 3 |
| Run 3 | 2.69 | 8 | 0.96 | 4 | 1.18 | 6 |
| Run 4 | 0.93 | 1 | 5.38 | 20 | 5.12 | 21 |
| Run 5 | 1.21 | 6 | 1.18 | 5 | 0.99 | 2 |

### Clock Drift Analysis

Drift between machines' logical clocks at the end of each run:

| Run | Max Drift | Machine 1 Final | Machine 2 Final | Machine 3 Final |
| --- | --- | --- | --- | --- |
| Run 1 | 117 | 298 | 181 | 294 |
| Run 2 | 0 | 328 | 328 | 328 |
| Run 3 | 141 | 161 | 302 | 302 |
| Run 4 | 48 | 351 | 332 | 303 |
| Run 5 | 2 | 372 | 370 | 372 |

## Summary Reflections

*This section should be filled in with reflections on the experimental results.*

Consider addressing these questions:

1. How large were the jumps in the logical clock values, and what factors affected them?
2. How significant was the drift between machines' logical clocks?
3. What impact did different clock rates have on queue lengths?
4. Were there any unexpected patterns or behaviors observed?
5. How do the observations relate to the theoretical concepts of logical clocks?

