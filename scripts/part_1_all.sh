#!/bin/bash
set -o xtrace

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
measure_commands_index1() {
    i = $1
    #define 3 file names called mcperf-output-i.txt
    file_name_1 = "mcperf-output-" + $i + "_0.txt"
    file_name_2 = "mcperf-output-" + $i + "_1.txt"
    file_name_3 = "mcperf-output-" + $i + "_2.txt"
    ~/google-cloud/google-cloud-sdk/bin/gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@$measure_name --zone europe-west3-a --command "
        cd &&
        cd memcache-perf &&
        echo 'Setup complete on client-measure.' &&
        sleep 10 &&
        echo 'Sleep done!' &&
        ./mcperf -s $MEMCACHED_IP --loadonly &&
        ./mcperf -s $MEMCACHED_IP -a $INTERNAL_AGENT_IP --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 5 -w 2 --scan 5000:55000:5000 | tee $file_name_1 &&
        sleep 10 &&
        echo 'Sleep done!' &&
        ./mcperf -s $MEMCACHED_IP --loadonly &&
        ./mcperf -s $MEMCACHED_IP -a $INTERNAL_AGENT_IP --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 5 -w 2 --scan 5000:55000:5000 | tee $file_name_2 &&
        sleep 10 &&
        echo 'Sleep done!' &&
        ./mcperf -s $MEMCACHED_IP --loadonly &&
        ./mcperf -s $MEMCACHED_IP -a $INTERNAL_AGENT_IP --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 5 -w 2 --scan 5000:55000:5000 | tee $file_name_3 &&
        echo 'Happy :)'
    "
}

measure_commands_index0() {
    i = $1
    #define 3 file names called mcperf-output-i.txt
    file_name_1 = "mcperf-output-" + $i + "_0.txt"
    file_name_2 = "mcperf-output-" + $i + "_1.txt"
    file_name_3 = "mcperf-output-" + $i + "_2.txt"
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
        ./mcperf -s $MEMCACHED_IP -a $INTERNAL_AGENT_IP --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 5 -w 2 --scan 5000:55000:5000 | tee $file_name_1 &&
        sleep 10 &&
        echo 'Sleep done!' &&
        ./mcperf -s $MEMCACHED_IP --loadonly &&
        ./mcperf -s $MEMCACHED_IP -a $INTERNAL_AGENT_IP --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 5 -w 2 --scan 5000:55000:5000 | tee $file_name_2 &&
        sleep 10 &&
        echo 'Sleep done!' &&
        ./mcperf -s $MEMCACHED_IP --loadonly &&
        ./mcperf -s $MEMCACHED_IP -a $INTERNAL_AGENT_IP --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 5 -w 2 --scan 5000:55000:5000 | tee $file_name_3 &&
        echo 'Happy :)'
    "
}



#loop over all interferences : 
benchmarks=("troll" "ibench-cpu" "ibench-l1d" "ibench-l1i" "ibench-l2" "ibench-llc" "ibench-membw")
index_i=0
for benchmark in "${benchmarks[@]}"; do
    #if i=0 create cluster
    if [ $index_i -eq 0 ]; then
        PROJECT=`~/google-cloud/google-cloud-sdk/bin/gcloud config get-value project`
        kops create -f part1.yaml
        kops create secret --name part1.k8s.local sshpublickey admin -i ~/.ssh/cloud-computing.pub
        kops update cluster --name part1.k8s.local --yes --admin
        kops validate cluster --wait 10m

        #create load and memcached
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

        #do the client and measure commands
        client_commands &
        measure_commands_index0 $index_i &
        sleep 300
        echo "All done!"
    fi


    #if i!=0 introduce interferance :
    if [ $index_i -ne 0 ]; then
        echo "get names" 
         # Run the kubectl command and extract the node names
        agent_name=$(kubectl get nodes -o wide | awk '/client-agent-/{print $1}')
        measure_name=$(kubectl get nodes -o wide | awk '/client-measure-/{print $1}')
        # Extract the required parts from the node names
        # extracted_names=$(echo "$node_names" | awk -F'-' '{print $(NF-1)}')
        # Get MEMCACHED_IP dynamically
        MEMCACHED_IP=$(kubectl get pod some-memcached -o jsonpath="{.status.podIP}")

        INTERNAL_AGENT_IP=$(kubectl get nodes -o wide | awk -v agent="$agent_name" '$1 ~ agent {print $6}')
        echo "INTERNAL_AGENT_IP: $INTERNAL_AGENT_IP"

        # Display MEMCACHED_IP
        echo "MEMCACHED_IP: $MEMCACHED_IP"


        echo "Introducing interference..."
        kubectl create -f interference/ibench-cpu.yaml
        #create interference/$benchmark.yaml
        yml_file = "interference/" + $benchmark + ".yaml"
        kubectl create -f $yml_file
        sleep 60

        measure_commands_index1 $index_i &
        sleep 300
        echo "All done!"
        echo delete benchmark
        kubectl delete pods $benchmark
    fi

    echo "Cluster created successfully!"
    ((index_i++))
done



echo "Launching client-agent and client-measure..."
client_commands &
measure_commands &

wait
echo "All done!"
set +o xtrace