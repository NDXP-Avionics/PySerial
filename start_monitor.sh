#!/bin/bash

source ./bin/activate;

./bin/python3 monitor.py &

sleep 1 && ./bin/python3 logger.py &

wait;