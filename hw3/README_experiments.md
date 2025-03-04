# Distributed System Simulation Experiments

This directory contains scripts for running experiments on the distributed system simulation.

## Available Scripts

### 1. run_demo.py
The demo script that runs a single simulation and generates visualizations and statistics.
- Creates logical clock plots
- Creates queue length plots
- Creates event distribution charts
- Generates summary statistics

### 2. run_experiment1.py
Runs the simulation multiple times with longer durations to analyze:
- Size of jumps in logical clock values
- Drift in logical clock values between machines
- Impact of different timings on queue lengths

Usage:
```
python run_experiment1.py --runs 5 --duration 60
```

Parameters:
- `--runs`: Number of simulation runs (default: 5)
- `--duration`: Duration of each run in seconds (default: 60)

Output:
- Creates a timestamped directory for all runs
- Provides visual comparisons and statistics across runs

### 3. run_experiment2.py
Tests the simulation with different parameter configurations:
1. Baseline with default parameters
2. Smaller variation in clock cycles (3-4 ticks/sec)
3. Smaller probability of internal events (0.4)
4. Both modifications combined

Usage:
```
python run_experiment2.py --duration 60
```

Parameters:
- `--duration`: Duration of each configuration run in seconds (default: 60)

Output:
- Creates a timestamped directory with subdirectories for each configuration
- Automatically modifies virtual_machine.py parameters for each run and restores defaults afterward

## Analysis

Both experiment scripts generate detailed analysis with:
- Raw data on logical clock jumps, drift, and queue lengths
- Comparative analysis across runs/configurations
- Visualizations for each run/configuration
- Areas for adding reflections on the results
