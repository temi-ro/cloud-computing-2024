import psutil
from time import sleep, time

# This script monitor CPU utilisation of the system

# Returns a list of CPU utilisation for each core
def get_all_cpu_utilisation():
    return psutil.cpu_percent(interval=None, percpu=True)

# Returns the current time in milliseconds
def get_time():
    return round(time() * 1000)

def main(n_cores=2):
    filename = f'cpu_util_{n_cores}.txt'

    with open(filename, 'w') as f:
        f.write("time | cpu_utils[0] + cpu_utils[1] | cpu_utils \n" if n_cores == 2 else "time | cpu_utils0 | cpu_utils\n")
        
        for i in range(0, 37):
            cpu_utils = get_all_cpu_utilisation()
            s = cpu_utils[0] + cpu_utils[1] if n_cores == 2 else cpu_utils[0]
            val = f"{get_time()} {s} {cpu_utils}"
            f.write(val + "\n")
            print(val) 
            
            sleep(2.5)

if __name__ == '__main__':
    main(2)