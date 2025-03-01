# Lab Notebook - Distributed System with Logical Clocks

## Design Decisions

### System Architecture
- We decided to implement each virtual machine as a separate process using Python's `multiprocessing` module
- Communication between machines is done using sockets
- Each machine maintains its own message queue and logical clock

### Logical Clock Implementation
- Following Lamport's rules for logical clocks:
  - Increment on internal events
  - On send: increment then send
  - On receive: set to max(local_clock, received_clock) + 1

### Random Event Generation
- Each machine generates events randomly on each clock cycle:
  - Values 1-3: Send messages to other machines
  - Values 4-10: Internal events

## Experimental Results

(Experiments will be recorded here after running the simulation)

### Experiment 1 (Date: 2025-03-01)
- Configuration: Standard, Duration: 60 seconds
- Observations: Check analysis in `experiment_results_20250301_133753/standard_experiment_1/analysis.txt` and plots in `experiment_results_20250301_133753/standard_experiment_1`.
- Analysis: TBD

### Experiment 2 (Date: 2025-03-01)
- Configuration: Standard, Duration: 60 seconds
- Observations: Check analysis in `experiment_results_20250301_133753/standard_experiment_2/analysis.txt` and plots in `experiment_results_20250301_133753/standard_experiment_2`.
- Analysis: TBD

### Experiment 3 (Date: 2025-03-01)
- Configuration: Standard, Duration: 60 seconds
- Observations: Check analysis in `experiment_results_20250301_133753/standard_experiment_3/analysis.txt` and plots in `experiment_results_20250301_133753/standard_experiment_3`.
- Analysis: TBD

### Experiment 4 (Date: 2025-03-01)
- Configuration: Standard, Duration: 60 seconds
- Observations: Check analysis in `experiment_results_20250301_133753/standard_experiment_4/analysis.txt` and plots in `experiment_results_20250301_133753/standard_experiment_4`.
- Analysis: TBD

### Experiment 5 (Date: 2025-03-01)
- Configuration: Standard, Duration: 60 seconds
- Observations: Check analysis in `experiment_results_20250301_133753/standard_experiment_5/analysis.txt` and plots in `experiment_results_20250301_133753/standard_experiment_5`.
- Analysis: TBD

### Modified Experiment 1 (Date: 2025-03-01)
- Modified parameters: Lower clock variation
- Configuration: clock_rate = random.randint(3, 6), Duration: 60 seconds
- Observations: Check analysis in `experiment_results_20250301_133753/modified_experiment_1/analysis.txt` and plots in `experiment_results_20250301_133753/modified_experiment_1`.
- Analysis: TBD

### Modified Experiment 2 (Date: 2025-03-01)
- Modified parameters: Higher send probability
- Configuration: event = random.randint(1, 5), Duration: 60 seconds
- Observations: Check analysis in `experiment_results_20250301_133753/modified_experiment_2/analysis.txt` and plots in `experiment_results_20250301_133753/modified_experiment_2`.
- Analysis: TBD

