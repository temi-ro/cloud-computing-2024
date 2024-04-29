import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.interpolate import interp1d

# Function to read data from a file and return QPS and 95th percentile values
def read_data(filename):
    data = np.loadtxt(filename, skiprows=1, usecols=(0,1), dtype=float)
    t = data[:, 0]
    # cpu0 = data[:, 1]
    # cpu1 = data[:, 2]
    # cpu_utils = list(map(lambda x: (float(x[0]) + float(x[1]))/2, zip(cpu0, cpu1)))
    cpu_utils = data[:, 1]
    return t, cpu_utils

def read_time_qps(filename):
    data = np.loadtxt(filename, skiprows=1, usecols=(16,18, 19), max_rows=25, dtype=float)
    qps = list(map(lambda x: x/1000, data[:, 0]))
    t_start = data[:, 1]
    t_end = data[:, 2]
    return qps, t_start, t_end


def interpolate_qps(time_values, qps_values):
    """
    Create a function to interpolate QPS values based on time.
    
    Args:
    - time_values (list): List of time values
    - qps_values (list): Corresponding list of QPS values
    
    Returns:
    - interpolation_function: A function that takes time as input and returns interpolated QPS
    """
    # Create interpolation function
    interpolation_function = interp1d(time_values, qps_values, kind='linear', fill_value='extrapolate')
    
    return interpolation_function

def main():
    # Plotting
    plt.figure(figsize=(10, 6))

    config = "1"
    formats = ["o-", "x-", "s-", "d-"]


    t, cpu_utils = read_data(f'./data/data_part4/cpu_utils{config}_3.txt')
    qps, t_start, t_end = read_time_qps(f'./data/data_part4/measure{config}_3.txt')


    # Find the first cpu_util value when the time is greater than the start time
    starting_time = t_start[0]
    starting_index = 0
    for i in range(len(t)):
        if t[i] > starting_time:
            starting_index = i
            break
        
    t = t[starting_index:]
    cpu_utils = cpu_utils[starting_index:]

    print(cpu_utils)

    # Filter the cpu utils that are smaller than a threshold
    new_cpu_utils = []
    threshold = 1
    for i in range(len(cpu_utils)):
        if cpu_utils[i] > threshold:
            new_cpu_utils.append(cpu_utils[i])
        else:
            np.delete(t, i)

    # cpu_utils = [cpu_utils[i] for i in range(len(cpu_utils)) if cpu_utils[i] > threshold]

    # Interpolate QPS values
    toQps = interpolate_qps(t_start, qps)

    plt.plot(toQps(t), cpu_utils, formats[0], label=f"CPU Utilisation for {config}")


    plt.yticks(np.arange(0, 210, 10))
    plt.xticks(np.arange(0, 135, 5))

    plt.title('CPU utilisation vs Achieved QPS')
    plt.xlabel('Thousands of Achieved Queries per Second (KQPS)')
    plt.ylabel('CPU utilisation (%)')
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == '__main__':
    main()
