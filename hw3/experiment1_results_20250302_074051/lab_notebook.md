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
- Ending Clock Value: 118
- Max Jump: 1
- Average Jump: 0.87

**Machine 2:**
- Starting Clock Value: 1
- Ending Clock Value: 235
- Max Jump: 3
- Average Jump: 1.09

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 232
- Max Jump: 10
- Average Jump: 2.20

#### Clock Drift Analysis

Maximum drift between logical clocks: 117 units

- Machine 1 final clock: 118
- Machine 2 final clock: 235
- Machine 3 final clock: 232

#### Queue Analysis

Machine 1:
- Max Queue Length: nan
- Average Queue Length: nan
- Median Queue Length: nan
- Note: No messages were received by this machine

Machine 2:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

Machine 3:
- Max Queue Length: 2.0
- Average Queue Length: 0.39
- Median Queue Length: 0.00

### Run 2

#### Clock Rates

- Machine 1: 5 ticks/second
- Machine 2: 6 ticks/second
- Machine 3: 6 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 295
- Max Jump: 1
- Average Jump: 0.91

**Machine 2:**
- Starting Clock Value: 4
- Ending Clock Value: 353
- Max Jump: 3
- Average Jump: 1.08

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 354
- Max Jump: 5
- Average Jump: 1.22

#### Clock Drift Analysis

Maximum drift between logical clocks: 59 units

- Machine 1 final clock: 295
- Machine 2 final clock: 353
- Machine 3 final clock: 354

#### Queue Analysis

Machine 1:
- Max Queue Length: nan
- Average Queue Length: nan
- Median Queue Length: nan
- Note: No messages were received by this machine

Machine 2:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

Machine 3:
- Max Queue Length: 2.0
- Average Queue Length: 0.19
- Median Queue Length: 0.00

### Run 3

#### Clock Rates

- Machine 1: 2 ticks/second
- Machine 2: 6 ticks/second
- Machine 3: 2 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 119
- Max Jump: 1
- Average Jump: 0.91

**Machine 2:**
- Starting Clock Value: 1
- Ending Clock Value: 345
- Max Jump: 2
- Average Jump: 1.09

**Machine 3:**
- Starting Clock Value: 2
- Ending Clock Value: 342
- Max Jump: 17
- Average Jump: 3.24

#### Clock Drift Analysis

Maximum drift between logical clocks: 226 units

- Machine 1 final clock: 119
- Machine 2 final clock: 345
- Machine 3 final clock: 342

#### Queue Analysis

Machine 1:
- Max Queue Length: nan
- Average Queue Length: nan
- Median Queue Length: nan
- Note: No messages were received by this machine

Machine 2:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

Machine 3:
- Max Queue Length: 2.0
- Average Queue Length: 0.39
- Median Queue Length: 0.00

### Run 4

#### Clock Rates

- Machine 1: 3 ticks/second
- Machine 2: 4 ticks/second
- Machine 3: 1 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 178
- Max Jump: 1
- Average Jump: 0.89

**Machine 2:**
- Starting Clock Value: 2
- Ending Clock Value: 236
- Max Jump: 2
- Average Jump: 1.04

**Machine 3:**
- Starting Clock Value: 2
- Ending Clock Value: 185
- Max Jump: 17
- Average Jump: 3.16

#### Clock Drift Analysis

Maximum drift between logical clocks: 58 units

- Machine 1 final clock: 178
- Machine 2 final clock: 236
- Machine 3 final clock: 185

#### Queue Analysis

Machine 1:
- Max Queue Length: nan
- Average Queue Length: nan
- Median Queue Length: nan
- Note: No messages were received by this machine

Machine 2:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

Machine 3:
- Max Queue Length: 18
- Average Queue Length: 10.17
- Median Queue Length: 12.00

### Run 5

#### Clock Rates

- Machine 1: 2 ticks/second
- Machine 2: 4 ticks/second
- Machine 3: 5 ticks/second

#### Logical Clock Analysis

**Machine 1:**
- Starting Clock Value: 1
- Ending Clock Value: 119
- Max Jump: 1
- Average Jump: 0.94

**Machine 2:**
- Starting Clock Value: 1
- Ending Clock Value: 235
- Max Jump: 3
- Average Jump: 1.13

**Machine 3:**
- Starting Clock Value: 1
- Ending Clock Value: 295
- Max Jump: 4
- Average Jump: 1.32

#### Clock Drift Analysis

Maximum drift between logical clocks: 176 units

- Machine 1 final clock: 119
- Machine 2 final clock: 235
- Machine 3 final clock: 295

#### Queue Analysis

Machine 1:
- Max Queue Length: nan
- Average Queue Length: nan
- Median Queue Length: nan
- Note: No messages were received by this machine

Machine 2:
- Max Queue Length: 0.0
- Average Queue Length: 0.00
- Median Queue Length: 0.00
- Note: No messages were received by this machine

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
| Run 1 | 0.87 | 1 | 1.09 | 3 | 2.20 | 10 |
| Run 2 | 0.91 | 1 | 1.08 | 3 | 1.22 | 5 |
| Run 3 | 0.91 | 1 | 1.09 | 2 | 3.24 | 17 |
| Run 4 | 0.89 | 1 | 1.04 | 2 | 3.16 | 17 |
| Run 5 | 0.94 | 1 | 1.13 | 3 | 1.32 | 4 |

### Clock Drift Analysis

Drift between machines' logical clocks at the end of each run:

| Run | Max Drift | Machine 1 Final | Machine 2 Final | Machine 3 Final |
| --- | --- | --- | --- | --- |
| Run 1 | 117 | 118 | 235 | 232 |
| Run 2 | 59 | 295 | 353 | 354 |
| Run 3 | 226 | 119 | 345 | 342 |
| Run 4 | 58 | 178 | 236 | 185 |
| Run 5 | 176 | 119 | 235 | 295 |

## Summary Reflections

*This section should be filled in with reflections on the experimental results.*

Consider addressing these questions:

1. How large were the jumps in the logical clock values, and what factors affected them?
2. How significant was the drift between machines' logical clocks?
3. What impact did different clock rates have on queue lengths?
4. Were there any unexpected patterns or behaviors observed?
5. How do the observations relate to the theoretical concepts of logical clocks?

