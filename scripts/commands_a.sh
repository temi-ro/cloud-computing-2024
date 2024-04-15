#!/bin/bash
set -o xtrace
echo 'Starting setup on client-agent...' 
sudo sh -c "echo deb-src http://europe-west3.gce.archive.ubuntu.com/ubuntu/ jammy main \restricted >> /etc/apt/sources.list" 
sudo apt-get update 
sudo apt-get install libevent-dev libzmq3-dev git make g++ --yes 
sudo apt-get build-dep memcached --yes 
git clone https://github.com/eth-easl/memcache-perf-dynamic.git 
cd memcache-perf-dynamic 
make 
echo 'Setup complete on client-agent a.' 
./mcperf -T 2 -A 
echo 'Client agent a is done!'
set +o xtrace