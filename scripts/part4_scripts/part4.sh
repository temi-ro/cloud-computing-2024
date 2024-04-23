#!/bin/bash

client_agent() {
    local_script="scripts/part4_scripts/client_agent.sh"
    remote_script="/tmp/client_agent.sh"
    gcloud compute scp --ssh-key-file ~/.ssh/cloud-computing "$local_script" ubuntu@$client_agent_name:$remote_script --zone europe-west3-a

    gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@$client_agent_name --zone europe-west3-a --command "
        chmod +x $remote_script && 
        $remote_script"
}

client_measure() {
    local_script="scripts/part4_scripts/client_measure.sh"
    remote_script="/tmp/client_measure.sh"
    gcloud compute scp --ssh-key-file ~/.ssh/cloud-computing "$local_script" ubuntu@$client_measure_name:$remote_script --zone europe-west3-a

    gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@$client_measure_name --zone europe-west3-a --command "
        chmod +x $remote_script && 
        $remote_script"
}

memcache_server() {
    local_script="scripts/part4_scripts/memcache_server.sh"
    remote_script="/tmp/memcache_server.sh"
    gcloud compute scp --ssh-key-file ~/.ssh/cloud-computing "$local_script" ubuntu@$memcache_server_name:$remote_script --zone europe-west3-a

    gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@$memcache_server_name --zone europe-west3-a --command "
        chmod +x $remote_script && 
        $remote_script"
}

client_agent_name=$(kubectl get nodes -o wide | awk '/client-agent-/{print $1}')
client_measure_name=$(kubectl get nodes -o wide | awk '/client-measure-/{print $1}')
memcache_server_name=$(kubectl get nodes -o wide | awk '/memcache-server-/{print $1}')

memcache_server &
client_measure &
client_agent &
sleep 100