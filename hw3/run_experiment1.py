#!/usr/bin/env python3
"""
Experiment 1: Run the distributed system model multiple times with longer durations.

This script runs the simulation 5 times for 1 minute each, and analyzes the results
to examine:
- Size of jumps in logical clock values
- Drift in logical clock values between machines
- Impact of different timings on gaps and queue lengths
"""

import os
import sys
import time
import datetime
import shutil
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import main
import analyze_logs
import re
from run_demo import create_clock_rate_comparison, write_summary_statistics, ensure_directory_exists

def run_experiment(num_runs=5, duration=60):
    """
    Run the experiment multiple times for the specified duration.
    
    Args:
        num_runs: Number of simulation runs
        duration: Duration of each run in seconds
    
    Returns:
        Path to the experiment results directory
    """
    # Create a timestamped directory for this experiment
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    exp_dir = os.path.join(os.getcwd(), f"experiment1_results_{timestamp}")
    ensure_directory_exists(exp_dir)
    
    # Create notebook for observations
    notebook_path = os.path.join(exp_dir, "lab_notebook.md")
    with open(notebook_path, 'w') as f:
        f.write("# Lab Notebook: Experiment 1\n\n")
        f.write("## Experimental Setup\n\n")
        f.write(f"- Number of runs: {num_runs}\n")
        f.write(f"- Duration per run: {duration} seconds\n")
        f.write("- Three virtual machines with varying clock rates\n\n")
        f.write("## Observations\n\n")
    
    all_runs_data = {}
    
    # Run the simulation multiple times
    for run in range(1, num_runs + 1):
        print(f"\n=== Running Simulation {run}/{num_runs} ===")
        
        # Create a directory for this run
        run_dir = os.path.join(exp_dir, f"run_{run}")
        ensure_directory_exists(run_dir)
        
        # Reset/clean logs directory
        if os.path.exists("logs"):
            for log_file in os.listdir("logs"):
                if log_file.endswith(".log"):
                    os.remove(os.path.join("logs", log_file))
        else:
            os.makedirs("logs")
        
        # Run the simulation
        print(f"Running simulation for {duration} seconds...")
        orig_argv = sys.argv
        sys.argv = ["main.py", "--duration", str(duration)]
        main.main()
        sys.argv = orig_argv
        
        # Analyze logs
        print("Analyzing logs...")
        machine_ids = [1, 2, 3]
        dfs = []
        analysis_results = {}
        
        # Parse logs for each machine
        for machine_id in machine_ids:
            log_file = f"logs/machine_{machine_id}.log"
            
            # Copy log to run directory
            if os.path.exists(log_file):
                shutil.copy(log_file, os.path.join(run_dir, f"machine_{machine_id}.log"))
                
                # Parse log file
                df = analyze_logs.parse_log_file(log_file)
                dfs.append(df)
                
                # Store analysis results
                analysis_results[machine_id] = {
                    'dataframe': df,
                    'total_events': len(df)
                }
        
        # Generate visualizations
        print("Generating visualizations...")
        analyze_logs.plot_logical_clocks(dfs, machine_ids, filename=os.path.join(run_dir, "logical_clocks.png"))
        analyze_logs.plot_queue_lengths(dfs, machine_ids, filename=os.path.join(run_dir, "queue_lengths.png"))
        analyze_logs.plot_event_distribution(dfs, machine_ids, filename=os.path.join(run_dir, "event_distribution.png"))
        
        # Create clock rate comparison
        create_clock_rate_comparison(analysis_results, run_dir)
        
        # Write summary statistics
        write_summary_statistics(analysis_results, run_dir)
        
        # Store data for overall analysis
        all_runs_data[run] = {
            'dfs': dfs,
            'machine_ids': machine_ids,
            'analysis_results': analysis_results
        }
        
        # Add to notebook
        with open(notebook_path, 'a') as f:
            f.write(f"### Run {run}\n\n")
            
            # Extract clock rates
            f.write("#### Clock Rates\n\n")
            for machine_id in range(1, 4):
                clock_rate = extract_clock_rate(f"logs/machine_{machine_id}.log")
                f.write(f"- Machine {machine_id}: {clock_rate} ticks/second\n")
            f.write("\n")
            
            # Add logical clock analysis
            f.write("#### Logical Clock Analysis\n\n")
            for machine_id, results in analysis_results.items():
                df = results.get('dataframe')
                if df is not None and 'logical_clock' in df.columns:
                    df_sorted = df.sort_values('log_time')
                    if len(df_sorted) > 1:
                        clock_values = df_sorted['logical_clock'].values
                        jumps = np.diff(clock_values)
                        f.write(f"**Machine {machine_id}:**\n")
                        f.write(f"- Starting Clock Value: {clock_values[0]}\n")
                        f.write(f"- Ending Clock Value: {clock_values[-1]}\n")
                        f.write(f"- Max Jump: {jumps.max()}\n")
                        f.write(f"- Average Jump: {jumps.mean():.2f}\n\n")
            
            # Add drift analysis
            f.write("#### Clock Drift Analysis\n\n")
            if len(machine_ids) >= 2:
                final_clocks = {}
                for machine_id, results in analysis_results.items():
                    df = results.get('dataframe')
                    if df is not None and 'logical_clock' in df.columns:
                        df_sorted = df.sort_values('log_time')
                        if not df_sorted.empty:
                            final_clocks[machine_id] = df_sorted['logical_clock'].iloc[-1]
                
                if len(final_clocks) >= 2:
                    max_drift = max(final_clocks.values()) - min(final_clocks.values())
                    f.write(f"Maximum drift between logical clocks: {max_drift} units\n\n")
                    for machine_id, final_clock in final_clocks.items():
                        f.write(f"- Machine {machine_id} final clock: {final_clock}\n")
                    f.write("\n")
            
            # Add queue analysis
            f.write("#### Queue Analysis\n\n")
            for machine_id, results in analysis_results.items():
                df = results.get('dataframe')
                if df is not None and 'queue_length' in df.columns:
                    queue_lengths = df['queue_length'].dropna()
                    if not queue_lengths.empty:
                        f.write(f"**Machine {machine_id}:**\n")
                        f.write(f"- Max Queue Length: {queue_lengths.max()}\n")
                        f.write(f"- Average Queue Length: {queue_lengths.mean():.2f}\n")
                        f.write(f"- Median Queue Length: {queue_lengths.median():.2f}\n\n")
    
    # Generate overall analysis
    generate_cross_run_analysis(all_runs_data, exp_dir, notebook_path)
    
    print(f"\nExperiment 1 complete! Results saved to {exp_dir}/ directory")
    print(f"Lab notebook available at: {notebook_path}")
    return exp_dir

