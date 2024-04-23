
#!/bin/bash

set -o xtrace

# Define function to run commands on client-agent a VM
client_commands_a() {
    local_script="scripts/commands_a.sh"
    remote_script="/tmp/commands_a.sh"
    gcloud compute scp --ssh-key-file ~/.ssh/cloud-computing "$local_script" ubuntu@$agent_name_a:$remote_script --zone europe-west3-a

    gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@$agent_name_a --zone europe-west3-a --command "
        chmod +x $remote_script && 
        $remote_script
    "
}

# Define function to run commands on client-agent b VM
client_commands_b() {
    local_script="scripts/commands_b.sh"
    remote_script="/tmp/commands_b.sh"
    gcloud compute scp --ssh-key-file ~/.ssh/cloud-computing "$local_script" ubuntu@$agent_name_b:$remote_script --zone europe-west3-a

    gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@$agent_name_b --zone europe-west3-a --command "
        chmod +x $remote_script && 
        $remote_script
    "
}

# Define function to run commands on client-measure VM
measure_commands_index1() {
    gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@$measure_name --zone europe-west3-a --command "
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
    # Name of the script to create
    # Name of the script to create
    file_name_1="MDR.txt"
    SCRIPT_NAME="scripts/commands.sh"

    # Create the script with the specified name
    echo "#!/bin/bash" > $SCRIPT_NAME
    echo "echo 'Starting setup on client-measure...'" >> $SCRIPT_NAME
    echo "sudo sh -c \"echo deb-src http://europe-west3.gce.archive.ubuntu.com/ubuntu/ jammy main restricted >> /etc/apt/sources.list\"" >> $SCRIPT_NAME
    echo "sudo apt-get update" >> $SCRIPT_NAME
    echo "sudo apt-get install libevent-dev libzmq3-dev git make g++ --yes" >> $SCRIPT_NAME
    echo "sudo apt-get build-dep memcached --yes" >> $SCRIPT_NAME
    echo "git clone https://github.com/eth-easl/memcache-perf-dynamic.git" >> $SCRIPT_NAME
    echo "cd memcache-perf-dynamic" >> $SCRIPT_NAME
    echo "make" >> $SCRIPT_NAME
    echo "echo 'Setup complete on client-measure.'" >> $SCRIPT_NAME
    echo "sleep 10" >> $SCRIPT_NAME
    echo "echo 'Sleep done!'" >> $SCRIPT_NAME
    echo "./mcperf -s $MEMCACHED_IP --loadonly" >> $SCRIPT_NAME
    echo "./mcperf -s $MEMCACHED_IP -a $INTERNAL_AGENT_A_IP -a $INTERNAL_AGENT_B_IP --noload -T 6 -C 4 -D 4 -Q 1000 -c 4 -t 10 --scan 30000:30500:5 | tee $file_name_1" >> $SCRIPT_NAME
    echo "echo 'Happy :)'" >> $SCRIPT_NAME

    local_script="scripts/commands.sh"
    remote_script="/tmp/script_name.sh"
    gcloud compute scp --ssh-key-file ~/.ssh/cloud-computing "$local_script" ubuntu@$measure_name:$remote_script --zone europe-west3-a

    gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@$measure_name --zone europe-west3-a --command "
        chmod +x $remote_script && 
        $remote_script
    "
}





export KOPS_STATE_STORE="gs://cca-eth-2024-group-020-aaigueperse/"
PROJECT=`gcloud config get-value project`
#PROJECT=`~/google-cloud/google-cloud-sdk/bin/gcloud config get-value project`
kops create -f part3.yaml
#kops create secret --name part3.k8s.local sshpublickey admin -i ~/.ssh/cloud-computing.pub
#kops create secret --name part3.k8s.local sshpublickey admin -i ~/.ssh/cloud-computing.pub
kops update cluster --name part3.k8s.local --yes --admin
kops validate cluster --wait 15m
kubectl get nodes -o wide
echo "VOILAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

