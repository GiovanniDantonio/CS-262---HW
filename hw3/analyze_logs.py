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
    
    # Regular expressions for parsing different log entry types
    init_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (Virtual Machine|Clock Rate|Listening on port|Peer ports|Network initialization completed|Starting main event loop)'
    receive_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - RECEIVE - System Time: (.*?), Logical Clock: (\d+), Queue Length: (\d+), From: Machine (\d+)'
    send_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - SEND - System Time: (.*?), Logical Clock: (\d+), To: Machine on port (\d+)'
    internal_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - INTERNAL - System Time: (.*?), Logical Clock: (\d+)'
    
    data = []
    
    try:
        with open(filename, 'r') as f:
            for line in f:
                # Try to match each pattern
                receive_match = re.match(receive_pattern, line)
                send_match = re.match(send_pattern, line)
                internal_match = re.match(internal_pattern, line)
                
                if receive_match:
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
    except Exception as e:
        print(f"Error parsing log file {filename}: {e}")
        return pd.DataFrame(columns=['log_time', 'system_time', 'event_type', 
                                    'logical_clock', 'queue_length', 'peer_id', 
                                    'target_port'])
    
    # Convert to DataFrame
    if data:
        df = pd.DataFrame(data)
        
        # Convert timestamp strings to datetime objects
        try:
            df['log_time'] = pd.to_datetime(df['log_time'], format='%Y-%m-%d %H:%M:%S,%f')
            df['system_time'] = pd.to_datetime(df['system_time'])
        except Exception as e:
            print(f"Error converting timestamps: {e}")
        
        return df
    else:
        print(f"No valid data found in log file {filename}")
        return pd.DataFrame(columns=['log_time', 'system_time', 'event_type', 
                                    'logical_clock', 'queue_length', 'peer_id', 
                                    'target_port'])

def analyze_clock_jumps(df: pd.DataFrame) -> Dict:
    """
    Analyze jumps in logical clock values.
    
    Args:
        df: DataFrame with parsed log data
        
    Returns:
        Dictionary with statistics about clock jumps
    """
    # Sort by timestamp
    df = df.sort_values('system_time')
    
    # Calculate clock jumps
    df['clock_jump'] = df['logical_clock'].diff()
    
    # Analyze jumps
    jumps = df['clock_jump'].dropna()
    
    return {
        'min_jump': jumps.min(),
        'max_jump': jumps.max(),
        'mean_jump': jumps.mean(),
        'median_jump': jumps.median(),
        'std_dev_jump': jumps.std()
    }

def analyze_queue_lengths(df: pd.DataFrame) -> Dict:
    """
    Analyze message queue lengths.
    
    Args:
        df: DataFrame with parsed log data
        
    Returns:
        Dictionary with statistics about queue lengths
    """
    # Filter for receive events (which have queue length)
    receive_df = df[df['event_type'] == 'RECEIVE']
    
    if receive_df.empty:
        return {
            'min_queue': None,
            'max_queue': None,
            'mean_queue': None,
            'median_queue': None
        }
    
    queue_lengths = receive_df['queue_length']
    
    return {
        'min_queue': queue_lengths.min(),
        'max_queue': queue_lengths.max(),
        'mean_queue': queue_lengths.mean(),
        'median_queue': queue_lengths.median()
    }

def plot_logical_clocks(dfs: List[pd.DataFrame], machine_ids: List[int], filename: str = 'logical_clocks.png'):
    """
    Plot logical clocks for all machines over time.
    
    Args:
        dfs: List of DataFrames with parsed log data for each machine
        machine_ids: List of corresponding machine IDs
        filename: Output filename for the plot
    """
    plt.figure(figsize=(12, 8))
    
    for i, df in enumerate(dfs):
        if not df.empty:
            # Sort by system time
            df = df.sort_values('system_time')
            
            plt.plot(df['system_time'], df['logical_clock'], 
                     label=f'Machine {machine_ids[i]}', 
                     marker='o', markersize=3, linestyle='-')
    
    plt.xlabel('System Time')
    plt.ylabel('Logical Clock Value')
    plt.title('Logical Clock Values Over Time')
    plt.legend()
    plt.grid(True)
    plt.savefig(filename)
    plt.close()

