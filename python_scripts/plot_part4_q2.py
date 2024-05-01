import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.interpolate import interp1d

# Function to read data from a file and return QPS and 95th percentile values
def read_data(filename):
    data = np.loadtxt(filename, skiprows=1, usecols=(0,1), dtype=float)
    t = data[:, 0]
    cpu_utils = data[:, 1]
    return t, cpu_utils

# Because of a small error, the first row of the data is sum of ALL cpu utilisation instead of the sum of the two cores
def read_data_cpu2(filename):
    data = np.loadtxt(filename, skiprows=1, usecols=(0,2,3), dtype=float)
    t = data[:, 0]
    cpu0 = data[:, 1]
    cpu1 = data[:, 2]
    cpu_utils = list(map(lambda x: x[0] + x[1], zip(cpu0, cpu1)))

    return t, cpu_utils

def read_time_qps(filename):
    data = np.loadtxt(filename, skiprows=1, usecols=(16,18,19, 13), max_rows=25, dtype=float)
    qps = list(map(lambda x: x/1000, data[:, 0]))
    t_start = data[:, 1]
    t_end = data[:, 2]
    p95 = list(map(lambda x: x/1000, data[:, 3]))
    return qps, t_start, t_end, p95

# Function to interpolate QPS values based on time
# Returns a function that takes time as input and returns interpolated QPS
def interpolate_qps(time_values, qps_values):
    interpolation_function = interp1d(time_values, qps_values, kind='linear', fill_value='extrapolate')
    return interpolation_function

def main(config="2"):
    # Plotting
    fig, ax1 = plt.subplots(figsize=(10, 6))

    formats = ["d-", "x-"]

    if config == "2":
        t, cpu_utils = read_data_cpu2(f'./data/data_part4/cpu{config}.txt')
    else:
        t, cpu_utils = read_data(f'./data/data_part4/cpu{config}.txt')

    qps, t_start, t_end, p95 = read_time_qps(f'./data/data_part4/latency{config}.txt')

    # Interpolate QPS values
    toQps = interpolate_qps(t_start, qps)
    
    # Plot 95th percentile latency on the left y-axis 
    ax1.plot(qps, p95, formats[1], label=f"95th percentile latency for {config} core{"s" if config == "2" else ""} and 2 threads", color='orange')
    ax1.set_ylabel('95th Percentile Latency (ms)', color='orange', fontweight='bold')
    ax1.set_yticks(np.arange(0, 2.1 if config == "2" else 3.1, 0.25 if config == "2" else 0.6))
    ax1.set_ylim(bottom=0, top=2 if config == "2" else 3)

    ax2 = ax1.twinx()

    # Plot CPU utilization on the right y-axis
    
    ax2.plot(toQps(t), cpu_utils, formats[0], label=f"CPU Utilisation for {config} core{"s" if config == "2" else ""} and 2 threads", color='tab:blue')
    ax2.set_ylabel('CPU Utilisation (%)', color='tab:blue', fontweight='bold')
    ax2.set_ylim(bottom=0, top=200 if config == "2" else 100)

    if config == "1":
        ax2.set_yticks(np.arange(0, 110, 20))
    else:
        ax2.set_yticks(np.arange(0, 210, 25))

    # x-axis label
    ax1.set_xlabel('Thousands of Achieved Queries per Second (KQPS)', fontweight='bold')
    ax1.set_xticks(np.arange(0, 135, 10))
    ax1.set_xlim(left=0, right=130)

    # Add horizontal line for SLO at p95=1.0
    ax1.axhline(y=1.0, color='red', linestyle='--', label='SLO at 1.0ms')

    fig.tight_layout()
    fig.legend(loc='upper left', bbox_to_anchor=(0.08, 0.9))

    plt.title('CPU Utilisation and 95th Percentile Latency vs Achieved QPS for Memcached Configurations', fontweight='bold')
    plt.grid(True)
    plt.show()

if __name__ == '__main__':
    # "1" if 1 core, "2" if 2 cores
    main("1")