#create load and memcached
# Run the kubectl command and extract the node names
agent_name_a=$(kubectl get nodes -o wide | awk '/client-agent-a-/{print $1}')
agent_name_b=$(kubectl get nodes -o wide | awk '/client-agent-b-/{print $1}')
measure_name=$(kubectl get nodes -o wide | awk '/client-measure-/{print $1}')
# Extract the required parts from the node names
# extracted_names=$(echo "$node_names" | awk -F'-' '{print $(NF-1)}')

# Print the extracted names
echo "Agent name: $agent_name_a"
echo "Agent name: $agent_name_b"
echo "Measure name: $measure_name"

kubectl create -f part3/memcache-t1-cpuset.yaml
kubectl expose pod some-memcached --name some-memcached-11211 --type LoadBalancer --port 11211 --protocol TCP

# Wait for memcached to be ready
echo "Waiting for memcached to be ready..."
sleep 60

kubectl get service some-memcached-11211

# Get MEMCACHED_IP dynamically
MEMCACHED_IP=$(kubectl get pod some-memcached -o jsonpath="{.status.podIP}")

INTERNAL_AGENT_A_IP=$(kubectl get nodes -o wide | awk -v agent="$agent_name_a" '$1 ~ agent {print $6}')
INTERNAL_AGENT_B_IP=$(kubectl get nodes -o wide | awk -v agent="$agent_name_b" '$1 ~ agent {print $6}')
echo "INTERNAL_AGENT_IP: $INTERNAL_AGENT_A_IP"
echo "INTERNAL_AGENT_IP: $INTERNAL_AGENT_B_IP"

# Display MEMCACHED_IP
echo "MEMCACHED_IP: $MEMCACHED_IP"

#do the client and measure commands
client_commands_a &
client_commands_b &
measure_commands_index0 $index_i &
sleep 100
echo "Index 0 done!"

# Run initial jobs: 
kubectl create -f part3/parsec-freqmine.yaml
kubectl create -f part3/parsec-radix.yaml  
kubectl create -f part3/parsec-dedup.yaml
kubectl create -f part3/parsec-ferret.yaml
kubectl create -f part3/parsec-canneal.yaml


# At Each tick
while true
do
    # For each dependency check if job completed
    # Record job status
    kubectl get jobs -o wide > temporary_file.raw
    ferret=`kubectl get jobs -o wide | grep parsec-ferret | awk '{print $2}'`
    freqmine=`kubectl get jobs -o wide | grep parsec-freqmine | awk '{print $2}'`
    blackscholes=`kubectl get jobs -o wide | grep parsec-blackscholes | awk '{print $2}'`
    dedup=`kubectl get jobs -o wide | grep parsec-dedup | awk '{print $2}'`
    canneal=`kubectl get jobs -o wide | grep parsec-canneal | awk '{print $2}'`
    vips=`kubectl get jobs -o wide | grep parsec-vips | awk '{print $2}'`
    radix=`kubectl get jobs -o wide | grep parsec-radix | awk '{print $2}'`
    
    incomplete="0/1"
    complete="1/1"

    

    #  dedup complete => vips
    if [ "$dedup" == "$complete" ]; then
        kubectl create -f part3/parsec-vips.yaml
        echo 'create vips '
    fi

    #  radix complete => blackscholes
    if [ "$radix" == "$complete" ]; then
        kubectl create -f part3/parsec-blackscholes.yaml
        echo 'create blackscholes '
    fi

    # Check for end of all jobs to deploy results 
    if [ "$ferret" == "$complete" ] && [ "$freqmine" == "$complete" ] && [ "$canneal"=="$complete" ] && [ "$dedup"=="$complete" ] && [ "$blackscholes"=="$complete" ] && [ "$vips"=="$complete" ] && [ "$radix"=="$complete" ]; then
		kubectl get pods -o json > results1.json
		python3 get_time.py results1.json
		break
    fi

    sleep 1

done


wait
echo "All done!"

# echo "Launching client-agent and client-measure..."
# client_commands &
# measure_commands &

# wait
set +o xtrace
