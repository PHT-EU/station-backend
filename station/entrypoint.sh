#!/bin/sh

set -e

if [ "$1" = 'app' ];
then
  python /home/run_station.py

fi

if [ "$1" = 'jupyter' ]; then
  python /home/run_station.py &
  exec jupyter lab

fi

exec "$@"