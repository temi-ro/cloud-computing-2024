import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.interpolate import interp1d
from datetime import datetime
from collections import defaultdict
import ast
import matplotlib.patches as mpatches
import json
from dateutil.parser import parse


# Function to read time and p95 latency from a file (mcperf)
def read_time_qps(filename, n):
    data = np.loadtxt(filename, skiprows=6, usecols=(12, 16, 18, 19), max_rows=n, dtype=float)
    p95 = list(map(lambda x: x/1000, data[:, 0]))
    qps = list(map(lambda x: x/1000, data[:, 1]))
    first_start_time = data[0, 2]
    # first_start_time = 0
    start_time = list(map(lambda x: (x - first_start_time)/1000, data[:, 2]))
    end_time = list(map(lambda x: (x - first_start_time)/1000, data[:, 3]))
    
    return p95, qps, start_time, end_time, first_start_time/1000

def convert_time_to_seconds(timestamp):
    timestamp = str(timestamp)
    # print("timestamp:", timestamp)
    # timestamp_dt = datetime.fromisoformat(timestamp)
    try:
        timestamp_dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
    except:
        timestamp_dt = parse(timestamp)
    # Convert datetime object to seconds
    time_sec = timestamp_dt.timestamp()
    return (time_sec)


def read_pods(pods, x):
    with open(pods) as f:
        data = json.load(f)
    pods = []
    start_time = convert_time_to_seconds(min([data['items'][i]['status']['startTime'] for i in range(len(data['items'])) if 'parsec-' in data['items'][i]['metadata']['name']]))
    print(start_time, x)
    start_time = convert_time_to_seconds(min([data['items'][i]['status']['startTime'] for i in range(len(data['items'])) if 'parsec-' in data['items'][i]['metadata']['name']]))
    print(start_time, x)
    for item in data['items']:
        if 'parsec-' in item['metadata']['name']:
            pod_info = {
                'name': item['metadata']['name'].split('-')[1],
                'start_time': convert_time_to_seconds(item['status']['startTime'])-start_time,
                'end_time': convert_time_to_seconds(item['status']['containerStatuses'][0]['state']['terminated']['finishedAt'])-start_time,
                'node': item['spec']['nodeName'],
                'runtime': (convert_time_to_seconds(item['status']['containerStatuses'][0]['state']['terminated']['finishedAt']) -
                            convert_time_to_seconds(item['status']['startTime']))
            }
            
            pods.append(pod_info)


    return pods

def plot_gantt_chart(ax_memcached, ax_vm4, ax_vm8, tasks, colors):
    n_cores = {
        "vips": 2,
        "radix": 2,
        "freqmine": 4,
        "blackscholes": 2,
        "dedup": 2,
        "ferret": 2,
        "canneal": 2,
        "memcached": 2
    }
    cores = {
        "vips": [4,5],
        "radix": [6,7],
        "freqmine": [0,1,2,3],
        "blackscholes": [6,7],
        "dedup": [4,5],
        "ferret": [0,1], # 8 or 10 which finishes first? canneal or vips
        "canneal": [2,3],
        "memcached": [0, 1]
    }
    for i, task in enumerate(tasks):
        # if task["name"] == "vips":
        #     continue
        print(task)
        # for c in cores[task['name']]:
        if "4core" in task["node"]:
            ax_vm4.barh(cores[task["name"]], task["end_time"]-task["start_time"], left=task['start_time'], color=colors[task['name']], label=task['name'])
        else:
            ax_vm8.barh(cores[task["name"]], task["end_time"]-task["start_time"], left=task['start_time'], color=colors[task['name']], label=task['name'])
    x = list(range(0,4)) + list(range(0,8)) + list(range(0,4))
    print(x)
    ax_memcached.barh(cores["memcached"], 180, left=0, color='#CCCCCC', label="memcached")
    ax_memcached.set_yticklabels([0, 1])
    ax_memcached.set_yticks(list(range(0,2)))

    ax_vm4.set_yticklabels([0, 1, 2, 3])
    ax_vm4.set_yticks(list(range(0,4)))

    ax_vm8.set_yticklabels([0, 1, 2, 3, 4, 5, 6, 7])
    ax_vm8.set_yticks(list(range(0,8)))

    # ax.set_yticklabels([0, 1, 2, 3, 0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3])
    # ax.set_yticks(list(range(0,12)))
    # ax.set_ylim(0, 12)
    # ax_vm4.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    # ax_vm8.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    ax_memcached.xaxis.set_visible(False)
    ax_vm4.xaxis.set_visible(False)
    ax_vm8.xaxis.set_visible(False)
    
    ax_vm4.set_ylabel('   4core VM')
    ax_memcached.set_ylabel('2core VM')

    ax_vm8.set_ylabel('8core VM')


