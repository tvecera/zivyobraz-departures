#!/bin/bash
while true; do
    python ./departures.py -c ./config/departures.yml
    sleep 60
done