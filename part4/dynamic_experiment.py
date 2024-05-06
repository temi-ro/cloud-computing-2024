import sys
import signal
import functools
import subprocess
from time import sleep
from enum import Enum
import docker
import psutil
import scheduler_logger
from scheduler_logger import Job

class State(Enum):
    HIGH = "high"
    NORMAL = "normal"

#create docker client
docker_client = docker.from_env()

#fill the queue with containers
def fill_queue(docker_client, q , q_containers):
    # Create the containers and add them to the queue
    for ctnr in q_containers:
        container = docker_client.containers.create(name=ctnr["name"], cpuset_cpus=ctnr["cpus"], image=ctnr["image"], command=ctnr["command"], detach=True, auto_remove=False)
        container.reload()
        q.append(container)

#remove previous containers (that currently exits)
def remove_previous_containers(docker_client):
    container_names = ["dedup", "splash2x-radix", "blackscholes", "canneal", "freqmine", "ferret", "vips"]
    # Loop through the container names and force removal
    for name in container_names:
        try:
            force_removal(docker_client.containers.get(name))
        except:
            print(f"{name} does not exist => not removed")

#force removal of a container
def force_removal(container):
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

#handle ctrl+c
def signal_handler(sig, frame):
    # Remove all containers
    remove_previous_containers(docker_client)
    sys.exit(0)

#set the cores of memcached
def set_cores_memcached(logger, pid, n_core):
    cmd = f"sudo taskset -a -cp {n_core} {pid}"
    subprocess.run(cmd.split(" "), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    if(n_core == "0"):
        logger.update_cores(Job.MEMCACHED, ["0"])
    else:
        logger.update_cores(Job.MEMCACHED, ["0", "1"])

# print the content of the queues
def print_content_queues(q2,q3):
    # Create a list of queues with their corresponding names for easier iteration and printing
    queues = [("q2", q2), ("q3", q3)]
    # Loop through each queue in the list
    for queue_name, queue in queues:
        # Use a list comprehension to collect the names of containers in the current queue
        container_names = [container.name for container in queue]
        # Print the queue name and the container names
        print(queue_name, container_names)

#map a string to a job
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

#reschedule the containers based on the load level
def reschedule(load, q2,q3, logger):
    #print all status
    print("q2")
    for container in q2:
        print(container.name, container.status)
    print("q3")
    for container in q3:
        print(container.name, container.status)
    print("reschedule with load ", load)
    #determine what job to run with what queue
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
    #run the containers previously decided to run 
    i=0
    for (q, nb) in [(q2,2), (q3,3)]: 
        j=0
        #run the appropriate containers
        while(i<len(to_run) and to_run[i]==nb):
            container_run(cores[i],q[j], nb, logger)
            i+=1
            j+=1
        #pause the others if needed
        while(j<len(q)):
            container_pause(q[j], logger)
            j+=1

#make a container run 
def container_run(cores, container, q, logger):
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

#pause a container
def container_pause(container, logger):
    try:
        container.reload()
        if container.status == "restarting" or  container.status == "running":
            print("pausing container", container.name)
            logger.job_pause(map_from_string_to_job( container.name))
            container.pause()
    except :
        print("error while pausing the container")

#cleaning all queues (removing exited containers)
def clean_all_queues(q2,q3, logger):
    for q in [q2,q3]:
        index_to_remove = 0
        for _ in range(0, len(q)):
            container = q[index_to_remove]
            cleaned = False
            container.reload()
            if container.status == "exited":
                logger.job_end(map_from_string_to_job( container.name))
                try:
                    container.remove()
                except:
                    force_removal(container)
                cleaned = True
            if cleaned:
                q.pop(index_to_remove)
            else:
                index_to_remove += 1

def experiment():
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
    fill_queue(docker_client, q2 , [containers["vips"], containers["ferret"], containers["dedup"], containers["freqmine"], containers["radix"]])
    fill_queue(docker_client, q3 , [containers["blackscholes"], containers["canneal"]])
    #fill_queue(docker_client, q2 , [containers["vips"], containers["radix"]])
    #fill_queue(docker_client, q3 , [containers["dedup"], containers["ferret"]])
    #initialize load level and logger
    load_level=State.NORMAL
    logger = scheduler_logger.SchedulerLogger()

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
    memcache_cores = "0"
    set_cores_memcached(logger, memcache_pid, memcache_cores)

    print_index = 0
    while True:

        cpu_usages = psutil.cpu_percent(interval=None, percpu=True)
        cpu_usage_0 = cpu_usages[0] # utilization of core 0
        cpu_usage_1 = cpu_usages[1] # utilization of core 1

        # memcache can run only on core 0
        if cpu_usage_0 + cpu_usage_1 < 75 and load_level == State.HIGH:  #31.5 et 10.5
            #back to NORMAL level
            load_level = State.NORMAL
            # set memcache n_core to 1
            memcache_cores= "0"
            set_cores_memcached(logger, memcache_pid, memcache_cores)

        # memcache needs to be on core 0 and 1
        if cpu_usage_0 > 35 and load_level == State.NORMAL: #a 35 et 75 ca passe bien 
            #back to high level
            load_level = State.HIGH

        # reschedule the jobs according to the load level
        reschedule(load_level, q2,q3, logger)
        # if we just changed the load from NORMAL to HIGH, set memcache n_core to 2 after having rescheduled the jobs (and therefore having freed core 1)
        if load_level == State.HIGH and memcache_cores == "0":
            memcache_cores= "0,1"
            set_cores_memcached(logger, memcache_pid, memcache_cores)


        # Remove containers if they are done.
        clean_all_queues(q2,q3, logger)

        #check if we are done
        if len(q2)==0 and len(q3)==0:
            # set memcache n_core to 2 for the end
            memcache_cores = "0,1"
            set_cores_memcached(logger, memcache_pid, memcache_cores)
            print("we are done, waiting 1 minute for memcahed before ending completely")
            sleep(62)
            logger.job_end(Job.MEMCACHED)
            logger.end()
            break

        if print_index % 40== 0:
            print_content_queues(q2,q3)
        print_index+=1

        sleep(0.3)


if __name__ == "__main__":
    experiment()