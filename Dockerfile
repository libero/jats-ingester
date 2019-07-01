FROM python:3.7.3-slim as base

# create airflow connection using environment variable
# for more info: # https://airflow.apache.org/howto/connection/index.html#creating-a-connection-with-environment-variables
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
COPY scripts/ scripts/

RUN chown -R airflow: .
USER airflow


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
