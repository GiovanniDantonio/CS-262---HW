# Distributed System Model with Logical Clocks

This project implements a model of a small, asynchronous distributed system with logical clocks. 
It simulates multiple machines running at different speeds on a single physical machine.

## Overview

- Each virtual machine runs at a random clock rate (1-6 ticks per second)
- Machines communicate via sockets
- Each machine implements a logical clock following Lamport's rules
- Events include:
  - Internal events
  - Sending messages to one other machine
  - Sending messages to both other machines
  - Receiving messages

## Running the Simulation

```bash
python main.py
```

## Lab Notebook

Observations and analysis of the simulation results are documented in `lab_notebook.md`.
