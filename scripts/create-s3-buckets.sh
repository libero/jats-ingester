#!/bin/sh

set -e

# Executable that waits for a port at an address to be open.
# For further details go to: https://github.com/ufoscout/docker-compose-wait
/wait

# create s3 buckets on localstack
awslocal s3 mb s3://dev-jats-ingester-incoming
awslocal s3 mb s3://dev-jats-ingester-expanded
awslocal s3 mb s3://dev-jats-ingester-logs

# copy contents of tests/assets to incoming bucket
awslocal s3 cp --recursive ./assets/ s3://dev-jats-ingester-incoming
