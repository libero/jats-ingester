#!/bin/bash
set -e

function finish {
    docker-compose logs
    docker-compose down --volumes
}

trap finish EXIT

docker-compose up -d
.scripts/docker/wait-healthy.sh elife-style-content-adapter-prototype_airflow_1
