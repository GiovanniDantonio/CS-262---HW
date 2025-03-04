#!/usr/bin/env python3
"""
Experiment 2: Run the distributed system model with parameter variations.

This script runs the simulation with:
1. Default parameters (baseline)
2. Smaller variation in clock cycles 
3. Smaller probability of internal events
4. Both modifications combined

Then analyzes and compares the results to identify differences.
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

def run_experiment(duration=60):
    """
    Run experiment with different parameter variations.
    
    Args:
        duration: Duration of each run in seconds
    
    Returns:
        Path to the experiment results directory
    """
    # Create a timestamped directory for this experiment
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    exp_dir = os.path.join(os.getcwd(), f"experiment2_results_{timestamp}")
    ensure_directory_exists(exp_dir)
    
    # Create notebook for observations
    notebook_path = os.path.join(exp_dir, "lab_notebook.md")
    with open(notebook_path, 'w') as f:
        f.write("# Lab Notebook: Experiment 2\n\n")
        f.write("## Experimental Setup\n\n")
        f.write(f"- Duration per configuration: {duration} seconds\n")
        f.write("- Four configurations tested:\n")
        f.write("  1. Baseline (default parameters)\n")
        f.write("  2. Smaller variation in clock cycles\n")
        f.write("  3. Smaller probability of internal events\n")
        f.write("  4. Both modifications combined\n\n")
        f.write("## Observations\n\n")
    
    # Define the experimental configurations
    configurations = [
        {
            'name': 'baseline',
            'description': 'Default parameters',
            'clock_min': 1,
            'clock_max': 6,
            'internal_prob': 0.8
        },
        {
            'name': 'smaller_clock_variation',
            'description': 'Smaller variation in clock cycles (3-4 ticks/sec)',
            'clock_min': 3,
            'clock_max': 4,
            'internal_prob': 0.8
        },
        {
            'name': 'smaller_internal_prob',
            'description': 'Smaller probability of internal events (0.4)',
            'clock_min': 1,
            'clock_max': 6,
            'internal_prob': 0.4
        },
        {
            'name': 'both_modifications',
            'description': 'Both smaller clock variation and internal probability',
            'clock_min': 3,
            'clock_max': 4,
            'internal_prob': 0.4
        }
    ]
    
    all_configs_data = {}
    
    # Run each configuration
    for config in configurations:
        print(f"\n=== Running Configuration: {config['name']} ===")
        print(f"Description: {config['description']}")
        
        # Create a directory for this configuration
        config_dir = os.path.join(exp_dir, config['name'])
        ensure_directory_exists(config_dir)
        
        # Modify virtual_machine.py to use the specified parameters
        modify_vm_parameters(config['clock_min'], config['clock_max'], config['internal_prob'])
        
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
            
            # Copy log to config directory
            if os.path.exists(log_file):
                shutil.copy(log_file, os.path.join(config_dir, f"machine_{machine_id}.log"))
                
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
        analyze_logs.plot_logical_clocks(dfs, machine_ids, filename=os.path.join(config_dir, "logical_clocks.png"))
        analyze_logs.plot_queue_lengths(dfs, machine_ids, filename=os.path.join(config_dir, "queue_lengths.png"))
        analyze_logs.plot_event_distribution(dfs, machine_ids, filename=os.path.join(config_dir, "event_distribution.png"))
        
        # Create clock rate comparison
        create_clock_rate_comparison(analysis_results, config_dir)
        
        # Write summary statistics
        write_summary_statistics(analysis_results, config_dir)
        
        # Store data for comparison
        all_configs_data[config['name']] = {
            'config': config,
            'dfs': dfs,
            'machine_ids': machine_ids,
            'analysis_results': analysis_results
        }
        
        # Add to notebook
        with open(notebook_path, 'a') as f:
            f.write(f"### Configuration: {config['name']}\n\n")
            f.write(f"**Parameters:**\n")
            f.write(f"- Clock Rate Range: {config['clock_min']}-{config['clock_max']} ticks/second\n")
            f.write(f"- Internal Event Probability: {config['internal_prob']}\n\n")
            
            # Extract actual clock rates
            f.write("**Actual Clock Rates:**\n\n")
            for machine_id in range(1, 4):
                clock_rate = extract_clock_rate(f"logs/machine_{machine_id}.log")
                f.write(f"- Machine {machine_id}: {clock_rate} ticks/second\n")
            f.write("\n")
            
            # Add logical clock analysis
            f.write("**Logical Clock Analysis:**\n\n")
            for machine_id, results in analysis_results.items():
                df = results.get('dataframe')
                if df is not None and 'logical_clock' in df.columns:
                    df_sorted = df.sort_values('log_time')
                    if len(df_sorted) > 1:
                        clock_values = df_sorted['logical_clock'].values
                        jumps = np.diff(clock_values)
                        f.write(f"Machine {machine_id}:\n")
                        f.write(f"- Starting Clock Value: {clock_values[0]}\n")
                        f.write(f"- Ending Clock Value: {clock_values[-1]}\n")
                        f.write(f"- Max Jump: {jumps.max()}\n")
                        f.write(f"- Average Jump: {jumps.mean():.2f}\n\n")
            
            # Add event distribution
            f.write("**Event Distribution:**\n\n")
            for machine_id, results in analysis_results.items():
                df = results.get('dataframe')
                if df is not None:
                    total_events = len(df)
                    internal_events = len(df[df['event_type'] == 'INTERNAL'])
                    send_events = len(df[df['event_type'] == 'SEND'])
                    receive_events = len(df[df['event_type'] == 'RECEIVE'])
                    
                    f.write(f"Machine {machine_id}:\n")
                    f.write(f"- Total Events: {total_events}\n")
                    f.write(f"- Internal Events: {internal_events} ({internal_events/total_events*100:.1f}%)\n")
                    f.write(f"- Send Events: {send_events} ({send_events/total_events*100:.1f}%)\n")
                    f.write(f"- Receive Events: {receive_events} ({receive_events/total_events*100:.1f}%)\n\n")
            
            # Add queue analysis
            f.write("**Queue Analysis:**\n\n")
            for machine_id, results in analysis_results.items():
                df = results.get('dataframe')
                if df is not None and 'queue_length' in df.columns:
                    queue_lengths = df['queue_length'].dropna()
                    if not queue_lengths.empty:
                        f.write(f"Machine {machine_id}:\n")
                        f.write(f"- Max Queue Length: {queue_lengths.max()}\n")
                        f.write(f"- Average Queue Length: {queue_lengths.mean():.2f}\n")
                        f.write(f"- Median Queue Length: {queue_lengths.median():.2f}\n\n")
    
    # Generate comparative analysis
    generate_comparative_analysis(all_configs_data, exp_dir, notebook_path)
    
    # Restore default parameters
    modify_vm_parameters(1, 6, 0.8)
    
    print(f"\nExperiment 2 complete! Results saved to {exp_dir}/ directory")
    print(f"Lab notebook available at: {notebook_path}")
    return exp_dir

def modify_vm_parameters(clock_min, clock_max, internal_prob):
    """
    Temporarily modify the VirtualMachine parameters in virtual_machine.py.
    
    Args:
        clock_min: Minimum clock rate
        clock_max: Maximum clock rate
        internal_prob: Probability of internal event
    """
    vm_file = 'virtual_machine.py'
    if not os.path.exists(vm_file):
        print(f"Error: Could not find {vm_file}")
        return
    
    # Read the file
    with open(vm_file, 'r') as f:
        lines = f.readlines()
    
    # Make a backup if it doesn't exist
    backup_file = 'virtual_machine.py.bak'
    if not os.path.exists(backup_file):
        with open(backup_file, 'w') as f:
            f.writelines(lines)
    
    # Modify the parameters
    for i, line in enumerate(lines):
        if 'self.clock_rate = random.randint(' in line:
            lines[i] = f'        self.clock_rate = random.randint({clock_min}, {clock_max})\n'
        if 'if random.random() < ' and 'INTERNAL_EVENT' in line:
            lines[i] = f'            if random.random() < {internal_prob}:  # INTERNAL_EVENT\n'
    
    # Write the file back
    with open(vm_file, 'w') as f:
        f.writelines(lines)
    
    print(f"Modified VM parameters: clock_rate={clock_min}-{clock_max}, internal_prob={internal_prob}")

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

def generate_comparative_analysis(all_configs_data, exp_dir, notebook_path):
    """Generate comparative analysis across all configurations."""
    with open(notebook_path, 'a') as f:
        f.write("## Comparative Analysis\n\n")
        f.write("This section compares results across different configurations.\n\n")
        
        # Compare event distributions
        f.write("### Event Distribution Comparison\n\n")
        f.write("| Configuration | Machine | Total Events | Internal Events (%) | Send Events (%) | Receive Events (%) |\n")
        f.write("| --- | --- | --- | --- | --- | --- |\n")
        
        for config_name, config_data in all_configs_data.items():
            for machine_id, results in config_data['analysis_results'].items():
                df = results.get('dataframe')
                if df is not None:
                    total_events = len(df)
                    internal_events = len(df[df['event_type'] == 'INTERNAL'])
                    send_events = len(df[df['event_type'] == 'SEND'])
                    receive_events = len(df[df['event_type'] == 'RECEIVE'])
                    
                    internal_pct = internal_events/total_events*100 if total_events > 0 else 0
                    send_pct = send_events/total_events*100 if total_events > 0 else 0
                    receive_pct = receive_events/total_events*100 if total_events > 0 else 0
                    
                    row = [
                        config_name,
                        f"Machine {machine_id}",
                        f"{total_events}",
                        f"{internal_events} ({internal_pct:.1f}%)",
                        f"{send_events} ({send_pct:.1f}%)",
                        f"{receive_events} ({receive_pct:.1f}%)"
                    ]
                    f.write("| " + " | ".join(row) + " |\n")
        
        f.write("\n")
        
        # Compare logical clock jumps
        f.write("### Logical Clock Jump Comparison\n\n")
        f.write("| Configuration | Machine | Starting Value | Ending Value | Max Jump | Avg Jump |\n")
        f.write("| --- | --- | --- | --- | --- | --- |\n")
        
        for config_name, config_data in all_configs_data.items():
            for machine_id, results in config_data['analysis_results'].items():
                df = results.get('dataframe')
                if df is not None and 'logical_clock' in df.columns:
                    df_sorted = df.sort_values('log_time')
                    if len(df_sorted) > 1:
                        clock_values = df_sorted['logical_clock'].values
                        jumps = np.diff(clock_values)
                        
                        row = [
                            config_name,
                            f"Machine {machine_id}",
                            f"{clock_values[0]}",
                            f"{clock_values[-1]}",
                            f"{jumps.max()}",
                            f"{jumps.mean():.2f}"
                        ]
                        f.write("| " + " | ".join(row) + " |\n")
        
        f.write("\n")
        
        # Compare queue statistics
        f.write("### Queue Length Comparison\n\n")
        f.write("| Configuration | Machine | Max Queue | Avg Queue | Median Queue |\n")
        f.write("| --- | --- | --- | --- | --- |\n")
        
        for config_name, config_data in all_configs_data.items():
            for machine_id, results in config_data['analysis_results'].items():
                df = results.get('dataframe')
                if df is not None and 'queue_length' in df.columns:
                    queue_lengths = df['queue_length'].dropna()
                    if not queue_lengths.empty:
                        row = [
                            config_name,
                            f"Machine {machine_id}",
                            f"{queue_lengths.max()}",
                            f"{queue_lengths.mean():.2f}",
                            f"{queue_lengths.median():.2f}"
                        ]
                        f.write("| " + " | ".join(row) + " |\n")
        
        f.write("\n")
        
        # Compare drift between machines
        f.write("### Clock Drift Comparison\n\n")
        f.write("| Configuration | Max Drift | Machine 1 Final | Machine 2 Final | Machine 3 Final |\n")
        f.write("| --- | --- | --- | --- | --- |\n")
        
        for config_name, config_data in all_configs_data.items():
            final_clocks = {}
            for machine_id, results in config_data['analysis_results'].items():
                df = results.get('dataframe')
                if df is not None and 'logical_clock' in df.columns:
                    df_sorted = df.sort_values('log_time')
                    if not df_sorted.empty:
                        final_clocks[machine_id] = df_sorted['logical_clock'].iloc[-1]
            
            if len(final_clocks) >= 2:
                max_drift = max(final_clocks.values()) - min(final_clocks.values())
                row = [
                    config_name,
                    f"{max_drift}",
                    f"{final_clocks.get(1, 'N/A')}",
                    f"{final_clocks.get(2, 'N/A')}",
                    f"{final_clocks.get(3, 'N/A')}"
                ]
                f.write("| " + " | ".join(row) + " |\n")
        
        f.write("\n")

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run distributed system parameter variation experiments")
    parser.add_argument("--duration", type=int, default=60, help="Duration of each configuration run in seconds")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    run_experiment(duration=args.duration)