def extract_clock_rate(log_file):
    """Extract the clock rate from a log file."""
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    if "Clock Rate:" in line:
                        match = re.search(r'Clock Rate: (\d+)', line)
                        if match:
                            return int(match.group(1))
        except Exception:
            pass
    return "Unknown"

def generate_cross_run_analysis(all_runs_data, exp_dir, notebook_path):
    """Generate analysis across all runs."""
    with open(notebook_path, 'a') as f:
        f.write("## Cross-Run Analysis\n\n")
        f.write("This section analyzes patterns and observations across all experimental runs.\n\n")
        
        # Analyze clock jumps across runs
        f.write("### Logical Clock Jump Analysis\n\n")
        jump_data = {}
        for run, run_data in all_runs_data.items():
            for machine_id, results in run_data['analysis_results'].items():
                key = f"Machine {machine_id}"
                if key not in jump_data:
                    jump_data[key] = []
                
                df = results.get('dataframe')
                if df is not None and 'logical_clock' in df.columns:
                    df_sorted = df.sort_values('log_time')
                    if len(df_sorted) > 1:
                        jumps = np.diff(df_sorted['logical_clock'].values)
                        avg_jump = jumps.mean()
                        max_jump = jumps.max()
                        jump_data[key].append((avg_jump, max_jump))
        
        # Create a summary table of jumps
        f.write("Average and maximum jumps by machine across runs:\n\n")
        f.write("| Run | " + " | ".join([f"{key} Avg | {key} Max" for key in sorted(jump_data.keys())]) + " |\n")
        f.write("| --- | " + " | ".join(["--- | ---" for _ in range(len(jump_data))]) + " |\n")
        
        for run in range(len(next(iter(jump_data.values())))):
            row = [f"Run {run+1}"]
            for key in sorted(jump_data.keys()):
                if run < len(jump_data[key]):
                    avg, max_val = jump_data[key][run]
                    row.append(f"{avg:.2f}")
                    row.append(f"{max_val}")
                else:
                    row.append("N/A")
                    row.append("N/A")
            f.write("| " + " | ".join(row) + " |\n")
        
        f.write("\n")
        
        # Analyze drift across runs
        f.write("### Clock Drift Analysis\n\n")
        f.write("Drift between machines' logical clocks at the end of each run:\n\n")
        f.write("| Run | Max Drift | Machine 1 Final | Machine 2 Final | Machine 3 Final |\n")
        f.write("| --- | --- | --- | --- | --- |\n")
        
        for run, run_data in all_runs_data.items():
            final_clocks = {}
            for machine_id, results in run_data['analysis_results'].items():
                df = results.get('dataframe')
                if df is not None and 'logical_clock' in df.columns:
                    df_sorted = df.sort_values('log_time')
                    if not df_sorted.empty:
                        final_clocks[machine_id] = df_sorted['logical_clock'].iloc[-1]
            
            if len(final_clocks) >= 2:
                max_drift = max(final_clocks.values()) - min(final_clocks.values())
                row = [
                    f"Run {run}",
                    f"{max_drift}",
                    f"{final_clocks.get(1, 'N/A')}",
                    f"{final_clocks.get(2, 'N/A')}",
                    f"{final_clocks.get(3, 'N/A')}"
                ]
                f.write("| " + " | ".join(row) + " |\n")
        
        f.write("\n")
        
        # Add summary reflections section for the user to fill in
        f.write("## Summary Reflections\n\n")
        f.write("*This section should be filled in with reflections on the experimental results.*\n\n")
        f.write("Consider addressing these questions:\n\n")
        f.write("1. How large were the jumps in the logical clock values, and what factors affected them?\n")
        f.write("2. How significant was the drift between machines' logical clocks?\n")
        f.write("3. What impact did different clock rates have on queue lengths?\n")
        f.write("4. Were there any unexpected patterns or behaviors observed?\n")
        f.write("5. How do the observations relate to the theoretical concepts of logical clocks?\n\n")

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run distributed system experiments")
    parser.add_argument("--runs", type=int, default=5, help="Number of simulation runs")
    parser.add_argument("--duration", type=int, default=60, help="Duration of each run in seconds")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    run_experiment(num_runs=args.runs, duration=args.duration)
