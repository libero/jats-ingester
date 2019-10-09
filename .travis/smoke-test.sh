#!/bin/bash
set -e

function finish {
    docker-compose logs
    docker-compose down --volumes
}

trap finish EXIT

docker-compose up -d

name=$(docker ps | grep airflow_webserver | awk '{print $1}')
.scripts/docker/wait-healthy.sh $name 60
./scripts/airflow-status-check.sh localhost:8080
