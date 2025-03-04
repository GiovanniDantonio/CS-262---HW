import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional

def parse_log_file(filename: str) -> pd.DataFrame:
    """
    Parse a log file and extract relevant data.
    
    Args:
        filename: Path to the log file
        
    Returns:
        DataFrame with parsed log data
    """
    print(f"Parsing log file: {filename}")
    
    # Regex for each event type
    receive_pattern = (
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) '
        r'- RECEIVE - System Time: (.*?), Logical Clock: (\d+), '
        r'Queue Length: (\d+), From: Machine (\d+)'
    )
    send_pattern = (
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) '
        r'- SEND - System Time: (.*?), Logical Clock: (\d+), '
        r'To: Machine on port (\d+)'
    )
    internal_pattern = (
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) '
        r'- INTERNAL - System Time: (.*?), Logical Clock: (\d+)'
    )
    
    data = []
    
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Try to match each pattern
                receive_match = re.search(receive_pattern, line)
                send_match = re.search(send_pattern, line)
                internal_match = re.search(internal_pattern, line)
                
                if receive_match:
                    # e.g. "2025-03-04 16:48:17,111 - RECEIVE - System Time: 2025-03-04 16:48:17.111026, Logical Clock: 2, Queue Length: 0, From: Machine 3"
                    log_time, system_time, logical_clock, queue_length, sender_id = receive_match.groups()
                    data.append({
                        'log_time': log_time,
                        'system_time': system_time,
                        'event_type': 'RECEIVE',
                        'logical_clock': int(logical_clock),
                        'queue_length': int(queue_length),
                        'peer_id': int(sender_id),
                        'target_port': None
                    })
                    
                elif send_match:
                    # e.g. "2025-03-04 16:48:17,449 - SEND - System Time: 2025-03-04 16:48:17.449700, Logical Clock: 3, To: Machine on port 10002"
                    log_time, system_time, logical_clock, target_port = send_match.groups()
                    data.append({
                        'log_time': log_time,
                        'system_time': system_time,
                        'event_type': 'SEND',
                        'logical_clock': int(logical_clock),
                        'queue_length': None,
                        'peer_id': None,
                        'target_port': int(target_port)
                    })
                    
                elif internal_match:
                    # e.g. "2025-03-04 16:48:18,126 - INTERNAL - System Time: 2025-03-04 16:48:18.126160, Logical Clock: 5"
                    log_time, system_time, logical_clock = internal_match.groups()
                    data.append({
                        'log_time': log_time,
                        'system_time': system_time,
                        'event_type': 'INTERNAL',
                        'logical_clock': int(logical_clock),
                        'queue_length': None,
                        'peer_id': None,
                        'target_port': None
                    })
                else:
                    # Unmatched line, can optionally debug print here
                    pass
    except Exception as e:
        print(f"Error parsing log file {filename}: {e}")
        return pd.DataFrame(columns=['log_time', 'system_time', 'event_type',
                                     'logical_clock', 'queue_length', 'peer_id',
                                     'target_port'])
    
    if not data:
        print(f"No valid lines matched in {filename}")
        return pd.DataFrame(columns=['log_time', 'system_time', 'event_type',
                                     'logical_clock', 'queue_length', 'peer_id',
                                     'target_port'])
    
    # Convert list of dicts to DataFrame
    df = pd.DataFrame(data)
    
    # Convert to datetime
    # log_time: "2025-03-04 16:48:17,111" -> use '%Y-%m-%d %H:%M:%S,%f'
    # system_time: "2025-03-04 16:48:17.111026" -> can parse with '%Y-%m-%d %H:%M:%S.%f'
    try:
        df['log_time'] = pd.to_datetime(df['log_time'], format='%Y-%m-%d %H:%M:%S,%f')
        df['system_time'] = pd.to_datetime(df['system_time'], format='%Y-%m-%d %H:%M:%S.%f')
    except Exception as e:
        print(f"Warning: could not parse timestamps perfectly: {e}")
    
    return df

def analyze_clock_jumps(df: pd.DataFrame) -> Dict:
    """
    Analyze jumps in logical clock values.
    """
    if df.empty:
        return {
            'min_jump': None,
            'max_jump': None,
            'mean_jump': None,
            'median_jump': None,
            'std_dev_jump': None
        }
    
    # Sort by log_time (not system_time, in case system_time is out of order)
    df_sorted = df.sort_values('log_time')
    # Calculate clock jumps
    clock_diff = df_sorted['logical_clock'].diff().dropna()
    
    return {
        'min_jump': clock_diff.min(),
        'max_jump': clock_diff.max(),
        'mean_jump': clock_diff.mean(),
        'median_jump': clock_diff.median(),
        'std_dev_jump': clock_diff.std()
    }

