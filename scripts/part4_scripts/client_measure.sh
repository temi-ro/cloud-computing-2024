#!/bin/bash
set -o xtrace
echo 'Starting setup on client-measure...' 
sudo sh -c "echo deb-src http://europe-west3.gce.archive.ubuntu.com/ubuntu/ jammy main \restricted >> /etc/apt/sources.list" 
sudo apt-get update 
sudo apt-get install libevent-dev libzmq3-dev git make g++ --yes 
sudo apt-get build-dep memcached --yes 
git clone https://github.com/eth-easl/memcache-perf-dynamic.git 
cd memcache-perf-dynamic 
make 
echo 'Setup complete on client-measure.' 

# Get the internal IPs
agent_name=$(kubectl get nodes -o wide | awk '/client-agent-/{print $1}')
memcache_server=$(kubectl get nodes -o wide | awk '/memcache-server-/{print $1}')

INTERNAL_AGENT_IP=$(kubectl get nodes -o wide | awk -v agent="$agent_name" '$1 ~ agent {print $6}')
INTERNAL_MEMCACHED_IP=$(kubectl get nodes -o wide | awk -v memcache="$memcache_server" '$1 ~ memcache {print $6}')

./mcperf -s $INTERNAL_MEMCACHED_IP --loadonly
./mcperf -s $INTERNAL_MEMCACHED_IP -a $INTERNAL_AGENT_IP --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 10 --qps_interval 2 --qps_min 5000 --qps_max 100000 | tee client_measure_log.txt
echo 'Client-measure is done!'

set +o xtrace