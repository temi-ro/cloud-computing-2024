import docker

NORMAL = "normal"
HIGH = "high"


class ContainerScheduler:
    def __init__(self, q0_conf, q1_conf, q2_conf, logger, load_level=NORMAL):
        self.__client = docker.from_env()
        self.hard_remove_everything()
        # 1 core
        self.__queue1 = [self.create_container(c_tuple) for c_tuple in q0_conf]
        # 2 core
        self.__queue2 = [self.create_container(c_tuple) for c_tuple in q1_conf]
        # 3 core
        self.__queue3 = [self.create_container(c_tuple) for c_tuple in q2_conf]

        self.__load_level = NORMAL  # Initialize the load level to normal
        self.__logger = logger
        # Initialize client object for docker.

        #self.start_or_unpause_container(self.__queue3[0]) => TODO what to start first ? 
        #print("run " + self.__queue3[0].name)
        self.__running = [0, 0, 0]

    def get_load_level(self):
        return self.__load_level

    def get_running(self):
        return self.__running

    def get_core_usage(self):
        return self.__running[0] + 2 * self.__running[1] + 3 * self.__running[2]

    def can_schedule_queue1(self, num=1):
        return len(self.__queue1) 

    def can_schedule_queue2(self, num=1):
        return len(self.__queue2) 

    def can_schedule_queue3(self, num=1):
        return len(self.__queue3) 



    def REMOVE_EXITED_CONTAINERS(self):
        # Remove exited containers.
        pop_location = 0
        running = self.__running[0]
        for x in range(0, running):
            removed = self.remove_if_done_container(self.__queue1[pop_location])
            if removed:
                self.__running[0] -= 1
                self.__queue1.pop(pop_location)
            else:
                pop_location += 1

        pop_location = 0
        running = self.__running[1]
        for x in range(0, running):
            removed = self.remove_if_done_container(self.__queue2[pop_location])
            if removed:
                self.__running[1] -= 1
                self.__queue2.pop(pop_location)
            else:
                pop_location += 1

        pop_location = 0
        running = self.__running[2]
        for x in range(0, running):
            removed = self.remove_if_done_container(self.__queue3[pop_location])
            if removed:
                self.__running[2] -= 1
                self.__queue3.pop(pop_location)
            else:
                pop_location += 1

    #returns what job to run and on what core 
    def get_best_distribution(self, load): 
        if(load ==NORMAL):
            if(self.can_schedule_queue3()>0):
                return [3],["1,2,3"]
            elif(self.can_schedule_queue2()>0 and self.can_schedule_queue1() > 0):
                return [2, 1],["2,3","1"] 
            elif(self.can_schedule_queue2()==0):
                if(self.can_schedule_queue1() >= 3):
                    return [1,1,1],["2","3","1"]
                elif(self.can_schedule_queue1() == 2):
                    return [1,1],["2,3","1"]
                elif(self.can_schedule_queue1() == 1):
                    return [1],["1,2,3"]
                else:
                    return [],[]
            else:
                if(self.can_schedule_queue2() >=2):
                    return [2,2],["2,3","1"]
                elif(self.can_schedule_queue2() == 1):
                    return [2],["1,2,3"]
                elif(self.can_schedule_queue2() == 0):
                    return [],[]
        elif(load == HIGH):
            if(self.can_schedule_queue2()>0):
                return [2],["2,3"]
            elif(self.can_schedule_queue1() > 1):
                return [1,1],["2","3"]
            elif(self.can_schedule_queue3()):
                return [3],["2,3"]
            else:
                if(self.can_schedule_queue1() > 0):
                    return [1],["2,3"]
                else:
                    return [],[]
        else :
            print("Invalid load level. Exiting.")
            return 

    def reschedule(self, load):
        print("trying to reschedule with load ", load)
        distr, cores = self.get_best_distribution(load)
        print("best distr ", distr)
        i=0
        j=0
        while(i<len(distr) and distr[i]==3):
            self.start_or_unpause_container(self.__queue3[j], cores[i])
            self.__running[2] += 1
            i+=1
            j+=1
        while(j<len(self.__queue3)):
            self.pause_container(self.__queue3[j],3)
            j+=1
        j=0
        while(i<len(distr) and distr[i]==2):
            self.start_or_unpause_container(self.__queue2[j], cores[i])
            self.__running[1] += 1
            i+=1
            j+=1
        while(j<len(self.__queue2)):
            self.pause_container(self.__queue2[j], 2)
            j+=1
        j=0
        while(i<len(distr) and distr[i]==2):
            self.start_or_unpause_container(self.__queue2[j], cores[i])
            self.__running[0] += 1
            i+=1
            j+=1
        while(j<len(self.__queue1)):
            self.pause_container(self.__queue1[j], 1)
            j+=1


    def DONE(self):
        return self.__running == [0, 0,
                                  0] and not self.__queue1 and not self.__queue2 and not self.__queue3

    def print_queues(self):
        print("queue1", [c.name for c in self.__queue1], end="  ")
        print("queue2", [c.name for c in self.__queue2], end="  ")
        print("queue3", [c.name for c in self.__queue3], end="\n")

    # Container management helpers.

    def create_container(self, c_tuple):
        cont = self.__client.containers.create(cpuset_cpus=c_tuple[0],
                                               name=c_tuple[1],
                                               detach=True,
                                               auto_remove=False,
                                               image=c_tuple[2],
                                               command=c_tuple[3])
        cont.reload()
        return cont

    def hard_remove_container(self, cont):
        if cont is None: return
        try:
            cont.reload()
            if cont.status == "paused":
                cont.unpause()
            cont.reload()
            if cont.status == "running":
                cont.kill()
            cont.remove()
        except:
            print("You fucked up the 'hard_remove thingy'")

    def remove_container(self, cont):
        if cont is None:
            # print("Inside remove container. Returning none.")
            return None
        try:
            # print(f"Removed {cont.name}.")
            cont.remove()
        except:
            self.hard_remove_container(cont)
        return None

    def remove_if_done_container(self, cont):
        if cont is None:
            # print("Inside remove if done, returning none.")
            return False
        cont.reload()
        if cont.status == "exited":
            # print(f"Removing {cont.name} because it is done.")
            self.__logger.log_container_event(cont.name, 'FINISH')
            self.remove_container(cont)
            return True

        return False
        # else:
        #    raise NotImplementedError("IMPLEMENT ME???")

    def pause_container(self, cont, queue):
        if cont is None:
            return
        try:
            cont.reload()
            if cont.status in ["running", "restarting"]:
                self.__logger.log_container_event(cont.name, 'PAUSE')
                cont.pause()
                self.__running[queue - 1] -= 1
        except:
            print("something seems to have gone wrong while PAUSING the container (But dont care)")

    def unpause_container(self, cont):
        if cont is None:
            return
        cont.reload()
        if cont.status == "paused":
            self.__logger.log_container_event(cont.name, 'UNPAUSE')
            cont.unpause()

    def start_or_unpause_container(self, cont, cores):
        if cont is None:
            return
        cont.reload()
        if cont.status == "paused":
            self.__logger.log_container_event(cont.name, 'UNPAUSE')
            cont.update(cpuset_cpus=cores)
            cont.unpause()
            print("unpause " + cont.name)
        elif cont.status == "created":
            self.__logger.log_container_event(cont.name, 'START')
            print("start " + cont.name)
            cont.update(cpuset_cpus=cores)
            cont.start()
        else:
            print("start_or_unpause didn't do anything.")
            return

    def update_container(self, cont, cpu_set):
        if cont is None:
            return
        if cont.status == "exited":
            return

        cont.update(cpuset_cpus=cpu_set)

    def hard_remove_everything(self):
        try:
            self.hard_remove_container(self.__client.containers.get("dedup"))
        except:
            print("Tried to remove Dedup, but didn't exist.")
        try:
            self.hard_remove_container(self.__client.containers.get("splash2x-fft"))
        except:
            print("Tried to remove FFT, but didn't exist.")
        try:
            self.hard_remove_container(self.__client.containers.get("blackscholes"))
        except:
            print("Tried to remove Blackscholes, but didn't exist.")
        try:
            self.hard_remove_container(self.__client.containers.get("canneal"))
        except:
            print("Tried to remove Canneal, but didn't exist.")
        try:
            self.hard_remove_container(self.__client.containers.get("freqmine"))
        except:
            print("Tried to remove Freqmine, but didn't exist.")
        try:
            self.hard_remove_container(self.__client.containers.get("ferret"))
        except:
            print("Tried to remove Ferret, but didn't exist.")