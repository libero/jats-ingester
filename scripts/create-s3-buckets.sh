#!/bin/sh

set -e

# Executable that waits for a port at an address to be open.
# For further details go to: https://github.com/ufoscout/docker-compose-wait
/wait

awslocal s3 mb s3://dev-jats-ingester-incoming
awslocal s3 mb s3://dev-jats-ingester-expanded
awslocal s3 cp ./elife-00666-vor-r1.zip s3://dev-jats-ingester-incoming
awslocal s3 cp ./elife-36842-vor-r3.zip s3://dev-jats-ingester-incoming
