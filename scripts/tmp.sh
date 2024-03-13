#!/bin/bash
set -o xtrace

# Run the kubectl command and extract the node names
agent_name=$(kubectl get nodes -o wide | awk '/client-agent-/{print $1}')
measure_name=$(kubectl get nodes -o wide | awk '/client-measure-/{print $1}')
# Extract the required parts from the node names
# extracted_names=$(echo "$node_names" | awk -F'-' '{print $(NF-1)}')

# Print the extracted names
echo "Agent name: $agent_name"
echo "Measure name: $measure_name"

kubectl create -f memcache-t1-cpuset.yaml
kubectl expose pod some-memcached --name some-memcached-11211 --type LoadBalancer --port 11211 --protocol TCP

# Wait for memcached to be ready
echo "Waiting for memcached to be ready..."
sleep 60

kubectl get service some-memcached-11211

# Get MEMCACHED_IP dynamically
MEMCACHED_IP=$(kubectl get pod some-memcached -o jsonpath="{.status.podIP}")

INTERNAL_AGENT_IP=$(kubectl get nodes -o wide | awk -v agent="$agent_name" '$1 ~ agent {print $6}')
echo "INTERNAL_AGENT_IP: $INTERNAL_AGENT_IP"

# Display MEMCACHED_IP
echo "MEMCACHED_IP: $MEMCACHED_IP"

# Define function to run commands on client-agent VM
client_commands() {
    ~/google-cloud/google-cloud-sdk/bin/gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@$agent_name --zone europe-west3-a --command "
        echo 'Starting setup on client-agent...' &&
        sudo apt-get update &&
        sudo apt-get install libevent-dev libzmq3-dev git make g++ --yes &&
        sudo cp /etc/apt/sources.list /etc/apt/sources.list~ &&
        sudo sed -Ei 's/^# deb-src /deb-src /' /etc/apt/sources.list &&
        sudo apt-get update &&
        sudo apt-get build-dep memcached --yes &&
        cd && git clone https://github.com/shaygalon/memcache-perf.git &&
        cd memcache-perf &&
        git checkout 0afbe9b &&
        make &&
        echo 'Setup complete on client-agent.' &&
        ./mcperf -T 16 -A &&
        echo 'Client agent is done!'
    "
}

# Define function to run commands on client-measure VM
measure_commands() {
    ~/google-cloud/google-cloud-sdk/bin/gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@$measure_name --zone europe-west3-a --command "
        echo 'Starting setup on client-measure...' &&
        sudo apt-get update &&
        sudo apt-get install libevent-dev libzmq3-dev git make g++ --yes &&
        sudo cp /etc/apt/sources.list /etc/apt/sources.list~ &&
        sudo sed -Ei 's/^# deb-src /deb-src /' /etc/apt/sources.list &&
        sudo apt-get update &&
        sudo apt-get build-dep memcached --yes &&
        cd && git clone https://github.com/shaygalon/memcache-perf.git &&
        cd memcache-perf &&
        git checkout 0afbe9b &&
        make &&
        echo 'Setup complete on client-measure.' &&
        sleep 10 &&
        echo 'Sleep done!' &&
        ./mcperf -s $MEMCACHED_IP --loadonly &&
        ./mcperf -s $MEMCACHED_IP -a $INTERNAL_AGENT_IP --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 5 -w 2 --scan 5000:55000:5000 | tee mcperf-output.txt &&
        echo 'Happy :)'
    "
}

echo "Launching client-agent and client-measure..."
client_commands &
measure_commands &

wait
echo "All done!"
set +o xtrace