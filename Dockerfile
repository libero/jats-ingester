FROM python:3.7.3-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV AIRFLOW_HOME=/src/airflow

WORKDIR /src/app

COPY ./requirements ./requirements

RUN pip install -U pip \
    && set -ex \
    && apt-get update -yq \
    && apt-get install -yq --no-install-recommends build-essential \
    && pip install --no-cache-dir -r ./requirements/base.txt \
    && apt-get remove --purge --autoremove -yq build-essential \
    && rm -rf ~/.cache/* \
    && rm -rf /tmp/*

ARG env
RUN pip install --no-cache-dir -r ./requirements/${env}.txt \
    && rm -rf /tmp/*

EXPOSE 8080

CMD airflow initdb && airflow webserver -p 8080 && airflow scheduler
