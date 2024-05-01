import docker
from scheduler_logger import Job
NORMAL = "normal"
HIGH = "high"


class Scheduler:
    def __init__(logger, self, q2_containers, q3_containers, load_level=NORMAL):
        self.docker_client = docker.from_env()
        self.remove_previous_containers()
        self.q2 = []
        self.q3 = []
        self.fill_queue(self.q2 , q2_containers)
        self.fill_queue(self.q2 , q3_containers)
        self.__load_level = load_level  
        self.__logger = logger


    def clean_all_queues(self):
        for q in [self.q1,self.q2]:
            index_to_remove = 0
            for _ in range(0, len(q)):
                if self.cleaned(q[index_to_remove]):
                    q.pop(index_to_remove)
                else:
                    index_to_remove += 1

    #returns what job to run and on what core 
    def next_to_run(self, load): 
        if(load == NORMAL):
            if(len(self.q3) >0):
                return [3],["1,2,3"]
            elif(len(self.q2) >1):
                return [2, 2],["1","2,3"] 
            elif(len(self.q2) ==1):
                return [2],["1,2,3"]
            else:
                return [],[]
        elif(load == HIGH):
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
        

    # Container management helpers.
    def fill_queue(self, q , q_containers):
        for ctnr in q_containers:
            container = self.docker_client.containers.create(name=ctnr[1], cpuset_cpus=ctnr[0], image=ctnr[2], command=ctnr[3], detach=True, auto_remove=False)
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
                self.__logger.job_end(map_from_string_to_job( container.name))
                self.container_clean_exited(container)
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
                    self.__logger.job_pause(map_from_string_to_job( container.name))
                    container.pause()
            except :
                print("error while pausing the container")


    def run_container(self, cores, container, q):
        if container is not None:
            container.reload()
            if container.status == "created":
                self.__logger.job_start(map_from_string_to_job( container.name), [int(num) for num in cores.split(',')], q)
                print( container.name + "is started")
                container.update(cpuset_cpus=cores)
                container.start()
            elif container.status == "paused":
                self.__logger.update_cores(map_from_string_to_job( container.name), [int(num) for num in cores.split(',')])
                container.update(cpuset_cpus=cores)
                self.__logger.job_unpause(map_from_string_to_job( container.name))
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