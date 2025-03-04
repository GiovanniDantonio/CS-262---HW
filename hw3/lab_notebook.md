# Lab Notebook - Distributed System with Logical Clocks

## Design Decisions

### System Architecture
- We decided to implement each virtual machine as a separate process using Python's `multiprocessing` module. We did this since, per Jared's Ed Post, ``the point is to model a distributed system with machines that have different clock rates, and that it doesn't make much sense for them to have shared memory if they're just communicating with each other, using processes probably makes more sense.''
- Communication between machines is done using sockets
- Each machine maintains its own message queue and logical clock

### Logical Clock Implementation
- Increment on internal events
- On send: increment then send
- On receive: set to max(local_clock, received_clock) + 1

### Random Event Generation
- Each machine generates events randomly on each clock cycle:
  - Values 1-3: Send messages to other machines
  - Values 4-10: Internal events

## Experimental Results

### Experiment 1 (Date: 2025-03-01)
- Configuration: Standard, Duration: 60 seconds
- Observations: Check plots and analysis in `experiment_1/analysis.txt`.

### Experiment 2 (Date: 2025-03-01)
- Configuration: Standard, Duration: 60 seconds
- Observations: Check plots and analysis in `experiment_1/analysis.txt`.

### Experiment 3 (Date: 2025-03-02)
- Configuration: Standard, Duration: 60 seconds
- Observations: Check plots and analysis in `experiment_1/analysis.txt`.

### Experiment 4 (Date: 2025-03-04)
- Configuration: Standard, Duration: 60 seconds
- Observations: Check plots and analysis in `experiment_1/analysis.txt`.

### Experiment 5 (Date: 2025-03-04)
- Configuration: Standard, Duration: 60 seconds
- Observations: Check plots and analysis in `experiment_1/analysis.txt`.

### Modified Experiment 1 (Date: 2025-03-01)
- Modified parameters: Lower clock variation
- Configuration: clock_rate = random.randint(3, 6), Duration: 60 seconds
- Observations: Check analysis and plots in `experiment2_results`.

### Modified Experiment 2 (Date: 2025-03-04)
- Modified parameters: Higher send probability
- Configuration: event = random.randint(1, 5), Duration: 60 seconds
- Observations: Check analysis and plots in `experiment2_results`.
