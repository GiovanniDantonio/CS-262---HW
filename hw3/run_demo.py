#!/usr/bin/env python3
"""
Demo script for Distributed Systems Simulation with Logical Clocks
"""

import os
import sys
import time
import shutil
import datetime
import argparse
import multiprocessing
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import glob
import main
import analyze_logs
import re
import numpy as np

def ensure_directory_exists(directory):
    """Ensure that a directory exists, create it if it doesn't."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def run_demo(duration=30):
    """
    Run a demonstration of the distributed system simulation.
    
    Args:
        duration: Duration of the simulation in seconds (default: 30)
    """
    # Timestamped demo results directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    demo_dir = f"demo_results_{timestamp}"
    ensure_directory_exists(demo_dir)
    
    # Ensure logs directory exists
    logs_dir = "logs"
    ensure_directory_exists(logs_dir)
    
    print(f"Running simulation for {duration} seconds...")
    orig_argv = sys.argv
    sys.argv = ["main.py", "--duration", str(duration)]
    
    # Run main function from main module
    main.main()
    
    # Restore original sys.argv
    sys.argv = orig_argv
    
    # Parse logs and analyze
    print("Analyzing logs...")
    dfs = []
    machine_ids = []
    analysis_results = {}
    for machine_id in range(1, 4):
        log_file = f"logs/machine_{machine_id}.log"
        if os.path.exists(log_file):
            df = analyze_logs.parse_log_file(log_file)
            
            if not df.empty:
                dfs.append(df)
                machine_ids.append(machine_id)
                
                # Store analysis results
                analysis_results[machine_id] = {
                    'dataframe': df,
                    'total_events': len(df),
                    'event_distribution': df['event_type'].value_counts().to_dict(),
                    'logical_clock_stats': analyze_logs.analyze_clock_jumps(df),
                }
                
                # Add queue stats if there are RECEIVE events
                if 'RECEIVE' in df['event_type'].values:
                    analysis_results[machine_id]['queue_stats'] = analyze_logs.analyze_queue_lengths(df)
    
    print("Generating visualizations...")
    analyze_logs.plot_logical_clocks(dfs, machine_ids, filename=os.path.join(demo_dir, "logical_clocks.png"))
    analyze_logs.plot_queue_lengths(dfs, machine_ids, filename=os.path.join(demo_dir, "queue_lengths.png"))
    analyze_logs.plot_event_distribution(dfs, machine_ids, filename=os.path.join(demo_dir, "event_distribution.png"))
    
    # Create clock rate comparison + summary statistics
    create_clock_rate_comparison(analysis_results, demo_dir)
    write_summary_statistics(analysis_results, demo_dir)
    
    # Copy logs to demo directory
    for machine_id in range(1, 4):
        log_file = f"logs/machine_{machine_id}.log"
        if os.path.exists(log_file):
            shutil.copy(log_file, os.path.join(demo_dir, f"machine_{machine_id}.log"))
    
    print(f"Demo complete! Results saved to {demo_dir}/ directory")
    return demo_dir

def create_clock_rate_comparison(analysis_results, output_dir):
    """
    Create a visualization comparing clock rates across machines.
    
    Args:
        analysis_results: Dictionary of analysis results by machine
        output_dir: Directory to save the output
    """
    fig, ax = plt.figure(figsize=(10, 6)), plt.gca()
    
    # Get clock rates from logs - we need to parse from the raw logs
    clock_rates = {}
    for machine_id in range(1, 4):
        log_file = f"logs/machine_{machine_id}.log"
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if "Clock Rate:" in line:
                            # Extract clock rate from the line
                            match = re.search(r'Clock Rate: (\d+)', line)
                            if match:
                                clock_rate = int(match.group(1))
                                clock_rates[machine_id] = clock_rate
                                break
            except Exception as e:
                print(f"Error parsing clock rate for machine {machine_id}: {e}")
    
    # Create a bar chart of clock rates
    if clock_rates:
        plt.bar(clock_rates.keys(), clock_rates.values(), color='skyblue')
        plt.xlabel('Machine ID')
        plt.ylabel('Clock Rate (ticks/second)')
        plt.title('Clock Rates Across Machines')
        plt.xticks(list(clock_rates.keys()))
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Save the plot
        plt.savefig(os.path.join(output_dir, 'clock_rate_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()

def write_summary_statistics(analysis_results, output_dir):
    """
    Write summary statistics about the simulation to a text file.
    
    Args:
        analysis_results: Dictionary of analysis results by machine
        output_dir: Directory to save the output
    """
    summary_file = os.path.join(output_dir, 'summary_statistics.txt')
    
    with open(summary_file, 'w') as f:
        f.write("DISTRIBUTED SYSTEM SIMULATION SUMMARY\n")
        f.write("====================================\n\n")
        
        # Get clock rates from logs
        f.write("CLOCK RATES:\n")
        for machine_id in range(1, 4):
            log_file = f"logs/machine_{machine_id}.log"
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as log_f:
                        for line in log_f:
                            if "Clock Rate:" in line:
                                # Extract clock rate from the line
                                match = re.search(r'Clock Rate: (\d+)', line)
                                if match:
                                    clock_rate = int(match.group(1))
                                    f.write(f"  Machine {machine_id}: {clock_rate} ticks/second\n")
                                break
                except Exception as e:
                    f.write(f"  Machine {machine_id}: Error reading clock rate - {e}\n")
        
        f.write("\n")
        
        # Summarize event counts
        f.write("EVENT COUNTS:\n")
        for machine_id, results in analysis_results.items():
            df = results.get('dataframe')
            if df is not None:
                total_events = len(df)
                internal_events = len(df[df['event_type'] == 'INTERNAL'])
                send_events = len(df[df['event_type'] == 'SEND'])
                receive_events = len(df[df['event_type'] == 'RECEIVE'])
                
                f.write(f"  Machine {machine_id}:\n")
                f.write(f"    Total Events: {total_events}\n")
                f.write(f"    Internal Events: {internal_events} ({internal_events/total_events*100:.1f}%)\n")
                f.write(f"    Send Events: {send_events} ({send_events/total_events*100:.1f}%)\n")
                f.write(f"    Receive Events: {receive_events} ({receive_events/total_events*100:.1f}%)\n")
        
        f.write("\n")
        
        # Summarize queue statistics
        f.write("QUEUE STATISTICS:\n")
        for machine_id, results in analysis_results.items():
            df = results.get('dataframe')
            if df is not None and 'queue_length' in df.columns:
                queue_lengths = df['queue_length'].dropna()
                if not queue_lengths.empty:
                    f.write(f"  Machine {machine_id}:\n")
                    f.write(f"    Max Queue Length: {queue_lengths.max()}\n")
                    f.write(f"    Average Queue Length: {queue_lengths.mean():.2f}\n")
                    f.write(f"    Median Queue Length: {queue_lengths.median():.2f}\n")
        
        f.write("\n")
        
        # Summarize logical clock jumps
        f.write("LOGICAL CLOCK ANALYSIS:\n")
        for machine_id, results in analysis_results.items():
            df = results.get('dataframe')
            if df is not None and 'logical_clock' in df.columns:
                # Sort by log time to get events in order
                df_sorted = df.sort_values('log_time')
                
                # Calculate clock jumps (difference between consecutive logical clock values)
                if len(df_sorted) > 1:
                    clock_values = df_sorted['logical_clock'].values
                    jumps = np.diff(clock_values)
                    
                    f.write(f"  Machine {machine_id}:\n")
                    f.write(f"    Starting Clock Value: {clock_values[0]}\n")
                    f.write(f"    Ending Clock Value: {clock_values[-1]}\n")
                    f.write(f"    Max Jump: {jumps.max()}\n")
                    f.write(f"    Average Jump: {jumps.mean():.2f}\n")
        
        f.write("\n")
        f.write("END OF SUMMARY\n")

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run a demonstration of the distributed system simulation")
    parser.add_argument("--duration", type=int, default=30, 
                        help="Duration of the simulation in seconds (default: 30)")
    return parser.parse_args()

if __name__ == "__main__":
    # Use multiprocessing start method 'spawn' for compatibility
    if sys.platform == 'darwin':  # macOS
        multiprocessing.set_start_method('spawn', force=True)
    
    args = parse_arguments()
    demo_dir = run_demo(duration=args.duration)
