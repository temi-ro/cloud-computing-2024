import subprocess

# Define the IP addresses
MEMCACHED_IP = "100.96.2.3"
INTERNAL_AGENT_IP = "10.0.32.2"

# Define the range of QPS values
qps_range = range(5000, 55001, 5000)

# Function to execute mcperf command and save output to a file
def run_mcperf_command(output_file):
    print("Running mcperf command")
    command = [
        "./mcperf",
        "-s", MEMCACHED_IP,
        "-a", INTERNAL_AGENT_IP,
        "--noload",
        "-T", "16",
        "-C", "4",
        "-D", "4",
        "-Q", "1000",
        "-c", "4",
        "-w", "2",
        "-t", "5",
        "--scan", "5000:55000:5000"
    ]
    # subprocess.run(command)
    with open(output_file, "w") as f:
        print("Writing in file")
        subprocess.run(command, stdout=f, stderr=subprocess.STDOUT)
        print("Done.")

def execute_mcperf_loadonly():
    print("Executing mcperf loadonly")
    command = [
        "./mcperf",
        "-s", MEMCACHED_IP,
        "--loadonly"
    ]
    subprocess.run(command)

def execute():
    print("Test command")
    command = [
        "ls"
    ]
    subprocess.run(command)

if __name__ == "__main__":
    # execute()

    # Perform the computations at least 3 times
    execute_mcperf_loadonly()
    print("Running mcperf")

    for i in range(1, 3):
        print(f"Running mcperf for the part1_{0}_{i}...")
        output_file = f"part1_{0}_{i}.txt"
        run_mcperf_command(output_file)
