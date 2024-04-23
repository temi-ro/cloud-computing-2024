#!/bin/bash
echo 'Starting setup on client-measure...'
sudo sh -c "echo deb-src http://europe-west3.gce.archive.ubuntu.com/ubuntu/ jammy main restricted >> /etc/apt/sources.list"
sudo apt-get update
sudo apt-get install libevent-dev libzmq3-dev git make g++ --yes
sudo apt-get build-dep memcached --yes
git clone https://github.com/eth-easl/memcache-perf-dynamic.git
cd memcache-perf-dynamic
make
echo 'Setup complete on client-measure.'
sleep 10
echo 'Sleep done!'
./mcperf -s 100.96.3.2 --loadonly
./mcperf -s 100.96.3.2 -a 10.0.16.2 -a 10.0.16.6 --noload -T 6 -C 4 -D 4 -Q 1000 -c 4 -t 10 --scan 30000:30500:5 | tee MDR.txt
echo 'Happy :)'
