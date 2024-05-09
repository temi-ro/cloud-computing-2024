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
    LOW = "low"


class Scheduler:
    def __init__(self,logger,  q2_containers, q3_containers, load_level=State.LOW):
        self.docker_client = docker.from_env()
        self.remove_previous_containers()
        self.q2 = []
        self.q3 = []
        self.fill_queue(self.q2 , q2_containers)
        self.fill_queue(self.q3 , q3_containers)
        self.log = logger


    def clean_all_queues(self):
        for q in [self.q2,self.q3]:
            index_to_remove = 0
            for _ in range(0, len(q)):
                if self.cleaned(q[index_to_remove]):
                    q.pop(index_to_remove)
                else:
                    index_to_remove += 1

    #returns what job to run and on what core 
    def next_to_run(self, load): 
        if(load == State.LOW):
            if(len(self.q3) >0):
                return [3],["1,2,3"]
            elif(len(self.q2) >1):
                return [2, 2],["1","2,3"] 
            elif(len(self.q2) ==1):
                return [2],["1,2,3"]
            else:
                return [],[]
        elif(load == State.HIGH):
            if(len(self.q2) >0):
                return [2],["2,3"]
            elif(len(self.q3)):
                return [3],["2,3"]
            else:
                    return [],[]

    def reschedule(self, load):
        #print all status
        print("q2")
        for container in self.q2:
            print(container.name, container.status)
        print("q3")
        for container in self.q3:
            print(container.name, container.status)
        print("reschedule with load ", load)
        to_run, cores = self.next_to_run(load)
        print("best distr ", to_run)
        i=0
        for (q, nb) in [(self.q2,2), (self.q3,3)]: 
            j=0
            while(i<len(to_run) and to_run[i]==nb):
                self.run_container(cores[i],q[j], nb)
                i+=1
                j+=1
            while(j<len(q)):
                self.container_pause(q[j])
                j+=1


    def end(self):
        return len(self.q2)==0 and len(self.q3)==0

    def print_content_queues(self):
        # Create a list of queues with their corresponding names for easier iteration and printing
        queues = [("q2", self.q2), ("q3", self.q3)]

        # Loop through each queue in the list
        for queue_name, queue in queues:
            # Use a list comprehension to collect the names of containers in the current queue
            container_names = [container.name for container in queue]
            # Print the queue name and the container names
            print(queue_name, container_names)
        

    #fill the queue with containers
    def fill_queue(self, q , q_containers):
        # Create the containers and add them to the queue
        for ctnr in q_containers:
            container = self.docker_client.containers.create(name=ctnr["name"], cpuset_cpus=ctnr["cpus"], image=ctnr["image"], command=ctnr["command"], detach=True, auto_remove=False)
            container.reload()
            q.append(container)

    def force_removal(self, container):
        if container is not None:
            try:
                container.reload()
                if container.status == "paused":
                    print("unpause container before deletion")
                    container.unpause()
                container.reload()
                if container.status == "running":
                    print("kill container")
                    container.kill()
                container.remove()
            except:
                print("issue with container removal")


    def cleaned(self, container):
        if container is not None:
            container.reload()
            if container.status == "exited":
                self.log.job_end(map_from_string_to_job( container.name))
                try:
                    container.remove()
                except:
                    self.force_removal(container)
                return True
            return False

    def container_pause(self, container):
        if container is not None:
            try:
                container.reload()
                if container.status == "restarting" or  container.status == "running":
                    self.log.job_pause(map_from_string_to_job( container.name))
                    container.pause()
            except :
                print("error while pausing the container")


    def run_container(self, cores, container, q):
        if container is not None:
            container.reload()
            if container.status == "created":
                self.log.job_start(map_from_string_to_job( container.name), [int(num) for num in cores.split(',')], q)
                print( container.name + "is started")
                container.update(cpuset_cpus=cores)
                container.start()
            elif container.status == "paused":
                self.log.update_cores(map_from_string_to_job( container.name), [int(num) for num in cores.split(',')])
                container.update(cpuset_cpus=cores)
                self.log.job_unpause(map_from_string_to_job( container.name))
                container.unpause()
                print("unpause " + container.name)
            else:
                return

    def remove_previous_containers(self):
        container_names = ["dedup", "splash2x-radix", "blackscholes", "canneal", "freqmine", "ferret", "vips"]
        for name in container_names:
            try:
                self.force_removal(self.docker_client.containers.get(name))
            except:
                print(f"{name} does not exist => not removed")


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