def plot_queue_lengths(dfs: List[pd.DataFrame], machine_ids: List[int], filename: str = 'queue_lengths.png'):
    """
    Plot message queue lengths for all machines over time.
    
    Args:
        dfs: List of DataFrames with parsed log data for each machine
        machine_ids: List of corresponding machine IDs
        filename: Output filename for the plot
    """
    plt.figure(figsize=(12, 8))
    
    for i, df in enumerate(dfs):
        # Filter for receive events (which have queue length)
        receive_df = df[df['event_type'] == 'RECEIVE']
        
        if not receive_df.empty:
            # Sort by system time
            receive_df = receive_df.sort_values('system_time')
            
            plt.plot(receive_df['system_time'], receive_df['queue_length'], 
                     label=f'Machine {machine_ids[i]}', 
                     marker='o', markersize=3, linestyle='-')
    
    plt.xlabel('System Time')
    plt.ylabel('Queue Length')
    plt.title('Message Queue Lengths Over Time')
    plt.legend()
    plt.grid(True)
    plt.savefig(filename)
    plt.close()

def plot_event_distribution(dfs: List[pd.DataFrame], machine_ids: List[int], filename: str = 'event_distribution.png'):
    """
    Plot distribution of event types for each machine.
    
    Args:
        dfs: List of DataFrames with parsed log data for each machine
        machine_ids: List of corresponding machine IDs
        filename: Output filename for the plot
    """
    plt.figure(figsize=(12, 8))
    
    event_counts = []
    for i, df in enumerate(dfs):
        if not df.empty:
            # Count event types
            event_count = df['event_type'].value_counts()
            event_counts.append({
                'Machine': f'Machine {machine_ids[i]}',
                'INTERNAL': event_count.get('INTERNAL', 0),
                'SEND': event_count.get('SEND', 0),
                'RECEIVE': event_count.get('RECEIVE', 0)
            })
    
    if event_counts:
        # Convert to DataFrame for plotting
        event_df = pd.DataFrame(event_counts)
        event_df.set_index('Machine', inplace=True)
        
        event_df.plot(kind='bar', stacked=True, figsize=(10, 6))
        plt.xlabel('Machine')
        plt.ylabel('Event Count')
        plt.title('Distribution of Event Types by Machine')
        plt.legend(title='Event Type')
        plt.savefig(filename)
        plt.close()

def main():
    """
    Main function to analyze log files.
    """
    # Get list of log files
    if not os.path.exists("logs"):
        print("No logs directory found. Run the simulation first.")
        return
        
    log_files = [f for f in os.listdir('logs') if f.startswith('machine_') and f.endswith('.log')]
    
    if not log_files:
        print("No log files found in logs directory. Run the simulation first.")
        return
    
    # Parse log files
    dfs = []
    machine_ids = []
    
    for log_file in log_files:
        # Extract machine ID from file
        machine_id = int(log_file.split('_')[1].split('.')[0])
        machine_ids.append(machine_id)
        
        # Parse log file with correct path
        log_path = os.path.join('logs', log_file)
        df = parse_log_file(log_path)
        dfs.append(df)
        
        # Analyze clock jumps
        clock_jumps = analyze_clock_jumps(df)
        # Analyze queue lengths
        queue_stats = analyze_queue_lengths(df)
        
        # Print statistics
        print(f"Analysis for Machine {machine_id}:")
        print(f"Total events: {len(df)}")
        print(f"Event distribution: {df['event_type'].value_counts().to_dict()}")
        print(f"Logical clock statistics:")
        print(f"  - Final value: {df['logical_clock'].max()}")
        print(f"  - Min jump: {clock_jumps['min_jump']}")
        print(f"  - Max jump: {clock_jumps['max_jump']}")
        print(f"  - Mean jump: {clock_jumps['mean_jump']:.2f}")
        print(f"Message queue statistics:")
        if queue_stats['max_queue'] is not None:
            print(f"  - Max length: {queue_stats['max_queue']}")
            print(f"  - Mean length: {queue_stats['mean_queue']:.2f}")
        else:
            print("  - No receive events recorded, queue statistics not available")
        print()
    
    print("Generating plots...")
    plot_logical_clocks(dfs, machine_ids)
    plot_queue_lengths(dfs, machine_ids)
    plot_event_distribution(dfs, machine_ids)
    
    print("Analysis complete, generated plot files.")

if __name__ == "__main__":
    main()
