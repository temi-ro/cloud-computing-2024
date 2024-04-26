# setup:

## CHANGE tmessmer
export KOPS_STATE_STORE="gs://cca-eth-2024-group-020-tmessmer/" 
PROJECT='gcloud config get-value project'
kops create -f part4.yaml

kops update cluster --name part4.k8s.local --yes --admin
kops validate cluster --wait 10m

# client_agent:
gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@[name] --zone europe-west3-a

sudo sh -c "echo deb-src http://europe-west3.gce.archive.ubuntu.com/ubuntu/ jammy main \restricted >> /etc/apt/sources.list" 
sudo apt-get update 
sudo apt-get install libevent-dev libzmq3-dev git make g++ --yes 
sudo apt-get build-dep memcached --yes 
git clone https://github.com/eth-easl/memcache-perf-dynamic.git 
cd memcache-perf-dynamic 
make 
echo 'Setup complete on client-agent.' 
./mcperf -T 16 -A 

# client_measure
gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@[name] --zone europe-west3-a

sudo sh -c "echo deb-src http://europe-west3.gce.archive.ubuntu.com/ubuntu/ jammy main \restricted >> /etc/apt/sources.list" 
sudo apt-get update 
sudo apt-get install libevent-dev libzmq3-dev git make g++ --yes 
sudo apt-get build-dep memcached --yes 
git clone https://github.com/eth-easl/memcache-perf-dynamic.git 
cd memcache-perf-dynamic 
make 
echo 'Setup complete on client-measure.' 

./mcperf -s $INTERNAL_MEMCACHED_IP --loadonly
## Execute just before running the python file
./mcperf -s $INTERNAL_MEMCACHED_IP -a $INTERNAL_AGENT_IP --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 1800 --qps_interval 10 --qps_min 5000 --qps_max 100000 | tee client_measure_log.txt

# memecache:
gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@[name] --zone europe-west3-a
sudo apt update
sudo apt install -y memcached libmemcached-tools

sudo systemctl status memcached

## change -m 1024 AND -l <IP_INTERNAL_MEMECACHE> AND -t 2
sudo nano /etc/memcached.conf

sudo systemctl restart memcached

sudo apt install -y python3-pip
sudo pip3 install psutil
sudo pip3 install docker

## Install pip and psutil and docker
sudo apt install docker.io

sudo docker pull anakli/cca:parsec_blackscholes
sudo docker pull anakli/cca:parsec_canneal
sudo docker pull anakli/cca:parsec_dedup
sudo docker pull anakli/cca:parsec_ferret
sudo docker pull anakli/cca:parsec_freqmine
sudo docker pull anakli/cca:splash2x_radix
sudo docker pull anakli/cca:parsec_vips

## Create all the python files
nano controller.py
nano scheduler.py
nano scheduler_logger.py

sudo python3 controller.py

## To delete containers
sudo docker rm $(sudo docker ps -qa)
