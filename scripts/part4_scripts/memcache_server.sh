#!/bin/bash

sudo apt update
sudo apt install -y memcached libmemcached-tools

sleep 30
sudo systemctl status memcached

# Get the internal IP address of the memcached VM
kubectl get nodes -o wide
memcache_server=$(kubectl get nodes -o wide | awk '/memcache-server-/{print $1}')
INTERNAL_IP=$(kubectl get nodes -o wide | awk -v memcache="$memcache_server" '$1 ~ memcache {print $6}')
echo "Internal IP: $INTERNAL_IP"

N_THREADS=4

# Update memcached configuration
sudo sed -i 's/^-m .*/-m 1024/' /etc/memcached.conf
sudo sed -i "s/^-l .*/-l $INTERNAL_IP/" /etc/memcached.conf 
sudo sed -i '/^-t/ d' /etc/memcached.conf  
echo "-t $N_THREADS" 

# Restart memcached service
sudo systemctl restart memcached

# Install pip and psutil and docker
echo "Installing pip and psutil"
sudo apt update
sudo apt install -y python3-pip
sudo pip3 install psutil
sudo pip3 install docker

sudo apt  install docker.io
echo "Docker pulling"
# docker pull
sudo docker pull anakli/cca:parsec_blackscholes
sudo docker pull anakli/cca:parsec_canneal
sudo docker pull anakli/cca:parsec_dedup
sudo docker pull anakli/cca:parsec_ferret
sudo docker pull anakli/cca:parsec_freqmine
sudo docker pull anakli/cca:splash2x_radix
sudo docker pull anakli/cca:parsec_vips