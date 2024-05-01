import subprocess
import psutil

# Run this script to run memcached with the specified number of cores

# Returns tuple with pid of memcached and number of cpus (=1)
def init_memcached_config(n_core):
    process_name = "memcache"
    pid = None

    # Find the pid of memcache
    for process in psutil.process_iter():
        if process_name in process.name():
            pid = process.pid
            break
    
    return set_memcached_core(pid, n_core)

def set_memcached_core(pid, n_core):
    n_core_format = ",".join(map(str, range(0, n_core)))
    cmd = f"sudo taskset -a -cp {n_core_format} {pid}"
    subprocess.run(cmd.split(" "), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        
    return pid, n_core


def main():
    pid, n_core = init_memcached_config()
    print(f"Memcached is running with pid: {pid} and cpu affinity: {n_core}")
        
if __name__ == "__main__":
    main(2)
