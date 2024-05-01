#!/bin/bash

./mcperf -s 10.0.16.4 -a 10.0.16.3 --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 5 --scan 5000:125000:5000 \
| tee /tmp/T2C1_0.txt

./mcperf -s 10.0.16.4 -a 10.0.16.3 --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 5 --scan 5000:125000:5000 \
| tee /tmp/T2C1_1.txt

./mcperf -s 10.0.16.4 -a 10.0.16.3 --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 5 --scan 5000:125000:5000 \
| tee /tmp/T2C1_2.txt
