#!/bin/bash

# Launch memcached using Kubernetes
kubectl create -f memcache-t1-cpuset.yaml
kubectl expose pod some-memcached --name some-memcached-11211 --type LoadBalancer --port 11211 --protocol TCP

# Wait for memcached to be ready
echo "Waiting for memcached to be ready..."
sleep 60

kubectl get service some-memcached-11211

# Get service information
memcached_service_info=$(kubectl get pods -o wide)

# Extract MEMCACHED_IP
MEMCACHED_IP=$(echo "$memcached_service_info" | awk '{print $6}' | tail -n 1)


# Display service information
echo "Service information:"
echo "$memcached_service_info"
echo "MEMCACHED_IP: $MEMCACHED_IP"

set password [lindex $argv 0]
spawn sudo ls
expect "password for"
send "$password\r"
expect eof

# Generate commands for client-agent
client_commands(){
    ~/google-cloud/google-cloud-sdk/bin/gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-agent-dhhh --zone europe-west3-a << EOF
    pwd &&
    rm -r memcache-perf &&
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
    echo "Client agent is ready!" &&
    ./mcperf -T 16 -A &&
    echo "Client is done!"
EOF
}

measure_commands(){
    ~/google-cloud/google-cloud-sdk/bin/gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@client-agent-dhhh --zone europe-west3-a << EOF
    echo "Starting client measure..." &&
    pwd &&
    rm -r memcache-perf &&
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
    echo "Client measure is ready!" &&
    # Load memcached database &&
    ./mcperf -s $MEMCACHED_IP --loadonly &&
    ./mcperf -s $MEMCACHED_IP -a $INTERNAL_AGENT_IP --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 5 -w 2 --scan 5000:10000:5000 | tee mcperf-output.txt &&
    echo "Client measure is done!"
EOF
}

echo "Launching client-agent and client-measure..."

client_commands &
measure_commands &

wait
echo "All done!"















# # Compile mcperf memcached load generator
# echo "Compiling mcperf..."
# sudo apt-get update
# sudo apt-get install libevent-dev libzmq3-dev git make g++ --yes
# sudo cp /etc/apt/sources.list /etc/apt/sources.list~
# sudo sed -Ei 's/^# deb-src /deb-src /' /etc/apt/sources.list
# sudo apt-get update
# sudo apt-get build-dep memcached --yes
# cd && git clone https://github.com/shaygalon/memcache-perf.git
# cd memcache-perf
# git checkout 0afbe9b
# make

# # Run mcperf on client-agent and client-measure VMs
# echo "Launching mcperf on client-agent with 16 threads..."
# ./mcperf -T 16 -A &

# echo "Launching mcperf on client-measure..."
# # Get internal IP of client-agent node
# INTERNAL_AGENT_IP=$(kubectl get nodes -o wide | awk '{print $7}' | tail -n 1)
# echo "INTERNAL_AGENT_IP: $INTERNAL_AGENT_IP"

# # Load memcached database
# ./mcperf -s $MEMCACHED_IP --loadonly

# # Query memcached with increasing throughput
# ./mcperf -s $MEMCACHED_IP -a $INTERNAL_AGENT_IP --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 5 -w 2 --scan 5000:55000:5000