def signal_handler(sched, sig, frame):
    sched.remove_previous_containers()
    sys.exit(0)

#set the cores of memcached
def set_cores_memcached(logger, pid, n_core):
    cmd = f"sudo taskset -a -cp {n_core} {pid}"
    subprocess.run(cmd.split(" "), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    if(n_core == "0"):
        logger.update_cores(Job.MEMCACHED, ["0"])
    else:
        logger.update_cores(Job.MEMCACHED, ["0", "1"])

def dynamic_experiment():
    containers = {
        "dedup": {
            "cpus": "0,1,2,3",
            "name": "dedup",
            "image": "anakli/cca:parsec_dedup",
            "command": "./run -a run -S parsec -p dedup -i native -n 3"
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
            "command": "./run -a run -S parsec -p ferret -i native -n 2"
        },
        "vips": {
            "cpus": "0,1,2,3",
            "name": "vips",
            "image": "anakli/cca:parsec_vips",
            "command": "./run -a run -S parsec -p vips -i native -n 3"
        }
    }

    q2 = [containers["canneal"], containers["ferret"], containers["freqmine"], containers["radix"]]
    q3 = [containers["blackscholes"], containers["vips"], containers["dedup"]]

    logger = scheduler_logger.SchedulerLogger()
    sched = Scheduler(logger, q2, q3)
    signal.signal(signal.SIGINT, functools.partial(signal_handler, sched)) # Clean interrupt


    # Discard first measurement, since it is always wrong.
    psutil.cpu_percent(interval=None, percpu=True)

    memcache_pid = 0
    for proc in psutil.process_iter():
        if "memcache" in proc.name():
            memcache_pid = proc.pid
            break
    logger.job_start(Job.MEMCACHED, [0], 2)
    memcache_cores = "0"
    set_cores_memcached(logger, memcache_pid, memcache_cores)

    # mc_process = psutil.Process(mc_pid)
    index_to_print = 0
    state = State.LOW
    file_path = 'example.txt'
    nb_high = 0
    nb_normal = 0
    with open(file_path, 'w') as f:
        while True:
            if index_to_print == 0:
                sched.print_content_queues()
            index_to_print = (index_to_print + 1) % 20

            # mc_utilization = mc_process.cpu_percent() # Does it give the total cpu utilization of memcached?
            cpu_utilizations = psutil.cpu_percent(interval=None, percpu=True)
            cpu_utilization_0 = cpu_utilizations[0] # utilization of core 0
            cpu_utilization_1 = cpu_utilizations[1] # utilization of core 1

            # memcache can run only on core 0
            if cpu_utilization_0 + cpu_utilization_1 < 31.2 and state == State.HIGH: #35 good
                load_level = State.LOW
                # set memcache n_core to 1
                memcache_cores= "0"
                set_cores_memcached(logger, memcache_pid, memcache_cores)
            elif cpu_utilization_0 > 12 and state == State.LOW: ##15 good
                #back to high level
                load_level = State.HIGH

            sched.reschedule(state)
            # if we just changed the load from NORMAL to HIGH, set memcache n_core to 2 after rescheduling
            if state == State.HIGH and memcache_cores == "0":
                memcache_cores= "0,1"
                set_cores_memcached(logger, memcache_pid, memcache_cores)
    
    
            # Remove containers if they are done.
            sched.clean_all_queues()
            if(state == State.LOW):
                nb_normal += 1
            if(state == State.HIGH):
                nb_high += 1

            f.write(f" normal : {nb_normal}, high : {nb_high}\n")
            print("loadLevel", state)
            # Start containers.
            # sched.SCHEDULE_NEXT()

            if sched.end():
                break
            sleep(0.25)
        memcache_cores = "0,1"
        set_cores_memcached(logger, memcache_pid, memcache_cores)
        print("we are done, waiting 1 minute for memcahed before ending completely")
        #wait 1 minute before ending
        sleep(62)
        logger.job_end(Job.MEMCACHED)
        logger.end()


if __name__ == "__main__":
    dynamic_experiment()
