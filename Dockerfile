FROM python:3.7.3-slim as base

# create airflow connection using environment variable
# for more info: # https://airflow.apache.org/howto/connection/index.html#creating-a-connection-with-environment-variables
# A connection id required to send airflow logs remotely
# If the value is empty then default boto settings are used or, you can set a
# different location to send logs. To do this value must be a URI followed by
# a query string of parameters like so: http://localstack:4572?host=http://localstack:4572
ENV AIRFLOW_CONN_REMOTE_LOGS=""
ENV AIRFLOW_HOME=/airflow

WORKDIR ${AIRFLOW_HOME}

COPY requirements/ requirements/

RUN pip install -U pip \
    && set -ex \
    && apt-get update -yq \
    && apt-get install -yq --no-install-recommends \
        build-essential \
        libmagickwand-dev \
    && useradd -s /bin/bash -d ${AIRFLOW_HOME} airflow \
    && pip install --no-cache-dir -r requirements/base.txt \
    && apt-get remove --purge --autoremove -yq build-essential \
    && rm -rf ~/.cache/* \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

COPY ./dags ${AIRFLOW_HOME}/dags

# add maintenance dags
ADD https://raw.githubusercontent.com/teamclairvoyant/airflow-maintenance-dags/master/clear-missing-dags/airflow-clear-missing-dags.py \
    ${AIRFLOW_HOME}/dags/maintenance-dags/airflow-clear-missing-dags.py
ADD https://raw.githubusercontent.com/teamclairvoyant/airflow-maintenance-dags/master/db-cleanup/airflow-db-cleanup.py \
    ${AIRFLOW_HOME}/dags/maintenance-dags/airflow-db-cleanup.py
ADD https://raw.githubusercontent.com/teamclairvoyant/airflow-maintenance-dags/master/kill-halted-tasks/airflow-kill-halted-tasks.py \
    ${AIRFLOW_HOME}/dags/maintenance-dags/airflow-kill-halted-tasks.py

COPY scripts/ scripts/

RUN chown -R airflow: .
USER airflow
ARG revision
LABEL org.opencontainers.image.revision=${revision}


FROM base as dev
USER root

ENV PYTHONUNBUFFERED=true
ENV PYTHONDONTWRITEBYTECODE=true

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.5.0/wait /wait
RUN chmod +x /wait

RUN pip install --no-cache-dir -r requirements/dev.txt \
    && rm -rf /tmp/*

USER airflow
ENTRYPOINT ["./scripts/airflow-entrypoint.sh"]
