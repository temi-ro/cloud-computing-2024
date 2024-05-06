import pandas as pd
import matplotlib.pyplot as plt
import json

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
                'node': item['spec']['nodeName']
            }
            pods.append(pod_info)
    return pd.DataFrame(pods)

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
        'blackscholes': '#7fc97f',
        'canneal': '#beaed4',
        'dedup': '#fdc086',
        'ferret': '#ffff99',
        'freqmine': '#386cb0',
        'radix': '#f0027f',
        'vips': '#bf5b17'
    }

    # Since mcperf_data doesn't contain job names, we'll use a single color for all data segments
    for index, row in mcperf_data.iterrows():
        plt.bar(x=row['ts_start'], height=row['p95'], width=(row['ts_end'] - row['ts_start']), color='grey', alpha=0.7)

    # Adding annotations and using specific colors for each batch job
    for index, row in pods_data.iterrows():
        job_name = row['name']
        color = color_map.get(job_name.split('-')[0].lower(), 'grey')  # Assuming job_name is formatted as "jobname-..."
        plt.axvline(x=row['start_time'], color=color, linestyle='--', label=f"{job_name} start (Node: {row['node']})")
        plt.axvline(x=row['end_time'], color=color, linestyle=':', label=f"{job_name} end (Node: {row['node']})")

    plt.title(f'Memcached 95th Percentile Latency Over Time (Run {run_number})')
    plt.xlabel('Time (s)')
    plt.ylabel('Latency (ms)')
    plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1))
    plt.grid(True)
    plt.savefig(f'plot_part3_run_{run_number}.png')
    plt.show()


for i in range(1, 4):
    mcperf_file = f'mcperf_{i}.txt'
    pods_file = f'pods_{i}.json'
    mcperf_data = load_mcperf(mcperf_file)
    pods_data = load_pods(pods_file)
    mcperf_data_adj, pods_data_adj = adjust_timestamps(mcperf_data, pods_data)
    plot_latency(mcperf_data_adj, pods_data_adj, i)
    print("plotted: ", i)

