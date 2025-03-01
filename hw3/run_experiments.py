import os
import subprocess
import time
import datetime
import shutil
from analyze_logs import main as analyze_logs

# Configuration for standard experiments
STANDARD_EXPERIMENTS = [
    {"name": "Standard Experiment 1", "duration": 60},
    {"name": "Standard Experiment 2", "duration": 60},
    {"name": "Standard Experiment 3", "duration": 60},
    {"name": "Standard Experiment 4", "duration": 60},
    {"name": "Standard Experiment 5", "duration": 60},
]

# Configuration for modified experiments
MODIFIED_EXPERIMENTS = [
    {"name": "Modified Experiment 1 (Lower Clock Variation)", "duration": 60, "mod_code": "clock_rate = random.randint(3, 6)"},
    {"name": "Modified Experiment 2 (Higher Internal Event Probability)", "duration": 60, "mod_code": "event = random.randint(1, 5)"},
]

def run_experiment(name, duration, output_dir, modified_code=None):
    """
    Run a single experiment and analyze the results.
    
    Args:
        name: Name of the experiment
        duration: Duration in seconds
        output_dir: Directory to store outputs
        modified_code: Code modification to apply (if any)
    """
    print(f"Running experiment: {name}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Modify code if necessary
    backup_file = None
    if modified_code:
        # Backup original file
        backup_file = "virtual_machine.py.bak"
        shutil.copy("virtual_machine.py", backup_file)
        
        # Apply modification
        with open("virtual_machine.py", 'r') as f:
            code = f.read()
        
        # Replace the clock rate line with the modified version
        if "clock_rate" in modified_code:
            code = code.replace("self.clock_rate = random.randint(1, 6)", modified_code)
        
        # Replace the event generation line with the modified version
        if "event = random.randint" in modified_code:
            code = code.replace("event = random.randint(1, 10)", modified_code)
            
        with open("virtual_machine.py", 'w') as f:
            f.write(code)
    
    # Run the simulation
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subprocess.run(["python", "main.py", "--duration", str(duration)], check=True)
    
    # Run analysis
    with open(os.path.join(output_dir, "analysis.txt"), 'w') as f:
        # Redirect stdout to file
        old_stdout = os.dup(1)
        os.dup2(f.fileno(), 1)
        
        analyze_logs()
        
        # Restore stdout
        os.dup2(old_stdout, 1)
    
    # Move log files and plots to output directory
    for file in os.listdir('.'):
        if file.startswith('machine_') and file.endswith('.log'):
            shutil.move(file, os.path.join(output_dir, file))
        elif file.endswith('.png'):
            shutil.move(file, os.path.join(output_dir, file))
    
    # Restore original code if modified
    if backup_file:
        shutil.move(backup_file, "virtual_machine.py")
    
    # Return experiment metadata
    return {
        "name": name,
        "start_time": start_time,
        "duration": duration,
        "output_dir": output_dir,
        "modified_code": modified_code
    }

def update_lab_notebook(experiments):
    """
    Update lab notebook with experiment results.
    
    Args:
        experiments: List of experiment metadata
    """
    notebook_file = "lab_notebook.md"
    
    # Read existing notebook content
    with open(notebook_file, 'r') as f:
        lines = f.readlines()
    
    # Find the sections to update
    standard_exp_index = -1
    modified_exp_index = -1
    
    for i, line in enumerate(lines):
        if line.startswith("### Experiment 1 (Date: TBD)"):
            standard_exp_index = i
        elif line.startswith("### Modified Experiment 1 (Date: TBD)"):
            modified_exp_index = i
    
    if standard_exp_index == -1 or modified_exp_index == -1:
        print("Could not find sections to update in lab notebook.")
        return
    
    # Update standard experiments
    standard_exps = [e for e in experiments if "Modified" not in e["name"]]
    new_standard_lines = []
    
    for i, exp in enumerate(standard_exps):
        exp_date = exp["start_time"].split()[0]
        new_standard_lines.extend([
            f"### Experiment {i+1} (Date: {exp_date})\n",
            f"- Configuration: Standard, Duration: {exp['duration']} seconds\n",
            f"- Observations: Check analysis in `{exp['output_dir']}/analysis.txt` and plots in `{exp['output_dir']}`.\n",
            "- Analysis: TBD\n",
            "\n"
        ])
    
    # Update modified experiments
    modified_exps = [e for e in experiments if "Modified" in e["name"]]
    new_modified_lines = []
    
    for i, exp in enumerate(modified_exps):
        exp_date = exp["start_time"].split()[0]
        mod_description = "Lower clock variation" if "clock_rate" in exp["modified_code"] else "Higher send probability"
        new_modified_lines.extend([
            f"### Modified Experiment {i+1} (Date: {exp_date})\n",
            f"- Modified parameters: {mod_description}\n",
            f"- Configuration: {exp['modified_code']}, Duration: {exp['duration']} seconds\n",
            f"- Observations: Check analysis in `{exp['output_dir']}/analysis.txt` and plots in `{exp['output_dir']}`.\n",
            "- Analysis: TBD\n",
            "\n"
        ])
    
    # Replace the sections in the lab notebook
    new_lines = lines[:standard_exp_index]
    new_lines.extend(new_standard_lines)
    new_lines.extend(lines[standard_exp_index+5*len(standard_exps):modified_exp_index])
    new_lines.extend(new_modified_lines)
    new_lines.extend(lines[modified_exp_index+5*len(modified_exps):])
    
    # Write updated notebook
    with open(notebook_file, 'w') as f:
        f.writelines(new_lines)
    
    print("Lab notebook updated with experiment results.")

def main():
    """
    Run all experiments and update the lab notebook.
    """
    # Create base output directory
    base_output_dir = f"experiment_results_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(base_output_dir, exist_ok=True)
    
    # Run all experiments
    all_experiments = []
    
    # Standard experiments
    for i, exp in enumerate(STANDARD_EXPERIMENTS):
        output_dir = os.path.join(base_output_dir, f"standard_experiment_{i+1}")
        all_experiments.append(run_experiment(exp["name"], exp["duration"], output_dir))
    
    # Modified experiments
    for i, exp in enumerate(MODIFIED_EXPERIMENTS):
        output_dir = os.path.join(base_output_dir, f"modified_experiment_{i+1}")
        all_experiments.append(run_experiment(exp["name"], exp["duration"], output_dir, exp["mod_code"]))
    
    # Update lab notebook
    update_lab_notebook(all_experiments)
    
    print(f"All experiments completed. Results stored in {base_output_dir}")

if __name__ == "__main__":
    main()
