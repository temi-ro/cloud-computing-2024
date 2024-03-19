import os
import json
import matplotlib.pyplot as plt


def extract_real_time(filename):
    with open(filename, 'r') as file:
        for line in file:
            if line.startswith("real"):
                time = line.split("\t")[1]
                minutes, seconds = time.split("m")
                seconds = seconds.strip()[:-1]  # remove trailing 's'

                return float(minutes) * 60 + float(seconds)
    return None

def get_speedups(directory):
    speedups = {}
    jobs = ['blackscholes', 'canneal', 'dedup', 'ferret', 'freqmine', 'vips', 'radix']
    threads = [1, 2, 4, 8]

    for job in jobs:
        time_baseline = None
        for thread in threads:
            filename = 'output_parsec_{0}_{1}.txt'.format(job, thread)
            time = extract_real_time(os.path.join(directory, filename))

            if thread == 1:
                time_baseline = time

            if time is not None:
                if job not in speedups:
                    speedups[job] = {}
                speedups[job][thread] = time_baseline/time


    return speedups

def plot_speedups(speedups):
    threads = [1, 2, 4, 8]

    plt.figure(figsize=(10, 6))

    for job, speedup_values in speedups.items():
        plt.plot(threads, [speedup_values[thread] for thread in threads], marker='o', label=job)

    plt.title("Speedup vs Number of Threads")
    plt.xlabel("Number of Threads")
    plt.ylabel("Speedup")
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    print(os.getcwd())
    directory = "../data/data_part2b"
    speedups = get_speedups(directory)
    if speedups is not None:
        print(json.dumps(speedups, indent=4))
        plot_speedups(speedups)


