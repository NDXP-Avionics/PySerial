#!/bin/bash
cd /home/ndxp/PySerial

source ./bin/activate;

python3 monitor.py &

sleep 1 && python3 logger.py &

wait;