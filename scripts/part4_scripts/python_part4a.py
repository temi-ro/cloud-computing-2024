import threading
import subprocess

# Run this script to:
# 1. Run memcached with the specified number of cores
# 2. Run a script to monitor CPU utilisation

def run_file1():
    subprocess.run(["python3", "run_memcached.py"])

def run_file2():
    subprocess.run(["python3", "cpu_utilisation.py"])

if __name__ == "__main__":
    thread1 = threading.Thread(target=run_file1)
    thread2 = threading.Thread(target=run_file2)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()
