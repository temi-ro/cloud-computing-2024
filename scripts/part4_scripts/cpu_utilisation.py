import psutil
from time import sleep, time

# When there are 2 cores
def get_total_cpu_utilisation():
    cpu_utilisation = psutil.cpu_percent(interval=None, percpu=True)
    return cpu_utilisation[0] + cpu_utilisation[1]

# When there is 1 core
def get_cpu_utilisation():
    return psutil.cpu_percent(interval=None, percpu=True)[0]

def get_all_cpu_utilisation():
    return psutil.cpu_percent(interval=None, percpu=True)

def get_time():
    return round(time() * 1000)

def main(n_cores=2):
    filename = f'cpu_util_{n_cores}.txt'
    max_s = 0

    with open(filename, 'w') as f:
        for i in range(0, 73):
            cpus = get_all_cpu_utilisation()
            s = sum(cpus)
            if s > 3*max_s/4:
                val = f"{get_time()} {s} {cpus}"
                f.write(val + "\n")
                print(val)    
            else:
                print("Skipping")

            sleep(2.5)
            max_s = max(s, max_s)

if __name__ == '__main__':
    main(2)