FROM python:3.7.3-slim as base

ENV AIRFLOW_HOME=/airflow
ENV AIRFLOW__CORE__DAGS_FOLDER=${AIRFLOW_HOME}/dags
ENV AIRFLOW__CORE__BASE_LOG_FOLDER=${AIRFLOW_HOME}/logs
ENV AIRFLOW__CORE__EXECUTOR=CeleryExecutor
ENV AIRFLOW__CORE__PLUGINS_FOLDER=${AIRFLOW_HOME}/plugins
ENV AIRFLOW__CORE__CHILD_PROCESS_LOG_DIRECTORY=${AIRFLOW_HOME}/logs/scheduler

ENV AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://postgres:example@db/airflow-db
ENV AIRFLOW__CORE__LOAD_EXAMPLES=false
ENV AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=false

ENV AIRFLOW__CELERY__BROKER_URL=sqla+${AIRFLOW__CORE__SQL_ALCHEMY_CONN}
ENV AIRFLOW__CELERY__RESULT_BACKEND=db+${AIRFLOW__CORE__SQL_ALCHEMY_CONN}

WORKDIR ${AIRFLOW_HOME}

COPY ./requirements.txt ./

RUN pip install -U pip \
    && set -ex \
    && apt-get update -yq \
    && apt-get install -yq --no-install-recommends build-essential \
    && useradd -s /bin/bash -d ${AIRFLOW_HOME} airflow \
    && pip install --no-cache-dir -r ./requirements.txt \
    && apt-get remove --purge --autoremove -yq build-essential \
    && rm -rf ~/.cache/* \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*

COPY ./dags ${AIRFLOW__CORE__DAGS_FOLDER}

RUN chown -R airflow: .

FROM base as dev

ENV PYTHONUNBUFFERED=true
ENV PYTHONDONTWRITEBYTECODE=true

ENV AIRFLOW__CORE__EXPOSE_CONFIG=true

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.5.0/wait /wait
RUN chmod +x /wait

COPY airflow_healthcheck.py airflow_entrypoint.sh ./

USER airflow
ENTRYPOINT ["./airflow_entrypoint.sh"]
