#!/bin/sh

set -e

# Executable that waits for a port at an address to be open.
# For further details go to: https://github.com/ufoscout/docker-compose-wait
/wait

# create s3 buckets
aws --endpoint-url http://s3:9000 s3 mb s3://dev-jats-ingester-incoming
aws --endpoint-url http://s3:9000 s3 mb s3://dev-jats-ingester-expanded
aws --endpoint-url http://s3:9000 s3 mb s3://dev-jats-ingester-completed-tasks
aws --endpoint-url http://s3:9000 s3 mb s3://dev-jats-ingester-logs

# copy contents of tests/assets to incoming bucket
# aws --endpoint-url http://s3:9000 s3 cp --recursive ./assets/ s3://dev-jats-ingester-incoming

aws --endpoint-url http://s3:9000 s3 cp ./assets/elife-00666-vor-r1.zip s3://dev-jats-ingester-incoming
