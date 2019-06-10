#!/bin/bash
set -e

function finish {
    docker-compose logs
    docker-compose down --volumes
}

trap finish EXIT

docker-compose up -d
.scripts/docker/wait-healthy.sh jatsingester_airflow_webserver_1 60
./scripts/airflow-status-check.sh localhost:8080
