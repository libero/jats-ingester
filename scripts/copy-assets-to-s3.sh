#!/bin/sh

set -e

# Executable that waits for a port at an address to be open.
# For further details go to: https://github.com/ufoscout/docker-compose-wait
/wait

# copy contents of tests/assets to incoming bucket
 aws --endpoint-url http://s3:9000 s3 cp --recursive ./assets/ s3://dev-jats-ingester-incoming
