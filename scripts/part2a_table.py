import os
import json

def extract_real_time(filename):
    with open(filename, 'r') as file:
        for line in file:
            if line.startswith("real"):
                time = line.split("\t")[1]
                minutes, seconds = time.split("m")
                seconds = seconds.strip()[:-1]  # remove trailing 's'
                # print(minutes, seconds)
                return float(minutes) * 60 + float(seconds)
    return None

def get_time(directory):
    times = {}
    jobs = ['blackscholes', 'canneal', 'dedup', 'ferret', 'freqmine', 'vips', 'radix']
    benchmarks = ['none', 'ibench-cpu', 'ibench-l1d', 'ibench-l1i', 'ibench-l2', 'ibench-llc', 'ibench-membw']

    for job in jobs:
        time_none = None
        for benchmark in benchmarks:
            filename = 'output_parsec_{0}_{1}.txt'.format(job, benchmark)
            time = extract_real_time(os.path.join(directory, filename))

            if benchmark == 'none':
                time_none = time

            if time is not None:
                if job not in times:
                    times[job] = {}
                times[job][benchmark] = time/time_none


    return times

# def normalize_times(directory):
#     none_time = None
#     times = {}
        
#     # Extract times for other workloads
#     for filename in os.listdir(directory):
#         if filename.startswith('output_parsec_') and filename.endswith('_ibench-membw.txt'):
#             job_benchmark = filename.split('_')[2]
#             workload = filename.split('_')[3].split('-')[1]  # Extract the workload name
#             time = extract_real_time(os.path.join(directory, filename))
#             if time is not None:
#                 if workload not in times:
#                     times[workload] = []
#                 times[workload].append({'benchmark': job_benchmark, 'normalized_time': time / none_time})
    
#     return times

# def print_table(times):
#     print("{:<15} {:<15} {:<10}".format('Workload', 'Benchmark', 'Normalized Time'))
#     for workload, benchmarks in times.items():
#         for benchmark in benchmarks:
#             print("{:<15} {:<15} {:<10.2f}".format(workload, benchmark['benchmark'], benchmark['normalized_time']))

if __name__ == "__main__":
    directory = "data/data_part2"
    times = get_time(directory)
    if times is not None:
        print(json.dumps(times, indent=4))
        # print(times)
