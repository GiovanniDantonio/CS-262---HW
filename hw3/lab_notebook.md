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

### Experiment 1 (Date: TBD)
- Configuration:
- Observations:
- Analysis:

### Experiment 2 (Date: TBD)
- Configuration:
- Observations:
- Analysis:

(And so on for at least 5 experiments)

## Additional Experiments with Modified Parameters

### Modified Experiment 1 (Date: TBD)
- Modified parameters:
- Observations:
- Analysis:

## Conclusions

(Final conclusions will be added after all experiments are complete)
