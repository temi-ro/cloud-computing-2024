import pandas as pd
import matplotlib.pyplot as plt
import json
import numpy as np

def load_mcperf(file):
    df = pd.read_csv(file, sep='\s+')
    df['ts_start'] = pd.to_datetime(df['ts_start'], unit='ms').dt.tz_localize(None)
    df['ts_end'] = pd.to_datetime(df['ts_end'], unit='ms').dt.tz_localize(None)
    return df

def load_pods(file):
    with open(file) as f:
        data = json.load(f)
    pods = []
    for item in data['items']:
        if 'parsec-' in item['metadata']['name']:
            pod_info = {
                'name': item['metadata']['name'].split('-')[1],
                'start_time': pd.to_datetime(item['status']['startTime']).tz_localize(None),
                'end_time': pd.to_datetime(item['status']['containerStatuses'][0]['state']['terminated']['finishedAt']).tz_localize(None),
                'node': item['spec']['nodeName'],
                'runtime': (pd.to_datetime(item['status']['containerStatuses'][0]['state']['terminated']['finishedAt']).tz_localize(None) -
                            pd.to_datetime(item['status']['startTime']).tz_localize(None)).total_seconds()
            }
            pods.append(pod_info)
    return pd.DataFrame(pods)

def calculate_statistics(pods_data):
    job_stats = {job: [] for job in pods_data['name'].unique()}
    for job in pods_data['name'].unique():
        runtimes = pods_data[pods_data['name'] == job]['runtime']
        job_stats[job].append(runtimes.mean())
    total_runtime = pods_data['runtime'].sum()
    job_stats['total_time'] = [total_runtime]
    return job_stats

def final_statistics(all_runs_stats):
    final_stats = {}
    for key in all_runs_stats[0]:
        all_runtimes = [run[key] for run in all_runs_stats]
        mean_runtimes = np.mean(all_runtimes, axis=0)
        std_runtimes = np.std(all_runtimes, axis=0)
        final_stats[key] = {'mean': mean_runtimes, 'std': std_runtimes}
    return final_stats

def adjust_timestamps(mcperf_data, pods_data):
    first_start_time = pods_data['start_time'].min()
    mcperf_data['ts_start_rel'] = (mcperf_data['ts_start'] - first_start_time).dt.total_seconds()
    mcperf_data['ts_end_rel'] = (mcperf_data['ts_end'] - first_start_time).dt.total_seconds()
    pods_data['start_time_rel'] = (pods_data['start_time'] - first_start_time).dt.total_seconds()
    pods_data['end_time_rel'] = (pods_data['end_time'] - first_start_time).dt.total_seconds()
    return mcperf_data, pods_data

def plot_latency(mcperf_data, pods_data, run_number):
    plt.figure(figsize=(14, 7))
    color_map = {
        'blackscholes': '#cca000',  # Beige
        'canneal': '#cccca9',  # Yellow-grey
        'dedup': '#ccacca',  # Light purple (Lavender)
        'ferret': '#a9ccca',  # Light blue-grey (Light Steel Blue)
        'freqmine': '#09ca00',  # Green
        'radix': '#00cc9f',  # Mint (Pale green)
        'vips': '#cc0b00'  # Red
    }

    for index, row in mcperf_data.iterrows():
        plt.bar(x=row['ts_start_rel'], height=row['p95'], width=(row['ts_end_rel'] - row['ts_start_rel']), color='grey', alpha=0.7)
    for index, row in pods_data.iterrows():
        job_name = row['name']
        color = color_map.get(job_name.split('-')[0].lower(), 'grey')
        plt.axvline(x=row['start_time_rel'], color=color, linestyle='--', label=f"{job_name} start (Node: {row['node']})")
        plt.axvline(x=row['end_time_rel'], color=color, linestyle=':', label=f"{job_name} end (Node: {row['node']})")
    plt.title(f'Memcached 95th Percentile Latency Over Time (Run {run_number})')
    plt.xlabel('Time (s)')
    plt.ylabel('Latency (ms)')
    plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1))
    plt.grid(True)
    plt.savefig(f'plot_part3_run_{run_number}.png')
    plt.show()

# Collect statistics from all runs
all_runs_stats = []

for i in range(1, 4):
    mcperf_file = f'mcperf_{i}.txt'
    pods_file = f'pods_{i}.json'
    mcperf_data = load_mcperf(mcperf_file)
    pods_data = load_pods(pods_file)
    mcperf_data_adj, pods_data_adj = adjust_timestamps(mcperf_data, pods_data)
    plot_latency(mcperf_data_adj, pods_data_adj, i)
    stats = calculate_statistics(pods_data_adj)
    all_runs_stats.append(stats)
    print(f"Statistics for Run {i}: {stats}")

# Calculate and print the final average and standard deviation across all runs
final_stats = final_statistics(all_runs_stats)
print("Final Statistics across All Runs:", final_stats)
