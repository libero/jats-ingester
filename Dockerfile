FROM python:3.7.3-slim as base

ENV AIRFLOW_HOME=/src/airflow

WORKDIR ${AIRFLOW_HOME}

COPY ./requirements ./requirements

RUN pip install -U pip \
    && set -ex \
    && apt-get update -yq \
    && apt-get install -yq --no-install-recommends build-essential \
    && pip install --no-cache-dir -r ./requirements/base.txt \
    && apt-get remove --purge --autoremove -yq build-essential \
    && rm -rf ~/.cache/* \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

FROM base as dev

ENV PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir -r ./requirements/dev.txt \
    && rm -rf ~/.cache/* \
    && rm -rf /tmp/*

EXPOSE 8080

CMD airflow initdb && airflow webserver -p 8080 && airflow scheduler
