#!/bin/bash
set -e

function finish {
    docker-compose logs
    docker-compose down --volumes
}

trap finish EXIT

name=$(docker ps | grep airflow_webserver | awk '{print $1}')

docker-compose up -d
.scripts/docker/wait-healthy.sh $name 60
./scripts/airflow-status-check.sh localhost:8080
