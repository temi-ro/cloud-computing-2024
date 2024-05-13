import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.interpolate import interp1d
from datetime import datetime
from collections import defaultdict
import ast
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings("ignore", category=UserWarning) 

# Function to read time values from a file (logger)
def read_time_logger(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
        l_start = lines[0]
        l_end = lines[-5] # last job is done
        start_time = convert_time_to_seconds(l_start.split()[0])
        end_time = convert_time_to_seconds(l_end.split()[0])

    # print("start_time:", int(start_time))
    # print("end_time:", int(end_time))
    return start_time, end_time

# Function to read p95 latency from a file (mcperf)
def read_time_p95(filename, n):
    data = np.loadtxt(filename, skiprows=6, usecols=(12, 16), max_rows=n, dtype=float)
    p95 = list(map(lambda x: x/1000, data[:, 0]))
    
    return p95

# Function to read end and start time values from a file (mcperf)
def read_time(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
        l_start = lines[3]
        l_end = lines[4]
        start_time = l_start.split()[-1] / 1000
        end_time = l_end.split()[-1] / 1000

    return start_time, end_time

def convert_time_to_seconds(timestamp):
    timestamp_dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")

    # Convert datetime object to seconds
    time_sec = timestamp_dt.timestamp()
    return time_sec

def get_execution_time(filename, start_time, tasks):
    # Dictionary to store execution time and last start time of each task
    # task -> (current execution time, last start time)
    execution_time = {}
    for task in tasks:
        execution_time[task] = [0, 0]

    with open(filename, 'r') as f:
        lines = f.readlines()

        for line in lines[:-1]:
            time, action, task = line.split()[0:3]
            time = convert_time_to_seconds(time) - start_time
            if task == "scheduler" or task == "memcached":
                continue

            if action == "start" or action == "unpause":
                execution_time[task] = [execution_time[task][0], time]
            elif action == "end" or action == "pause":
                execution_time[task] = [execution_time[task][0] + time - execution_time[task][1], 0]

    return {task: execution_time[task][0] for task in tasks}

INTERVAL = 10
TASKS = [
        'blackscholes',
        'canneal',
        'dedup',
        'ferret',
        'freqmine',
        'radix',
        'vips'
    ]
def main():
    execution_time_runs = defaultdict(list)
    for run in range(1, 4):
        logger_filename = f'./part4/new_goat_logger_{run}_interval_{INTERVAL}.txt'
        mcperf_filename = f'./part4/new_goat_mcperf_{run}_interval_{INTERVAL}.txt'

        start_time, end_time = read_time_logger(logger_filename)

        execution_time = get_execution_time(logger_filename, start_time, TASKS)

        print("Total execution time:", sum(execution_time.values()))
        # This time starts when memcached starts and ends (thus it is not the time we want)
        total_time = end_time - start_time
        print("Total time:", total_time) 

        execution_time_runs["total"].append(sum(execution_time.values()))
        for task in TASKS:
            execution_time_runs[task].append(execution_time[task])


        # Get the ratio that does not respect the SLO        
        num_qps = int(total_time / INTERVAL) + 1
        p95_list = read_time_p95(mcperf_filename, num_qps)
        num_violations = 0
        num_total_qps = len(p95_list)
        for p95 in p95_list:
            if p95 > 1:
                num_violations += 1

        print("Number of violations:", num_violations)
        print("Total number of QPS:", num_total_qps)
        print("Ratio SLO:", (num_violations / num_total_qps)*100)
        print("\n")

    rounding = 2
    print("Task: Average Execution Time (s) Standard Deviation (s)")
    for task in TASKS:
        print(f'{task}: {round(sum(execution_time_runs[task])/3, rounding)} {round(np.std(execution_time_runs[task]), rounding)}')
    print(f'Total: {round(sum(execution_time_runs["total"])/3, rounding)} {round(np.std(execution_time_runs["total"]),rounding)}')

if __name__ == '__main__':
    main()
