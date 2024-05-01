import functools
import subprocess
from time import sleep

import psutil
import scheduler
import signal
import sys
import scheduler_logger
from scheduler_logger import Job

HIGH = "high"
NORMAL = "normal"

def handle_signal(sched, sig, frame):
    print("aborting...")
    sched.hard_remove_everything()
    sys.exit(0)

def print_memcached_cores(pid):
    try:
        memcached_process = psutil.Process(pid)
        cores = memcached_process.cpu_affinity()
        print(f"Memcached is currently running on cores: {cores}")
    except psutil.NoSuchProcess:
        print("Memcached process not found.")
        
# Returns tuple with pid of memcached and number of cpus (=1)
def init_memcached_config(logger):
    process_name = "memcache"
    pid = None

    # Find the pid of memcache
    for process in psutil.process_iter():
        if process_name in process.name():
            pid = process.pid
            break
    
    logger.job_start(Job.MEMCACHED, [0], 2)
    #command = f"sudo renice -n -19 -p {pid}"
    #subprocess.run(command.split(" "), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    # Set the cpu affinity of memcached to CPU 0
    return set_memcached_core(pid, 2, logger)


# Set the cpu affinity of memcached to the given cpu
# def set_memcached_cpu(pid, no_of_cpus, logger):
#     cpu_affinity = ",".join(map(str, range(0, no_of_cpus)))
#     print(f'Setting Memcached CPU affinity to {cpu_affinity}')
#     command = f'sudo taskset -a -cp {cpu_affinity} {pid}'
#     logger.log_memchached_state(no_of_cpus)
#     subprocess.run(command.split(" "), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
#     return pid, no_of_cpus

def set_memcached_core(pid, n_core, logger):
    n_core =1
    n_core_format = ",".join(map(str, range(0, n_core)))
    cmd = f"sudo taskset -a -cp {n_core_format} {pid}"
    subprocess.run(cmd.split(" "), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    print_memcached_cores(pid)
    
    logger.update_cores(Job.MEMCACHED, [str(i) for i in range(0, n_core)])
    
    return pid, n_core

dedup = ("0,1,2,3",
         "dedup",
         "anakli/cca:parsec_dedup",
         "./run -a run -S parsec -p dedup -i native -n 2")
radix = ("0,1,2,3",
         "radix",
         "anakli/cca:splash2x_radix",
         "./run -a run -S splash2x -p radix -i native -n 2")
blackscholes = ("0,1,2,3",
                "blackscholes",
                "anakli/cca:parsec_blackscholes",
                "./run -a run -S parsec -p blackscholes -i native -n 3")
canneal = ("0,1,2,3",
           "canneal",
           "anakli/cca:parsec_canneal",
           "./run -a run -S parsec -p canneal -i native -n 3")
freqmine = ("0,1,2,3",
            "freqmine",
            "anakli/cca:parsec_freqmine",
            "./run -a run -S parsec -p freqmine -i native -n 2")
ferret = ("0,1,2,3",
          "ferret",
          "anakli/cca:parsec_ferret",
          "./run -a run -S parsec -p ferret -i native -n 3")
vips = ("0,1,2,3",
        "vips",
        "anakli/cca:parsec_vips",
        "./run -a run -S parsec -p vips -i native -n 2")

def main():
    #command = "sudo systemctl restart docker"
    #subprocess.run(command.split(" "), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    nb_normal = 0
    nb_high = 0
    q1 = [dedup, radix]
    q2 = [canneal, blackscholes, vips]
    q3 = [ferret, freqmine]
    q2=[vips, canneal, dedup, freqmine, radix]
    q3=[blackscholes, ferret]
    q1=[]



    file_path = "loads.txt"
    with open(file_path, 'w') as file:

        logger = scheduler_logger.SchedulerLogger()
        sched = scheduler.ContainerScheduler(logger, q2, q3)
        signal.signal(signal.SIGINT, functools.partial(handle_signal, sched)) # Clean interrupt


        # Discard first measurement, since it is always wrong.
        psutil.cpu_percent(interval=None, percpu=True)
        mc_pid, mc_n_core = init_memcached_config(logger)

        # mc_process = psutil.Process(mc_pid)
        i = 0
        loadLevel = NORMAL

        while True:
            if i == 0:
                sched.print_content_queues()
                file.write("high: " + str(nb_high) + "\n")
                file.write("normal: " + str(nb_normal) + "\n")
            i = (i + 1) % 20

            # mc_utilization = mc_process.cpu_percent() # Does it give the total cpu utilization of memcached?
            cpu_utilizations = psutil.cpu_percent(interval=None, percpu=True)
            cpu_utilization_0 = cpu_utilizations[0] # utilization of core 0
            cpu_utilization_1 = cpu_utilizations[1] # utilization of core 1

            # memcache can run only on core 0
            if cpu_utilization_0 + cpu_utilization_1 < 90 and loadLevel == HIGH: #testé 115, 80
                loadLevel = NORMAL
                # set memcache n_core to 1
                pid, mc_n_core = set_memcached_core(mc_pid, 1, logger)
    
            # memcache needs to be on core 0 and 1
            if cpu_utilization_0 > 55 and loadLevel == NORMAL: #a 35 et 75 ca passe bien 
                loadLevel = HIGH

            if loadLevel == NORMAL:
                #write in file "normal":
                nb_normal += 1
                #write nb normal in file
                
            else:
                #write in file "high":
                nb_high += 1
                
            # if cpu_utilization_0 < 100 and sched.get_core_usage() <= 1:
            #     sched.add(4)

            # elif cpu_utilization_0 < 200 and sched.get_core_usage() <= 2:
            #     sched.add(3)

            # elif cpu_utilization_0 < 300 and sched.get_core_usage() <= 3:
            #     sched.add(2)
            # elif cpu_utilization_0 < 350 and sched.get_core_usage() <= 4:
            #     sched.add(1)

            # elif cpu_utilization_0 > 380:
            #     if mc_utilization > 60:
            #         # reduce to 2 cores
            #         sched.remove(sched.get_core_usage() - 3)
            #     if mc_utilization > 150:
            #         # reduce to 1 core
            #         sched.remove(sched.get_core_usage() - 2)


            sched.reschedule(loadLevel)
            # if we just changed the load from NORMAL to HIGH, set memcache n_core to 2 after rescheduling
            if loadLevel == HIGH and mc_n_core == 1:
                pid, mc_n_core = set_memcached_core(mc_pid, 2, logger)
    
    
            # Remove containers if they are done.
            sched.clean_all_queues()

            # Start containers.
            # sched.SCHEDULE_NEXT()

            if sched.end():
                print("all other jobs have been completed")
                pid, mc_n_core = set_memcached_core(mc_pid, 2, logger)
                # set_memcached_core(mc_pid, 4, logger) # Should we give all core to memcached?
                sleep(62)
                logger.job_end(Job.MEMCACHED)
                logger.end()
                break

            sleep(0.25)


if __name__ == "__main__":
    main()
