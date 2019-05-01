#!/bin/sh

set -e

# If arguments are not supplied then exit and supply explaination
if [ "$#" -lt 1 ]; then
    echo "Please add the command you would like to run with Airflow."
    exit 1
fi

# Executable that waits for a port at an address to be open.
# For further details go to: https://github.com/ufoscout/docker-compose-wait
/wait

# If the argument supplied is not `initdb` it is assumed that another airflow
# service is running this script.
#
# The airflow webserver and scheduler try to access tables in the db at startup.
# These containers will fail and shutdown if the db has not been initialized.
if [ "$1" != "initdb" ]; then
    # using sleep for simplicity but another solution would be to check if the
    # correct tables are in the db.
    sleep 5
fi

airflow $@
