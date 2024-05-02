import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.interpolate import interp1d
from datetime import datetime
from collections import defaultdict
import ast
import matplotlib.patches as mpatches

# Function to read data from a file and return QPS and 95th percentile values
def read_data(filename):
    data = np.loadtxt(filename, skiprows=1, usecols=(0,1), dtype=float)
    print(data)
    t = data[:, 0]
    cpu_utils = data[:, 1]
    return t, cpu_utils

# Function to read end and start time values from a file (mcperf)
def read_time(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
        l_start = lines[3]
        l_end = lines[4]
        start_time = int(l_start.split()[-1]) // 1000
        end_time = int(l_end.split()[-1]) // 1000

    return start_time, end_time

def read_time_qps(filename, n):
    data = np.loadtxt(filename, skiprows=6, usecols=(12, 16), max_rows=n, dtype=float)
    p95 = list(map(lambda x: x/1000, data[:, 0]))
    qps = list(map(lambda x: x/1000, data[:, 1]))
    
    return p95, qps

# Return the number of cores allocated to memcached
def read_core_memcached(filename, start_time, end_time):
    cores = []
    time_cores = []
    with open(filename, 'r') as f:
        lines = f.readlines()

        for line in lines[:-1]:
            time, action, task = line.split()[0:3]
            time = convert_time_to_seconds(time) - start_time
            if task == "memcached":
                if action == "start" or action == "update_cores":
                    print(len(ast.literal_eval(line.split()[3])), time)
                    cores.append(len(ast.literal_eval(line.split()[3])))
                    time_cores.append(time)

    cores = cores + [cores[-1]]
    time_cores = time_cores + [end_time]
    return cores, time_cores

# Function to read time values from a file (logger)
def read_time_logger(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
        l_start = lines[0]
        l_end = lines[-2]
        start_time = convert_time_to_seconds(l_start.split()[0])
        end_time = convert_time_to_seconds(l_end.split()[0])

    # print("start_time:", int(start_time))
    # print("end_time:", int(end_time))
    return int(start_time), int(end_time)

# Function to interpolate QPS values based on time
# Returns a function that takes time as input and returns interpolated QPS
def interpolate_qps(time_values, qps_values):
    interpolation_function = interp1d(time_values, qps_values, kind='linear', fill_value='extrapolate')
    return interpolation_function

def convert_time_to_seconds(timestamp):
    # print("timestamp:", timestamp)
    # timestamp_dt = datetime.fromisoformat(timestamp)
    timestamp_dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")

    # Convert datetime object to seconds
    time_sec = timestamp_dt.timestamp()
    return int(time_sec)

def plot_gantt_chart(ax, tasks, colors):
        # Example colors for tasks

    # Set y-axis limit
    ax.set_ylim(1, 3)

    # Set labels for y-axis ticks
    ax.set_yticks([1,2,3])
    ax.set_yticklabels(['Core 1', 'Core 2', 'Core 3'])

    # Plot bars for each task
    for task in tasks:
        for i in range(0, len(tasks[task])-1, 2):
            start, cores = tasks[task][i]
            end, _ = tasks[task][i+1]
            duration = end - start

            for c in cores:
                ax.barh(c, duration, height=1, left=start, color=colors[task], alpha=1)
            # ax.barh(cores, duration, left=start, color=colors[task], alpha=1)

    # Remove gridlines
    ax.grid(False)
    # Remove y-axis labels
    ax.xaxis.set_visible(False)

def get_tasks(filename, start_time):
    task = []    
    with open(filename, 'r') as f:
        lines = f.readlines()
        tasks = defaultdict(list)
        cores = defaultdict(list)

        for line in lines[:-1]:
            time, action, task = line.split()[0:3]
            time = convert_time_to_seconds(time) - start_time
            if task == "scheduler" or task == "memcached":
                continue

            if action == "start":
                cores[task] = ast.literal_eval(line.split()[3])
                tasks[task].append((time, cores[task]))
            elif action == "update_cores":
                cores[task] = ast.literal_eval(line.split()[3])
            else: # pause or unpause or end
                tasks[task].append((time, cores[task]))

    return tasks

INTERVAL = 10

def main(run):
    # Plotting
    fig, ax1 = plt.subplots(figsize=(10, 6))

    logger_filename = f'./part4/logger_{run}_interval_10.txt'
    mcperf_filename = f'./part4/mcperf_{run}_interval_10.txt'
    
    start_time, end_time = read_time_logger(logger_filename)
    
    # num of interval
    n = (end_time - start_time) // INTERVAL + 1 

    p95, qps = read_time_qps(mcperf_filename, n)

    cores, time_cores = read_core_memcached(logger_filename, start_time, end_time)

    total_time = end_time - start_time
    time_qps = range(0, total_time, INTERVAL)

    # Plot 95th percentile latency on the left y-axis 
    handles1, = ax1.step(time_cores, cores, '-', label=f"Cores to Memcached", color='orange', zorder=5, alpha=0.8)
    ax1.set_ylabel('CPU Cores Allocated to Memcached', color='orange', fontweight='bold')
    ax1.set_yticks(np.arange(0, 3.1, 1))
    ax1.set_ylim(0,3)
   
    ax2 = ax1.twinx()

    ax1.set_zorder(5)
    ax1.patch.set_visible(False)
    # Plot QPS on the right y-axis
    # ax2.plot(time_qps, qps, formats[0], label=f"Achieved Thousands of QPS", color='tab:blue')
    handles2 = ax2.bar(time_qps, qps, width=10, label=f"QPS", color='tab:blue', alpha=0.8, zorder=1)
    ax2.set_ylabel(f"Achieved Thousands of QPS (kQPS)", color='tab:blue', fontweight='bold')
    ax2.set_ylim(bottom=0, top=120)
    ax2.set_yticks(np.arange(0, 115, 20))

    # x-axis label
    ax1.set_xlabel('Time (s)', fontweight='bold')
    ax1.set_xticks(list(range(0, 800, 100)) + [total_time])
    ax1.set_xlim(left=0, right=total_time)

    tasks = get_tasks(logger_filename, start_time)

    ax_gantt = fig.add_subplot(9, 1, 1, sharex=ax1)

    colors = {
        'vips': '#CC0A00',
        'radix': '#00CCA0',
        'freqmine': '#0CCA00',
        'blackscholes': '#CCA000',
        'dedup': '#CCACCA',
        'ferret': '#AACCCA',
        'canneal': '#CCCCAA'
    }

    # Plot the Gantt chart
    plot_gantt_chart(ax_gantt, tasks, colors)

    # Add horizontal line for SLO at p95=1.0
    # ax1.axhline(y=1.0, color='red', linestyle='--', label='SLO at 1.0ms')

    ax1.grid(False, alpha=0.5)
    ax2.grid(True, alpha=0.5)

    # Create a legend with all the tasks
    tasks_handles = [mpatches.Patch(color=colors[task], label=task) for task in tasks]
    handles = [handles1, handles2] + tasks_handles

    plt.tight_layout(rect=[0, 0, .8, 1])
    plt.legend(handles=handles, loc='upper right', bbox_to_anchor=(1.43, 0.1))

    plt.title(f"{run}B", fontweight='bold')
    plt.grid(True)
    plt.show()

if __name__ == '__main__':
    main(3)
