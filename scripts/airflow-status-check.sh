#!/bin/sh

set -e

# If arguments are not supplied then exit and supply explanation
if [ "$#" -lt 1 ]; then
    echo "Please add the Airflow host address and port number. eg. localhost:8080"
    exit 1
fi

status=`curl -s $1/api/experimental/test | jq -r '.status'`

if [ "${status}" != "OK" ]; then
    echo "Airflow status: ${status}"
    exit 2
fi
