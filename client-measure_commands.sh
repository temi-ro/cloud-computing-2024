#!/bin/bash

# Load memcached database
./mcperf -s 34.107.67.81 --loadonly

# Query memcached with increasing throughput
./mcperf -s 34.107.67.81 -a  --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 5 -w 2 --scan 5000:55000:5000