def analyze_queue_lengths(df: pd.DataFrame) -> Dict:
    """
    Analyze message queue lengths for RECEIVE events only.
    """
    if df.empty:
        return {
            'min_queue': None,
            'max_queue': None,
            'mean_queue': None,
            'median_queue': None
        }
    receive_df = df[df['event_type'] == 'RECEIVE']
    if receive_df.empty:
        return {
            'min_queue': None,
            'max_queue': None,
            'mean_queue': None,
            'median_queue': None
        }
    qlens = receive_df['queue_length'].dropna()
    if qlens.empty:
        return {
            'min_queue': None,
            'max_queue': None,
            'mean_queue': None,
            'median_queue': None
        }
    return {
        'min_queue': qlens.min(),
        'max_queue': qlens.max(),
        'mean_queue': qlens.mean(),
        'median_queue': qlens.median()
    }

def plot_logical_clocks(dfs: List[pd.DataFrame], machine_ids: List[int], filename: str = 'logical_clocks.png'):
    """
    Plot logical clocks for all machines over time.
    """
    plt.figure(figsize=(12, 8))
    
    for i, df in enumerate(dfs):
        if not df.empty:
            df_sorted = df.sort_values('log_time')
            plt.plot(
                df_sorted['log_time'],
                df_sorted['logical_clock'],
                label=f"Machine {machine_ids[i]}",
                marker='o', markersize=3, linestyle='-'
            )
    
    plt.xlabel('Log Timestamp')
    plt.ylabel('Logical Clock Value')
    plt.title('Logical Clock Values Over Time')
    plt.legend()
    plt.grid(True)
    plt.savefig(filename)
    plt.close()
    print(f"Saved logical clock plot to {filename}")

def plot_queue_lengths(dfs: List[pd.DataFrame], machine_ids: List[int], filename: str = 'queue_lengths.png'):
    """
    Plot queue lengths for RECEIVE events only.
    """
    plt.figure(figsize=(12, 8))
    
    for i, df in enumerate(dfs):
        if not df.empty:
            receive_df = df[df['event_type'] == 'RECEIVE'].sort_values('log_time')
            if not receive_df.empty:
                plt.plot(
                    receive_df['log_time'],
                    receive_df['queue_length'],
                    label=f"Machine {machine_ids[i]}",
                    marker='o', markersize=3, linestyle='-'
                )
    
    plt.xlabel('Log Timestamp')
    plt.ylabel('Queue Length')
    plt.title('Message Queue Lengths Over Time')
    plt.legend()
    plt.grid(True)
    plt.savefig(filename)
    plt.close()
    print(f"Saved queue length plot to {filename}")

def plot_event_distribution(dfs: List[pd.DataFrame], machine_ids: List[int], filename: str = 'event_distribution.png'):
    """
    Plot distribution of event types for each machine.
    """
    # Build up a summary of event counts
    event_counts = []
    for i, df in enumerate(dfs):
        if df.empty:
            event_counts.append({
                'Machine': f'Machine {machine_ids[i]}',
                'INTERNAL': 0,
                'SEND': 0,
                'RECEIVE': 0
            })
        else:
            counts = df['event_type'].value_counts()
            event_counts.append({
                'Machine': f'Machine {machine_ids[i]}',
                'INTERNAL': counts.get('INTERNAL', 0),
                'SEND': counts.get('SEND', 0),
                'RECEIVE': counts.get('RECEIVE', 0)
            })
    
    if not event_counts:
        print("No event data to plot.")
        return
    
    event_df = pd.DataFrame(event_counts).set_index('Machine')
    
    # Plot stacked bar
    event_df.plot(kind='bar', stacked=True, figsize=(10, 6))
    plt.xlabel('Machine')
    plt.ylabel('Event Count')
    plt.title('Distribution of Event Types by Machine')
    plt.legend(title='Event Type')
    plt.savefig(filename)
    plt.close()
    print(f"Saved event distribution plot to {filename}")

def main():
    """
    Main analysis function (if you want to run it standalone).
    """
    if not os.path.exists("logs"):
        print("No logs directory found.")
        return
    
    log_files = [
        f for f in os.listdir('logs')
        if f.startswith('machine_') and f.endswith('.log')
    ]
    
    if not log_files:
        print("No log files found in logs directory.")
        return
    
    dfs = []
    machine_ids = []
    
    for log_file in sorted(log_files):
        machine_id = int(log_file.split('_')[1].split('.')[0])
        log_path = os.path.join('logs', log_file)
        df = parse_log_file(log_path)
        dfs.append(df)
        machine_ids.append(machine_id)
        
        print(f"Machine {machine_id}: parsed {len(df)} log lines.")
        if not df.empty:
            # Stats
            clock_stats = analyze_clock_jumps(df)
            queue_stats = analyze_queue_lengths(df)
            print(f"  Final clock value: {df['logical_clock'].max()}")
            print(f"  Clock jumps: {clock_stats}")
            print(f"  Queue stats: {queue_stats}")
        print()
    
    # Generate plots
    plot_logical_clocks(dfs, machine_ids, filename='logical_clocks.png')
    plot_queue_lengths(dfs, machine_ids, filename='queue_lengths.png')
    plot_event_distribution(dfs, machine_ids, filename='event_distribution.png')
    
    print("Analysis complete.")

if __name__ == "__main__":
    main()