def main(i):
    mcperf_filename = f'./part3/mcperf_{i}.txt'
    pods_filename = f'./part3/pods_{i}.json'


    # Read the data from the file
    p95, qps, start_time, end_time, overall_start_time = read_time_qps(mcperf_filename, 1000)
    # Read the pods data
    pods_data = read_pods(pods_filename, overall_start_time)
    overall_end_time = max([pod['end_time'] for pod in pods_data])

    fig, ax1 = plt.subplots(figsize=(20, 7))


    # Plot the p95 latency vs time
    handle1, = ax1.plot(start_time, p95, "-o", label='p95 latency vs time', color="orange")
    ax1.set_xlim(0, overall_end_time)
    ax1.set_xticks(np.arange(0, overall_end_time, 10))
    # Set the y-axis limits
    ax1.set_ylim(0, 1.5)
    ax1.set_yticks(np.arange(0, 0.8, 0.1))
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('p95 latency (ms)                                                       ', color="orange")

    # Plot the QPS vs time
    ax2 = ax1.twinx()
    handle2, = ax2.step(start_time, qps, where="post", label='QPS vs time', color="tab:blue")
    # ax2.plot(start_time, qps, "-o", label='QPS vs time', color="orange")
    ax2.set_ylim(0, 70)
    ax2.set_yticks(np.arange(0, 36, 5))
    ax2.set_ylabel('Achieved KQPS                                                       ', color="tab:blue")
    
    ax2.tick_params(axis='y', colors='tab:blue')
    ax1.tick_params(axis='y', colors='orange')

    ax_memcached = fig.add_subplot(15, 1, 7, sharex=ax1)
    ax_vm4 = fig.add_subplot(8, 1, 3, sharex=ax1)
    ax_vm8 = fig.add_subplot(4, 1, 1, sharex=ax1)
    colors = {
        'vips': '#CC0A00',
        'radix': '#00CCA0',
        'freqmine': '#0CCA00',
        'blackscholes': '#CCA000',
        'dedup': '#CCACCA',
        'ferret': '#AACCCA',
        'canneal': '#CCCCAA',
        'memcached': '#CCCCCC'
    }

    # Plot the Gantt chart
    plot_gantt_chart(ax_memcached, ax_vm4, ax_vm8, pods_data, colors)
    
    # Create a dummy task for memcached for the legend
    memcached_legend = mpatches.Patch(color=colors['memcached'], label='memcached')

    tasks_handles = [mpatches.Patch(color=colors[task["name"]], label=task["name"]) for task in pods_data]
    tasks_handles.append(memcached_legend)  # Add memcached to the legend

    plt.suptitle('p95 latency, achieved QPS and job schdeuling vs time', y=0.95)
    handles = tasks_handles + [handle1] + [handle2]
    print(handles)
    leg = plt.legend(handles=handles, ncol=2)
    plt.draw()

    bb = leg.get_bbox_to_anchor().transformed(ax1.transAxes.inverted())
    offset = -0.02
    bb.x0 += offset
    bb.x1 += offset
    yoffset = 0.75
    bb.y0 -= yoffset
    bb.y1 -= yoffset
    leg.set_bbox_to_anchor(bb, transform = ax1.transAxes)

    # plt.subplots_adjust(right=0.85)
    plt.show()

if __name__ == '__main__':
    for i in range(1, 4):
        main(i)
