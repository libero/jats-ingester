#!/bin/sh

set -e

if [ "$#" -lt 1 ]; then
    echo "Please add the command you would like to run with Airflow."
    exit
fi

/wait

if [ "$1" != "initdb" ]; then
    sleep 5
fi

airflow $@
