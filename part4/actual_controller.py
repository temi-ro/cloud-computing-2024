import sys
import signal
import functools
import subprocess
from time import sleep
from enum import Enum
import docker
import psutil
import scheduler
import scheduler_logger
from scheduler_logger import Job

class State(Enum):
    HIGH = "high"
    NORMAL = "normal"

def fill_queue(docker_client, q , q_containers):
    for ctnr in q_containers:
        container = docker_client.containers.create(name=ctnr["name"], cpuset_cpus=ctnr["cpus"], image=ctnr["image"], command=ctnr["command"], detach=True, auto_remove=False)
        container.reload()
        q.append(container)

def remove_previous_containers(docker_client):
        container_names = ["dedup", "splash2x-radix", "blackscholes", "canneal", "freqmine", "ferret", "vips"]
        for name in container_names:
            try:
                force_removal(docker_client.containers.get(name))
            except:
                print(f"{name} does not exist => not removed")

def force_removal(container):
        if container is not None:
            try:
                container.reload()
                if container.status == "paused":
                    container.unpause()
                container.reload()
                if container.status == "running":
                    container.kill()
                container.remove()
            except:
                print("issue with container removal")

def signal_handler(sig, frame):
    remove_previous_containers()
    sys.exit(0)


def set_cores_memcached(logger, pid, n_core):
    n_core_format = ",".join(map(str, range(0, n_core)))
    cmd = f"sudo taskset -a -cp {n_core_format} {pid}"
    subprocess.run(cmd.split(" "), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    
    logger.update_cores(Job.MEMCACHED, [str(i) for i in range(0, n_core)])

def print_content_queues(q2,q3):
        # Create a list of queues with their corresponding names for easier iteration and printing
        queues = [("q2", q2), ("q3", q3)]

        # Loop through each queue in the list
        for queue_name, queue in queues:
            # Use a list comprehension to collect the names of containers in the current queue
            container_names = [container.name for container in queue]
            # Print the queue name and the container names
            print(queue_name, container_names)

def map_from_string_to_job(name):
    if name == "dedup":
        return Job.DEDUP
    if name == "radix":
        return Job.RADIX
    if name == "blackscholes":
        return Job.BLACKSCHOLES
    if name == "canneal":
        return Job.CANNEAL
    if name == "freqmine":
        return Job.FREQMINE
    if name == "ferret":
        return Job.FERRET
    if name == "vips":
        return Job.VIPS
    return None

def reschedule(load, q2,q3, logger):
        #print all status
        print("q2")
        for container in q2:
            print(container.name, container.status)
        print("q3")
        for container in q3:
            print(container.name, container.status)
        print("reschedule with load ", load)
        to_run=[] 
        cores = []
        if(load == State.NORMAL):
            if(len(q3) >0):
                to_run= [3]
                cores=["1,2,3"]
            elif(len(q2) >1):
                to_run = [2, 2]
                cores = ["1","2,3"] 
            elif(len(q2) ==1):
                to_run = [2]
                cores = ["1,2,3"]
            else:
                to_run = []
                cores = []
        elif(load == State.HIGH):
            if(len(q2) >0):
                to_run = [2]
                cores = ["2,3"]
            elif(len(q3)):
                to_run = [3]
                cores = ["2,3"]
        else:
                to_run =[]
                cores =[]
        print("what to run: ", to_run)
        i=0
        for (q, nb) in [(q2,2), (q3,3)]: 
            j=0
            while(i<len(to_run) and to_run[i]==nb):
                container_run(cores[i],q[j], nb, logger)
                i+=1
                j+=1
            while(j<len(q)):
                container_pause(q[j], logger)
                j+=1

def container_run(cores, container, q, logger):
        if container is not None:
            container.reload()
            if container.status == "created":
                logger.job_start(map_from_string_to_job( container.name), [int(num) for num in cores.split(',')], q)
                print( container.name + "is started")
                container.update(cpuset_cpus=cores)
                container.start()
            elif container.status == "paused":
                logger.update_cores(map_from_string_to_job( container.name), [int(num) for num in cores.split(',')])
                container.update(cpuset_cpus=cores)
                logger.job_unpause(map_from_string_to_job( container.name))
                container.unpause()
                print("unpause " + container.name)
            else:
                return
            
def container_pause(container, logger):
        if container is not None:
            try:
                container.reload()
                if container.status == "restarting" or  container.status == "running":
                    logger.job_pause(map_from_string_to_job( container.name))
                    container.pause()
            except :
                print("error while pausing the container")

def clean_all_queues(q2,q3, logger):
        for q in [q2,q3]:
            index_to_remove = 0
            for _ in range(0, len(q)):
                container = q[index_to_remove]
                cleaned = False
                if container.status == "exited":
                    logger.job_end(map_from_string_to_job( container.name))
                    container_clean_exited(container)
                    try:
                        container.remove()
                    except:
                        force_removal(container)
                    cleaned = True
                if cleaned:
                    q.pop(index_to_remove)
                else:
                    index_to_remove += 1

def container_clean_exited(container, logger):
        if container is None:
            return False
        container.reload()
        if container.status == "exited":
            logger.log_container_event(container.name, 'FINISH')
            try:
                container.remove()
            except:
                force_removal(container)
            return True

        return False



def main():
    #create docker client
    docker_client = docker.from_env()
    containers = {
        "dedup": {
            "cpus": "0,1,2,3",
            "name": "dedup",
            "image": "anakli/cca:parsec_dedup",
            "command": "./run -a run -S parsec -p dedup -i native -n 2"
        },
        "radix": {
            "cpus": "0,1,2,3",
            "name": "radix",
            "image": "anakli/cca:splash2x_radix",
            "command": "./run -a run -S splash2x -p radix -i native -n 2"
        },
        "blackscholes": {
            "cpus": "0,1,2,3",
            "name": "blackscholes",
            "image": "anakli/cca:parsec_blackscholes",
            "command": "./run -a run -S parsec -p blackscholes -i native -n 3"
        },
        "canneal": {
            "cpus": "0,1,2,3",
            "name": "canneal",
            "image": "anakli/cca:parsec_canneal",
            "command": "./run -a run -S parsec -p canneal -i native -n 2"
        },
        "freqmine": {
            "cpus": "0,1,2,3",
            "name": "freqmine",
            "image": "anakli/cca:parsec_freqmine",
            "command": "./run -a run -S parsec -p freqmine -i native -n 2"
        },
        "ferret": {
            "cpus": "0,1,2,3",
            "name": "ferret",
            "image": "anakli/cca:parsec_ferret",
            "command": "./run -a run -S parsec -p ferret -i native -n 3"
        },
        "vips": {
            "cpus": "0,1,2,3",
            "name": "vips",
            "image": "anakli/cca:parsec_vips",
            "command": "./run -a run -S parsec -p vips -i native -n 2"
        }
    }
    #remove previous containers
    remove_previous_containers(docker_client)
    #fill the queues with containers
    q2 = []
    q3 = []
    fill_queue(docker_client, q2 , [containers["vips"], containers["canneal"], containers["dedup"], containers["freqmine"], containers["radix"]])
    fill_queue(docker_client, q3 , [containers["blackscholes"], containers["ferret"]])
    #initialize load level and logger
    load_level=State.NORMAL
    logger = scheduler_logger.SchedulerLogger()

    sched = scheduler.ContainerScheduler(logger, q2, q3)
    #handle ctrl+c
    signal.signal(signal.SIGINT, signal_handler)


    #first measure is wrong
    psutil.cpu_percent(interval=None, percpu=True)
    #initiate memcached
    memcache_pid = 0
    for proc in psutil.process_iter():
        if "memcache" in proc.name():
            memcache_pid = proc.pid
            break
    logger.job_start(Job.MEMCACHED, [0], 2)
    memcache_cores = 1
    set_cores_memcached(logger, memcache_pid, memcache_cores)

    print_index = 0
    while True:

        if print_index % 40== 0:
            print_content_queues(q2,q3)
        print_index+=1

        cpu_usages = psutil.cpu_percent(interval=None, percpu=True)
        cpu_usage_0 = cpu_usages[0] # utilization of core 0
        cpu_usage_1 = cpu_usages[1] # utilization of core 1

        # memcache can run only on core 0
        if cpu_usage_0 + cpu_usage_1 < 90 and load_level == State.HIGH: 
            #back to NORMAL level
            load_level = State.NORMAL
            # set memcache n_core to 1
            mc_n_core= 1
            set_cores_memcached(logger, memcache_pid, mc_n_core)

        # memcache needs to be on core 0 and 1
        if cpu_usage_0 > 55 and load_level == State.NORMAL: #a 35 et 75 ca passe bien 
            #back to high level
            load_level = State.HIGH


        reschedule(load_level, q2,q3, logger)
        # if we just changed the load from NORMAL to HIGH, set memcache n_core to 2 having rescheduled the jobs
        if load_level == State.HIGH and mc_n_core == 1:
            mc_n_core= 2
            set_cores_memcached(logger, memcache_pid, mc_n_core)


        # Remove containers if they are done.
        clean_all_queues(q2,q3, logger)


        if len(q2)==0 and len(q3)==0:
            mc_n_core = 2
            set_cores_memcached(logger, memcache_pid, mc_n_core)
            # set_memcached_core(mc_pid, 4, logger) # Should we give all core to memcached?
            print("we are done, waiting 1 minute for memcahed before ending completely")
            sleep(62)
            logger.job_end(Job.MEMCACHED)
            logger.end()
            break

        sleep(0.3)


if __name__ == "__main__":
    main()